"""Task implementations for CyberSOC environment"""

from .base_task import BaseTask, ActionResult
from .phishing_triage import PhishingTriageTask
from .malware_investigation import MalwareInvestigationTask
from .incident_response import IncidentResponseTask

__all__ = [
    "BaseTask",
    "ActionResult",
    "PhishingTriageTask",
    "MalwareInvestigationTask",
    "IncidentResponseTask",
]
