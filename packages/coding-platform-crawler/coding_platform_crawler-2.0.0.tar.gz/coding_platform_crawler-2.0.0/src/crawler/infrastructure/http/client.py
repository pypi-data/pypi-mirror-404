"""
HTTP client with retry logic and rate limiting.

This module provides an HTTP client that implements exponential backoff
retry logic with jitter and integrates rate limiting to respect API limits.
"""

import random
import time
from logging import Logger
from typing import Any, Dict, Optional

import requests

from ...domain.exceptions import NetworkException
from .rate_limiter import RateLimiter
from .retry_config import RetryConfig


class HTTPClient:
    """HTTP client with retry and rate limiting capabilities.

    This client wraps the requests library and adds:
    - Exponential backoff retry logic with jitter
    - Rate limiting using token bucket algorithm
    - Comprehensive error handling and logging

    Attributes:
        retry_config: Configuration for retry behavior
        rate_limiter: Rate limiter for controlling request rate
        logger: Logger for tracking requests and errors
        session: Persistent HTTP session for connection pooling

    Example:
        >>> config = RetryConfig(max_retries=3, initial_delay=1.0)
        >>> limiter = RateLimiter(requests_per_second=2.0)
        >>> client = HTTPClient(config, limiter, logger)
        >>> response = client.get("https://api.example.com/data")
    """

    def __init__(self, retry_config: RetryConfig, rate_limiter: RateLimiter, logger: Logger):
        """Initialize the HTTP client.

        Args:
            retry_config: Configuration for retry behavior
            rate_limiter: Rate limiter for controlling request rate
            logger: Logger for tracking requests and errors
        """
        self.retry_config = retry_config
        self.rate_limiter = rate_limiter
        self.logger = logger
        self.session = requests.Session()

    def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """Execute a POST request with retry logic.

        Args:
            url: The URL to send the POST request to
            json: JSON data to send in the request body (optional)
            headers: HTTP headers to include (optional)
            **kwargs: Additional arguments to pass to requests.post

        Returns:
            The HTTP response object

        Raises:
            NetworkException: If the request fails after all retries
        """
        return self._request_with_retry("POST", url, json=json, headers=headers, **kwargs)

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """Execute a GET request with retry logic.

        Args:
            url: The URL to send the GET request to
            params: Query parameters to include (optional)
            headers: HTTP headers to include (optional)
            **kwargs: Additional arguments to pass to requests.get

        Returns:
            The HTTP response object

        Raises:
            NetworkException: If the request fails after all retries
        """
        return self._request_with_retry("GET", url, params=params, headers=headers, **kwargs)

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute an HTTP request with exponential backoff retry.

        This method implements the retry logic with exponential backoff and jitter.
        It will retry on network errors and HTTP 5xx errors, but not on 4xx errors
        (which typically indicate client errors that won't be fixed by retrying).

        Args:
            method: HTTP method (GET, POST, etc.)
            url: The URL to send the request to
            **kwargs: Additional arguments to pass to the request

        Returns:
            The HTTP response object

        Raises:
            NetworkException: If the request fails after all retries
        """
        last_exception = None

        for attempt in range(self.retry_config.max_retries):
            try:
                # Apply rate limiting
                self.rate_limiter.acquire()

                # Make request
                self.logger.debug(
                    f"Attempt {attempt + 1}/{self.retry_config.max_retries}: {method} {url}"
                )
                response = self.session.request(method, url, **kwargs)

                # Check for HTTP errors
                # Don't retry on 4xx errors (client errors) - raise immediately
                if 400 <= response.status_code < 500:
                    # Log response body for debugging
                    try:
                        self.logger.debug(f"Response body: {response.text[:500]}")
                    except:
                        pass
                    response.raise_for_status()
                    # If raise_for_status didn't raise, return the response
                    return response

                # Retry on 5xx errors (server errors)
                if response.status_code >= 500:
                    raise requests.exceptions.HTTPError(
                        f"Server error: {response.status_code}", response=response
                    )

                # Success (2xx or 3xx)
                self.logger.debug(f"Request successful: {method} {url}")
                return response

            except requests.exceptions.HTTPError as e:
                # Re-raise 4xx errors immediately without retry
                # Check if we can determine the status code
                if hasattr(e, "response") and e.response is not None:
                    if 400 <= e.response.status_code < 500:
                        raise
                # If we can't determine status code but we know it's from raise_for_status
                # on a 4xx response, re-raise it
                elif 400 <= response.status_code < 500:
                    raise

                # For 5xx errors or unknown errors, continue to retry logic below
                last_exception = e
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.retry_config.max_retries}): {e}"
                )

                # Don't retry if this was the last attempt
                if attempt < self.retry_config.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    self.logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.retry_config.max_retries}): {e}"
                )

                # Don't retry if this was the last attempt
                if attempt < self.retry_config.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    self.logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)

        # All retries exhausted
        error_msg = f"Request failed after {self.retry_config.max_retries} attempts"
        self.logger.error(f"{error_msg}: {last_exception}")

        # Extract status code if available
        status_code = None
        if isinstance(last_exception, requests.exceptions.HTTPError):
            if hasattr(last_exception, "response") and last_exception.response is not None:
                status_code = last_exception.response.status_code

        raise NetworkException(error_msg, url=url, status_code=status_code) from last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with optional jitter.

        The delay is calculated as:
            delay = min(initial_delay * (exponential_base ^ attempt), max_delay)

        If jitter is enabled, the delay is multiplied by a random factor
        between 0.5 and 1.0 to prevent thundering herd problems.

        Args:
            attempt: The current attempt number (0-indexed)

        Returns:
            The delay in seconds
        """
        # Calculate exponential backoff
        delay = min(
            self.retry_config.initial_delay * (self.retry_config.exponential_base**attempt),
            self.retry_config.max_delay,
        )

        # Add jitter if enabled
        if self.retry_config.jitter:
            # Random factor between 0.5 and 1.0
            delay *= 0.5 + random.random() * 0.5

        return delay
