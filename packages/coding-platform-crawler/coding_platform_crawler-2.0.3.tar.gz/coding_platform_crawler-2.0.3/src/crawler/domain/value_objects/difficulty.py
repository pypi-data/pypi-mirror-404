"""Difficulty value object"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Difficulty:
    """Immutable difficulty level for coding problems"""

    level: str

    VALID_LEVELS = {"Easy", "Medium", "Hard"}

    def __post_init__(self):
        if self.level not in self.VALID_LEVELS:
            raise ValueError(
                f"Invalid difficulty: {self.level}. " f"Must be one of {self.VALID_LEVELS}"
            )

    def is_easy(self) -> bool:
        """Check if difficulty is Easy"""
        return self.level == "Easy"

    def is_medium(self) -> bool:
        """Check if difficulty is Medium"""
        return self.level == "Medium"

    def is_hard(self) -> bool:
        """Check if difficulty is Hard"""
        return self.level == "Hard"
