"""
Orchestrator - Main entry point that manages both agents in a LiveKit room
"""

import asyncio
import logging
from typing import Optional
from livekit import agents, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents.pipeline import VoicePipelineAgent

from agents.stage_manager import StageManager, InterviewStage
from agents.llm_client import LLMClient
from agents.self_intro_agent import SelfIntroAgent
from agents.experience_agent import ExperienceAgent
import redis.asyncio as redis
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class InterviewOrchestrator:
    """Orchestrates both agents in the interview"""
    
    def __init__(
        self,
        room: rtc.Room,
        stage_manager: StageManager,
        llm_client: LLMClient
    ):
        self.room = room
        self.stage_manager = stage_manager
        self.llm_client = llm_client
        self.self_intro_agent: Optional[SelfIntroAgent] = None
        self.experience_agent: Optional[ExperienceAgent] = None
        self.current_agent: Optional[VoicePipelineAgent] = None
        
    async def initialize(self):
        """Initialize both agents"""
        # Create both agents
        self.self_intro_agent = SelfIntroAgent(
            stage_manager=self.stage_manager,
            llm_client=self.llm_client
        )
        
        self.experience_agent = ExperienceAgent(
            stage_manager=self.stage_manager,
            llm_client=self.llm_client
        )
        
        # Start monitoring stage changes
        asyncio.create_task(self._monitor_stage_changes())
        
        logger.info("Orchestrator initialized")
    
    async def _monitor_stage_changes(self):
        """Monitor stage changes and activate appropriate agent"""
        last_stage = None
        
        while True:
            try:
                current_stage = await self.stage_manager.get_current_stage()
                
                if current_stage != last_stage:
                    logger.info(f"Stage changed to: {current_stage.value}")
                    
                    # Stop current agent
                    if self.current_agent:
                        try:
                            await self.current_agent.aclose()
                        except Exception as e:
                            logger.error(f"Error closing agent: {e}")
                    
                    # Activate appropriate agent
                    if current_stage == InterviewStage.SELF_INTRO:
                        self.current_agent = self.self_intro_agent
                        self.current_agent.start(self.room)
                        logger.info("Self-intro agent activated")
                    elif current_stage == InterviewStage.EXPERIENCE:
                        self.current_agent = self.experience_agent
                        self.current_agent.start(self.room)
                        logger.info("Experience agent activated")
                    elif current_stage == InterviewStage.END:
                        logger.info("Interview ended")
                        break
                    
                    last_stage = current_stage
                
                await asyncio.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Error in stage monitor: {e}")
                await asyncio.sleep(1)
    
    async def cleanup(self):
        """Cleanup orchestrator"""
        if self.current_agent:
            try:
                await self.current_agent.aclose()
            except Exception as e:
                logger.error(f"Error closing agent: {e}")


async def entrypoint(ctx: JobContext):
    """Main entry point for the interview orchestrator"""
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    logger.info(f"Starting interview orchestrator for room: {ctx.room.sid}")
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Connect to Redis
    redis_config = config.get("redis", {})
    redis_url = f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}/{redis_config.get('db', 0)}"
    
    if redis_config.get("password"):
        redis_url = f"redis://:{redis_config['password']}@{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}/{redis_config.get('db', 0)}"
    
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialize stage manager
    stage_manager = StageManager(redis_client=redis_client, config_path=config_path)
    await stage_manager.initialize(ctx.room.sid)
    
    # Initialize LLM client
    llm_client = LLMClient(config_path=config_path)
    
    # Create orchestrator
    orchestrator = InterviewOrchestrator(
        room=ctx.room,
        stage_manager=stage_manager,
        llm_client=llm_client
    )
    
    await orchestrator.initialize()
    
    # Wait for interview to complete
    try:
        while True:
            current_stage = await stage_manager.get_current_stage()
            if current_stage == InterviewStage.END:
                break
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Orchestrator interrupted")
    finally:
        await orchestrator.cleanup()
        await stage_manager.cleanup()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

