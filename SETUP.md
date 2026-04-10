# CyberSOC OpenEnv - Quick Setup Guide

## What's Been Implemented

The CyberSOC OpenEnv environment is now ready with the following components:

### Core Components ✅
- **Environment** (`cybersoc/environment.py`): Main OpenEnv-compliant environment
- **Models** (`cybersoc/models.py`): Pydantic models for type safety
- **Rewards** (`cybersoc/rewards.py`): Hierarchical reward function
- **Server** (`cybersoc/server.py`): FastAPI server for HF Space deployment

### Tasks ✅
1. **Phishing Triage** (Easy) - Email classification
2. **Malware Investigation** (Medium) - Host alert analysis

### Graders ✅
- Phishing Grader: Evaluates email triage performance
- Malware Grader: Evaluates investigation completeness

### Infrastructure ✅
- **Dockerfile**: Ready for containerization
- **inference.py**: Baseline LLM agent script
- **Tests**: Unit tests for graders, rewards, and environment
- **Scripts**: Validation and baseline running scripts

## Quick Start

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run Tests
```bash
python -m pytest tests/ -v
```

### 3. Test Environment Locally
```python
import asyncio
from cybersoc.environment import CyberSOCEnv

async def test():
    env = CyberSOCEnv(task_name="phishing_triage")
    obs = await env.reset()
    print(f"Alert: {obs.current_alert.description}")
    
asyncio.run(test())
```

### 4. Run Baseline Inference
```bash
export HF_TOKEN="your_token_here"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
python inference.py
```

### 5. Build Docker Image
```bash
docker build -t cybersoc-openenv:latest .
docker run -p 7860:7860 cybersoc-openenv:latest
```

## Project Structure

```
cybersoc-openenv/
├── cybersoc/
│   ├── __init__.py
│   ├── environment.py       # Main environment
│   ├── models.py            # Pydantic models
│   ├── rewards.py           # Reward calculator
│   ├── server.py            # FastAPI server
│   ├── tasks/
│   │   ├── base_task.py
│   │   ├── phishing_triage.py
│   │   └── malware_investigation.py
│   └── graders/
│       ├── base_grader.py
│       ├── phishing_grader.py
│       └── malware_grader.py
├── tests/
│   ├── test_environment.py
│   ├── test_graders.py
│   └── test_rewards.py
├── scripts/
│   ├── validate-submission.sh
│   └── run_baseline.sh
├── Dockerfile
├── inference.py
├── openenv.yaml
├── requirements.txt
└── README.md
```

## Next Steps

1. **Test the environment**: Run the tests to ensure everything works
2. **Try the baseline**: Run inference.py with your HF token
3. **Deploy to HF Space**: Push to a Hugging Face Space repository
4. **Add third task** (optional): Implement incident_response task for hard difficulty

## Environment API

### Reset
```python
observation = await env.reset()
# Returns: CyberSOCObservation with alert details
```

### Step
```python
action = CyberSOCAction(
    action=InvestigationAction(
        action_type="check_reputation",
        target="sender@example.com",
        confidence=0.8
    )
)
observation = await env.step(action)
```

### Available Actions
- `query_logs`: Examine system/email logs
- `check_reputation`: Verify sender/IP/domain reputation
- `isolate_host`: Quarantine a system
- `collect_forensics`: Gather evidence
- `escalate`: Forward to senior responder
- `conclude`: Make final determination

## Troubleshooting

### Import Errors
Make sure all dependencies are installed:
```bash
python -m pip install -r requirements.txt
```

### Docker Build Issues
Ensure Docker is running and you have sufficient disk space.

### Test Failures
Check that you're in the project root directory when running tests.

## Support

For issues or questions, refer to:
- README.md for detailed documentation
- OpenEnv documentation: https://github.com/openenv/openenv
- Tests for usage examples
