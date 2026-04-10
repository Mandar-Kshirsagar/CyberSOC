"""Base task interface for CyberSOC tasks"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..models import Alert, InvestigationAction


class ActionResult(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    is_terminal: bool = False
    metadata: Dict[str, Any] = {}


class BaseTask(ABC):
    """Abstract base class for CyberSOC tasks"""

    def __init__(self):
        self.current_alert: Optional[Alert] = None
        self.ground_truth: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {}

    @abstractmethod
    def generate_alert(self) -> Alert:
        """Generate a new alert for this task"""
        pass

    @abstractmethod
    def execute_action(
        self, action: InvestigationAction, history: List[InvestigationAction]
    ) -> ActionResult:
        """Execute an investigation action and return result"""
        pass

    @abstractmethod
    def get_grader(self):
        """Return the grader for this task"""
        pass

    def get_available_actions(self) -> List[str]:
        """Return list of valid action types for this task"""
        return [
            "query_logs",
            "check_reputation",
            "isolate_host",
            "collect_forensics",
            "escalate",
            "conclude",
        ]

    def get_initial_context(self) -> Dict[str, Any]:
        """Return initial context data"""
        return {}

    def get_updated_context(self) -> Dict[str, Any]:
        """Return updated context data"""
        return self.state.get("context", {})

    def get_initial_hints(self) -> Optional[List[str]]:
        """Return initial hints for the agent"""
        return None

    def get_adaptive_hints(
        self, history: List[InvestigationAction]
    ) -> Optional[List[str]]:
        """Return hints based on investigation progress"""
        return None

    def get_ground_truth(self) -> Dict[str, Any]:
        """Return ground truth for grading"""
        return self.ground_truth

    def get_current_alert(self) -> Alert:
        """Return current alert"""
        return self.current_alert

    def get_state(self) -> Dict[str, Any]:
        """Return current task state"""
        return self.state
