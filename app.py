from fastapi import FastAPI, HTTPException
import sys
import os

# Ensure models can be imported from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import ActionRequest, ResetRequest, ResetResponse, StepResponse, State
from environment import CyberEnvironment

app = FastAPI(title="OpenEnv - Cyber Security Environment")
env = CyberEnvironment(max_steps=100)

@app.post("/reset", response_model=ResetResponse)
def reset_env(req: ResetRequest = ResetRequest()):
    return env.reset(task_id=req.task_id)

@app.post("/step", response_model=StepResponse)
def step_env(req: ActionRequest):
    return env.step(req.action)

@app.get("/state", response_model=State)
def get_state():
    return env.state_info()
