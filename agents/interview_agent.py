"""
Unified Interview Agent - Handles both self-intro and experience stages
Uses LiveKit Agents SDK v1.3+ with AgentServer and AgentSession
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional
from livekit import agents, rtc
from livekit.agents import AgentServer, WorkerOptions
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit.plugins.openai import STT, TTS
import yaml

from agents.stage_manager import StageManager, InterviewStage
from agents.ollama_llm import OllamaLLM

logger = logging.getLogger(__name__)


class InterviewAssistant(Agent):
    """Interview agent that conducts mock interviews"""
    
    def __init__(self, stage_manager: StageManager):
        super().__init__(
            instructions="""You are a professional interview assistant conducting a mock interview.
            You are friendly, professional, and help candidates practice their interview skills.
            Your responses are concise, natural, and conversational.
            You ask follow-up questions to understand the candidate better.
            You transition smoothly between interview stages."""
        )
        self.stage_manager = stage_manager
        self.conversation_history = []
        self.follow_up_count = 0
        self.room_id = None

    async def save_to_transcript(self, role: str, content: str):
        """Save message to Redis transcript"""
        if not self.stage_manager.redis_client or not self.room_id:
            return
        
        try:
            import json
            from datetime import datetime
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            transcript_key = f"interview:{self.room_id}:transcript"
            await self.stage_manager.redis_client.rpush(transcript_key, json.dumps(message))
            await self.stage_manager.redis_client.expire(transcript_key, 86400)  # 24 hours
        except Exception as e:
            logger.error(f"Error saving to transcript: {e}")


# Create AgentServer instance
# agent_name is set via LIVEKIT_AGENT_NAME environment variable in docker-compose.yml
server = AgentServer()


@server.rtc_session()
async def interview_agent(ctx: agents.JobContext):
    """Main entry point for interview agent using new AgentServer pattern"""
    try:
        room_sid = ctx.room.sid  # sid is a property, not a method
        logger.info(f"🎯 Job received! Room: {ctx.room.name}, Job ID: {ctx.job.id}, Room SID: {room_sid}")
    except Exception as e:
        logger.error(f"❌ Error getting room SID: {e}", exc_info=True)
        raise
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Connect to Redis - use environment variables directly
    import redis.asyncio as redis
    import os
    
    # Get from environment (set by docker-compose) or use defaults
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    redis_password = os.getenv("REDIS_PASSWORD", "")
    
    if redis_password:
        redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
    else:
        redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
    
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialize stage manager
    room_sid = ctx.room.sid  # sid is a property, not a method
    stage_manager = StageManager(redis_client=redis_client, config_path=config_path)
    await stage_manager.initialize(room_sid)
    
    # Initialize Ollama LLM
    llm_config = config.get("llm", {})
    ollama_llm = OllamaLLM(
        model=llm_config.get("model", "gpt-oss:120b-cloud"),  # Use your actual model name
        base_url=llm_config.get("base_url", "http://host.docker.internal:11434")
    )
    
    # Create assistant agent
    assistant = InterviewAssistant(stage_manager)
    assistant.room_id = room_sid
    
    # Set up event handlers to capture conversation
    async def on_user_speech(text: str):
        """Capture user speech"""
        if text:
            logger.info(f"👤 User said: {text}")
            assistant.conversation_history.append({"role": "user", "content": text})
            await assistant.save_to_transcript("user", text)
    
    async def on_agent_speech(text: str):
        """Capture agent speech"""
        if text:
            logger.info(f"🤖 Agent said: {text}")
            assistant.conversation_history.append({"role": "assistant", "content": text})
            await assistant.save_to_transcript("assistant", text)
    
    # Create AgentSession with Ollama LLM
    # IMPORTANT: STT and TTS are REQUIRED for voice interaction!
    # Without STT: Agent cannot hear/transcribe your speech
    # Without TTS: Agent cannot speak responses back
    # 
    # Option 1: Use OpenAI STT/TTS (requires OPENAI_API_KEY in .env)
    # Option 2: Use other providers (Deepgram, Azure, etc.)
    # Option 3: For testing, you can use OpenAI's free tier
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if openai_api_key:
        logger.info("✅ Using OpenAI STT and TTS")
        session = AgentSession(
            vad=silero.VAD.load(),
            stt=STT(),  # OpenAI STT - transcribes your speech
            llm=ollama_llm,
            tts=TTS(),  # OpenAI TTS - speaks responses
            allow_interruptions=True,
        )
    else:
        logger.warning("⚠️  No OPENAI_API_KEY found! Agent will NOT be able to hear or speak.")
        logger.warning("   Add OPENAI_API_KEY to .env file for voice interaction.")
        logger.warning("   Without STT/TTS: Agent can only detect voice activity, not understand speech.")
        # AgentSession without STT/TTS - will only detect voice but not transcribe or speak
        session = AgentSession(
            vad=silero.VAD.load(),
            llm=ollama_llm,
            allow_interruptions=True,
        )
    
    try:
        logger.info("📡 Starting AgentSession...")
        await session.start(
            room=ctx.room,
            agent=assistant,
        )
        logger.info("✅ AgentSession started successfully - tracks should be publishing now")
    except Exception as e:
        logger.error(f"❌ Error starting AgentSession: {e}", exc_info=True)
        raise
    
    # Start the stage management loop
    asyncio.create_task(run_stage_loop(session, stage_manager, assistant))
    
    logger.info("🎉 Agent fully started and running!")
    
    # Wait for interview to complete
    try:
        while True:
            current_stage = await stage_manager.get_current_stage()
            if current_stage == InterviewStage.END:
                break
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Agent interrupted")
    finally:
        try:
            await session.aclose()
            logger.info("Agent session closed")
        except Exception as e:
            logger.error(f"Error closing agent session: {e}")


async def run_stage_loop(session: AgentSession, stage_manager: StageManager, assistant: InterviewAssistant):
    """Event loop for handling stages and transitions"""
    await asyncio.sleep(1)  # Wait for connection to stabilize
    
    while True:
        try:
            current_stage = stage_manager.get_stage()
            if current_stage == InterviewStage.SELF_INTRO.value:
                await handle_self_intro(session, stage_manager, assistant)
            elif current_stage == InterviewStage.EXPERIENCE.value:
                await handle_experience(session, stage_manager, assistant)
            elif current_stage == InterviewStage.END.value:
                await session.generate_reply(user_input="Thank you! The interview is complete.")
                break
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error in stage loop: {e}")
            await asyncio.sleep(1)


async def handle_self_intro(session: AgentSession, stage_manager: StageManager, assistant: InterviewAssistant):
    """Handle self-introduction stage"""
    if not stage_manager.flag_intro_start:
        stage_manager.flag_intro_start = True
        greeting = "Hello! I'm conducting your interview today. To start, could you tell me a bit about yourself - your background, what you're passionate about, and what brings you here today?"
        await session.generate_reply(user_input=greeting)
        await assistant.save_to_transcript("assistant", greeting)
        logger.info("Self-intro stage started")
        
        stage_config = stage_manager.config.get("stages", {}).get("self_intro", {})
        fallback_timeout = stage_config.get("fallback_timeout_seconds", 45)
        await asyncio.sleep(fallback_timeout)
        
        if stage_manager.get_stage() == InterviewStage.SELF_INTRO.value:
            logger.info(f"Self-intro fallback timer triggered after {fallback_timeout}s")
            await stage_manager.transition_to_next()


async def handle_experience(session: AgentSession, stage_manager: StageManager, assistant: InterviewAssistant):
    """Handle experience stage"""
    if not stage_manager.flag_exp_start:
        stage_manager.flag_exp_start = True
        transition_msg = "Let's dive into your past experience. Can you tell me about a project you're particularly proud of? What was your role, and what challenges did you face?"
        await session.generate_reply(user_input=transition_msg)
        await assistant.save_to_transcript("assistant", transition_msg)
        logger.info("Experience stage started")
        
        stage_config = stage_manager.config.get("stages", {}).get("experience", {})
        fallback_timeout = stage_config.get("fallback_timeout_seconds", 120)
        await asyncio.sleep(fallback_timeout)
        
        if stage_manager.get_stage() == InterviewStage.EXPERIENCE.value:
            logger.info(f"Experience fallback timer triggered after {fallback_timeout}s")
            await stage_manager.transition_to_next()


if __name__ == "__main__":
    # Use WorkerOptions to set agent_name - this is what LiveKit uses for dispatch
    # The entrypoint is the @server.rtc_session() decorated function
    agents.cli.run_app(WorkerOptions(
        entrypoint_fnc=interview_agent,
        agent_name="interview-agent"
    ))
