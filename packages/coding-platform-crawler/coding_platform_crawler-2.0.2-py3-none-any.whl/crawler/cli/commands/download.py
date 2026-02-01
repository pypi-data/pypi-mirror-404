"""
Download command for fetching a single problem via CLI.

This module implements the DownloadCommand for downloading individual problems
from coding platforms. It handles argument parsing, validation, and orchestrates
the FetchProblemUseCase to fetch and save problems.
"""

import argparse
from logging import Logger
from typing import Optional

from crawler.application.interfaces.formatter import OutputFormatter
from crawler.application.interfaces.platform_client import PlatformClient
from crawler.application.interfaces.repository import ProblemRepository
from crawler.application.use_cases.fetch_problem import FetchProblemUseCase
from crawler.cli.commands.base import Command, CommandResult
from crawler.domain.exceptions import (
    AuthenticationException,
    CrawlerException,
    NetworkException,
    ProblemNotFoundException,
    RepositoryException,
    UnsupportedPlatformException,
)


class DownloadCommand(Command):
    """
    Command for downloading a single problem from a coding platform.

    This command fetches a problem by ID from the specified platform and saves
    it to the local repository using the configured output format. It supports
    force mode to bypass the cache and always fetch fresh data.

    The command handles all errors gracefully and provides user-friendly error
    messages with actionable suggestions for common issues.

    Attributes:
        problem_id: The platform-specific problem identifier
        platform: The platform name (e.g., "leetcode", "hackerrank")
        force: Whether to bypass cache and force re-download
        output_format: The output format (e.g., "python", "markdown", "json")
        client: Platform client for API communication
        repository: Repository for problem persistence
        formatter: Output formatter for the specified format
        logger: Logger for operation tracking

    Example:
        >>> command = DownloadCommand(
        ...     problem_id="two-sum",
        ...     platform="leetcode",
        ...     force=False,
        ...     output_format="python",
        ...     client=leetcode_client,
        ...     repository=file_repo,
        ...     formatter=python_formatter,
        ...     logger=logger
        ... )
        >>> result = command.execute()
        >>> print(result.message)
        "Successfully downloaded problem 'two-sum' from leetcode"
    """

    def __init__(
        self,
        problem_id: str,
        platform: str,
        force: bool,
        output_format: str,
        client: PlatformClient,
        repository: ProblemRepository,
        formatter: OutputFormatter,
        logger: Logger,
    ):
        """
        Initialize the DownloadCommand.

        Args:
            problem_id: The problem identifier (e.g., "two-sum")
            platform: The platform name (e.g., "leetcode")
            force: Whether to force re-download (bypass cache)
            output_format: The output format (e.g., "python", "markdown", "json")
            client: Platform client for fetching problems
            repository: Repository for saving problems
            formatter: Output formatter for the specified format
            logger: Logger for tracking operations
        """
        self.problem_id = problem_id
        self.platform = platform
        self.force = force
        self.output_format = output_format
        self.client = client
        self.repository = repository
        self.formatter = formatter
        self.logger = logger

    def execute(self) -> CommandResult:
        """
        Execute the download command.

        This method:
        1. Validates the input parameters
        2. Creates a FetchProblemUseCase instance
        3. Fetches the problem (from cache or platform)
        4. Saves the problem to the repository
        5. Returns a CommandResult with success/failure status

        All errors are caught and converted to CommandResult with appropriate
        error messages and suggestions for resolution.

        Returns:
            CommandResult: The result of the command execution with:
                - success: True if download succeeded, False otherwise
                - message: Human-readable message describing the result
                - data: The fetched Problem entity (if successful)
                - error: The exception that occurred (if failed)

        Example:
            >>> result = command.execute()
            >>> if result.success:
            ...     print(f"Downloaded: {result.data.title}")
            ... else:
            ...     print(f"Error: {result.message}")
        """
        try:
            # Validate inputs
            self._validate_inputs()

            # Log the operation
            self.logger.info(
                f"Starting download of problem '{self.problem_id}' "
                f"from platform '{self.platform}' "
                f"(force={self.force}, format={self.output_format})"
            )

            # Create use case and execute
            use_case = FetchProblemUseCase(
                client=self.client,
                repository=self.repository,
                logger=self.logger,
            )

            problem = use_case.execute(
                problem_id=self.problem_id,
                platform=self.platform,
                force=self.force,
            )

            # Fetch submission if authenticated
            submission = None
            try:
                self.logger.info(f"Fetching submission for problem '{self.problem_id}'")
                submission = self.client.fetch_submission(self.problem_id, "")
                if (
                    submission
                    and submission.code
                    and "Authentication required" not in submission.code
                ):
                    self.logger.info(f"Successfully fetched submission in {submission.language}")
                else:
                    self.logger.info("No submission available or authentication required")
                    submission = None
            except Exception as e:
                self.logger.warning(f"Could not fetch submission: {e}")
                submission = None

            # Save problem with submission to repository
            self.repository.save(problem, submission)

            # Success message
            cache_status = "from platform" if self.force else "from cache or platform"
            message = (
                f"Successfully downloaded problem '{problem.title}' "
                f"(ID: {self.problem_id}) from {self.platform} {cache_status}. "
                f"Saved as {self.output_format} format."
            )

            self.logger.info(message)

            return CommandResult(
                success=True,
                message=message,
                data=problem,
            )

        except ProblemNotFoundException as e:
            error_message = (
                f"Problem '{self.problem_id}' not found on {self.platform}. "
                f"Please check the problem ID and try again. "
                f"Tip: Problem IDs are usually lowercase with hyphens (e.g., 'two-sum')."
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
                f"Network error while downloading problem '{self.problem_id}': {str(e)}. "
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
                f"Failed to save problem '{self.problem_id}' to repository: {str(e)}. "
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
                f"Error downloading problem '{self.problem_id}': {str(e)}. "
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
                f"Unexpected error downloading problem '{self.problem_id}': {str(e)}. "
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
        if not self.problem_id or not self.problem_id.strip():
            raise ValueError("Problem ID cannot be empty")

        if not self.platform or not self.platform.strip():
            raise ValueError("Platform cannot be empty")

        if not self.output_format or not self.output_format.strip():
            raise ValueError("Output format cannot be empty")

    @staticmethod
    def create_argument_parser() -> argparse.ArgumentParser:
        """
        Create an argument parser for the download command.

        This static method creates an ArgumentParser configured with all
        the arguments needed for the download command. It can be used by
        the CLI main module to parse command-line arguments.

        Returns:
            argparse.ArgumentParser: Configured argument parser

        Example:
            >>> parser = DownloadCommand.create_argument_parser()
            >>> args = parser.parse_args(["two-sum", "--platform", "leetcode"])
            >>> print(args.problem_id)
            "two-sum"
        """
        parser = argparse.ArgumentParser(
            description="Download a single problem from a coding platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Download a problem from LeetCode
  download two-sum --platform leetcode

  # Force re-download (bypass cache)
  download two-sum --platform leetcode --force

  # Download with specific output format
  download two-sum --platform leetcode --format markdown

  # Download with all options
  download two-sum --platform leetcode --force --format json
            """,
        )

        parser.add_argument(
            "problem_id",
            type=str,
            help="Problem identifier (e.g., 'two-sum' for LeetCode)",
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
            "--force",
            "-f",
            action="store_true",
            default=False,
            help="Force re-download, bypassing cache (default: False)",
        )

        parser.add_argument(
            "--format",
            type=str,
            default="python",
            choices=["python", "markdown", "json"],
            help="Output format for the problem file (default: python)",
        )

        return parser
