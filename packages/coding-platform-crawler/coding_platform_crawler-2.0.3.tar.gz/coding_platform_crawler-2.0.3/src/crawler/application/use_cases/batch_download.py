"""Use case for batch downloading problems."""

import time
from dataclasses import dataclass
from logging import Logger
from typing import List, Optional

from crawler.application.interfaces.formatter import OutputFormatter
from crawler.application.interfaces.observer import DownloadObserver
from crawler.application.interfaces.platform_client import PlatformClient
from crawler.application.interfaces.repository import ProblemRepository
from crawler.domain.entities import Problem, Submission, UpdateMode


@dataclass
class BatchDownloadOptions:
    """
    Configuration options for batch download operations.

    This dataclass encapsulates all the parameters needed to perform
    a batch download of problems from a coding platform. It includes
    user identification, platform selection, update behavior, and
    optional filters for difficulty and topics.

    Attributes:
        username: The username on the platform whose solved problems to download
        platform: The platform name (e.g., "leetcode", "hackerrank")
        update_mode: How to handle existing files (SKIP, UPDATE, or FORCE)
        include_community: Whether to download community solutions (default: False)
        limit: Optional maximum number of problems to download (default: None = all)
        difficulty_filter: Optional list of difficulty levels to include
                          (e.g., ["Easy", "Medium"]). If None, all difficulties
                          are included.
        topic_filter: Optional list of topics to include (e.g., ["Array", "Hash Table"]).
                     If None, all topics are included.

    Example:
        >>> # Download all problems, skipping existing ones
        >>> options = BatchDownloadOptions(
        ...     username="john_doe",
        ...     platform="leetcode",
        ...     update_mode=UpdateMode.SKIP
        ... )

        >>> # Download only recent 50 Easy and Medium problems on Array topic
        >>> options = BatchDownloadOptions(
        ...     username="john_doe",
        ...     platform="leetcode",
        ...     update_mode=UpdateMode.UPDATE,
        ...     limit=50,
        ...     difficulty_filter=["Easy", "Medium"],
        ...     topic_filter=["Array"]
        ... )
    """

    username: str
    platform: str
    update_mode: UpdateMode
    include_community: bool = False
    limit: Optional[int] = None
    difficulty_filter: Optional[List[str]] = None
    topic_filter: Optional[List[str]] = None


@dataclass
class DownloadStats:
    """
    Statistics for a batch download operation.

    This dataclass tracks the results of a batch download operation,
    including counts of successful downloads, skipped files, failures,
    and the total time taken. These statistics are useful for reporting
    progress and diagnosing issues.

    The sum of downloaded + skipped + failed should equal total for
    a complete batch operation.

    Attributes:
        total: Total number of problems attempted
        downloaded: Number of problems successfully downloaded
        skipped: Number of problems skipped (already exist and update_mode=SKIP)
        failed: Number of problems that failed to download
        duration: Total time taken for the operation in seconds

    Example:
        >>> stats = DownloadStats(
        ...     total=100,
        ...     downloaded=75,
        ...     skipped=20,
        ...     failed=5,
        ...     duration=245.3
        ... )
        >>> print(f"Success rate: {stats.downloaded / stats.total * 100:.1f}%")
        Success rate: 75.0%
    """

    total: int
    downloaded: int
    skipped: int
    failed: int
    duration: float


