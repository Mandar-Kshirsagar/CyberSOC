"""Tests for CyberSOC environment"""

import pytest
import asyncio
from cybersoc.environment import CyberSOCEnv
from cybersoc.models import CyberSOCAction, InvestigationAction


@pytest.mark.asyncio
async def test_environment_reset():
    """Test environment reset functionality"""
    env = CyberSOCEnv(task_name="phishing_triage")
    observation = await env.reset()

    assert observation is not None
    assert observation.current_alert is not None
    assert observation.time_remaining == 15
    assert len(observation.investigation_history) == 0


@pytest.mark.asyncio
async def test_environment_step():
    """Test environment step functionality"""
    env = CyberSOCEnv(task_name="phishing_triage")
    await env.reset()

    # Take a query action
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="query_logs",
            parameters={"query_type": "email_headers"},
            confidence=0.8,
        )
    )

    observation = await env.step(action)

    assert observation is not None
    assert isinstance(env.done, bool)
    assert len(observation.investigation_history) == 1


@pytest.mark.asyncio
async def test_environment_conclude():
    """Test environment conclusion"""
    env = CyberSOCEnv(task_name="phishing_triage")
    await env.reset()

    # Conclude immediately
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="conclude",
            parameters={"label": "phishing"},
            confidence=0.7,
        ),
        conclusion={"label": "phishing", "reasoning": "Test conclusion"},
    )

    observation = await env.step(action)

    assert env.done is True
    assert observation is not None


@pytest.mark.asyncio
async def test_environment_state():
    """Test environment state retrieval"""
    env = CyberSOCEnv(task_name="phishing_triage")
    await env.reset()

    state = await env.state()

    assert "task_name" in state
    assert "current_step" in state
    assert "max_steps" in state
    assert state["task_name"] == "phishing_triage"
