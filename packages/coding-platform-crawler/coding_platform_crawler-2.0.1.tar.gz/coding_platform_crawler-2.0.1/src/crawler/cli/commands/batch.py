"""
Batch download command for downloading multiple problems via CLI.

This module implements the BatchDownloadCommand for batch downloading all solved
problems for a user from coding platforms. It handles argument parsing, validation,
and orchestrates the BatchDownloadUseCase to fetch and save multiple problems with
progress tracking.
"""

import argparse
from logging import Logger
from typing import List, Optional

from crawler.application.interfaces.formatter import OutputFormatter
from crawler.application.interfaces.observer import DownloadObserver
from crawler.application.interfaces.platform_client import PlatformClient
from crawler.application.interfaces.repository import ProblemRepository
from crawler.application.use_cases.batch_download import (
    BatchDownloadOptions,
    BatchDownloadUseCase,
    DownloadStats,
)
from crawler.cli.commands.base import Command, CommandResult
from crawler.domain.entities import UpdateMode
from crawler.domain.exceptions import (
    AuthenticationException,
    CrawlerException,
    NetworkException,
    ProblemNotFoundException,
    RepositoryException,
    UnsupportedPlatformException,
)


class BatchDownloadCommand(Command):
    """
    Command for batch downloading all solved problems for a user.

    This command fetches all problems solved by a user from the specified platform
    and saves them to the local repository using the configured output format. It
    supports different update modes (SKIP, UPDATE, FORCE) and optional filters for
    difficulty and topics.

    The command provides real-time progress feedback through observers and handles
    partial failures gracefully, continuing to download remaining problems even if
    some fail.

    Attributes:
        username: The username on the platform whose problems to download
        platform: The platform name (e.g., "leetcode", "hackerrank")
        update_mode: How to handle existing files (SKIP, UPDATE, or FORCE)
        difficulty_filter: Optional list of difficulty levels to include
        topic_filter: Optional list of topics to include
        include_community: Whether to download community solutions
        output_format: The output format (e.g., "python", "markdown", "json")
        client: Platform client for API communication
        repository: Repository for problem persistence
        formatter: Output formatter for the specified format
        observers: List of observers for progress tracking
        logger: Logger for operation tracking

    Example:
        >>> command = BatchDownloadCommand(
        ...     username="john_doe",
        ...     platform="leetcode",
        ...     update_mode=UpdateMode.SKIP,
        ...     difficulty_filter=["Easy", "Medium"],
        ...     topic_filter=None,
        ...     include_community=False,
        ...     output_format="python",
        ...     client=leetcode_client,
        ...     repository=file_repo,
        ...     formatter=python_formatter,
        ...     observers=[console_observer],
        ...     logger=logger
        ... )
        >>> result = command.execute()
        >>> print(result.message)
        "Successfully downloaded 75 problems (20 skipped, 5 failed) in 245.3 seconds"
    """

    def __init__(
        self,
        username: str,
        platform: str,
        update_mode: UpdateMode,
        difficulty_filter: Optional[List[str]],
        topic_filter: Optional[List[str]],
        include_community: bool,
        output_format: str,
        limit: Optional[int],
        client: PlatformClient,
        repository: ProblemRepository,
        formatter: OutputFormatter,
        observers: List[DownloadObserver],
        logger: Logger,
    ):
        """
        Initialize the BatchDownloadCommand.

        Args:
            username: The username on the platform
            platform: The platform name (e.g., "leetcode")
            update_mode: How to handle existing files (SKIP, UPDATE, or FORCE)
            difficulty_filter: Optional list of difficulty levels (e.g., ["Easy", "Medium"])
            topic_filter: Optional list of topics (e.g., ["Array", "Hash Table"])
            include_community: Whether to download community solutions
            output_format: The output format (e.g., "python", "markdown", "json")
            limit: Optional maximum number of problems to download
            client: Platform client for fetching problems
            repository: Repository for saving problems
            formatter: Output formatter for the specified format
            observers: List of observers for progress tracking
            logger: Logger for tracking operations
        """
        self.username = username
        self.platform = platform
        self.update_mode = update_mode
        self.difficulty_filter = difficulty_filter
        self.topic_filter = topic_filter
        self.include_community = include_community
        self.output_format = output_format
        self.limit = limit
        self.client = client
        self.repository = repository
        self.formatter = formatter
        self.observers = observers
        self.logger = logger

    def execute(self) -> CommandResult:
        """
        Execute the batch download command.

        This method:
        1. Validates the input parameters
        2. Creates a BatchDownloadUseCase instance
        3. Configures BatchDownloadOptions with filters
        4. Executes the batch download with progress tracking
        5. Returns a CommandResult with download statistics

        All errors are caught and converted to CommandResult with appropriate
        error messages and suggestions for resolution. Partial failures are
        handled gracefully - the command continues downloading remaining problems
        even if some fail.

        Returns:
            CommandResult: The result of the command execution with:
                - success: True if at least one problem was downloaded, False otherwise
                - message: Human-readable message with download statistics
                - data: DownloadStats object with detailed statistics
                - error: The exception that occurred (if complete failure)

        Example:
            >>> result = command.execute()
            >>> if result.success:
            ...     stats = result.data
            ...     print(f"Downloaded: {stats.downloaded}, Skipped: {stats.skipped}")
            ... else:
            ...     print(f"Error: {result.message}")
        """
        try:
            # Validate inputs
            self._validate_inputs()

            # Log the operation
            self.logger.info(
                f"Starting batch download for user '{self.username}' "
                f"on platform '{self.platform}' "
                f"(mode={self.update_mode.value}, format={self.output_format})"
            )

            if self.difficulty_filter:
                self.logger.info(f"Difficulty filter: {self.difficulty_filter}")
            if self.topic_filter:
                self.logger.info(f"Topic filter: {self.topic_filter}")

            # Create batch download options
            options = BatchDownloadOptions(
                username=self.username,
                platform=self.platform,
                update_mode=self.update_mode,
                include_community=self.include_community,
                limit=self.limit,
                difficulty_filter=self.difficulty_filter,
                topic_filter=self.topic_filter,
            )

            # Create use case and execute
            use_case = BatchDownloadUseCase(
                client=self.client,
                repository=self.repository,
                formatter=self.formatter,
                observers=self.observers,
                logger=self.logger,
            )

            stats = use_case.execute(options)

            # Determine success based on whether any problems were downloaded
            success = stats.downloaded > 0 or (stats.total == stats.skipped and stats.failed == 0)

            # Build success message
            message = self._build_result_message(stats)

            self.logger.info(message)

            return CommandResult(
                success=success,
                message=message,
                data=stats,
            )

        except ProblemNotFoundException as e:
            error_message = (
                f"User '{self.username}' not found on {self.platform}. "
                f"Please check the username and try again. "
                f"Tip: Usernames are case-sensitive on most platforms."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except AuthenticationException as e:
            error_message = (
                f"Authentication failed for {self.platform}: {e.reason}. "
                f"Please check your credentials in the configuration. "
                f"Tip: Set the appropriate environment variable or config file entry "
                f"for {self.platform} authentication."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except NetworkException as e:
            error_message = (
                f"Network error during batch download: {str(e)}. "
                f"Please check your internet connection and try again. "
            )
            if e.status_code:
                error_message += f"HTTP Status Code: {e.status_code}. "
            if e.url:
                error_message += f"URL: {e.url}. "
            error_message += (
                "Tip: If the problem persists, the platform may be experiencing issues."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except UnsupportedPlatformException as e:
            error_message = (
                f"Platform '{self.platform}' is not supported. "
                f"Currently supported platforms: leetcode. "
                f"Tip: Check the documentation for a list of supported platforms."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except RepositoryException as e:
            error_message = (
                f"Failed to save problems to repository: {str(e)}. "
                f"Please check file permissions and disk space. "
                f"Tip: Ensure the output directory is writable."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except CrawlerException as e:
            error_message = (
                f"Error during batch download: {str(e)}. "
                f"Please check the error message and try again."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except Exception as e:
            error_message = (
                f"Unexpected error during batch download: {str(e)}. "
                f"This is likely a bug. Please report it with the full error message."
            )
            self.logger.exception(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

    def _validate_inputs(self) -> None:
        """
        Validate command inputs.

        Raises:
            ValueError: If any input is invalid
        """
        if not self.username or not self.username.strip():
            raise ValueError("Username cannot be empty")

        if not self.platform or not self.platform.strip():
            raise ValueError("Platform cannot be empty")

        if not self.output_format or not self.output_format.strip():
            raise ValueError("Output format cannot be empty")

        # Validate difficulty filter values
        if self.difficulty_filter:
            valid_difficulties = {"Easy", "Medium", "Hard"}
            for difficulty in self.difficulty_filter:
                if difficulty not in valid_difficulties:
                    raise ValueError(
                        f"Invalid difficulty '{difficulty}'. "
                        f"Must be one of: {', '.join(valid_difficulties)}"
                    )

    def _build_result_message(self, stats: DownloadStats) -> str:
        """
        Build a human-readable result message from download statistics.

        Args:
            stats: Download statistics

        Returns:
            Formatted message string
        """
        if stats.total == 0:
            return "No problems found to download."

        message_parts = []

        # Main success message
        if stats.downloaded > 0:
            message_parts.append(f"Successfully downloaded {stats.downloaded} problem(s)")
        else:
            message_parts.append("No new problems downloaded")

        # Add skipped count if any
        if stats.skipped > 0:
            message_parts.append(f"{stats.skipped} skipped")

        # Add failed count if any
        if stats.failed > 0:
            message_parts.append(f"{stats.failed} failed")

        # Add total and duration
        message_parts.append(f"out of {stats.total} total in {stats.duration:.2f} seconds")

        # Join all parts
        message = " (".join(message_parts[:1] + [", ".join(message_parts[1:])])
        if len(message_parts) > 1:
            message += ")"
        else:
            message += f" in {stats.duration:.2f} seconds"

        # Add success rate if there were any attempts
        if stats.total > 0:
            success_rate = (stats.downloaded / stats.total) * 100
            message += f". Success rate: {success_rate:.1f}%"

        return message

    @staticmethod
    def create_argument_parser() -> argparse.ArgumentParser:
        """
        Create an argument parser for the batch download command.

        This static method creates an ArgumentParser configured with all
        the arguments needed for the batch download command. It can be used by
        the CLI main module to parse command-line arguments.

        Returns:
            argparse.ArgumentParser: Configured argument parser

        Example:
            >>> parser = BatchDownloadCommand.create_argument_parser()
            >>> args = parser.parse_args([
            ...     "john_doe",
            ...     "--platform", "leetcode",
            ...     "--mode", "skip"
            ... ])
            >>> print(args.username)
            "john_doe"
        """
        parser = argparse.ArgumentParser(
            description="Batch download all solved problems for a user",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Download all solved problems, skipping existing ones
  batch john_doe --platform leetcode --mode skip

  # Force re-download all problems
  batch john_doe --platform leetcode --mode force

  # Download only Easy and Medium problems
  batch john_doe --platform leetcode --mode update --difficulty Easy Medium

  # Download only recent 50 problems
  batch john_doe --platform leetcode --mode skip --limit 50

  # Download problems with specific topics
  batch john_doe --platform leetcode --mode skip --topics Array "Hash Table"

  # Download with all options
  batch john_doe --platform leetcode --mode update \\
    --difficulty Easy Medium --topics Array --format markdown --limit 100
            """,
        )

        parser.add_argument(
            "username",
            type=str,
            help="Username on the platform whose problems to download",
        )

        parser.add_argument(
            "--platform",
            "-p",
            type=str,
            required=True,
            choices=["leetcode"],  # Extensible for future platforms
            help="Platform to download from (currently only 'leetcode' is supported)",
        )

        parser.add_argument(
            "--mode",
            "-m",
            type=str,
            required=True,
            choices=["skip", "update", "force"],
            help=(
                "Update mode: 'skip' = skip existing files, "
                "'update' = update if newer submission exists, "
                "'force' = always overwrite"
            ),
        )

        parser.add_argument(
            "--difficulty",
            "-d",
            type=str,
            nargs="+",
            choices=["Easy", "Medium", "Hard"],
            help="Filter by difficulty levels (can specify multiple)",
        )

        parser.add_argument(
            "--topics",
            "-t",
            type=str,
            nargs="+",
            help="Filter by topics (can specify multiple, e.g., 'Array' 'Hash Table')",
        )

        parser.add_argument(
            "--include-community",
            action="store_true",
            default=False,
            help="Include community solutions (default: False)",
        )

        parser.add_argument(
            "--format",
            "-f",
            type=str,
            default="python",
            choices=["python", "markdown", "json"],
            help="Output format for the problem files (default: python)",
        )

        parser.add_argument(
            "--limit",
            "-l",
            type=int,
            help="Maximum number of problems to download (default: all)",
        )

        return parser
