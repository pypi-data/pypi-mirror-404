"""Use case for listing problems with filtering and sorting."""

from dataclasses import dataclass
from logging import Logger
from typing import List, Optional

from crawler.application.interfaces.repository import ProblemRepository
from crawler.domain.entities import Problem


@dataclass
class ListOptions:
    """
    Configuration options for listing problems.

    This dataclass encapsulates all the parameters needed to list
    problems from the repository with optional filtering and sorting.
    It allows users to narrow down the list by platform, difficulty,
    and topics, and to sort the results by various criteria.

    Attributes:
        platform: Optional platform name to filter by (e.g., "leetcode").
                 If None, problems from all platforms are included.
        difficulty: Optional list of difficulty levels to include
                   (e.g., ["Easy", "Medium"]). If None, all difficulties
                   are included.
        topics: Optional list of topics to filter by (e.g., ["Array", "Hash Table"]).
               If None, all topics are included. A problem matches if it has
               at least one of the specified topics.
        sort_by: Field to sort by. Valid values: "id", "title", "difficulty",
                "acceptance_rate", "platform". Default is "id".
        reverse: If True, sort in descending order. If False, sort in
                ascending order. Default is False.

    Example:
        >>> # List all problems sorted by ID
        >>> options = ListOptions()

        >>> # List only LeetCode Easy problems
        >>> options = ListOptions(
        ...     platform="leetcode",
        ...     difficulty=["Easy"]
        ... )

        >>> # List Medium and Hard problems on Array topic, sorted by acceptance rate
        >>> options = ListOptions(
        ...     difficulty=["Medium", "Hard"],
        ...     topics=["Array"],
        ...     sort_by="acceptance_rate",
        ...     reverse=True
        ... )
    """

    platform: Optional[str] = None
    difficulty: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    sort_by: str = "id"
    reverse: bool = False


