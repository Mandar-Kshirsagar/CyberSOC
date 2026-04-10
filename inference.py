"""CyberSOC Baseline Inference Script

Runs a baseline LLM agent against the CyberSOC environment.

ENVIRONMENT VARIABLES (REQUIRED):
API_BASE_URL   - LLM API endpoint (default: Hugging Face router)
MODEL_NAME     - Model identifier for inference
HF_TOKEN       - Hugging Face API key
IMAGE_NAME     - Docker image name for local testing

STDOUT FORMAT (STRICT):
[START] task=<name> env=cybersoc model=<model>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<bool> error=<msg|null>
[END]   success=<bool> steps=<n> score=<score> rewards=<r1,r2,...>
"""

import asyncio
import os
import json
import textwrap
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] openai package not installed. Run: pip install openai")
    exit(1)

# Import environment
from cybersoc.environment import CyberSOCEnv
from cybersoc.models import CyberSOCAction, InvestigationAction

# === Configuration from Environment Variables ===
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
TASK_NAME = os.getenv("CYBERSOC_TASK", "phishing_triage")
BENCHMARK = "cybersoc"
MAX_STEPS = 15
TEMPERATURE = 0.3
MAX_TOKENS = 300

# Scoring thresholds
SUCCESS_SCORE_THRESHOLD = 0.5

# === System Prompt for Security Analyst Persona ===
SYSTEM_PROMPT = textwrap.dedent(
    """
You are a senior Security Operations Center (SOC) analyst. Your task is to investigate security alerts and make accurate decisions.

AVAILABLE ACTIONS:
- query_logs: Examine system/email logs for indicators
- check_reputation: Verify sender/IP/domain reputation
- isolate_host: Quarantine a compromised system (use cautiously)
- collect_forensics: Gather evidence for analysis
- escalate: Forward to senior incident responder
- conclude: Make final determination (REQUIRED to end episode)

GUIDELINES:
1. Gather evidence before concluding
2. Prefer non-destructive actions when uncertain
3. Calibrate confidence: high confidence only with strong evidence
4. For phishing: check sender reputation, email headers, link safety
5. For malware: examine process trees, network connections, file hashes
6. For incidents: prioritize containment, preserve evidence, document timeline

RESPONSE FORMAT:
Return a JSON object with:
{
    "action_type": "query_logs|check_reputation|...|conclude",
    "target": "optional target identifier",
    "parameters": {"key": "value"},
    "confidence": 0.0-1.0,
    "conclusion": {"label": "phishing|legitimate|malware|benign", "reasoning": "..."} // only for conclude
}

Be concise and precise. Security decisions have real consequences.
"""
).strip()


# === Logging Functions (MANDATORY FORMAT) ===
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action_str: str, reward: float, done: bool, error: Optional[str]
) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# === LLM Interaction ===
def build_user_prompt(step: int, observation: dict, history: List[str]) -> str:
    """Construct prompt from environment observation"""
    alert = observation["current_alert"]
    available = observation["available_actions"]
    context = observation.get("context_data", {})
    hints = observation.get("hints", [])

    prompt = textwrap.dedent(
        f"""
STEP {step}/{MAX_STEPS}

ALERT DETAILS:
- ID: {alert["id"]}
- Type: {alert["alert_type"]}
- Severity: {alert["severity"]}
- Source: {alert["source"]}
- Description: {alert["description"]}

RAW DATA: {json.dumps(alert["raw_data"], indent=2)[:500]}...

AVAILABLE ACTIONS: {", ".join(available)}

INVESTIGATION HISTORY:
{chr(10).join(history[-3:]) if history else "  (none yet)"}

CONTEXT: {json.dumps(context, indent=2)[:300]}

HINTS: {hints if hints else "  (none)"}

What action do you take? Return valid JSON.
"""
    ).strip()

    return prompt


def get_agent_action(
    client: OpenAI, step: int, observation: dict, history: List[str]
) -> CyberSOCAction:
    """Get action from LLM with error handling"""
    user_prompt = build_user_prompt(step, observation, history)

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

        content = (completion.choices[0].message.content or "").strip()

        # Parse JSON response
        try:
            # Handle markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```json")[-1].split("```")[0].strip()
            action_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: extract JSON from text
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                action_data = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from: {content[:100]}")

        # Convert to CyberSOCAction
        investigation = InvestigationAction(
            action_type=action_data["action_type"],
            target=action_data.get("target"),
            parameters=action_data.get("parameters", {}),
            confidence=action_data.get("confidence", 0.5),
        )

        conclusion = (
            action_data.get("conclusion")
            if action_data["action_type"] == "conclude"
            else None
        )

        return CyberSOCAction(action=investigation, conclusion=conclusion)

    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        # Safe fallback action
        return CyberSOCAction(
            action=InvestigationAction(
                action_type="conclude", confidence=0.3, parameters={"fallback": True}
            ),
            conclusion={"label": "unknown", "reasoning": "Error generating action"},
        )


# === Main Execution Loop ===
async def main() -> None:
    if not HF_TOKEN:
        print("[ERROR] HF_TOKEN environment variable not set")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    # Initialize environment
    env = CyberSOCEnv(task_name=TASK_NAME)

    # Episode state tracking
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    # Log episode start (MANDATORY)
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset environment
        result = await env.reset()
        observation = result.observation.dict()

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            # Get action from agent
            action = get_agent_action(client, step, observation, history)

            # Execute action
            result = await env.step(action)
            observation = result.observation.dict()

            # Extract logging data
            reward = result.reward if result.reward is not None else 0.0
            done = result.done
            error = result.info.metadata.get("error") if result.info else None

            # Format action for logging (concise representation)
            action_str = f"{action.action.action_type}({action.action.target or 'self'})"

            # Log step (MANDATORY)
            log_step(step=step, action_str=action_str, reward=reward, done=done, error=error)

            # Update tracking
            rewards.append(reward)
            steps_taken = step
            history.append(f"Step {step}: {action_str} → reward {reward:+.2f}")

            if done:
                break

        # Calculate final score (normalized to [0, 1])
        total_reward = sum(rewards)
        # Normalize: assume max possible reward is 2.0 per step * MAX_STEPS
        max_possible = 2.0 * MAX_STEPS
        score = min(1.0, max(0.0, total_reward / max_possible))
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Episode error: {e}", flush=True)
        success = False
        score = 0.0

    finally:
        # Log end (ALWAYS EMIT [END])
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())
