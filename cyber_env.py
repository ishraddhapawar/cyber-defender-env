import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CyberSecurityEnv(gym.Env):
    """
    Autonomous Intrusion Response Environment

    State:
    - threat_level (0–10)
    - anomaly_score (0.0-1.0)
    - system_health (0.0-100.0)
    - intrusion_detected (bool)

    Actions:
    - 0: monitor
    - 1: deep_scan
    - 2: block_ip
    - 3: isolate_host

    Reward:
    - +10 for stopping attacks
    - -5 for false positives
    - -20 for system compromise
    """

    def __init__(self, max_steps=100):
        super(CyberSecurityEnv, self).__init__()

        self.max_steps = max_steps
        self.current_step = 0

        # Action Space
        # 0: monitor, 1: deep_scan, 2: block_ip, 3: isolate_host
        self.action_space = spaces.Discrete(4)

        # Observation Space
        self.observation_space = spaces.Dict(
            {
                "threat_level": spaces.Discrete(11), # 0 to 10
                "anomaly_score": spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32),
                "system_health": spaces.Box(low=0.0, high=100.0, shape=(1,), dtype=np.float32),
                "intrusion_detected": spaces.Discrete(2) # 0 or 1
            }
        )

        # Hidden dynamics state
        self._is_under_attack = False
        self._attack_progress = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        
        self._is_under_attack = False
        self._attack_progress = 0

        # Initial state
        self.state = {
            "threat_level": 0,
            "anomaly_score": np.array([0.0], dtype=np.float32),
            "system_health": np.array([100.0], dtype=np.float32),
            "intrusion_detected": 0
        }

        return self.state, {}

    def step(self, action):
        self.current_step += 1
        reward = 0
        terminated = False
        truncated = False

        # Randomly initiate an attack if not currently under attack
        if not self._is_under_attack and self.np_random.random() < 0.15: # 15% chance per step
            self._is_under_attack = True
            self._attack_progress = 1

        # Evaluate action
        if action == 0:  # monitor
            # Does nothing to stop attack, just observes
            pass
        
        elif action == 1:  # deep_scan
            # Accurately sets intrusion_detected if under attack
            if self._is_under_attack:
                self.state["intrusion_detected"] = 1
                self.state["anomaly_score"][0] = min(1.0, self.state["anomaly_score"][0] + 0.3)
            else:
                self.state["intrusion_detected"] = 0
                self.state["anomaly_score"][0] = max(0.0, self.state["anomaly_score"][0] - 0.2)
                
        elif action in [2, 3]:  # block_ip or isolate_host
            if self._is_under_attack:
                # Successfully stopped the attack
                reward = 10
                self._is_under_attack = False
                self._attack_progress = 0
                self.state["threat_level"] = max(0, self.state["threat_level"] - 3)
                self.state["intrusion_detected"] = 0
            else:
                # False positive: Took mitigation without active attack
                reward = -5

        # Update underlying dynamics if attack is ongoing
        if self._is_under_attack:
            self._attack_progress += 1
            
            # Health penalty for ongoing attack
            damage = self.np_random.uniform(5.0, 15.0)
            self.state["system_health"][0] = max(0.0, self.state["system_health"][0] - damage)
            
            # Threat level increases as attack progresses
            self.state["threat_level"] = min(10, self.state["threat_level"] + 1)
            
            # Anomaly score naturally fluctuates upwards
            noise = self.np_random.uniform(0.05, 0.2)
            self.state["anomaly_score"][0] = min(1.0, self.state["anomaly_score"][0] + noise)
            
            # Passive detection might happen if anomaly gets high enough
            if self.state["anomaly_score"][0] > 0.7:
                self.state["intrusion_detected"] = 1
        else:
            # Naturally recover health and lower threat when safe
            self.state["system_health"][0] = min(100.0, self.state["system_health"][0] + 1.0)
            if self.state["threat_level"] > 0 and self.np_random.random() < 0.3:
                self.state["threat_level"] -= 1
            self.state["anomaly_score"][0] = max(0.0, self.state["anomaly_score"][0] - 0.1)

        # Check termination condition
        if self.state["system_health"][0] <= 0:
            reward = -20  # System compromised
            terminated = True
            
        if self.current_step >= self.max_steps:
            truncated = True

        return self.state, reward, terminated, truncated, {}
