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
from livekit.plugins.openai import LLM as OpenAILLM

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
    
    # Initialize OpenAI LLM (much better than Ollama - no networking issues!)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is required! Add it to .env file")
    
    # Use OpenAI GPT-4 or GPT-3.5-turbo for conversation
    llm_config = config.get("llm", {})
    openai_llm = OpenAILLM(
        model=llm_config.get("model", "gpt-4o-mini"),  # Fast and cheap, or use "gpt-4o" for better quality
    )
    logger.info(f"✅ Using OpenAI LLM: {llm_config.get('model', 'gpt-4o-mini')}")
    
    # Create assistant agent with proactive instructions
    assistant = InterviewAssistant(stage_manager)
    assistant.room_id = room_sid
    
    # Note: We'll trigger greeting in the stage loop instead of using event handlers
    # Event handlers on ctx.room need to be set up after session.start()
    
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
    
    # Use OpenAI for everything: STT, LLM, and TTS
    logger.info("✅ Using OpenAI for STT, LLM, and TTS")
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=STT(),  # OpenAI STT - transcribes your speech
        llm=openai_llm,  # OpenAI LLM - generates responses
        tts=TTS(),  # OpenAI TTS - speaks responses
        allow_interruptions=True,
    )
    
    try:
        logger.info("📡 Starting AgentSession...")
        logger.info(f"🔗 Connecting to room: {ctx.room.name} (SID: {ctx.room.sid})")
        
        await session.start(
            room=ctx.room,
            agent=assistant,
        )
        
        logger.info("✅ AgentSession started successfully")
        
        # Verify agent is in the room
        participants = ctx.room.remote_participants
        logger.info(f"👥 Room participants: {len(participants)} remote participants")
        
        # Check if agent participant exists
        local_participant = ctx.room.local_participant
        if local_participant:
            logger.info(f"🤖 Agent participant: {local_participant.identity}")
            tracks = local_participant.track_publications
            logger.info(f"📡 Published tracks: {len(tracks)} tracks")
            for track in tracks:
                logger.info(f"   - Track: {track.name} ({track.kind})")
            
            # If no tracks published (no TTS), publish a silent audio track so client sees the agent
            if len(tracks) == 0:
                logger.info("ℹ️  No tracks yet - publishing silent audio track so client can see agent")
                try:
                    # Create a silent audio track so the client knows the agent is there
                    from livekit import rtc
                    import numpy as np
                    
                    # Create silent audio source (48kHz, mono, 16-bit)
                    sample_rate = 48000
                    num_samples = sample_rate  # 1 second of silence
                    silent_audio = np.zeros(num_samples, dtype=np.int16)
                    
                    # Create audio source
                    source = rtc.AudioSource(sample_rate, num_channels=1)
                    track = rtc.LocalAudioTrack.create_audio_track("agent-audio", source)
                    
                    # Publish the track
                    await local_participant.publish_track(track)
                    logger.info("✅ Published silent audio track - agent should now be visible!")
                except Exception as e:
                    logger.warning(f"⚠️  Could not publish silent track: {e}")
                    logger.info("   Agent is connected but may not appear until it speaks")
        
        logger.info("✅ Agent connected to room!")
        
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
    await asyncio.sleep(3)  # Wait for connection to stabilize and user to potentially join
    
    # Always start the interview - transition to self_intro if still in start stage
    current_stage = stage_manager.get_stage()
    logger.info(f"📊 Current stage: {current_stage}")
    
    # If still in start stage, transition to self_intro first
    if current_stage == InterviewStage.START.value or current_stage == "start":
        logger.info("🔄 Transitioning from start to self_intro...")
        await stage_manager.transition_to_next()
        current_stage = stage_manager.get_stage()
        logger.info(f"📊 New stage: {current_stage}")
    
    # Now start the interview
    if current_stage == InterviewStage.SELF_INTRO.value or current_stage == "self_intro":
        logger.info("🚀 Starting interview - sending greeting...")
        await handle_self_intro(session, stage_manager, assistant)
    
    while True:
        try:
            current_stage = stage_manager.get_stage()
            if current_stage == InterviewStage.EXPERIENCE.value:
                await handle_experience(session, stage_manager, assistant)
            elif current_stage == InterviewStage.END.value:
                try:
                    await session.say("Thank you! The interview is complete.", allow_interruptions=True)
                except Exception as e:
                    logger.warning(f"Could not send final message: {e}")
                break
            await asyncio.sleep(0.5)
        except Exception as e:
            # Don't exit on errors, just log and continue
            logger.error(f"Error in stage loop: {e}", exc_info=True)
            await asyncio.sleep(1)


async def handle_self_intro(session: AgentSession, stage_manager: StageManager, assistant: InterviewAssistant):
    """Handle self-introduction stage"""
    if not stage_manager.flag_intro_start:
        stage_manager.flag_intro_start = True
        greeting = "Hello! I'm conducting your interview today. To start, could you tell me a bit about yourself - your background, what you're passionate about, and what brings you here today?"
        logger.info(f"🎤 Attempting to send greeting: {greeting[:50]}...")
        try:
            # Use say() to make the agent speak proactively
            logger.info("Calling session.say()...")
            # session.say() returns a SpeechHandle - we can await it or just call it
            speech_handle = await session.say(greeting, allow_interruptions=True)
            logger.info(f"✅ session.say() returned: {type(speech_handle)}")
            # Wait a bit for speech to start
            await asyncio.sleep(0.5)
            logger.info(f"✅ Agent said greeting successfully!")
        except Exception as e:
            logger.error(f"❌ Error with session.say(): {e}", exc_info=True, stack_info=True)
            # Fallback: try generate_reply - this should work for proactive speech
            try:
                logger.info("Trying fallback: generate_reply()...")
                # generate_reply needs user_input - but we can pass the greeting as if user said it
                await session.generate_reply(user_input=greeting)
                logger.info("✅ Fallback generate_reply() succeeded")
            except Exception as e2:
                logger.error(f"❌ Fallback also failed: {e2}", exc_info=True)
        await assistant.save_to_transcript("assistant", greeting)
        logger.info("✅ Self-intro stage started")
        
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
        try:
            await session.say(transition_msg, allow_interruptions=True)
            logger.info(f"✅ Agent said transition: {transition_msg[:50]}...")
        except Exception as e:
            logger.error(f"❌ Error sending transition: {e}")
            try:
                await session.generate_reply(user_input=transition_msg)
            except:
                pass
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
