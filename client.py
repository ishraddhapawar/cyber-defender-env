import requests
from urllib.parse import urljoin
from models import Action, Observation, StepResponse

class HTTPEnvClient:
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url
        
    def reset(self, task_id: str = "easy") -> Observation:
        url = urljoin(self.base_url, "/reset")
        payload = {"task_id": task_id}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return Observation(**data["observation"])
        
    def step(self, action: Action) -> StepResponse:
        url = urljoin(self.base_url, "/step")
        payload = {"action": action.value}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return StepResponse(**response.json())
        
    def state(self) -> dict:
        url = urljoin(self.base_url, "/state")
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Test runner script simulation
if __name__ == "__main__":
    import random
    
    print("Testing HTTP Env Client...")
    client = HTTPEnvClient()
    
    try:
        obs = client.reset()
        print("[*] Environment Reset")
        print(f"    Initial Observation: {obs}")
        
        total_reward = 0.0
        
        for i in range(1, 15):
            # Select random action
            action = random.choice(list(Action))
            step_info = client.step(action)
            
            total_reward += step_info.reward
            
            print(f"[*] Step {i} - Action: {action.name}")
            print(f"    Reward: {step_info.reward}")
            print(f"    Obs: {step_info.observation}")
            print(f"    Terminated: {step_info.terminated}")
            
            if step_info.terminated or step_info.truncated:
                print(f"[!] Episode complete. Total Reward: {total_reward}")
                break
    except requests.exceptions.ConnectionError:
        print("[!] Connection Error: Is the FastAPI server running?")
