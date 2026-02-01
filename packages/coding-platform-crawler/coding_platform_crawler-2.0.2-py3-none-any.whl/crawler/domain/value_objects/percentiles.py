"""Percentiles value object"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Percentiles:
    """Immutable performance percentiles for runtime and memory"""

    runtime: float
    memory: float

    def __post_init__(self):
        if not (0 <= self.runtime <= 100):
            raise ValueError(f"Runtime percentile must be between 0 and 100, got {self.runtime}")
        if not (0 <= self.memory <= 100):
            raise ValueError(f"Memory percentile must be between 0 and 100, got {self.memory}")
