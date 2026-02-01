"""Constraint value object"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Constraint:
    """Immutable constraint value object with validation"""

    text: str

    def __post_init__(self):
        """Validate constraint text is not empty or whitespace-only"""
        if not self.text or not self.text.strip():
            raise ValueError("Constraint text cannot be empty")
