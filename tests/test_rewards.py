"""Tests for CyberSOC reward function"""

import pytest
from cybersoc.rewards import RewardCalculator
from cybersoc.models import InvestigationAction
from cybersoc.tasks.base_task import ActionResult


def test_reward_calculator_useful_action():
    """Test reward for useful investigation action"""
    calc = RewardCalculator("phishing_triage")

    action = InvestigationAction(
        action_type="query_logs", confidence=0.8, parameters={}
    )
    result = ActionResult(success=True, data={})

    reward = calc.calculate(
        action=action, result=result, step=1, history=[], task_state={}
    )

    assert reward.step_reward > 0
    assert -2.0 <= reward.total <= 2.0


def test_reward_calculator_invalid_action():
    """Test penalty for invalid action"""
    calc = RewardCalculator("phishing_triage")

    action = InvestigationAction(
        action_type="query_logs", confidence=0.8, parameters={}
    )
    result = ActionResult(success=False, data={})

    reward = calc.calculate(
        action=action, result=result, step=1, history=[], task_state={}
    )

    assert reward.penalty < 0
    assert -2.0 <= reward.total <= 2.0


def test_reward_calculator_repetitive_loop():
    """Test penalty for repetitive actions"""
    calc = RewardCalculator("phishing_triage")

    action = InvestigationAction(
        action_type="query_logs", confidence=0.8, parameters={}
    )
    result = ActionResult(success=True, data={})

    # Create history with repeated actions
    history = [
        InvestigationAction(action_type="query_logs", confidence=0.8, parameters={})
        for _ in range(3)
    ]

    reward = calc.calculate(
        action=action, result=result, step=4, history=history, task_state={}
    )

    assert reward.penalty < 0  # Should penalize repetition


def test_reward_calculator_correct_conclusion():
    """Test reward for correct conclusion"""
    calc = RewardCalculator("phishing_triage")

    action = InvestigationAction(
        action_type="conclude", confidence=0.8, parameters={"label": "phishing"}
    )
    result = ActionResult(
        success=True, is_terminal=True, data={"classification": "phishing"}
    )

    # Add some investigation history to avoid premature conclusion penalty
    history = [
        InvestigationAction(action_type="query_logs", confidence=0.8, parameters={}),
        InvestigationAction(action_type="check_reputation", confidence=0.8, parameters={}),
    ]

    task_state = {"ground_truth": {"is_phishing": True}}

    reward = calc.calculate(
        action=action, result=result, step=3, history=history, task_state=task_state
    )

    # Should get positive reward for correct conclusion
    assert reward.total > 0


def test_reward_components_sum():
    """Test that reward components sum correctly"""
    calc = RewardCalculator("phishing_triage")

    action = InvestigationAction(
        action_type="query_logs", confidence=0.8, parameters={}
    )
    result = ActionResult(success=True, data={})

    reward = calc.calculate(
        action=action, result=result, step=1, history=[], task_state={}
    )

    # Check that total equals sum of components (within floating point tolerance)
    expected_total = reward.step_reward + reward.progress_bonus + reward.penalty
    assert abs(reward.total - expected_total) < 0.01
