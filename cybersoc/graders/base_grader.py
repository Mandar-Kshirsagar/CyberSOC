"""Base grader interface for CyberSOC tasks"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseGrader(ABC):
    """Abstract base class for task graders"""

    @abstractmethod
    def grade(
        self,
        episode_history: List,
        ground_truth: Dict,
        final_conclusion: Optional[Dict],
    ) -> float:
        """Grade episode performance
        
        Args:
            episode_history: List of InvestigationAction objects
            ground_truth: Ground truth data for the episode
            final_conclusion: Final conclusion dict (if any)
            
        Returns:
            Score in range [0.0, 1.0]
        """
        pass
