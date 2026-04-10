# 🛡️ CyberSOC OpenEnv Environment

> AI-powered Cybersecurity Incident Response Simulator for training and evaluating security analyst agents

## 🎯 Environment Description

CyberSOC simulates a real Security Operations Center (SOC) where AI agents act as security analysts. Agents receive simulated security alerts, investigate using available tools, and make response decisions. The environment provides a safe, scalable platform for training RL agents on cybersecurity reasoning tasks.

### Why CyberSOC?

- **Real-world relevance**: Models actual SOC analyst workflows
- **Progressive difficulty**: Three tasks from email triage to complex incident response
- **Meaningful rewards**: Dense reward signals guide learning toward effective investigation practices
- **Standardized evaluation**: Deterministic graders enable fair comparison across agents

## 📦 Action & Observation Spaces

### Observation Space (`CyberSOCObservation`)

```python
{
    "current_alert": Alert,           # Current security alert details
    "investigation_history": List[Action],  # Actions taken so far
    "available_actions": List[str],   # Valid actions this step
    "context_data": Dict,            # Task-specific context (logs, assets, etc.)
    "time_remaining": int,           # Steps left in episode
    "hints": Optional[List[str]]     # Optional guidance (more in easy tasks)
}
```

### Action Space (`CyberSOCAction`)

```python
{
    "action": {
        "action_type": "query_logs|check_reputation|isolate_host|collect_forensics|escalate|conclude",
        "target": Optional[str],        # Asset/IP/user to investigate
        "parameters": Dict,             # Action-specific parameters
        "confidence": float             # Agent confidence (0.0-1.0)
    },
    "conclusion": Optional[Dict]      # Final decision (only when action_type="conclude")
}
```

## 🎮 Tasks & Difficulty Progression

### Task 1: Phishing Email Triage (Easy)
- **Objective**: Classify email alerts as phishing or legitimate
- **Max Steps**: 10
- **Success Criteria**: Correct classification with appropriate confidence
- **Key Skills**: Indicator analysis, reputation checking, confidence calibration

### Task 2: Malware Investigation (Medium)
- **Objective**: Determine if host alert indicates active malware infection
- **Max Steps**: 15
- **Success Criteria**: Correct malware identification + complete investigation trail
- **Key Skills**: Multi-source correlation, process analysis, evidence gathering

### Task 3: Multi-Vector Incident Response (Hard)
- **Objective**: Contain coordinated attack across multiple systems
- **Max Steps**: 20
- **Success Criteria**: Accurate timeline, effective containment, minimal false positives
- **Key Skills**: Strategic prioritization, cross-system correlation, business impact assessment

## 🚀 Setup & Usage

### Prerequisites
- Python 3.10+
- Docker (for containerized execution)
- Hugging Face account (for Space deployment)

### Local Development

```bash
# Clone repository
git clone https://github.com/your-org/cybersoc-openenv
cd cybersoc-openenv

# Install dependencies
pip install -r requirements.txt

# Validate OpenEnv spec
openenv validate

# Run tests
pytest tests/
```

### Docker Execution

```bash
# Build image
docker build -t cybersoc-openenv:latest .

# Run environment server
docker run -p 7860:7860 cybersoc-openenv:latest

# Test reset endpoint
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{}'
```

### Running Baseline Inference

```bash
# Set required environment variables
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_hf_token_here"
export IMAGE_NAME="cybersoc-openenv:latest"

# Run inference on all tasks
python inference.py
```

## 📜 License

Apache License 2.0 - See LICENSE file for details.

## 🙏 Acknowledgments

- OpenEnv team for specification and tooling
- Cybersecurity practitioners who informed task design
- Hugging Face for Spaces infrastructure
