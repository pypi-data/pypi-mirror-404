"""Problem entity"""

from dataclasses import dataclass
from typing import List

from ..value_objects.constraint import Constraint
from ..value_objects.difficulty import Difficulty
from ..value_objects.example import Example


@dataclass
class Problem:
    """Represents a coding problem from any platform"""

    id: str
    platform: str
    title: str
    difficulty: Difficulty
    description: str
    topics: List[str]
    constraints: List[Constraint]
    examples: List[Example]
    hints: List[str]
    acceptance_rate: float

    def __post_init__(self):
        """Validate Problem entity fields"""
        if not self.id:
            raise ValueError("Problem ID cannot be empty")
        if not self.title:
            raise ValueError("Problem title cannot be empty")
        if not self.platform:
            raise ValueError("Problem platform cannot be empty")
        if self.acceptance_rate < 0 or self.acceptance_rate > 100:
            raise ValueError("Acceptance rate must be between 0 and 100")

    @property
    def constraints_text(self) -> str:
        """Return constraints as formatted string for backward compatibility

        Returns:
            str: Newline-separated constraint text
        """
        return "\n".join(c.text for c in self.constraints)
