"""Incident Response Task - Hard Difficulty"""

import random
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Optional, Dict, Any
from .base_task import BaseTask, ActionResult
from ..models import Alert, AlertSeverity, AlertType, InvestigationAction


# Complex multi-stage attack scenarios
INCIDENT_SCENARIOS = [
    {
        "name": "Ransomware Attack",
        "initial_alert": "Multiple hosts showing file encryption activity",
        "affected_hosts": ["workstation_042", "workstation_087", "server_db01"],
        "attack_stages": [
            {"stage": "initial_access", "indicator": "phishing_email", "timestamp": 0},
            {"stage": "execution", "indicator": "malicious_macro", "timestamp": 5},
            {"stage": "lateral_movement", "indicator": "smb_scanning", "timestamp": 15},
            {"stage": "impact", "indicator": "file_encryption", "timestamp": 30},
        ],
        "correct_timeline": ["initial_access", "execution", "lateral_movement", "impact"],
        "containment_actions": ["isolate_host", "block_ip", "disable_accounts"],
        "is_true_positive": True,
        "attack_type": "ransomware",
    },
    {
        "name": "Data Exfiltration",
        "initial_alert": "Unusual outbound traffic detected",
        "affected_hosts": ["server_web01", "workstation_123"],
        "attack_stages": [
            {"stage": "initial_access", "indicator": "web_exploit", "timestamp": 0},
            {"stage": "credential_access", "indicator": "password_dump", "timestamp": 10},
            {"stage": "collection", "indicator": "data_staging", "timestamp": 20},
            {"stage": "exfiltration", "indicator": "large_upload", "timestamp": 35},
        ],
        "correct_timeline": ["initial_access", "credential_access", "collection", "exfiltration"],
        "containment_actions": ["block_ip", "isolate_host", "collect_forensics"],
        "is_true_positive": True,
        "attack_type": "data_exfil",
    },
    {
        "name": "False Positive - Legitimate Activity",
        "initial_alert": "Suspicious process execution detected",
        "affected_hosts": ["workstation_099"],
        "attack_stages": [
            {"stage": "legitimate_admin", "indicator": "scheduled_task", "timestamp": 0},
            {"stage": "legitimate_update", "indicator": "software_install", "timestamp": 10},
        ],
        "correct_timeline": ["legitimate_admin", "legitimate_update"],
        "containment_actions": [],  # No containment needed
        "is_true_positive": False,
        "attack_type": "false_positive",
    },
]


