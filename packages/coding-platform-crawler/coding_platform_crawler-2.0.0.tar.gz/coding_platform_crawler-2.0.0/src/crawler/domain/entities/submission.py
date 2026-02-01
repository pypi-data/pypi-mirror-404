"""Submission entity"""

from dataclasses import dataclass
from typing import Optional

from ..value_objects import Percentiles
from .enums import SubmissionStatus


@dataclass
class Submission:
    """User's code submission entity"""

    id: str
    problem_id: str
    language: str
    code: str
    status: SubmissionStatus
    runtime: str
    memory: str
    timestamp: int
    percentiles: Optional[Percentiles] = None

    def __post_init__(self):
        """Validate submission data"""
        if not self.code:
            raise ValueError("Submission code cannot be empty")
        if self.timestamp < 0:
            raise ValueError(f"Timestamp must be non-negative, got {self.timestamp}")
        if not self.problem_id:
            raise ValueError("Problem ID cannot be empty")
        if not self.language:
            raise ValueError("Language cannot be empty")
