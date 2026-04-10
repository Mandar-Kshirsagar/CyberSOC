"""Incident response task grader"""

from typing import List, Dict, Optional
from .base_grader import BaseGrader


class IncidentGrader(BaseGrader):
    """Grades incident response task performance
    
    Scoring (Hard Difficulty):
    - Correct classification (true/false positive): +0.3
    - Timeline reconstruction accuracy: +0.3
    - Appropriate containment actions: +0.2
    - Investigation completeness: +0.1
    - Efficiency (minimal business disruption): +0.1
    
    Penalties:
    - Over-containment on false positive: -0.3
    - Under-containment on true positive: -0.2
    - Premature conclusion without investigation: -0.2
    """

    def grade(
        self,
        episode_history: List,
        ground_truth: Dict,
        final_conclusion: Optional[Dict],
    ) -> float:
        if not final_conclusion:
            return 0.0  # No conclusion reached

        base_score = 0.0

        # 1. Classification accuracy (0.3 points)
        classification = final_conclusion.get("classification", "").lower()
        expected = "true_positive" if ground_truth.get("is_true_positive") else "false_positive"
        
        if classification == expected:
            base_score += 0.3
        else:
            # Partial credit if investigation was thorough
            if self._thorough_investigation(episode_history):
                base_score += 0.1

        # 2. Timeline reconstruction (0.3 points)
        proposed_timeline = final_conclusion.get("timeline", [])
        correct_timeline = ground_truth.get("correct_timeline", [])
        
        if proposed_timeline:
            # Calculate timeline accuracy
            timeline_accuracy = self._calculate_timeline_accuracy(
                proposed_timeline, correct_timeline
            )
            base_score += 0.3 * timeline_accuracy
        else:
            # Partial credit if they identified key stages
            if self._identified_key_stages(episode_history, correct_timeline):
                base_score += 0.1

        # 3. Containment appropriateness (0.2 points)
        containment_score = self._evaluate_containment(
            episode_history, ground_truth
        )
        base_score += 0.2 * containment_score

        # 4. Investigation completeness (0.1 points)
        investigation_types = self._get_investigation_types(episode_history)
        required_types = {"query_logs", "check_reputation", "collect_forensics"}
        
        completeness = len(investigation_types.intersection(required_types)) / len(required_types)
        base_score += 0.1 * completeness

        # 5. Efficiency bonus (0.1 points)
        if len(episode_history) <= 12 and base_score > 0.5:
            base_score += 0.1

        # Penalties
        
        # Over-containment on false positive
        if not ground_truth.get("is_true_positive"):
            aggressive_actions = [
                a for a in episode_history 
                if a.action_type == "isolate_host"
            ]
            if len(aggressive_actions) > 0:
                base_score = max(0.0, base_score - 0.3)

        # Under-containment on true positive
        if ground_truth.get("is_true_positive"):
            containment_actions = [
                a for a in episode_history 
                if a.action_type in ["isolate_host", "block_ip"]
            ]
            if len(containment_actions) == 0:
                base_score = max(0.0, base_score - 0.2)

        # Premature conclusion
        if len(episode_history) < 4:
            base_score = max(0.0, base_score - 0.2)

        return min(1.0, max(0.0, base_score))

    def _calculate_timeline_accuracy(
        self, proposed: List[str], correct: List[str]
    ) -> float:
        """Calculate accuracy of timeline reconstruction"""
        if not proposed or not correct:
            return 0.0

        # Check order and presence
        correct_positions = 0
        for i, stage in enumerate(proposed):
            if i < len(correct) and stage == correct[i]:
                correct_positions += 1

        # Partial credit for identifying stages even if order is wrong
        identified_stages = set(proposed).intersection(set(correct))
        stage_recall = len(identified_stages) / len(correct)

        # Order accuracy
        order_accuracy = correct_positions / len(correct)

        # Weighted combination
        return 0.6 * order_accuracy + 0.4 * stage_recall

    def _evaluate_containment(
        self, history: List, ground_truth: Dict
    ) -> float:
        """Evaluate containment action appropriateness"""
        is_true_positive = ground_truth.get("is_true_positive", False)
        required_actions = set(ground_truth.get("required_containment", []))
        
        taken_actions = set([
            a.action_type for a in history 
            if a.action_type in ["isolate_host", "block_ip", "collect_forensics", "disable_accounts"]
        ])

        if not is_true_positive:
            # False positive - should avoid aggressive containment
            aggressive = taken_actions.intersection({"isolate_host", "block_ip"})
            if len(aggressive) == 0:
                return 1.0  # Perfect - no over-reaction
            else:
                return 0.3  # Penalty for over-containment

        else:
            # True positive - should take appropriate actions
            if not required_actions:
                return 1.0

            overlap = taken_actions.intersection(required_actions)
            if len(overlap) == 0:
                return 0.0  # No appropriate actions taken
            
            # Score based on coverage
            coverage = len(overlap) / len(required_actions)
            
            # Bonus for not over-containing
            if len(taken_actions) <= len(required_actions) + 1:
                return min(1.0, coverage + 0.2)
            
            return coverage

    def _thorough_investigation(self, history: List) -> bool:
        """Check if investigation was thorough"""
        investigation_actions = [
            a for a in history 
            if a.action_type in ["query_logs", "check_reputation", "collect_forensics"]
        ]
        return len(investigation_actions) >= 4

    def _identified_key_stages(self, history: List, correct_timeline: List[str]) -> bool:
        """Check if agent identified key attack stages"""
        # Look for timeline-related queries
        timeline_queries = [
            a for a in history 
            if a.action_type == "query_logs" and 
            a.parameters.get("query_type") == "timeline"
        ]
        return len(timeline_queries) >= 2

    def _get_investigation_types(self, history: List) -> set:
        """Get set of investigation action types used"""
        return set([
            a.action_type for a in history 
            if a.action_type != "conclude"
        ])
