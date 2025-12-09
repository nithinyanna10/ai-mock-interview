"""
Base Agent - Common functionality for all interview agents
"""

import logging
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

from .stage_manager import StageManager, InterviewStage
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class BaseInterviewAgent(VoicePipelineAgent):
    """Base class for interview agents with common functionality"""
    
    def __init__(
        self,
        stage: InterviewStage,
        stage_manager: StageManager,
        llm_client: LLMClient,
        system_prompt: str,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.stage = stage
        self.stage_manager = stage_manager
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.follow_up_count = 0
        self.max_follow_ups = 2
        
    async def on_participant_connected(self, participant: rtc.RemoteParticipant):
        """Called when a participant connects"""
        logger.info(f"Participant {participant.identity} connected")
    
    async def on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        """Called when a participant disconnects"""
        logger.info(f"Participant {participant.identity} disconnected")
    
    async def should_speak(self) -> bool:
        """Check if agent should speak based on current stage"""
        return await self.stage_manager.should_agent_speak(self.stage)
    
    async def check_stage_transition(self) -> bool:
        """Check if stage should transition and handle it"""
        current_stage = await self.stage_manager.get_current_stage()
        
        # If we're past our stage, don't speak
        if current_stage != self.stage:
            return False
        
        # Check if we should transition based on follow-ups or duration
        stage_duration = await self.stage_manager.get_stage_duration()
        stage_config = self.stage_manager.config.get("stages", {}).get(self.stage.value, {})
        max_duration = stage_config.get("max_duration_seconds", 45)
        
        if self.follow_up_count >= self.max_follow_ups or stage_duration >= max_duration:
            logger.info(f"Transitioning from {self.stage.value} after {stage_duration}s")
            await self.stage_manager.transition_to_next()
            return False
        
        return True

