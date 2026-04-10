"""Core CyberSOC Environment Implementation"""

import asyncio
from typing import Optional, Tuple, Dict, Any
from openenv.core import Environment, Observation, Action
from .models import (
    CyberSOCObservation,
    CyberSOCAction,
    CyberSOCReward,
    CyberSOCInfo,
    Alert,
    InvestigationAction,
)
from .tasks import BaseTask, PhishingTriageTask
from .rewards import RewardCalculator
from .graders import BaseGrader


class CyberSOCEnv(Environment):
    """Cybersecurity Incident Response Simulation Environment
    
    Agents act as SOC analysts, receiving alerts and making investigation decisions.
    """

    def __init__(self, task_name: str = "phishing_triage"):
        super().__init__()
        self.task_name = task_name
        self.task: BaseTask = self._load_task(task_name)
        self.grader: BaseGrader = self.task.get_grader()
        self.reward_calc = RewardCalculator(task_name)
        self.current_step = 0
        self.max_steps = 15
        self.done = False
        self.history = []
        self.total_reward = 0.0

    def _load_task(self, task_name: str) -> BaseTask:
        from .tasks import PhishingTriageTask, MalwareInvestigationTask, IncidentResponseTask
        
        tasks = {
            "phishing_triage": PhishingTriageTask,
            "malware_investigation": MalwareInvestigationTask,
            "incident_response": IncidentResponseTask,
        }
        if task_name not in tasks:
            raise ValueError(f"Unknown task: {task_name}")
        return tasks[task_name]()

    async def reset(self) -> Observation:
        """Reset environment to initial state"""
        self.current_step = 0
        self.done = False
        self.history = []
        self.total_reward = 0.0

        # Generate initial alert based on task
        alert = self.task.generate_alert()

        observation = CyberSOCObservation(
            current_alert=alert,
            investigation_history=[],
            available_actions=self.task.get_available_actions(),
            context_data=self.task.get_initial_context(),
            time_remaining=self.max_steps,
            hints=self.task.get_initial_hints(),
        )

        return observation

    async def step(self, action: Action) -> Observation:
        """Execute agent action and return new state"""
        if self.done:
            raise RuntimeError("Episode already completed. Call reset() first.")

        self.current_step += 1

        # Parse action - expecting CyberSOCAction format
        if isinstance(action, dict):
            cyber_action = CyberSOCAction(**action)
        else:
            cyber_action = action

        # Validate and execute action
        try:
            result = self.task.execute_action(cyber_action.action, self.history)
            self.history.append(cyber_action.action)

            # Calculate reward with partial progress signals
            reward_components = self.reward_calc.calculate(
                action=cyber_action.action,
                result=result,
                step=self.current_step,
                history=self.history,
                task_state=self.task.get_state(),
            )
            self.total_reward += reward_components.total

            # Check termination conditions
            self.done = (
                cyber_action.action.action_type == "conclude"
                or self.current_step >= self.max_steps
                or result.is_terminal
            )

            # Generate new observation
            observation = CyberSOCObservation(
                current_alert=self.task.get_current_alert(),
                investigation_history=self.history.copy(),
                available_actions=self.task.get_available_actions(),
                context_data=self.task.get_updated_context(),
                time_remaining=max(0, self.max_steps - self.current_step),
                hints=self.task.get_adaptive_hints(self.history),
            )

            return observation

        except Exception as e:
            # Handle invalid actions gracefully
            return self._get_error_observation(str(e))

    async def state(self) -> Dict[str, Any]:
        """Return current environment state for debugging"""
        return {
            "task_name": self.task_name,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "done": self.done,
            "total_reward": self.total_reward,
            "history": [a.dict() for a in self.history],
            "task_state": self.task.get_state(),
        }

    def _get_error_observation(self, error_msg: str) -> CyberSOCObservation:
        """Fallback observation for error states"""
        from .models import AlertSeverity, AlertType

        return CyberSOCObservation(
            current_alert=Alert(
                id="error",
                timestamp="2024-01-01T00:00:00Z",
                source="system",
                severity=AlertSeverity.LOW,
                alert_type=AlertType.SUSPICIOUS_ACTIVITY,
                description=f"Environment error: {error_msg}",
            ),
            investigation_history=self.history.copy(),
            available_actions=["conclude"],
            context_data={"error": error_msg},
            time_remaining=max(0, self.max_steps - self.current_step),
        )
