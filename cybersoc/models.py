"""Pydantic models for OpenEnv spec compliance"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List, Dict, Any
from enum import Enum


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    PHISHING = "phishing"
    MALWARE = "malware"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfil"
    SUSPICIOUS_ACTIVITY = "suspicious"


class Alert(BaseModel):
    id: str = Field(..., description="Unique alert identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    source: str = Field(..., description="Alert source (SIEM, EDR, etc.)")
    severity: AlertSeverity
    alert_type: AlertType
    description: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    affected_assets: List[str] = Field(default_factory=list)


class InvestigationAction(BaseModel):
    action_type: Literal[
        "query_logs",
        "check_reputation",
        "isolate_host",
        "collect_forensics",
        "escalate",
        "conclude",
    ]
    target: Optional[str] = Field(None, description="Target asset/IP/user")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, description="Agent confidence in action")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class CyberSOCObservation(BaseModel):
    current_alert: Alert
    investigation_history: List[InvestigationAction] = Field(default_factory=list)
    available_actions: List[str]
    context_data: Dict[str, Any] = Field(default_factory=dict)
    time_remaining: int = Field(ge=0, description="Steps remaining in episode")
    hints: Optional[List[str]] = Field(default=None, description="Optional guidance")


class CyberSOCAction(BaseModel):
    action: InvestigationAction
    conclusion: Optional[Dict[str, Any]] = Field(
        None, description="Final decision when action_type='conclude'"
    )


class CyberSOCReward(BaseModel):
    step_reward: float = Field(ge=-1.0, le=1.0)
    progress_bonus: float = Field(ge=0.0, le=1.0)  # Increased from 0.5 to 1.0
    penalty: float = Field(ge=-1.0, le=0.0)
    total: float = Field(ge=-2.0, le=2.0)

    @field_validator("total")
    @classmethod
    def validate_total(cls, v, info):
        values = info.data
        expected = (
            values.get("step_reward", 0)
            + values.get("progress_bonus", 0)
            + values.get("penalty", 0)
        )
        if abs(v - expected) > 0.01:
            raise ValueError(f"Total {v} != sum of components {expected}")
        return v


class CyberSOCInfo(BaseModel):
    task_name: str
    episode_id: str
    ground_truth: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
