"""Phishing triage task grader"""

from typing import List, Dict, Optional
from .base_grader import BaseGrader


class PhishingGrader(BaseGrader):
    """Grades phishing triage task performance
    
    Scoring:
    - Correct classification: +0.7
    - Appropriate confidence calibration: +0.2
    - Efficient investigation (≤3 actions): +0.1 bonus
    - Incorrect classification: 0.0
    - Destructive action (e.g., deleting legitimate email): -0.3 penalty
    """

    def grade(
        self,
        episode_history: List,
        ground_truth: Dict,
        final_conclusion: Optional[Dict],
    ) -> float:
        if not final_conclusion:
            return 0.0  # No conclusion reached

        # Check classification accuracy
        predicted = final_conclusion.get("label", "").lower()
        actual = ground_truth.get("is_phishing", False)
        expected_label = "phishing" if actual else "legitimate"

        if predicted == expected_label:
            base_score = 0.7
        else:
            # Partial credit for high-confidence wrong answers that used good indicators
            confidence = final_conclusion.get("confidence", 0.0)
            if confidence > 0.8 and self._used_valid_indicators(episode_history):
                base_score = 0.3  # "Good process, wrong conclusion"
            else:
                base_score = 0.0

        # Confidence calibration bonus
        confidence = final_conclusion.get("confidence", 0.0)
        if predicted == expected_label and 0.7 <= confidence <= 0.95:
            base_score += 0.2  # Well-calibrated confidence
        elif predicted != expected_label and confidence < 0.5:
            base_score += 0.1  # Appropriately uncertain when wrong

        # Efficiency bonus
        investigation_actions = [
            a for a in episode_history if a.action_type != "conclude"
        ]
        if len(investigation_actions) <= 3 and base_score > 0:
            base_score += 0.1

        # Penalty for destructive actions
        if self._has_destructive_action(episode_history):
            base_score = max(0.0, base_score - 0.3)

        return min(1.0, max(0.0, base_score))

    def _used_valid_indicators(self, history: List) -> bool:
        """Check if agent used at least one valid investigation technique"""
        valid_actions = {"check_reputation", "query_logs"}
        return any(a.action_type in valid_actions for a in history)

    def _has_destructive_action(self, history: List) -> bool:
        """Detect actions that would cause harm if executed in production"""
        destructive = {"delete_email", "block_sender_permanently"}
        return any(a.action_type in destructive for a in history)
