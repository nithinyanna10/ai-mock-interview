"""
Self-Introduction Agent - Handles the self-introduction stage of the interview
"""

import logging
from pathlib import Path
from typing import Optional
from livekit import agents, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero

from .base_agent import BaseInterviewAgent
from .stage_manager import StageManager, InterviewStage
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class SelfIntroAgent(BaseInterviewAgent):
    """Agent for conducting self-introduction stage"""
    
    def __init__(
        self,
        stage_manager: StageManager,
        llm_client: LLMClient,
        *args,
        **kwargs
    ):
        # Load system prompt
        prompt_path = Path(__file__).parent.parent / "config" / "prompts" / "self_intro.txt"
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        super().__init__(
            stage=InterviewStage.SELF_INTRO,
            stage_manager=stage_manager,
            llm_client=llm_client,
            system_prompt=system_prompt,
            *args,
            **kwargs
        )
        
        self.max_follow_ups = 2
        self.conversation_history = []
    
    async def on_user_speech_committed(self, message: str):
        """Called when user speech is committed"""
        logger.info(f"User said: {message}")
        self.conversation_history.append({"role": "user", "content": message})
        
        # Check if we should still be in this stage
        if not await self.should_speak():
            logger.info("Stage changed, stopping self-intro agent")
            return
        
        # Check if we should transition
        if not await self.check_stage_transition():
            return
        
        # Generate response
        await self._generate_and_speak(message)
    
    async def _generate_and_speak(self, user_message: str):
        """Generate LLM response and speak it"""
        try:
            # Build conversation context
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self.conversation_history[-5:]  # Last 5 messages
            ])
            
            prompt = f"""Based on the conversation so far:

{context}

Generate a natural, conversational response. Keep it brief (2-3 sentences max)."""
            
            # Generate response using Ollama
            response_text = ""
            async for chunk in self.llm_client.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.7,
                max_tokens=200,
                stream=True
            ):
                response_text += chunk
            
            if response_text.strip():
                logger.info(f"Agent responding: {response_text[:100]}...")
                self.conversation_history.append({"role": "assistant", "content": response_text})
                self.follow_up_count += 1
                
                # Speak the response
                await self.say(response_text, allow_interruptions=True)
                
                # Check if response indicates stage completion
                if any(phrase in response_text.lower() for phrase in [
                    "let's move on", "next stage", "move to", "let's discuss"
                ]):
                    logger.info("Agent indicated stage completion")
                    await self.stage_manager.transition_to_next()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await self.say("I apologize, could you repeat that?", allow_interruptions=True)
    
    async def on_room_connected(self, room: rtc.Room):
        """Called when room is connected"""
        logger.info("Self-intro agent connected to room")
        
        # Wait for stage to be SELF_INTRO
        current_stage = await self.stage_manager.get_current_stage()
        if current_stage == InterviewStage.SELF_INTRO:
            # Start with introduction
            greeting = "Hello! I'm conducting your interview today. To start, could you tell me a bit about yourself - your background, what you're passionate about, and what brings you here today?"
            await self.say(greeting, allow_interruptions=True)
            self.conversation_history.append({"role": "assistant", "content": greeting})


async def entrypoint(ctx: JobContext):
    """Entry point for self-intro agent"""
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Initialize dependencies
    from .stage_manager import StageManager
    from .llm_client import LLMClient
    import redis.asyncio as redis
    
    # Connect to Redis
    redis_client = redis.from_url(
        "redis://localhost:6379/0",
        decode_responses=True
    )
    
    # Initialize stage manager
    stage_manager = StageManager(redis_client=redis_client)
    await stage_manager.initialize(ctx.room.sid)
    
    # Initialize LLM client
    llm_client = LLMClient()
    
    # Create agent
    agent = SelfIntroAgent(
        stage_manager=stage_manager,
        llm_client=llm_client
    )
    
    # Connect agent to room
    agent.start(ctx.room)
    
    # Wait for completion
    await agent.aclose()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

