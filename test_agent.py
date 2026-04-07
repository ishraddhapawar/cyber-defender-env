import gymnasium as gym
import numpy as np
from cyber_env import CyberSecurityEnv

def print_state(state):
    print(f"  Threat Level: {state['threat_level']}")
    print(f"  Anomaly Score: {state['anomaly_score'][0]:.2f}")
    print(f"  System Health: {state['system_health'][0]:.2f}")
    print(f"  Intrusion Detected: {bool(state['intrusion_detected'])}")

def run_random_agent():
    print("Initializing CyberSecurityEnv...\n")
    
    # Register the environment or just instantiate directly
    env = CyberSecurityEnv(max_steps=50)
    
    state, info = env.reset(seed=42)
    
    ACTION_NAMES = {
        0: "MONITOR",
        1: "DEEP_SCAN",
        2: "BLOCK_IP",
        3: "ISOLATE_HOST"
    }
    
    print("--- Initial State ---")
    print_state(state)
    print("---------------------\n")
    
    total_reward = 0
    
    for step in range(1, 51):
        # We will heavily bias towards monitoring (0) or deep scan (1) 
        # so the system doesn't immediately false positive and terminate
        action = np.random.choice([0, 0, 0, 0, 1, 1, 2, 3])
        
        # Or, a simple rule-based agent to show smarter behavior:
        # if state['intrusion_detected'] or state['anomaly_score'][0] > 0.8:
        #     action = 2
        # else:
        #     action = np.random.choice([0, 1])

        state, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        # Only print steps where something significant happens or every 5 steps
        if reward != 0 or step % 5 == 0 or env.unwrapped._is_under_attack:
            print(f"Step: {step} | Under Attack: {env.unwrapped._is_under_attack}")
            print(f"Agent took action: {ACTION_NAMES[action]}")
            print(f"Reward obtained: {reward}")
            print_state(state)
            print("-" * 20)
            
        if terminated or truncated:
            print(f"\nEpisode ended at Step {step}.")
            if terminated:
                print("Reason: SYSTEM COMPROMISED.")
            elif truncated:
                print("Reason: TIME LIMIT REACHED.")
            break
            
    print(f"\nTotal Cumulative Reward: {total_reward}")

if __name__ == "__main__":
    run_random_agent()
