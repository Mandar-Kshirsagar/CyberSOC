"""Reward function implementation for CyberSOC tasks"""

from typing import Dict, List
from .models import InvestigationAction, CyberSOCReward
from .tasks.base_task import ActionResult


class RewardCalculator:
    """Hierarchical reward function with partial progress signals
    
    Design Principles:
    1. Dense rewards: Provide signal at every step, not just episode end
    2. Shaped rewards: Guide agent toward good investigation practices
    3. Penalize anti-patterns: Infinite loops, destructive actions, rash conclusions
    4. Task-adaptive: Different weightings for easy/medium/hard tasks
    """

    def __init__(self, task_name: str):
        self.task_name = task_name
        self.weights = self._get_task_weights(task_name)

    def _get_task_weights(self, task_name: str) -> Dict[str, float]:
        """Task-specific reward weightings"""
        base_weights = {
            "useful_action": 0.1,  # +0.1 for valid investigation step
            "progress_milestone": 0.3,  # +0.3 for correct intermediate conclusion
            "correct_final": 0.6,  # +0.6 for correct final decision
            "efficiency_bonus": 0.1,  # +0.1 for completing in ≤N steps
            "invalid_action": -0.1,  # -0.1 for nonsensical action
            "destructive_action": -0.3,  # -0.3 for harmful action
            "premature_conclusion": -0.2,  # -0.2 for concluding without investigation
            "timeout": -0.5,  # -0.5 for exceeding step limit without conclusion
        }

        # Adjust weights by task difficulty
        if task_name == "phishing_triage":
            base_weights["progress_milestone"] = 0.0  # Single-step task
            base_weights["correct_final"] = 0.8
        elif task_name == "incident_response":
            base_weights["progress_milestone"] = 0.4  # Reward multi-step coordination
            base_weights["efficiency_bonus"] = 0.2

        return base_weights

    def calculate(
        self,
        action: InvestigationAction,
        result: ActionResult,
        step: int,
        history: List,
        task_state: Dict,
    ) -> CyberSOCReward:
        """Calculate reward components for this step"""
        step_reward = 0.0
        progress_bonus = 0.0
        penalty = 0.0

        # Base action reward
        if result.success:
            if self._is_useful_investigation(action, task_state):
                step_reward += self.weights["useful_action"]
        else:
            penalty += self.weights["invalid_action"]

        # Progress detection
        if self._reached_milestone(action, result, history, task_state):
            progress_bonus += self.weights["progress_milestone"]

        # Final conclusion evaluation
        if action.action_type == "conclude":
            if self._is_correct_conclusion(action, result, task_state):
                progress_bonus += self.weights["correct_final"]
            elif len(history) < 2:
                penalty += self.weights["premature_conclusion"]

        # Anti-pattern penalties
        if self._is_destructive(action):
            penalty += self.weights["destructive_action"]

        if self._is_repetitive_loop(history, action):
            penalty += self.weights["invalid_action"] * 2

        # Efficiency consideration (only on completion)
        if action.action_type == "conclude" and result.is_terminal:
            if step <= self._get_efficiency_threshold():
                progress_bonus += self.weights["efficiency_bonus"]

        # Timeout penalty
        if step >= 15 and action.action_type != "conclude":
            penalty += self.weights["timeout"]

        total = step_reward + progress_bonus + penalty

        # Clamp to valid range
        total = max(-2.0, min(2.0, total))

        return CyberSOCReward(
            step_reward=round(step_reward, 2),
            progress_bonus=round(progress_bonus, 2),
            penalty=round(penalty, 2),
            total=round(total, 2),
        )

    def _is_useful_investigation(
        self, action: InvestigationAction, task_state: Dict
    ) -> bool:
        """Heuristic: Does this action gather relevant information?"""
        useful_actions = {"query_logs", "check_reputation", "collect_forensics"}
        return action.action_type in useful_actions

    def _reached_milestone(
        self, action, result, history, task_state
    ) -> bool:
        """Detect meaningful progress toward task completion"""
        return result.metadata.get("milestone_reached", False)

    def _is_correct_conclusion(
        self, action: InvestigationAction, result: ActionResult, task_state: Dict
    ) -> bool:
        """Check if conclusion matches ground truth"""
        ground_truth = task_state.get("ground_truth", {})
        classification = result.data.get("classification", "").lower()
        
        if "is_phishing" in ground_truth:
            expected = "phishing" if ground_truth["is_phishing"] else "legitimate"
            return classification == expected
        
        return False

    def _is_destructive(self, action: InvestigationAction) -> bool:
        """Identify actions that would cause harm in production"""
        destructive_actions = {"isolate_host", "block_ip"}
        return action.action_type in destructive_actions and action.confidence < 0.8

    def _is_repetitive_loop(
        self, history: List, current_action: InvestigationAction
    ) -> bool:
        """Detect if agent is repeating the same action without progress"""
        if len(history) < 3:
            return False
        recent = [a.action_type for a in history[-3:]]
        return recent.count(current_action.action_type) >= 3

    def _get_efficiency_threshold(self) -> int:
        """Get step threshold for efficiency bonus"""
        thresholds = {
            "phishing_triage": 5,
            "malware_investigation": 10,
            "incident_response": 15,
        }
        return thresholds.get(self.task_name, 10)
