---
title: Cyber Defender Env
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# Autonomous Intrusion Response Environment

## Description and Motivation
The Autonomous Intrusion Response Environment (CyberSecurityEnv) is an OpenEnv specifications compliant environment that trains AI agents to act as automated cybersecurity defenders within a Security Operations Center (SOC). 
Modern SOC analysts often deal with massive alert fatigue and delayed responses to active intrusions. This environment bridges the gap by enabling reinforcement learning agents to actively monitor threat logs, deep-scan network nodes for hidden irregularities, and enact life-saving mitigation maneuvers in real-time.

## Spaces
### Observation Space
The state is exposed as a typed object containing:
- `threat_level` (int): Scale from 0 to 10 defining global threat heuristics.
- `anomaly_score` (float): From 0.0 to 1.0 indicating suspicious payload traffic.
- `system_health` (float): From 0.0 to 100.0, the core metric for survival.
- `intrusion_detected` (bool): A strict boolean flag indicating a heavily verified threat present.

### Action Space
Discrete actions mapped directly to SOC capabilities:
- `0`: **MONITOR** (Passively observes, recovers health slowly if safe, but allows attacks to damage system).
- `1`: **DEEP_SCAN** (Actively investigates anomalies to confirm true `intrusion_detected` status, costs steps).
- `2`: **BLOCK_IP** (Standard mitigation for isolating external nodes).
- `3`: **ISOLATE_HOST** (Severe mitigation to quarantine an internal sector).

*(Action 2 and 3 both neutralize threats natively in this abstraction but carry heavy score penalties if executed mistakenly during a False-Positive).*

## Tasks
The environment comprises three heavily graded tasks with rewards normalized to `[0.0, 1.0]`:
1. **Easy (`easy`)**: A single, obvious active threat is engaged immediately on reset. The agent must successfully `BLOCK_IP` or `ISOLATE_HOST` to resolve it efficiently.
2. **Medium (`medium`)**: A stealthier sequence mimicking normal operations but utilizing decoy false-positives. The agent must use `DEEP_SCAN` appropriately to investigate before blocking.
3. **Hard (`hard`)**: Extremely volatile attacks triggering major health penalties immediately. The agent must prioritize action over extended monitoring to preserve maximum health score logic.

## Baseline Scores
Running `./baseline_inference.py` deterministically solves the challenges with the following heuristic benchmark scores:
* **Easy**: ~0.95+
* **Medium**: ~0.90+
* **Hard**: ~0.85+

## Setup & Usage Instructions

### Docker Execution (Hugging Face / OpenEnv Compliant)
The repository is packed with a production-ready HF Spaces `Dockerfile`.
```bash
docker build -t openenv-cyber .
docker run -p 7860:7860 openenv-cyber
```
This deploys the backend server on port 7860 natively.

### Direct Python Execution
```bash
pip install fastapi uvicorn pydantic requests
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Running Inference
In a separate terminal, to execute the agent:
```bash
python baseline_inference.py
```
