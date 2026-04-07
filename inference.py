import os
import textwrap
from typing import List, Optional
from openai import OpenAI

from client import HTTPEnvClient
from models import Action

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
BENCHMARK = os.getenv("BENCHMARK", "CyberSecurityEnv")
MAX_STEPS = 20
TEMPERATURE = 0.3
MAX_TOKENS = 50

SYSTEM_PROMPT = textwrap.dedent(
    """
    Evaluate the provided threat_level (0-10), anomaly_score (0.0-1.0), and intrusion_detected (bool).
    Available Actions:
    0 = MONITOR (do nothing, observe)
    1 = DEEP_SCAN (investigate high anomaly without penalty, clarifies intrusion status)
    2 = BLOCK_IP (neutralize exact threat, penalizes -0.5 if False Positive)
    3 = ISOLATE_HOST (severe quarantine, same neutralization and penalty mechanics)
    
    Respond with EXACTLY ONE DIGIT corresponding to your action choice: 0, 1, 2, or 3. No other text or prefix.
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True, # Added space required? No, example: [STEP] step=1 action=click('123') reward=0.00 done=false error=null
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(step: int, obs: dict, history: List[str]) -> str:
    history_block = "\n".join(history[-4:]) if history else "None"
    return textwrap.dedent(
        f"""
        Step: {step}
        Observation state:
        - Threat Level: {obs['threat_level']}
        - Anomaly Score: {obs['anomaly_score']:.2f}
        - System Health: {obs['system_health']:.2f}/100.0
        - Intrusion Verified: {obs['intrusion_detected']}
        
        Previous actions:
        {history_block}
        
        Choose your next action (0, 1, 2, or 3):
        """
    ).strip()

def get_model_action(client: OpenAI, step: int, obs: dict, history: List[str]) -> Action:
    user_prompt = build_user_prompt(step, obs, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        
        # Extract integer from text safely
        import re
        match = re.search(r'[0-3]', text)
        if match:
            return Action(int(match.group(0)))
        return Action.MONITOR
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return Action.MONITOR

def main():
    # If using local docker without port setting, defaults to localhost:8000
    env_url = os.getenv("ENV_URL", "http://localhost:7860")
    client_env = HTTPEnvClient(base_url=env_url)
    
    # Initialize LLM Client
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    tasks_to_run = ["easy", "medium", "hard"]
    task_override = os.getenv("TASK_NAME")
    if task_override:
        tasks_to_run = [task_override]
        
    for task_name in tasks_to_run:
        history: List[str] = []
        rewards: List[float] = []
        steps_taken = 0
        success = False
        final_score = 0.0
        
        log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
        
        try:
            obs = client_env.reset(task_id=task_name)
            
            for step in range(1, MAX_STEPS + 1):
                # We need obs as dict for prompt formatter
                # Observation is a pydantic model, convert to dict properly for v2
                obs_dict = obs.model_dump()
                
                action = get_model_action(client, step, obs_dict, history)
                
                step_info = client_env.step(action)
                reward = step_info.reward or 0.0
                done = step_info.terminated or step_info.truncated
                obs = step_info.observation
                error = None
                
                rewards.append(reward)
                steps_taken = step
                
                action_str = action.name
                log_step(step=step, action=action_str, reward=reward, done=done, error=error)
                
                history.append(f"Step {step}: took {action.name} -> reward {reward:+.2f}")
                
                if done:
                    # Score is simply the final reward since it is normalized [0, 1] internally!
                    final_score = float(reward)
                    break
            
            # Clamp and set success flag
            final_score = min(max(final_score, 0.0), 1.0)
            success = final_score > 0.5  # Arbitrary threshold to evaluate success
                
        except Exception as e:
            print(f"[DEBUG] env error: {e}", flush=True)
            
        finally:
            log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)

if __name__ == "__main__":
    main()
