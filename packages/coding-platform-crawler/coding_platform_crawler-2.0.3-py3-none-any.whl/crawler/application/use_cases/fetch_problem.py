"""Use case for fetching a single problem."""

from logging import Logger

from crawler.application.interfaces.platform_client import PlatformClient
from crawler.application.interfaces.repository import ProblemRepository
from crawler.domain.entities import Problem


class FetchProblemUseCase:
    """
    Use case for fetching a single problem from a platform.

    This use case implements cache-first logic: it checks the repository
    (cache) first before fetching from the platform. This reduces API calls
    and improves performance.

    The force flag allows bypassing the cache to always fetch fresh data
    from the platform, useful when the problem has been updated or when
    the cached version is suspected to be stale.

    Attributes:
        client: Platform client for fetching problems from the API
        repository: Repository for caching problems locally
        logger: Logger for tracking operations

    Example:
        >>> use_case = FetchProblemUseCase(client, repository, logger)
        >>> problem = use_case.execute("two-sum", "leetcode", force=False)
        >>> print(problem.title)
        "Two Sum"
    """

    def __init__(
        self,
        client: PlatformClient,
        repository: ProblemRepository,
        logger: Logger,
    ):
        """
        Initialize the FetchProblemUseCase.

        Args:
            client: Platform client for API communication
            repository: Repository for problem persistence
            logger: Logger for operation tracking
        """
        self.client = client
        self.repository = repository
        self.logger = logger

    def execute(self, problem_id: str, platform: str, force: bool = False) -> Problem:
        """
        Fetch a problem from the platform or cache.

        This method implements the following logic:
        1. If force=False, check the repository cache first
        2. If found in cache, return the cached problem
        3. If not found or force=True, fetch from the platform
        4. Save the fetched problem to the repository
        5. Return the problem

        Args:
            problem_id: The platform-specific problem identifier
                       (e.g., "two-sum" for LeetCode)
            platform: The platform name (e.g., "leetcode", "hackerrank")
            force: If True, bypass cache and fetch from platform (default: False)

        Returns:
            Problem: The fetched problem entity with all metadata

        Raises:
            ProblemNotFoundException: If the problem doesn't exist on the platform
            NetworkException: If the network request fails
            AuthenticationException: If authentication is required but not provided
            RepositoryException: If saving to the repository fails

        Example:
            >>> # First call fetches from platform
            >>> problem = use_case.execute("two-sum", "leetcode")
            >>> # Second call uses cache
            >>> problem = use_case.execute("two-sum", "leetcode")
            >>> # Force refresh from platform
            >>> problem = use_case.execute("two-sum", "leetcode", force=True)
        """
        # Check cache first unless force is True
        if not force:
            self.logger.debug(f"Checking cache for problem '{problem_id}' on platform '{platform}'")
            cached = self.repository.find_by_id(problem_id, platform)
            if cached:
                self.logger.info(f"Found problem '{problem_id}' in cache for platform '{platform}'")
                return cached
            self.logger.debug(
                f"Problem '{problem_id}' not found in cache for platform '{platform}'"
            )
        else:
            self.logger.debug(
                f"Force flag set, bypassing cache for problem '{problem_id}' on platform '{platform}'"
            )

        # Fetch from platform
        self.logger.info(f"Fetching problem '{problem_id}' from platform '{platform}'")
        try:
            problem = self.client.fetch_problem(problem_id)
            self.logger.info(
                f"Successfully fetched problem '{problem_id}' from platform '{platform}'"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to fetch problem '{problem_id}' from platform '{platform}': {e}"
            )
            raise

        # Note: Problem is not saved here - the caller (command) will save it
        # along with the submission if available
        return problem
