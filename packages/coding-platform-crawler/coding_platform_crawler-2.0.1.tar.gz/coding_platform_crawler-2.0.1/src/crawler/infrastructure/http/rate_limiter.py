"""
Rate limiter implementation using token bucket algorithm.

This module provides a thread-safe rate limiter that controls the rate
of operations using the token bucket algorithm.
"""

import threading
import time


class RateLimiter:
    """Token bucket rate limiter for controlling request rates.

    The token bucket algorithm allows for burst traffic while maintaining
    an average rate limit. Tokens are added to the bucket at a constant rate,
    and each request consumes one token. If no tokens are available, the
    request blocks until a token becomes available.

    Attributes:
        requests_per_second: Maximum number of requests allowed per second
        tokens: Current number of available tokens
        last_update: Timestamp of last token refill
        lock: Thread lock for thread-safe operations

    Example:
        >>> limiter = RateLimiter(requests_per_second=2.0)
        >>> limiter.acquire()  # Consumes one token
        >>> limiter.acquire()  # Consumes another token
        >>> limiter.acquire()  # Blocks until token is available
    """

    def __init__(self, requests_per_second: float):
        """Initialize the rate limiter.

        Args:
            requests_per_second: Maximum number of requests allowed per second.
                                Must be positive.

        Raises:
            ValueError: If requests_per_second is not positive
        """
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")

        self.requests_per_second = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Acquire a token, blocking if necessary.

        This method will block the calling thread if no tokens are available,
        waiting until a token becomes available through the refill process.

        The method is thread-safe and can be called from multiple threads
        simultaneously.
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(
                self.requests_per_second, self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now

            # Wait if no tokens available
            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.requests_per_second
                time.sleep(sleep_time)
                self.tokens = 0
            else:
                self.tokens -= 1