class ListProblemsUseCase:
    """
    Use case for listing problems from the repository.

    This use case retrieves problems from the repository and applies
    filtering and sorting based on user-specified criteria. It's useful
    for viewing what problems have been downloaded, finding problems
    by difficulty or topic, and organizing the problem list.

    The use case implements the following workflow:
    1. Fetch all problems from the repository (optionally filtered by platform)
    2. Apply difficulty filter if specified
    3. Apply topic filter if specified
    4. Sort problems by the specified field
    5. Return the filtered and sorted list

    Attributes:
        repository: Repository for accessing stored problems
        logger: Logger for tracking operations

    Example:
        >>> use_case = ListProblemsUseCase(repository, logger)
        >>> options = ListOptions(
        ...     platform="leetcode",
        ...     difficulty=["Easy", "Medium"],
        ...     sort_by="acceptance_rate",
        ...     reverse=True
        ... )
        >>> problems = use_case.execute(options)
        >>> for problem in problems:
        ...     print(f"{problem.title} - {problem.difficulty.level}")
    """

    def __init__(
        self,
        repository: ProblemRepository,
        logger: Logger,
    ):
        """
        Initialize the ListProblemsUseCase.

        Args:
            repository: Repository for accessing stored problems
            logger: Logger for operation tracking
        """
        self.repository = repository
        self.logger = logger

    def execute(self, options: ListOptions) -> List[Problem]:
        """
        List problems from repository with filtering and sorting.

        This method retrieves problems from the repository and applies
        the specified filters and sorting. All filtering is done in-memory
        after fetching from the repository.

        The filtering logic:
        - Platform filter: Exact match on platform name
        - Difficulty filter: Problem difficulty must be in the specified list
        - Topic filter: Problem must have at least one of the specified topics

        The sorting logic:
        - Supports sorting by: id, title, difficulty, acceptance_rate, platform
        - Difficulty sorting order: Easy < Medium < Hard
        - Reverse flag inverts the sort order

        Args:
            options: Configuration for listing including filters and sorting

        Returns:
            List[Problem]: List of problems matching the criteria, sorted
                          according to the specified options

        Raises:
            RepositoryException: If reading from the repository fails

        Example:
            >>> # List all Easy problems sorted by title
            >>> options = ListOptions(
            ...     difficulty=["Easy"],
            ...     sort_by="title"
            ... )
            >>> problems = use_case.execute(options)

            >>> # List LeetCode problems on Dynamic Programming topic
            >>> options = ListOptions(
            ...     platform="leetcode",
            ...     topics=["Dynamic Programming"],
            ...     sort_by="acceptance_rate",
            ...     reverse=True
            ... )
            >>> problems = use_case.execute(options)
        """
        self.logger.info(
            f"Listing problems with filters: platform={options.platform}, "
            f"difficulty={options.difficulty}, topics={options.topics}, "
            f"sort_by={options.sort_by}, reverse={options.reverse}"
        )

        # Fetch all problems from repository
        try:
            self.logger.debug(
                f"Fetching problems from repository for platform: {options.platform or 'all'}"
            )
            problems = self.repository.list_all(options.platform)
            self.logger.info(f"Found {len(problems)} problems in repository")
        except Exception as e:
            self.logger.error(f"Failed to fetch problems from repository: {e}")
            raise

        # Apply difficulty filter
        if options.difficulty:
            self.logger.debug(f"Applying difficulty filter: {options.difficulty}")
            initial_count = len(problems)
            problems = [p for p in problems if p.difficulty.level in options.difficulty]
            self.logger.debug(
                f"After difficulty filter: {len(problems)} problems "
                f"(filtered out {initial_count - len(problems)})"
            )

        # Apply topic filter
        if options.topics:
            self.logger.debug(f"Applying topic filter: {options.topics}")
            initial_count = len(problems)
            problems = [p for p in problems if any(topic in p.topics for topic in options.topics)]
            self.logger.debug(
                f"After topic filter: {len(problems)} problems "
                f"(filtered out {initial_count - len(problems)})"
            )

        # Sort problems
        self.logger.debug(
            f"Sorting problems by '{options.sort_by}' " f"(reverse={options.reverse})"
        )
        problems = self._sort_problems(problems, options.sort_by, options.reverse)

        self.logger.info(f"Returning {len(problems)} problems after filtering and sorting")
        return problems

    def _sort_problems(self, problems: List[Problem], sort_by: str, reverse: bool) -> List[Problem]:
        """
        Sort problems by the specified field.

        This method handles sorting for different field types:
        - String fields (id, title, platform): Alphabetical sorting
        - Numeric fields (acceptance_rate): Numeric sorting
        - Difficulty: Custom sorting (Easy < Medium < Hard)

        Args:
            problems: List of problems to sort
            sort_by: Field name to sort by
            reverse: If True, sort in descending order

        Returns:
            Sorted list of problems

        Raises:
            ValueError: If sort_by field is not supported
        """
        # Define difficulty order for sorting
        difficulty_order = {"Easy": 1, "Medium": 2, "Hard": 3}

        # Define sort key functions for each field
        sort_keys = {
            "id": lambda p: p.id,
            "title": lambda p: p.title.lower(),  # Case-insensitive sorting
            "difficulty": lambda p: difficulty_order.get(p.difficulty.level, 999),
            "acceptance_rate": lambda p: p.acceptance_rate,
            "platform": lambda p: p.platform.lower(),  # Case-insensitive sorting
        }

        # Validate sort_by field
        if sort_by not in sort_keys:
            valid_fields = ", ".join(sort_keys.keys())
            error_msg = f"Invalid sort_by field: '{sort_by}'. " f"Valid fields are: {valid_fields}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Sort using the appropriate key function
        try:
            sorted_problems = sorted(problems, key=sort_keys[sort_by], reverse=reverse)
            self.logger.debug(
                f"Successfully sorted {len(sorted_problems)} problems " f"by '{sort_by}'"
            )
            return sorted_problems
        except Exception as e:
            self.logger.error(f"Failed to sort problems by '{sort_by}': {e}")
            raise
