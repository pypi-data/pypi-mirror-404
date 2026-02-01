"""User entity"""

from dataclasses import dataclass
from typing import List


@dataclass
class User:
    """User profile entity on a coding platform"""

    username: str
    platform: str
    solved_count: int
    problems_solved: List[str]

    def __post_init__(self):
        """Validate user data"""
        if not self.username:
            raise ValueError("Username cannot be empty")
        if not self.platform:
            raise ValueError("Platform cannot be empty")
        if self.solved_count < 0:
            raise ValueError(f"Solved count must be non-negative, got {self.solved_count}")
        if len(self.problems_solved) != self.solved_count:
            raise ValueError(
                f"Problems solved list length ({len(self.problems_solved)}) "
                f"must match solved count ({self.solved_count})"
            )
