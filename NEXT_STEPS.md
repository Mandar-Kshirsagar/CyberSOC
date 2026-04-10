# CyberSOC OpenEnv - Next Steps

## ✅ Completed

- Core environment implementation with OpenEnv compliance
- Two complete tasks (Phishing Triage, Malware Investigation)
- Graders with deterministic scoring
- Reward function with partial progress signals
- FastAPI server for deployment
- Baseline inference script
- Full test suite (14/14 tests passing)
- Docker configuration
- Documentation

## 🎯 Recommended Next Steps

### 1. Test the Environment Locally (5 minutes)

Create a simple test script to verify everything works:

```python
# test_local.py
import asyncio
from cybersoc.environment import CyberSOCEnv
from cybersoc.models import CyberSOCAction, InvestigationAction

async def main():
    env = CyberSOCEnv(task_name="phishing_triage")
    
    # Reset
    obs = await env.reset()
    print(f"🚨 Alert: {obs.current_alert.description}")
    print(f"📧 Sender: {obs.current_alert.raw_data.get('sender')}")
    print(f"💡 Hints: {obs.hints}")
    
    # Take action
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="check_reputation",
            target=obs.current_alert.raw_data.get('sender'),
            confidence=0.8
        )
    )
    
    obs = await env.step(action)
    print(f"\n✅ Action taken, {obs.time_remaining} steps remaining")
    
    # Conclude
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="conclude",
            confidence=0.7,
            parameters={"label": "phishing"}
        ),
        conclusion={"label": "phishing", "reasoning": "Suspicious sender"}
    )
    
    obs = await env.step(action)
    print(f"🏁 Episode complete: {env.done}")
    print(f"📊 Total reward: {env.total_reward:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_local.py
```

### 2. Test the FastAPI Server (10 minutes)

Start the server locally:
```bash
python -m uvicorn cybersoc.server:app --host 0.0.0.0 --port 7860
```

Test the endpoints:
```bash
# Health check
curl http://localhost:7860/health

# Reset environment
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "phishing_triage"}'

# Get state
curl http://localhost:7860/state
```

### 3. Build and Test Docker Image (15 minutes)

```bash
# Build
docker build -t cybersoc-openenv:latest .

# Run
docker run -p 7860:7860 cybersoc-openenv:latest

# Test (in another terminal)
curl http://localhost:7860/health
```

### 4. Run Baseline Inference (Optional - requires HF token)

If you have a Hugging Face token:

```bash
//export HF_TOKEN="your_token_here"
export HF_TOKEN="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"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export API_BASE_URL="https://router.huggingface.co/v1"

python inference.py
```

Expected output format:
```
[START] task=phishing_triage env=cybersoc model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=check_reputation(sender@example.com) reward=0.10 done=false error=null
[STEP] step=2 action=conclude(self) reward=0.80 done=true error=null
[END] success=true steps=2 score=0.450 rewards=0.10,0.80
```

### 5. Deploy to Hugging Face Space (30 minutes)

#### Option A: Create New Space
1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose "Docker" as SDK
4. Name it "cybersoc-openenv"
5. Clone the repo and push your code

#### Option B: Use Existing Repo
```bash
# Add HF remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/cybersoc-openenv

# Push
git push hf main
```

The Space will automatically:
- Build the Docker image
- Start the FastAPI server on port 7860
- Expose the /reset, /step, /state, /health endpoints

### 6. Validate OpenEnv Compliance (5 minutes)

```bash
# If openenv CLI is available
openenv validate

# Check all required files exist
ls openenv.yaml
ls Dockerfile
ls inference.py
ls README.md
```

### 7. Add Third Task (Optional - 2-3 hours)

Create `cybersoc/tasks/incident_response.py` for the hard difficulty task:

```python
"""Incident Response Task - Hard Difficulty"""

class IncidentResponseTask(BaseTask):
    """Task: Coordinate response to multi-vector security incident
    
    Difficulty: Hard - Multi-host, multi-stage attack
    Success Criteria: Accurate timeline, effective containment, minimal false positives
    """
    
    def generate_alert(self) -> Alert:
        # Generate coordinated attack scenario
        # - Multiple affected hosts
        # - Lateral movement indicators
        # - Data exfiltration attempts
        pass
    
    def execute_action(self, action, history) -> ActionResult:
        # Handle complex investigation actions
        # - Cross-host correlation
        # - Timeline reconstruction
        # - Containment actions
        pass
```

Then add the grader in `cybersoc/graders/incident_grader.py`.

### 8. Improve Documentation (30 minutes)

Add to README.md:
- Example episodes with screenshots
- Baseline performance benchmarks
- Common failure modes
- Tips for training agents

### 9. Create Demo Video/GIF (Optional - 1 hour)

Record a demo showing:
1. Environment reset
2. Agent taking investigation actions
3. Final conclusion and scoring
4. Different task difficulties

### 10. Submit to OpenEnv Competition

Once everything is tested:
1. Ensure all validation checks pass
2. Deploy to HF Space with `openenv` tag
3. Submit the Space URL
4. Include baseline scores in README

## 🔍 Validation Checklist

Before submission, verify:

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Docker builds successfully
- [ ] Docker container runs and responds to /reset
- [ ] inference.py produces correct [START]/[STEP]/[END] format
- [ ] openenv.yaml is valid
- [ ] README.md has all required sections
- [ ] Graders are deterministic (same input = same output)
- [ ] Tasks have clear success criteria
- [ ] Baseline scores are documented

## 📊 Expected Baseline Scores

Target scores for a basic LLM agent:

| Task | Difficulty | Target Score | Success Rate |
|------|-----------|--------------|--------------|
| Phishing Triage | Easy | 0.60-0.70 | 70-80% |
| Malware Investigation | Medium | 0.45-0.55 | 50-60% |
| Incident Response | Hard | 0.30-0.40 | 30-40% |

## 🐛 Known Issues / Future Improvements

1. **State management**: Currently simple dict, could use more structured state
2. **Alert generation**: Templates are static, could be more dynamic
3. **Reward shaping**: Could add more nuanced partial rewards
4. **Third task**: Incident response task not yet implemented
5. **Visualization**: No built-in visualization of investigation timeline
6. **Multi-agent**: No support for collaborative investigation

## 🎓 Learning Resources

- OpenEnv docs: https://github.com/openenv/openenv
- MITRE ATT&CK: https://attack.mitre.org/
- NIST Incident Response: https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final
- Pydantic docs: https://docs.pydantic.dev/

## 💡 Ideas for Extensions

1. **Adaptive difficulty**: Adjust alert complexity based on agent performance
2. **Adversarial mode**: Generate alerts designed to fool the agent
3. **Human-in-the-loop**: Allow human analysts to provide feedback
4. **Multi-agent**: Team of specialized agents (triage, investigation, response)
5. **Real data**: Train on anonymized real SOC data
6. **Explainability**: Require agents to justify their decisions
7. **Time pressure**: Add time constraints for realistic SOC environment
8. **Cost modeling**: Different actions have different costs (API calls, analyst time)

## 🚀 Quick Commands Reference

```bash
# Run tests
python -m pytest tests/ -v

# Start server
python -m uvicorn cybersoc.server:app --reload

# Build Docker
docker build -t cybersoc-openenv:latest .

# Run Docker
docker run -p 7860:7860 cybersoc-openenv:latest

# Run inference
python inference.py

# Validate
openenv validate
```

---

**Current Status**: ✅ Core implementation complete, ready for local testing and deployment

**Recommended Next Action**: Test locally with `test_local.py` script, then build Docker image
