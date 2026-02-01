"""
Retry configuration for HTTP client.

This module defines the configuration for retry behavior including
exponential backoff parameters and jitter settings.
"""

from dataclasses import dataclass


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 60.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        jitter: Whether to add random jitter to delays (default: True)

    Example:
        >>> config = RetryConfig(max_retries=5, initial_delay=2.0)
        >>> config.max_retries
        5
        >>> config.initial_delay
        2.0
    """

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    def __post_init__(self):
        """Validate retry configuration parameters."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.initial_delay <= 0:
            raise ValueError("initial_delay must be positive")
        if self.max_delay <= 0:
            raise ValueError("max_delay must be positive")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be greater than or equal to initial_delay")
        if self.exponential_base <= 1:
            raise ValueError("exponential_base must be greater than 1")