class BatchDownloadUseCase:
    """
    Use case for batch downloading multiple problems from a platform.

    This use case orchestrates the download of multiple problems based on
    user-specified criteria. It handles filtering, update modes, progress
    tracking, and partial failure scenarios gracefully.

    The use case implements the following workflow:
    1. Fetch list of solved problems for the user
    2. Apply difficulty and topic filters
    3. Notify observers that batch download is starting
    4. For each problem:
       a. Check if it should be skipped based on update mode
       b. Download problem and submission
       c. Save to repository
       d. Notify observers of progress
    5. Handle partial failures (continue with remaining problems)
    6. Notify observers of completion with statistics

    Attributes:
        client: Platform client for fetching problems from the API
        repository: Repository for caching problems locally
        formatter: Output formatter for saving problems
        observers: List of observers for progress tracking
        logger: Logger for tracking operations

    Example:
        >>> use_case = BatchDownloadUseCase(
        ...     client=leetcode_client,
        ...     repository=file_repo,
        ...     formatter=python_formatter,
        ...     observers=[console_observer, logging_observer],
        ...     logger=logger
        ... )
        >>> options = BatchDownloadOptions(
        ...     username="john_doe",
        ...     platform="leetcode",
        ...     update_mode=UpdateMode.SKIP,
        ...     difficulty_filter=["Easy", "Medium"]
        ... )
        >>> stats = use_case.execute(options)
        >>> print(f"Downloaded {stats.downloaded} problems")
    """

    def __init__(
        self,
        client: PlatformClient,
        repository: ProblemRepository,
        formatter: OutputFormatter,
        observers: List[DownloadObserver],
        logger: Logger,
    ):
        """
        Initialize the BatchDownloadUseCase.

        Args:
            client: Platform client for API communication
            repository: Repository for problem persistence
            formatter: Output formatter for problem files
            observers: List of observers for progress tracking
            logger: Logger for operation tracking
        """
        self.client = client
        self.repository = repository
        self.formatter = formatter
        self.observers = observers
        self.logger = logger

    def execute(self, options: BatchDownloadOptions) -> DownloadStats:
        """
        Download multiple problems based on options.

        This method orchestrates the entire batch download process:
        1. Fetches the list of solved problems
        2. Applies filters (difficulty, topics)
        3. Downloads each problem with appropriate update logic
        4. Tracks progress and handles errors gracefully
        5. Returns comprehensive statistics

        Args:
            options: Configuration for the batch download operation

        Returns:
            DownloadStats: Statistics about the download operation including
                          total, downloaded, skipped, failed counts and duration

        Raises:
            NetworkException: If fetching the problem list fails
            AuthenticationException: If authentication is required but not provided

        Example:
            >>> options = BatchDownloadOptions(
            ...     username="john_doe",
            ...     platform="leetcode",
            ...     update_mode=UpdateMode.UPDATE,
            ...     difficulty_filter=["Medium", "Hard"]
            ... )
            >>> stats = use_case.execute(options)
            >>> print(f"Success rate: {stats.downloaded / stats.total * 100:.1f}%")
        """
        start_time = time.time()

        self.logger.info(
            f"Starting batch download for user '{options.username}' "
            f"on platform '{options.platform}' with mode '{options.update_mode.value}'"
        )

        # Fetch list of solved problems
        try:
            self.logger.info(f"Fetching all solved problems for user '{options.username}'")
            # Use fetch_all_problems_with_status to get complete list of solved problems
            problems = self.client.fetch_all_problems_with_status(status_filter="ac")
            self.logger.info(f"Found {len(problems)} solved problems")
        except Exception as e:
            self.logger.error(f"Failed to fetch solved problems for user '{options.username}': {e}")
            raise

        # Apply filters (difficulty, topics)
        problems = self._apply_filters(problems, options)
        self.logger.info(f"After filtering: {len(problems)} problems")

        # For SKIP mode, filter out already-downloaded problems BEFORE applying limit
        # This ensures --limit applies to NEW problems only
        if options.update_mode == UpdateMode.SKIP:
            original_count = len(problems)
            problems = [p for p in problems if not self.repository.exists(p.id, p.platform)]
            already_downloaded = original_count - len(problems)
            if already_downloaded > 0:
                self.logger.info(
                    f"Found {already_downloaded} already-downloaded problems, "
                    f"will skip them ({len(problems)} new problems available)"
                )

        # Apply limit AFTER filtering out existing problems
        # This ensures --limit X downloads X NEW problems, not X total problems
        if options.limit and options.limit < len(problems):
            self.logger.info(
                f"Limiting to {options.limit} new problems to download "
                f"(out of {len(problems)} available)"
            )
            problems = problems[: options.limit]

        self.logger.info(f"Will download {len(problems)} problems")

        # Notify observers that batch is starting
        self._notify_start(len(problems))

        # Initialize statistics
        stats = DownloadStats(
            total=len(problems),
            downloaded=0,
            skipped=0,
            failed=0,
            duration=0.0,
        )

        # Download each problem
        for i, problem in enumerate(problems):
            try:
                self._download_problem(problem, options, stats)
                self._notify_progress(i + 1, len(problems), problem)
            except Exception as e:
                stats.failed += 1
                self._notify_error(problem, e)
                self.logger.error(f"Failed to download problem '{problem.id}': {e}", exc_info=True)
                # Continue with next problem (partial failure handling)

        # Calculate duration and notify completion
        stats.duration = time.time() - start_time
        self._notify_complete(stats)

        self.logger.info(
            f"Batch download complete: {stats.downloaded} downloaded, "
            f"{stats.skipped} skipped, {stats.failed} failed out of {stats.total} total "
            f"in {stats.duration:.2f} seconds"
        )

        return stats

    def _apply_filters(
        self, problems: List[Problem], options: BatchDownloadOptions
    ) -> List[Problem]:
        """
        Apply difficulty and topic filters to the problem list.

        Args:
            problems: List of problems to filter
            options: Batch download options containing filter criteria

        Returns:
            Filtered list of problems
        """
        filtered = problems

        # Apply difficulty filter
        if options.difficulty_filter:
            self.logger.debug(f"Applying difficulty filter: {options.difficulty_filter}")
            filtered = [p for p in filtered if p.difficulty.level in options.difficulty_filter]
            self.logger.debug(f"After difficulty filter: {len(filtered)} problems remain")

        # Apply topic filter
        if options.topic_filter:
            self.logger.debug(f"Applying topic filter: {options.topic_filter}")
            filtered = [
                p for p in filtered if any(topic in p.topics for topic in options.topic_filter)
            ]
            self.logger.debug(f"After topic filter: {len(filtered)} problems remain")

        return filtered

    def _download_problem(
        self,
        problem: Problem,
        options: BatchDownloadOptions,
        stats: DownloadStats,
    ) -> None:
        """
        Download a single problem based on update mode.

        This method implements the update mode logic:
        - SKIP: Skip if problem already exists
        - UPDATE: Download if problem doesn't exist or submission is newer
        - FORCE: Always download, overwriting existing files

        Args:
            problem: The problem to download
            options: Batch download options
            stats: Statistics object to update

        Raises:
            Exception: Any exception during download (caught by caller)
        """
        problem_exists = self.repository.exists(problem.id, problem.platform)

        # Handle SKIP mode - should not reach here if already exists (pre-filtered)
        if options.update_mode == UpdateMode.SKIP and problem_exists:
            self.logger.debug(f"Skipping problem '{problem.id}' (already exists, mode=SKIP)")
            stats.skipped += 1
            self._notify_skip(problem, "Already exists")
            return

        # Handle UPDATE mode - check if submission is newer
        if options.update_mode == UpdateMode.UPDATE and problem_exists:
            # Get stored submission timestamp
            stored_timestamp = self.repository.get_submission_timestamp(
                problem.id, problem.platform
            )

            if stored_timestamp is not None:
                # Fetch latest submission from platform to compare timestamps
                try:
                    latest_submission = self.client.fetch_submission(problem.id, options.username)

                    # Compare timestamps - skip if stored submission is same or newer
                    if latest_submission.timestamp <= stored_timestamp:
                        self.logger.debug(
                            f"Skipping problem '{problem.id}' "
                            f"(stored submission is up-to-date, mode=UPDATE)"
                        )
                        stats.skipped += 1
                        self._notify_skip(problem, "Submission is up-to-date")
                        return
                    else:
                        self.logger.info(
                            f"Newer submission found for '{problem.id}' "
                            f"(platform: {latest_submission.timestamp}, "
                            f"stored: {stored_timestamp})"
                        )
                        # Continue to download the newer submission
                except Exception as e:
                    self.logger.warning(
                        f"Failed to fetch submission for comparison on '{problem.id}': {e}. "
                        "Skipping update."
                    )
                    stats.skipped += 1
                    self._notify_skip(problem, "Failed to check for newer submission")
                    return
            else:
                # Problem exists but has no submission stored - re-download to add submission
                self.logger.info(
                    f"Problem '{problem.id}' exists but has no submission, will update"
                )
                # Continue to download

        # Download problem (FORCE mode or problem doesn't exist)
        self.logger.info(f"Downloading problem '{problem.id}'")

        # Fetch problem details (may already have them, but fetch to ensure fresh data)
        problem_details = self.client.fetch_problem(problem.id)

        # Fetch submission
        submission: Optional[Submission] = None
        try:
            self.logger.debug(
                f"Fetching submission for problem '{problem.id}' " f"by user '{options.username}'"
            )
            submission = self.client.fetch_submission(problem.id, options.username)
            self.logger.debug(f"Successfully fetched submission for '{problem.id}'")
            # Add extra delay after submission fetch to avoid rate limiting
            # LeetCode's submission API is more aggressive with rate limits
            time.sleep(1.0)
        except Exception as e:
            self.logger.warning(
                f"Failed to fetch submission for problem '{problem.id}': {e}. "
                "Saving problem without submission."
            )
            # Continue without submission

        # Save to repository
        self.logger.debug(f"Saving problem '{problem.id}' to repository")
        self.repository.save(problem_details, submission)

        stats.downloaded += 1
        self.logger.info(f"Successfully downloaded problem '{problem.id}'")

    def _notify_start(self, total: int) -> None:
        """Notify all observers that batch download is starting."""
        for observer in self.observers:
            try:
                observer.on_start(total)
            except Exception as e:
                self.logger.warning(f"Observer {observer.__class__.__name__} failed on_start: {e}")

    def _notify_progress(self, current: int, total: int, problem: Problem) -> None:
        """Notify all observers of download progress."""
        for observer in self.observers:
            try:
                observer.on_progress(current, total, problem)
            except Exception as e:
                self.logger.warning(
                    f"Observer {observer.__class__.__name__} failed on_progress: {e}"
                )

    def _notify_skip(self, problem: Problem, reason: str) -> None:
        """Notify all observers that a problem was skipped."""
        for observer in self.observers:
            try:
                observer.on_skip(problem, reason)
            except Exception as e:
                self.logger.warning(f"Observer {observer.__class__.__name__} failed on_skip: {e}")

    def _notify_error(self, problem: Problem, error: Exception) -> None:
        """Notify all observers that an error occurred."""
        for observer in self.observers:
            try:
                observer.on_error(problem, error)
            except Exception as e:
                self.logger.warning(f"Observer {observer.__class__.__name__} failed on_error: {e}")

    def _notify_complete(self, stats: DownloadStats) -> None:
        """Notify all observers that batch download is complete."""
        for observer in self.observers:
            try:
                observer.on_complete(stats)
            except Exception as e:
                self.logger.warning(
                    f"Observer {observer.__class__.__name__} failed on_complete: {e}"
                )
