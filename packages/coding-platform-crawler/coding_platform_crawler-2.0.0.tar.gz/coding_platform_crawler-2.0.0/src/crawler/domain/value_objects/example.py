"""Example value object"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Example:
    """Immutable problem example with input, output, and optional explanation"""

    input: str
    output: str
    explanation: Optional[str] = None

    def __post_init__(self):
        if not self.input:
            raise ValueError("Example input cannot be empty")
        if not self.output:
            raise ValueError("Example output cannot be empty")
