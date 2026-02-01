"""
List command for listing downloaded problems via CLI.

This module implements the ListCommand for listing all downloaded problems
with optional filtering and sorting. It handles argument parsing, validation,
and orchestrates the ListProblemsUseCase to retrieve and display problems.
"""

import argparse
from logging import Logger
from typing import List, Optional

from crawler.application.interfaces.repository import ProblemRepository
from crawler.application.use_cases.list_problems import ListOptions, ListProblemsUseCase
from crawler.cli.commands.base import Command, CommandResult
from crawler.domain.entities import Problem
from crawler.domain.exceptions import CrawlerException, RepositoryException


class ListCommand(Command):
    """
    Command for listing downloaded problems with filtering and sorting.

    This command retrieves all problems from the local repository and displays
    them with optional filtering by platform, difficulty, and topics. It also
    supports sorting by various fields (id, title, difficulty, acceptance_rate,
    platform) in ascending or descending order.

    The command provides a convenient way to view what problems have been
    downloaded, find problems by specific criteria, and organize the problem
    list for review.

    Attributes:
        platform: Optional platform name to filter by (e.g., "leetcode")
        difficulty_filter: Optional list of difficulty levels to include
        topic_filter: Optional list of topics to include
        sort_by: Field to sort by (id, title, difficulty, acceptance_rate, platform)
        reverse: Whether to sort in descending order
        repository: Repository for accessing stored problems
        logger: Logger for operation tracking

    Example:
        >>> command = ListCommand(
        ...     platform="leetcode",
        ...     difficulty_filter=["Easy", "Medium"],
        ...     topic_filter=None,
        ...     sort_by="acceptance_rate",
        ...     reverse=True,
        ...     repository=file_repo,
        ...     logger=logger
        ... )
        >>> result = command.execute()
        >>> print(result.message)
        "Found 42 problems matching criteria"
    """

    def __init__(
        self,
        platform: Optional[str],
        difficulty_filter: Optional[List[str]],
        topic_filter: Optional[List[str]],
        sort_by: str,
        reverse: bool,
        repository: ProblemRepository,
        logger: Logger,
    ):
        """
        Initialize the ListCommand.

        Args:
            platform: Optional platform name to filter by (e.g., "leetcode")
            difficulty_filter: Optional list of difficulty levels (e.g., ["Easy", "Medium"])
            topic_filter: Optional list of topics (e.g., ["Array", "Hash Table"])
            sort_by: Field to sort by (id, title, difficulty, acceptance_rate, platform)
            reverse: Whether to sort in descending order (default: False)
            repository: Repository for accessing stored problems
            logger: Logger for tracking operations
        """
        self.platform = platform
        self.difficulty_filter = difficulty_filter
        self.topic_filter = topic_filter
        self.sort_by = sort_by
        self.reverse = reverse
        self.repository = repository
        self.logger = logger

    def execute(self) -> CommandResult:
        """
        Execute the list command.

        This method:
        1. Validates the input parameters
        2. Creates a ListProblemsUseCase instance
        3. Configures ListOptions with filters and sorting
        4. Retrieves the filtered and sorted list of problems
        5. Returns a CommandResult with the list of problems

        All errors are caught and converted to CommandResult with appropriate
        error messages and suggestions for resolution.

        Returns:
            CommandResult: The result of the command execution with:
                - success: True if listing succeeded, False otherwise
                - message: Human-readable message describing the result
                - data: List of Problem entities matching the criteria
                - error: The exception that occurred (if failed)

        Example:
            >>> result = command.execute()
            >>> if result.success:
            ...     for problem in result.data:
            ...         print(f"{problem.id}: {problem.title} ({problem.difficulty.level})")
            ... else:
            ...     print(f"Error: {result.message}")
        """
        try:
            # Validate inputs
            self._validate_inputs()

            # Log the operation
            filter_desc = self._build_filter_description()
            self.logger.info(
                f"Listing problems with filters: {filter_desc}, "
                f"sort_by={self.sort_by}, reverse={self.reverse}"
            )

            # Create list options
            options = ListOptions(
                platform=self.platform,
                difficulty=self.difficulty_filter,
                topics=self.topic_filter,
                sort_by=self.sort_by,
                reverse=self.reverse,
            )

            # Create use case and execute
            use_case = ListProblemsUseCase(
                repository=self.repository,
                logger=self.logger,
            )

            problems = use_case.execute(options)

            # Build success message
            message = self._build_result_message(problems, filter_desc)

            self.logger.info(message)

            return CommandResult(
                success=True,
                message=message,
                data=problems,
            )

        except RepositoryException as e:
            error_message = (
                f"Failed to list problems from repository: {str(e)}. "
                f"Please check file permissions and ensure the repository directory exists. "
                f"Tip: Ensure the output directory is readable."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except ValueError as e:
            error_message = (
                f"Invalid parameter: {str(e)}. "
                f"Please check your command arguments and try again."
            )
            self.logger.error(error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=e,
            )

        except CrawlerException as e:
            error_message = (
                f"Error listing problems: {str(e)}. "
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
                f"Unexpected error listing problems: {str(e)}. "
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
        # Validate sort_by field
        valid_sort_fields = {"id", "title", "difficulty", "acceptance_rate", "platform"}
        if self.sort_by not in valid_sort_fields:
            raise ValueError(
                f"Invalid sort_by field '{self.sort_by}'. "
                f"Must be one of: {', '.join(sorted(valid_sort_fields))}"
            )

        # Validate difficulty filter values
        if self.difficulty_filter:
            valid_difficulties = {"Easy", "Medium", "Hard"}
            for difficulty in self.difficulty_filter:
                if difficulty not in valid_difficulties:
                    raise ValueError(
                        f"Invalid difficulty '{difficulty}'. "
                        f"Must be one of: {', '.join(sorted(valid_difficulties))}"
                    )

        # Validate platform if specified
        if self.platform and not self.platform.strip():
            raise ValueError("Platform cannot be empty string")

    def _build_filter_description(self) -> str:
        """
        Build a human-readable description of active filters.

        Returns:
            String describing the active filters
        """
        filters = []

        if self.platform:
            filters.append(f"platform={self.platform}")

        if self.difficulty_filter:
            filters.append(f"difficulty={', '.join(self.difficulty_filter)}")

        if self.topic_filter:
            filters.append(f"topics={', '.join(self.topic_filter)}")

        return ", ".join(filters) if filters else "no filters"

    def _build_result_message(self, problems: List[Problem], filter_desc: str) -> str:
        """
        Build a human-readable result message.

        Args:
            problems: List of problems returned by the use case
            filter_desc: Description of active filters

        Returns:
            Formatted message string
        """
        count = len(problems)

        if count == 0:
            if filter_desc == "no filters":
                return "No problems found in repository. Download some problems first."
            else:
                return f"No problems found matching criteria ({filter_desc})."

        # Build message with count and filters
        if count == 1:
            message = "Found 1 problem"
        else:
            message = f"Found {count} problems"

        if filter_desc != "no filters":
            message += f" matching criteria ({filter_desc})"

        # Add sorting info
        sort_order = "descending" if self.reverse else "ascending"
        message += f", sorted by {self.sort_by} ({sort_order})"

        return message + "."

    @staticmethod
    def create_argument_parser() -> argparse.ArgumentParser:
        """
        Create an argument parser for the list command.

        This static method creates an ArgumentParser configured with all
        the arguments needed for the list command. It can be used by
        the CLI main module to parse command-line arguments.

        Returns:
            argparse.ArgumentParser: Configured argument parser

        Example:
            >>> parser = ListCommand.create_argument_parser()
            >>> args = parser.parse_args([
            ...     "--platform", "leetcode",
            ...     "--difficulty", "Easy", "Medium",
            ...     "--sort-by", "acceptance_rate",
            ...     "--reverse"
            ... ])
            >>> print(args.platform)
            "leetcode"
        """
        parser = argparse.ArgumentParser(
            description="List downloaded problems with filtering and sorting",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # List all downloaded problems
  list

  # List problems from a specific platform
  list --platform leetcode

  # List only Easy and Medium problems
  list --difficulty Easy Medium

  # List problems with specific topics
  list --topics Array "Hash Table"

  # List problems sorted by acceptance rate (highest first)
  list --sort-by acceptance_rate --reverse

  # List Easy LeetCode problems on Array topic, sorted by title
  list --platform leetcode --difficulty Easy --topics Array --sort-by title

  # List all problems sorted by difficulty (Easy to Hard)
  list --sort-by difficulty
            """,
        )

        parser.add_argument(
            "--platform",
            "-p",
            type=str,
            choices=["leetcode"],  # Extensible for future platforms
            help="Filter by platform (e.g., 'leetcode')",
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
            "--sort-by",
            "-s",
            type=str,
            default="id",
            choices=["id", "title", "difficulty", "acceptance_rate", "platform"],
            help="Field to sort by (default: id)",
        )

        parser.add_argument(
            "--reverse",
            "-r",
            action="store_true",
            default=False,
            help="Sort in descending order (default: ascending)",
        )

        return parser
