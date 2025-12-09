"""
Stage Manager - Finite State Machine for Interview Orchestration
Coordinates stage transitions, manages timers, and enforces single-agent speaking rules.
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class InterviewStage(str, Enum):
    """Interview stage enumeration"""
    START = "start"
    SELF_INTRO = "self_intro"
    EXPERIENCE = "experience"
    END = "end"


class StageManager:
    """
    Manages interview stage transitions using a finite state machine.
    Handles time-based fallbacks and semantic stage transitions.
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        config_path: Optional[Path] = None
    ):
        self.redis_client = redis_client
        self.current_stage = InterviewStage.START
        self.stage_start_time: Optional[datetime] = None
        self.stage_timers: Dict[str, asyncio.Task] = {}
        self.config = self._load_config(config_path)
        self.room_id: Optional[str] = None
        # Flags for stage handling
        self.flag_intro_start = False
        self.flag_exp_start = False
        
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return {
                "stages": {
                    "self_intro": {"fallback_timeout_seconds": 45},
                    "experience": {"fallback_timeout_seconds": 120}
                }
            }
    
    async def initialize(self, room_id: str):
        """Initialize stage manager for a room"""
        self.room_id = room_id
        await self._set_stage(InterviewStage.START)
        logger.info(f"Stage manager initialized for room {room_id}")
    
    async def _set_stage(self, stage: InterviewStage):
        """Set the current stage and update Redis"""
        old_stage = self.current_stage
        self.current_stage = stage
        self.stage_start_time = datetime.now()
        
        # Cancel old timer
        if old_stage.value in self.stage_timers:
            self.stage_timers[old_stage.value].cancel()
        
        # Update Redis
        if self.redis_client:
            try:
                await self.redis_client.set(
                    f"interview:{self.room_id}:stage",
                    stage.value,
                    ex=3600  # 1 hour expiry
                )
                await self.redis_client.set(
                    f"interview:{self.room_id}:stage_start",
                    self.stage_start_time.isoformat(),
                    ex=3600
                )
            except Exception as e:
                logger.error(f"Failed to update Redis: {e}")
        
        logger.info(f"Stage transition: {old_stage.value} -> {stage.value}")
        
        # Start fallback timer for new stage
        if stage != InterviewStage.END:
            await self._start_fallback_timer(stage)
    
    async def _start_fallback_timer(self, stage: InterviewStage):
        """Start a timer that will force stage transition after timeout"""
        stage_config = self.config.get("stages", {}).get(stage.value, {})
        timeout = stage_config.get("fallback_timeout_seconds", 45)
        
        async def timer_task():
            try:
                await asyncio.sleep(timeout)
                # Check if still in same stage
                if self.current_stage == stage:
                    logger.warning(
                        f"Fallback timer triggered for {stage.value} after {timeout}s"
                    )
                    await self.transition_to_next()
            except asyncio.CancelledError:
                pass
        
        self.stage_timers[stage.value] = asyncio.create_task(timer_task())
    
    async def get_current_stage(self) -> InterviewStage:
        """Get current stage, checking Redis if available"""
        if self.redis_client:
            try:
                stage_str = await self.redis_client.get(
                    f"interview:{self.room_id}:stage"
                )
                if stage_str:
                    self.current_stage = InterviewStage(stage_str.decode() if isinstance(stage_str, bytes) else stage_str)
            except Exception as e:
                logger.error(f"Failed to read from Redis: {e}")
        
        return self.current_stage
    
    async def transition_to_next(self) -> bool:
        """Transition to the next stage in the FSM"""
        current = await self.get_current_stage()
        
        transitions = {
            InterviewStage.START: InterviewStage.SELF_INTRO,
            InterviewStage.SELF_INTRO: InterviewStage.EXPERIENCE,
            InterviewStage.EXPERIENCE: InterviewStage.END,
            InterviewStage.END: InterviewStage.END
        }
        
        next_stage = transitions.get(current)
        if next_stage and next_stage != current:
            await self._set_stage(next_stage)
            return True
        
        return False
    
    async def transition_to_stage(self, stage: InterviewStage) -> bool:
        """Manually transition to a specific stage"""
        current = await self.get_current_stage()
        
        # Validate transition
        valid_transitions = {
            InterviewStage.START: [InterviewStage.SELF_INTRO],
            InterviewStage.SELF_INTRO: [InterviewStage.EXPERIENCE, InterviewStage.END],
            InterviewStage.EXPERIENCE: [InterviewStage.END],
            InterviewStage.END: []
        }
        
        if stage in valid_transitions.get(current, []):
            await self._set_stage(stage)
            return True
        
        logger.warning(f"Invalid transition: {current.value} -> {stage.value}")
        return False
    
    async def should_agent_speak(self, agent_stage: InterviewStage) -> bool:
        """Check if an agent should be speaking based on current stage"""
        current = await self.get_current_stage()
        return current == agent_stage
    
    async def get_stage_duration(self) -> float:
        """Get duration in seconds since stage started"""
        if self.stage_start_time:
            return (datetime.now() - self.stage_start_time).total_seconds()
        return 0.0
    
    async def check_silence_timeout(self, silence_duration: float) -> bool:
        """Check if silence duration exceeds threshold"""
        threshold = self.config.get("audio", {}).get("silence_timeout_seconds", 10.0)
        return silence_duration >= threshold
    
    def get_stage(self) -> str:
        """Get current stage as string (synchronous for AgentSession)"""
        return self.current_stage.value
    
    def switch_stage(self, new_stage: str):
        """Switch to a new stage (synchronous for AgentSession)"""
        try:
            stage = InterviewStage(new_stage)
            asyncio.create_task(self._set_stage(stage))
        except ValueError:
            logger.warning(f"Invalid stage: {new_stage}")
    
    async def cleanup(self):
        """Cleanup timers and Redis keys"""
        for timer in self.stage_timers.values():
            timer.cancel()
        
        if self.redis_client and self.room_id:
            try:
                await self.redis_client.delete(
                    f"interview:{self.room_id}:stage",
                    f"interview:{self.room_id}:stage_start"
                )
            except Exception as e:
                logger.error(f"Failed to cleanup Redis: {e}")

