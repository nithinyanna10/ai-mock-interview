"""
FastAPI Server - REST API for managing interview sessions
"""

import logging
import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis
from datetime import datetime
import yaml
from pathlib import Path

from agents.stage_manager import StageManager, InterviewStage

# LiveKit API for agent dispatch
try:
    from livekit.api import LiveKitAPI
    from livekit.api.agent_dispatch_service import CreateAgentDispatchRequest
    LIVEKIT_API_AVAILABLE = True
except ImportError:
    LIVEKIT_API_AVAILABLE = False
    logger.warning("livekit-api not available, agent dispatch will not work")

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Mock Interview API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Redis client
redis_client: Optional[redis.Redis] = None
active_sessions: Dict[str, StageManager] = {}


class InterviewStartRequest(BaseModel):
    room_id: str
    candidate_name: Optional[str] = None


class InterviewStatusResponse(BaseModel):
    room_id: str
    stage: str
    stage_start_time: Optional[str] = None
    stage_duration: float
    status: str


class InterviewStopResponse(BaseModel):
    room_id: str
    message: str
    final_stage: str


@app.on_event("startup")
async def startup():
    """Initialize Redis connection on startup"""
    global redis_client
    try:
        import os
        # Use environment variables first (set by docker-compose), then defaults
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", "")
        
        if redis_password:
            redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info(f"Redis connection established at {redis_host}:{redis_port}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()
    logger.info("Shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "redis_connected": redis_client is not None and await redis_client.ping() if redis_client else False,
        "active_sessions": len(active_sessions)
    }


@app.post("/interview/start")
async def start_interview(request: InterviewStartRequest):
    """Start a new interview session"""
    try:
        # Initialize stage manager
        stage_manager = StageManager(redis_client=redis_client)
        await stage_manager.initialize(request.room_id)
        
        # Transition to self-intro stage
        await stage_manager.transition_to_next()
        
        # Store in active sessions
        active_sessions[request.room_id] = stage_manager
        
        # Store metadata
        if redis_client:
            await redis_client.set(
                f"interview:{request.room_id}:metadata",
                f"candidate_name:{request.candidate_name or 'Unknown'}",
                ex=3600
            )
        
        return {
            "room_id": request.room_id,
            "stage": "self_intro",
            "message": "Interview started",
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interview/{room_id}/status")
async def get_interview_status(room_id: str):
    """Get current status of an interview"""
    try:
        stage_manager = active_sessions.get(room_id)
        
        if not stage_manager:
            # Try to load from Redis
            if redis_client:
                stage_str = await redis_client.get(f"interview:{room_id}:stage")
                if not stage_str:
                    raise HTTPException(status_code=404, detail="Interview not found")
                
                stage_manager = StageManager(redis_client=redis_client)
                await stage_manager.initialize(room_id)
                active_sessions[room_id] = stage_manager
            else:
                raise HTTPException(status_code=404, detail="Interview not found")
        
        current_stage = await stage_manager.get_current_stage()
        stage_duration = await stage_manager.get_stage_duration()
        
        stage_start_time = None
        if redis_client:
            stage_start_str = await redis_client.get(f"interview:{room_id}:stage_start")
            if stage_start_str:
                stage_start_time = stage_start_str
        
        return InterviewStatusResponse(
            room_id=room_id,
            stage=current_stage.value,
            stage_start_time=stage_start_time,
            stage_duration=stage_duration,
            status="active" if current_stage != InterviewStage.END else "completed"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview/{room_id}/transition")
async def transition_stage(room_id: str, target_stage: Optional[str] = None):
    """Manually transition to next stage or specific stage"""
    try:
        stage_manager = active_sessions.get(room_id)
        
        if not stage_manager:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        if target_stage:
            # Transition to specific stage
            try:
                target = InterviewStage(target_stage)
                success = await stage_manager.transition_to_stage(target)
                if not success:
                    raise HTTPException(status_code=400, detail="Invalid stage transition")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {target_stage}")
        else:
            # Transition to next stage
            success = await stage_manager.transition_to_next()
            if not success:
                raise HTTPException(status_code=400, detail="Cannot transition further")
        
        current_stage = await stage_manager.get_current_stage()
        
        return {
            "room_id": room_id,
            "stage": current_stage.value,
            "message": "Stage transitioned successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transitioning stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview/{room_id}/stop")
async def stop_interview(room_id: str):
    """Stop an interview session"""
    try:
        stage_manager = active_sessions.get(room_id)
        
        if not stage_manager:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Transition to END stage
        await stage_manager.transition_to_stage(InterviewStage.END)
        current_stage = await stage_manager.get_current_stage()
        
        # Cleanup
        await stage_manager.cleanup()
        if room_id in active_sessions:
            del active_sessions[room_id]
        
        return InterviewStopResponse(
            room_id=room_id,
            message="Interview stopped",
            final_stage=current_stage.value
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/token")
async def generate_token(request: Request):
    """Generate LiveKit access token and dispatch agent"""
    try:
        data = await request.json()
        room_id = data.get("room", "")
        identity = data.get("identity", f"user-{int(datetime.now().timestamp())}")
        
        try:
            import jwt
            import time
            
            api_key = os.getenv("LIVEKIT_API_KEY", "API4xeZWnJCKVyg")
            api_secret = os.getenv("LIVEKIT_API_SECRET", "yheogye7QX27H6sD83tajnckfRW5c6h9eQvpePTAjeaN")
            livekit_url = os.getenv("LIVEKIT_URL", "wss://test-hll5bwms.livekit.cloud")
            
            token = jwt.encode({
                "iss": api_key,
                "sub": identity,
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,
                "video": {"room": room_id, "roomJoin": True},
                "audio": {"room": room_id, "roomJoin": True}
            }, api_secret, algorithm="HS256")
            
            # Dispatch agent to room (non-blocking, agent should auto-dispatch)
            # Note: In LiveKit Agents SDK, agents auto-dispatch when participants join
            # This is just a manual trigger if needed
            if LIVEKIT_API_AVAILABLE and room_id:
                try:
                    # LiveKitAPI expects full URL with https://
                    # Convert wss:// to https://
                    if livekit_url.startswith("wss://"):
                        api_url = livekit_url.replace("wss://", "https://")
                    elif livekit_url.startswith("ws://"):
                        api_url = livekit_url.replace("ws://", "http://")
                    elif livekit_url.startswith("https://"):
                        api_url = livekit_url
                    else:
                        api_url = f"https://{livekit_url}"
                    
                    logger.info(f"Attempting to dispatch agent to room: {room_id}, API URL: {api_url}")
                    api = LiveKitAPI(url=api_url, api_key=api_key, api_secret=api_secret)
                    dispatch_req = CreateAgentDispatchRequest(
                        room=room_id,
                        agent_name="interview-agent",  # Match the agent_name in WorkerOptions
                    )
                    result = await api.agent_dispatch.create_dispatch(dispatch_req)
                    logger.info(f"✅ Agent dispatched to room: {room_id}, dispatch_id: {result.id if hasattr(result, 'id') else 'N/A'}")
                except Exception as dispatch_error:
                    # Log the error but don't fail token generation
                    logger.warning(f"⚠️ Manual dispatch failed (agent may auto-dispatch): {dispatch_error}", exc_info=True)
            
            return {"token": token, "room": room_id, "identity": identity}
        except ImportError:
            raise HTTPException(status_code=500, detail="PyJWT not installed. Install in container: pip install PyJWT")
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dispatch/{room_id}")
async def dispatch_agent(room_id: str):
    """Manually dispatch agent to a room"""
    if not LIVEKIT_API_AVAILABLE:
        raise HTTPException(status_code=503, detail="LiveKit API not available")
    
    try:
        api_key = os.getenv("LIVEKIT_API_KEY", "API4xeZWnJCKVyg")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "yheogye7QX27H6sD83tajnckfRW5c6h9eQvpePTAjeaN")
        livekit_url = os.getenv("LIVEKIT_URL", "wss://test-hll5bwms.livekit.cloud")
        
        # LiveKitAPI expects full URL with https://
        # Convert wss:// to https://
        if livekit_url.startswith("wss://"):
            api_url = livekit_url.replace("wss://", "https://")
        elif livekit_url.startswith("ws://"):
            api_url = livekit_url.replace("ws://", "http://")
        elif livekit_url.startswith("https://"):
            api_url = livekit_url
        else:
            api_url = f"https://{livekit_url}"
        
        api = LiveKitAPI(url=api_url, api_key=api_key, api_secret=api_secret)
        dispatch_req = CreateAgentDispatchRequest(
            room=room_id,
            agent_name="interview-agent",  # Match the agent_name in WorkerOptions
        )
        result = await api.agent_dispatch.create_dispatch(dispatch_req)
        logger.info(f"Agent dispatched to room: {room_id}, dispatch_id: {result.id if hasattr(result, 'id') else 'N/A'}")
        
        return {
            "status": "dispatched",
            "room_id": room_id,
            "dispatch_id": result.id if hasattr(result, 'id') else None
        }
    except Exception as e:
        logger.error(f"Error dispatching agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interview/{room_id}/transcript")
async def get_transcript(room_id: str):
    """Get interview transcript (full conversation)"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis not available")
        
        transcript_key = f"interview:{room_id}:transcript"
        messages_raw = await redis_client.lrange(transcript_key, 0, -1)
        
        messages = []
        for msg_str in messages_raw:
            try:
                import json
                msg = json.loads(msg_str) if isinstance(msg_str, str) else msg_str
                messages.append(msg)
            except (json.JSONDecodeError, TypeError):
                # Try eval as fallback for old format
                try:
                    msg = eval(msg_str) if isinstance(msg_str, str) else msg_str
                    messages.append(msg)
                except:
                    continue
        
        return {
            "room_id": room_id,
            "message_count": len(messages),
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

