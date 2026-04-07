import random
from models import Observation, State, StepResponse, Action, ResetResponse

class CyberEnvironment:
    def __init__(self, max_steps: int = 100):
        self.max_steps = max_steps
        self.state = None
        self.current_task = "easy"
        self.reset()
        
    def reset(self, task_id: str = "easy") -> ResetResponse:
        self.current_task = task_id
        
        # Default initialization
        obs = Observation(
            threat_level=0,
            anomaly_score=0.0,
            system_health=100.0,
            intrusion_detected=False
        )
        self.state = State(
            observation=obs,
            current_step=0,
            under_attack=False,
            attack_progress=0
        )
        
        # Apply task specific initial states
        if task_id == "easy":
            # Start immediately with an obvious attack
            self.state.under_attack = True
            obs.threat_level = 8
            obs.anomaly_score = 0.95
        elif task_id == "medium":
            # Start with a false positive (high anomaly, no actual attack)
            self.state.under_attack = False
            obs.threat_level = 2
            obs.anomaly_score = 0.8
        elif task_id == "hard":
            # Fast acting attack
            self.state.under_attack = True
            obs.threat_level = 5
            obs.anomaly_score = 0.5
            
        return ResetResponse(observation=obs)
        
    def state_info(self) -> State:
        return self.state
        
    def step(self, action: Action) -> StepResponse:
        self.state.current_step += 1
        reward = 0.0
        terminated = False
        truncated = False
        
        obs = self.state.observation
        
        damage_multiplier = 1.0
        if self.current_task == "hard":
            damage_multiplier = 3.0

        # Evaluate action
        if action == Action.MONITOR:
            pass
        elif action == Action.DEEP_SCAN:
            if self.state.under_attack:
                obs.intrusion_detected = True
                obs.anomaly_score = min(1.0, obs.anomaly_score + 0.3)
            else:
                obs.intrusion_detected = False
                obs.anomaly_score = 0.0 # Clarified
        elif action in (Action.BLOCK_IP, Action.ISOLATE_HOST):
            if self.state.under_attack:
                # Correctly neutralized
                self.state.under_attack = False
                obs.threat_level = 0
                obs.intrusion_detected = False
                
                # Grading Score Calculation (0.0 to 1.0)
                reward = obs.system_health / 100.0
                terminated = True
            else:
                # False positive mitigation penalty
                # Severe score hit
                reward = -0.5
                terminated = True

        # Update underlying dynamics if attack is ongoing
        if self.state.under_attack and not terminated:
            self.state.attack_progress += 1
            damage = random.uniform(5.0, 15.0) * damage_multiplier
            obs.system_health = max(0.0, obs.system_health - damage)
            obs.threat_level = min(10, obs.threat_level + int(1 * damage_multiplier))
            obs.anomaly_score = min(1.0, obs.anomaly_score + 0.1)
            
            if obs.anomaly_score > 0.8:
                obs.intrusion_detected = True
        elif not self.state.under_attack and not terminated:
            if self.current_task != "medium":
                obs.system_health = min(100.0, obs.system_health + 1.0)
                
            # For testing: medium might randomly launch a real attack later
            if self.current_task == "medium" and self.state.current_step > 3 and random.random() < 0.5:
                self.state.under_attack = True

        # Check termination bounds
        if obs.system_health <= 0.0:
            reward = 0.0 # Lowest score
            terminated = True
            
        if self.state.current_step >= self.max_steps and not terminated:
            truncated = True
            # Partial score if survived but didn't mitigate
            reward = (obs.system_health / 200.0) 

        return StepResponse(
            observation=obs,
            reward=max(0.0, min(1.0, reward)) if terminated else reward, # Clamp final scores if terminated
            terminated=terminated,
            truncated=truncated
        )
