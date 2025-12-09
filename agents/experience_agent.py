"""
Experience Agent - Handles the past experience and projects stage of the interview
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


class ExperienceAgent(BaseInterviewAgent):
    """Agent for conducting past experience and projects stage"""
    
    def __init__(
        self,
        stage_manager: StageManager,
        llm_client: LLMClient,
        *args,
        **kwargs
    ):
        # Load system prompt
        prompt_path = Path(__file__).parent.parent / "config" / "prompts" / "experience.txt"
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        super().__init__(
            stage=InterviewStage.EXPERIENCE,
            stage_manager=stage_manager,
            llm_client=llm_client,
            system_prompt=system_prompt,
            *args,
            **kwargs
        )
        
        self.max_follow_ups = 5
        self.conversation_history = []
        self.project_context = {}
    
    async def on_user_speech_committed(self, message: str):
        """Called when user speech is committed"""
        logger.info(f"User said: {message}")
        self.conversation_history.append({"role": "user", "content": message})
        
        # Extract project/technical context
        self._extract_context(message)
        
        # Check if we should still be in this stage
        if not await self.should_speak():
            logger.info("Stage changed, stopping experience agent")
            return
        
        # Check if we should transition
        if not await self.check_stage_transition():
            return
        
        # Generate response
        await self._generate_and_speak(message)
    
    def _extract_context(self, message: str):
        """Extract technical context from user message"""
        # Simple keyword extraction (could be enhanced with NER)
        tech_keywords = [
            "python", "javascript", "react", "node", "api", "database",
            "algorithm", "system", "architecture", "deployment", "testing"
        ]
        
        message_lower = message.lower()
        for keyword in tech_keywords:
            if keyword in message_lower:
                self.project_context[keyword] = self.project_context.get(keyword, 0) + 1
    
    async def _generate_and_speak(self, user_message: str):
        """Generate LLM response and speak it"""
        try:
            # Build conversation context
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self.conversation_history[-8:]  # Last 8 messages for more context
            ])
            
            # Add technical context
            tech_context = ""
            if self.project_context:
                tech_context = f"\n\nTechnical topics mentioned: {', '.join(self.project_context.keys())}"
            
            prompt = f"""Based on the conversation so far:

{context}{tech_context}

Generate a natural, technical interview response. Use STAR method when appropriate. Keep it concise (3-4 sentences max). Ask follow-up questions to dig deeper into technical details."""
            
            # Generate response using Ollama
            response_text = ""
            async for chunk in self.llm_client.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.6,
                max_tokens=300,
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
                    "thank you", "that's great", "wrap up", "conclude"
                ]) and self.follow_up_count >= 3:
                    logger.info("Agent indicated stage completion")
                    await self.stage_manager.transition_to_next()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await self.say("I apologize, could you repeat that?", allow_interruptions=True)
    
    async def on_room_connected(self, room: rtc.Room):
        """Called when room is connected"""
        logger.info("Experience agent connected to room")
        
        # Wait for stage to be EXPERIENCE
        current_stage = await self.stage_manager.get_current_stage()
        if current_stage == InterviewStage.EXPERIENCE:
            # Start with experience question
            greeting = "Let's dive into your past experience. Can you tell me about a project you're particularly proud of? What was your role, and what challenges did you face?"
            await self.say(greeting, allow_interruptions=True)
            self.conversation_history.append({"role": "assistant", "content": greeting})


async def entrypoint(ctx: JobContext):
    """Entry point for experience agent"""
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
    agent = ExperienceAgent(
        stage_manager=stage_manager,
        llm_client=llm_client
    )
    
    # Connect agent to room
    agent.start(ctx.room)
    
    # Wait for completion
    await agent.aclose()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

