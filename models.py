from enum import IntEnum
from pydantic import BaseModel
from typing import Optional

class Action(IntEnum):
    MONITOR = 0
    DEEP_SCAN = 1
    BLOCK_IP = 2
    ISOLATE_HOST = 3

class Observation(BaseModel):
    threat_level: int
    anomaly_score: float
    system_health: float
    intrusion_detected: bool

class State(BaseModel):
    observation: Observation
    current_step: int
    under_attack: bool
    attack_progress: int

class StepResponse(BaseModel):
    observation: Observation
    reward: float
    terminated: bool
    truncated: bool

class ResetRequest(BaseModel):
    task_id: str = "easy"

class ResetResponse(BaseModel):
    observation: Observation

class ActionRequest(BaseModel):
    action: Action
