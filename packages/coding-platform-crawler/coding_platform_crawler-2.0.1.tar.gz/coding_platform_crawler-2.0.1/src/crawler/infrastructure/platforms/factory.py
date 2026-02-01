"""
Platform client factory for creating platform-specific clients.

This module implements the Factory pattern to create platform clients
based on platform identifiers. It provides extensibility for adding
new platforms without modifying existing code.
"""

from logging import Logger

from crawler.application.interfaces import PlatformClient
from crawler.config.settings import Config
from crawler.domain.exceptions import UnsupportedPlatformException
from crawler.infrastructure.http import HTTPClient

from .leetcode.adapter import LeetCodeAdapter
from .leetcode.client import LeetCodeClient


class PlatformClientFactory:
    """Factory for creating platform-specific clients.

    This factory implements the Factory pattern to create concrete
    PlatformClient implementations based on platform identifiers.
    It centralizes object creation and makes it easy to add support
    for new platforms.

    The factory currently supports:
    - LeetCode (implemented)

    Future platforms can be added by:
    1. Implementing the PlatformClient interface
    2. Creating a platform-specific adapter
    3. Adding a new elif branch in the create() method

    Attributes:
        http_client: HTTP client with retry and rate limiting
        config: Configuration settings
        logger: Logger for tracking operations

    Example:
        >>> from crawler.infrastructure.http import HTTPClient, RateLimiter, RetryConfig
        >>> from crawler.config import get_logger
        >>>
        >>> retry_config = RetryConfig()
        >>> rate_limiter = RateLimiter(2.0)
        >>> http_client = HTTPClient(retry_config, rate_limiter, logger)
        >>> config = Config()
        >>> logger = get_logger(__name__)
        >>>
        >>> factory = PlatformClientFactory(http_client, config, logger)
        >>> leetcode_client = factory.create("leetcode")
        >>> problem = leetcode_client.fetch_problem("two-sum")
    """

    def __init__(self, http_client: HTTPClient, config: Config, logger: Logger):
        """Initialize the platform client factory.

        Args:
            http_client: HTTP client with retry and rate limiting
            config: Configuration settings
            logger: Logger for tracking operations
        """
        self.http_client = http_client
        self.config = config
        self.logger = logger

    def create(self, platform: str) -> PlatformClient:
        """Create a platform client based on platform identifier.

        This method creates and returns a concrete PlatformClient
        implementation for the specified platform. The platform
        identifier is case-insensitive.

        Args:
            platform: Platform identifier (e.g., "leetcode", "hackerrank")

        Returns:
            Concrete PlatformClient implementation for the platform

        Raises:
            UnsupportedPlatformException: If the platform is not supported

        Example:
            >>> factory = PlatformClientFactory(http_client, config, logger)
            >>> client = factory.create("leetcode")
            >>> isinstance(client, LeetCodeClient)
            True

            >>> factory.create("unsupported")
            Traceback (most recent call last):
                ...
            UnsupportedPlatformException: Platform 'unsupported' is not supported
        """
        platform = platform.lower()

        if platform == "leetcode":
            self.logger.info(f"Creating LeetCode client")
            adapter = LeetCodeAdapter()
            return LeetCodeClient(self.http_client, adapter, self.config, self.logger)

        # Future platforms can be added here:
        # elif platform == "hackerrank":
        #     adapter = HackerRankAdapter()
        #     return HackerRankClient(
        #         self.http_client,
        #         adapter,
        #         self.config,
        #         self.logger
        #     )
        # elif platform == "codechef":
        #     adapter = CodeChefAdapter()
        #     return CodeChefClient(
        #         self.http_client,
        #         adapter,
        #         self.config,
        #         self.logger
        #     )
        # elif platform == "codeforces":
        #     adapter = CodeforcesAdapter()
        #     return CodeforcesClient(
        #         self.http_client,
        #         adapter,
        #         self.config,
        #         self.logger
        #     )

        else:
            self.logger.error(f"Unsupported platform requested: {platform}")
            raise UnsupportedPlatformException(platform)