class IncidentResponseTask(BaseTask):
    """Task: Coordinate response to multi-vector security incident
    
    Difficulty: Hard - Multi-host, multi-stage attack requiring:
    - Timeline reconstruction
    - Cross-host correlation
    - Strategic containment decisions
    - False positive discrimination
    
    Success Criteria:
    - Accurate attack timeline identification
    - Correct classification (true positive vs false positive)
    - Appropriate containment actions
    - Minimal business disruption (avoid over-containment)
    """

    def __init__(self):
        super().__init__()
        self.discovered_stages = set()
        self.timeline_attempts = []
        self.containment_actions_taken = []

    def generate_alert(self) -> Alert:
        """Generate complex multi-stage incident alert"""
        scenario = random.choice(INCIDENT_SCENARIOS)

        self.current_alert = Alert(
            id=f"incident_{uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            source="SIEM Correlation Engine",
            severity=AlertSeverity.CRITICAL if scenario["is_true_positive"] else AlertSeverity.HIGH,
            alert_type=AlertType.SUSPICIOUS_ACTIVITY,
            description=scenario["initial_alert"],
            raw_data={
                "incident_name": scenario["name"],
                "affected_hosts": scenario["affected_hosts"],
                "initial_indicators": [stage["indicator"] for stage in scenario["attack_stages"][:2]],
                "alert_count": len(scenario["attack_stages"]),
            },
            affected_assets=scenario["affected_hosts"],
        )

        self.ground_truth = {
            "scenario": scenario,
            "is_true_positive": scenario["is_true_positive"],
            "attack_type": scenario["attack_type"],
            "correct_timeline": scenario["correct_timeline"],
            "required_containment": scenario["containment_actions"],
            "affected_hosts": scenario["affected_hosts"],
        }

        self.state = {
            "context": {
                "scenario": scenario,
                "discovered_stages": [],
                "timeline_reconstructed": False,
                "containment_complete": False,
            },
            "relevant_indicators": [stage["indicator"] for stage in scenario["attack_stages"]],
            "investigation_complete": False,
        }

        return self.current_alert

    def execute_action(
        self, action: InvestigationAction, history: List[InvestigationAction]
    ) -> ActionResult:
        """Process investigation action and return result"""
        scenario = self.ground_truth["scenario"]

        if action.action_type == "query_logs":
            # Query logs for specific host or indicator
            query_type = action.parameters.get("query_type", "timeline")
            target_host = action.target or scenario["affected_hosts"][0]

            if query_type == "timeline":
                # Return timeline data for correlation
                relevant_stages = [
                    stage for stage in scenario["attack_stages"]
                    if target_host in scenario["affected_hosts"]
                ]
                self.discovered_stages.update([s["stage"] for s in relevant_stages])
                
                return ActionResult(
                    success=True,
                    data={
                        "timeline_events": [
                            {
                                "stage": s["stage"],
                                "indicator": s["indicator"],
                                "relative_time": f"T+{s['timestamp']}min",
                            }
                            for s in relevant_stages
                        ],
                        "host": target_host,
                    },
                    metadata={"query_type": "timeline", "milestone_reached": len(self.discovered_stages) >= 3},
                )

            elif query_type == "network":
                # Return network connections
                return ActionResult(
                    success=True,
                    data={
                        "connections": [
                            {"src": target_host, "dst": "192.168.1.100", "port": 445},
                            {"src": target_host, "dst": "10.0.0.50", "port": 443},
                        ]
                    },
                    metadata={"query_type": "network"},
                )

        elif action.action_type == "check_reputation":
            # Check reputation of IPs/domains involved
            indicator = action.parameters.get("indicator") or action.target
            is_malicious = scenario["is_true_positive"] and "legitimate" not in indicator
            
            return ActionResult(
                success=True,
                data={
                    "indicator": indicator,
                    "reputation": "malicious" if is_malicious else "clean",
                    "threat_intel": "Known APT infrastructure" if is_malicious else "Legitimate service",
                },
                metadata={"api_call": "threat_intel"},
            )

        elif action.action_type == "collect_forensics":
            # Collect forensic evidence
            target_host = action.target or scenario["affected_hosts"][0]
            self.state["investigation_complete"] = True
            
            return ActionResult(
                success=True,
                data={
                    "forensics_collected": True,
                    "host": target_host,
                    "artifacts": ["memory_dump", "disk_image", "network_pcap"],
                },
                metadata={"milestone_reached": True},
            )

        elif action.action_type == "isolate_host":
            # Containment action - isolate compromised host
            target_host = action.target or scenario["affected_hosts"][0]
            self.containment_actions_taken.append(("isolate_host", target_host))
            
            # Check if this is appropriate
            is_appropriate = (
                scenario["is_true_positive"] and 
                "isolate_host" in scenario["containment_actions"]
            )
            
            return ActionResult(
                success=True,
                data={
                    "host_isolated": target_host,
                    "business_impact": "high" if not is_appropriate else "acceptable",
                },
                metadata={
                    "containment_action": True,
                    "appropriate": is_appropriate,
                },
            )

        elif action.action_type == "escalate":
            # Escalate to senior incident responder
            return ActionResult(
                success=True,
                data={"escalated": True, "team": "Incident Response"},
                metadata={"escalation": True},
            )

        elif action.action_type == "conclude":
            # Final determination
            conclusion = action.parameters.get("conclusion", {})
            
            # Check timeline reconstruction
            proposed_timeline = conclusion.get("timeline", [])
            timeline_correct = proposed_timeline == scenario["correct_timeline"]
            
            # Check classification
            classification = conclusion.get("classification", "").lower()
            expected_class = "true_positive" if scenario["is_true_positive"] else "false_positive"
            classification_correct = classification == expected_class
            
            # Check containment appropriateness
            containment_appropriate = self._evaluate_containment(scenario)
            
            return ActionResult(
                success=True,
                is_terminal=True,
                data={
                    "classification": classification,
                    "timeline_correct": timeline_correct,
                    "classification_correct": classification_correct,
                    "containment_appropriate": containment_appropriate,
                },
                metadata={
                    "confidence": action.confidence,
                    "timeline_accuracy": 1.0 if timeline_correct else 0.0,
                    "classification_accuracy": 1.0 if classification_correct else 0.0,
                    "containment_score": 1.0 if containment_appropriate else 0.5,
                },
            )

        return ActionResult(
            success=False, data={}, metadata={"error": "Invalid action for task"}
        )

    def _evaluate_containment(self, scenario: Dict[str, Any]) -> bool:
        """Evaluate if containment actions were appropriate"""
        if not scenario["is_true_positive"]:
            # False positive - should not take aggressive containment
            aggressive_actions = [a for a in self.containment_actions_taken if a[0] == "isolate_host"]
            return len(aggressive_actions) == 0
        else:
            # True positive - should take appropriate containment
            required = set(scenario["containment_actions"])
            taken = set([a[0] for a in self.containment_actions_taken])
            # At least some required actions taken
            return len(required.intersection(taken)) >= len(required) // 2

    def get_grader(self):
        from ..graders.incident_grader import IncidentGrader
        return IncidentGrader()

    def get_initial_hints(self) -> Optional[List[str]]:
        """Return initial hints for the agent"""
        return [
            "Investigate timeline across all affected hosts",
            "Correlate events to identify attack stages",
            "Distinguish between true attacks and false positives",
            "Balance containment with business continuity",
        ]

    def get_adaptive_hints(
        self, history: List[InvestigationAction]
    ) -> Optional[List[str]]:
        """Return hints based on investigation progress"""
        if len(history) < 3:
            return ["Start by querying logs for timeline reconstruction"]
        elif len(self.discovered_stages) < 2:
            return ["Query logs for multiple hosts to correlate events"]
        elif not self.containment_actions_taken and len(history) > 5:
            return ["Consider containment actions if this is a true incident"]
        return None
