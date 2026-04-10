"""FastAPI server for HF Space deployment"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from .environment import CyberSOCEnv
from .models import CyberSOCAction

app = FastAPI(title="CyberSOC OpenEnv", version="1.0.0")

# Global environment instance (HF Spaces are single-user)
env_instance = None


class ResetRequest(BaseModel):
    task: str = "phishing_triage"


@app.on_event("startup")
async def startup_event():
    global env_instance
    # Initialize with default task; task can be changed via reset()
    env_instance = CyberSOCEnv(task_name="phishing_triage")


@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()):
    """Reset environment and return initial observation"""
    global env_instance
    try:
        # Reinitialize with requested task
        env_instance = CyberSOCEnv(task_name=request.task)
        result = await env_instance.reset()
        return {
            "observation": result.observation.dict(),
            "info": result.info.dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
async def step(action: CyberSOCAction):
    """Execute action and return new state"""
    global env_instance
    if env_instance is None:
        raise HTTPException(
            status_code=400, detail="Environment not initialized. Call /reset first."
        )

    try:
        result = await env_instance.step(action)
        return {
            "observation": result.observation.dict(),
            "reward": result.reward,
            "done": result.done,
            "info": result.info.dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_state():
    """Return current environment state for debugging"""
    global env_instance
    if env_instance is None:
        raise HTTPException(status_code=400, detail="Environment not initialized")

    state = await env_instance.state()
    return state


@app.get("/health")
async def health_check():
    """Health check endpoint for HF Space"""
    return {"status": "healthy", "env_initialized": env_instance is not None}
