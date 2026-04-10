"""Phishing Email Triage Task - Easy Difficulty"""

import random
from datetime import datetime
from uuid import uuid4
from typing import List, Optional
from .base_task import BaseTask, ActionResult
from ..models import Alert, AlertSeverity, AlertType, InvestigationAction


# Phishing email templates
PHISHING_TEMPLATES = [
    {
        "sender": "security@paypa1-verify.com",
        "subject": "Urgent: Verify your account now",
        "body": "Your account has been locked. Click here to verify: http://paypa1-verify.com/login",
        "links": ["http://paypa1-verify.com/login"],
        "attachments": [],
        "headers": {"SPF": "fail", "DKIM": "fail"},
        "indicators": ["suspicious_domain", "urgency", "spf_fail"],
    },
    {
        "sender": "admin@company-internal.xyz",
        "subject": "Password Reset Required",
        "body": "IT requires all users to reset passwords. Download form: invoice.exe",
        "links": [],
        "attachments": ["invoice.exe"],
        "headers": {"SPF": "neutral", "DKIM": "none"},
        "indicators": ["executable_attachment", "impersonation", "urgency"],
    },
]

LEGITIMATE_TEMPLATES = [
    {
        "sender": "notifications@company.com",
        "subject": "Weekly Team Meeting Reminder",
        "body": "Reminder: Team sync tomorrow at 10 AM in Conference Room B",
        "links": [],
        "attachments": [],
        "headers": {"SPF": "pass", "DKIM": "pass"},
        "indicators": ["internal_sender", "routine_communication"],
    },
    {
        "sender": "support@vendor.com",
        "subject": "Your Order #12345 Has Shipped",
        "body": "Your order has been shipped. Track it here: https://vendor.com/track/12345",
        "links": ["https://vendor.com/track/12345"],
        "attachments": [],
        "headers": {"SPF": "pass", "DKIM": "pass"},
        "indicators": ["legitimate_domain", "spf_pass"],
    },
]


class PhishingTriageTask(BaseTask):
    """Task: Classify incoming email alerts as legitimate or phishing
    
    Difficulty: Easy - Single decision point, clear indicators
    Success Criteria: Correct classification with appropriate confidence
    """

    def generate_alert(self) -> Alert:
        """Generate synthetic phishing alert"""
        is_phishing = random.random() < 0.5
        templates = PHISHING_TEMPLATES if is_phishing else LEGITIMATE_TEMPLATES
        template = random.choice(templates)

        self.current_alert = Alert(
            id=f"phish_{uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            source="Email Gateway",
            severity=AlertSeverity.MEDIUM,
            alert_type=AlertType.PHISHING,
            description=f"Suspicious email detected from {template['sender']}",
            raw_data={
                "sender": template["sender"],
                "subject": template["subject"],
                "body_preview": template["body"][:200],
                "attachments": template.get("attachments", []),
                "links": template.get("links", []),
                "headers": template.get("headers", {}),
            },
            affected_assets=[f"user_{random.randint(1000,9999)}@company.com"],
        )

        self.ground_truth = {
            "is_phishing": is_phishing,
            "indicators": template.get("indicators", []),
            "template": template,
        }

        self.state = {
            "context": {"email_data": template},
            "relevant_indicators": template.get("indicators", []),
        }

        return self.current_alert

    def execute_action(
        self, action: InvestigationAction, history: List[InvestigationAction]
    ) -> ActionResult:
        """Process investigation action and return result"""
        
        if action.action_type == "check_reputation":
            sender = action.parameters.get("sender") or action.target or self.current_alert.raw_data.get("sender")
            reputation = self._check_sender_reputation(sender)
            return ActionResult(
                success=True,
                data={
                    "reputation_score": reputation,
                    "risk_level": self._score_to_risk(reputation),
                },
                metadata={"api_call": "reputation_check"},
            )

        elif action.action_type == "query_logs":
            return ActionResult(
                success=True,
                data={"headers": self.current_alert.raw_data.get("headers", {})},
                metadata={"query_type": "email_headers"},
            )

        elif action.action_type == "conclude":
            return ActionResult(
                success=True,
                is_terminal=True,
                data={"classification": action.parameters.get("label")},
                metadata={"confidence": action.confidence},
            )

        return ActionResult(
            success=False, data={}, metadata={"error": "Invalid action for task"}
        )

    def _check_sender_reputation(self, sender: str) -> float:
        """Simulate reputation check API"""
        # Check against known indicators
        if any(indicator in sender for indicator in ["paypa1", "verify", ".xyz"]):
            return random.uniform(0.1, 0.3)  # Low reputation
        elif "company.com" in sender or "vendor.com" in sender:
            return random.uniform(0.8, 0.95)  # High reputation
        return random.uniform(0.4, 0.6)  # Neutral

    def _score_to_risk(self, score: float) -> str:
        """Convert reputation score to risk level"""
        if score < 0.3:
            return "high"
        elif score < 0.6:
            return "medium"
        return "low"

    def get_grader(self):
        from ..graders.phishing_grader import PhishingGrader
        return PhishingGrader()

    def get_initial_hints(self) -> Optional[List[str]]:
        """Return initial hints for the agent"""
        return [
            "Check sender reputation and email headers",
            "Look for urgency indicators and suspicious links",
            "Verify SPF/DKIM authentication results",
        ]
