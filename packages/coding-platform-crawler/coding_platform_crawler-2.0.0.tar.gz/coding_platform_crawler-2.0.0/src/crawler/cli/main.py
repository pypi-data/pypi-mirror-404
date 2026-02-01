"""
Main CLI entry point for the coding platform crawler.

This module provides the main entry point for the CLI application. It handles:
- Argument parsing with subcommands (download, batch, list)
- Configuration loading from multiple sources (CLI, ENV, config file, defaults)
- Dependency injection for all components
- Logging configuration
- Command execution with error handling

The CLI follows the Command pattern where each subcommand is implemented as
a separate Command class. This module orchestrates the creation and execution
of these commands.

Example usage:
    # Download a single problem
    python -m crawler.cli.main download two-sum --platform leetcode

    # Batch download all solved problems
    python -m crawler.cli.main batch john_doe --platform leetcode --mode skip

    # List downloaded problems
    python -m crawler.cli.main list --platform leetcode --difficulty Easy Medium
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from crawler.cli.commands.batch import BatchDownloadCommand
from crawler.cli.commands.download import DownloadCommand
from crawler.cli.commands.list import ListCommand
from crawler.cli.observers.console_progress import ConsoleProgressObserver
from crawler.cli.observers.logging_observer import LoggingObserver
from crawler.config.logging_config import get_logger, setup_logging
from crawler.config.settings import Config
from crawler.domain.entities import UpdateMode
from crawler.infrastructure.formatters.json_formatter import JSONFormatter
from crawler.infrastructure.formatters.markdown_formatter import MarkdownFormatter
from crawler.infrastructure.formatters.python_formatter import PythonFormatter
from crawler.infrastructure.http.client import HTTPClient
from crawler.infrastructure.http.rate_limiter import RateLimiter
from crawler.infrastructure.http.retry_config import RetryConfig
from crawler.infrastructure.platforms.factory import PlatformClientFactory
from crawler.infrastructure.repositories.filesystem import FileSystemRepository


def create_main_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser with subcommands.

    This function creates the top-level argument parser and adds subparsers
    for each command (download, batch, list). It also adds global options
    that apply to all commands.

    Returns:
        Configured ArgumentParser with all subcommands

    Example:
        >>> parser = create_main_parser()
        >>> args = parser.parse_args(["download", "two-sum", "--platform", "leetcode"])
        >>> print(args.command)
        "download"
    """
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="Coding platform crawler - Download and manage coding problems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a single problem
  crawler download two-sum --platform leetcode

  # Batch download all solved problems
  crawler batch john_doe --platform leetcode --mode skip

  # List downloaded problems
  crawler list --platform leetcode --difficulty Easy Medium

  # Use custom config file
  crawler --config config.yaml download two-sum --platform leetcode

  # Enable verbose logging
  crawler --verbose batch john_doe --platform leetcode --mode update

For more information on each command, use:
  crawler <command> --help
        """,
    )

    # Global options (apply to all commands)
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to configuration file (YAML or JSON)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose output (DEBUG log level)",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        help="Path to log file (optional)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Base directory for downloaded problems (default: ./problems)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        required=True,
        help="Command to execute",
    )

    # Add download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download a single problem",
        parents=[DownloadCommand.create_argument_parser()],
        add_help=False,
    )

    # Add batch command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Batch download all solved problems",
        parents=[BatchDownloadCommand.create_argument_parser()],
        add_help=False,
    )

    # Add list command
    list_parser = subparsers.add_parser(
        "list",
        help="List downloaded problems",
        parents=[ListCommand.create_argument_parser()],
        add_help=False,
    )

    return parser


def load_configuration(args: argparse.Namespace) -> Config:
    """
    Load configuration from all sources with proper precedence.

    Configuration precedence (highest to lowest):
    1. CLI arguments
    2. Environment variables
    3. Config file
    4. Defaults

    Args:
        args: Parsed command-line arguments

    Returns:
        Config instance with values from all sources

    Example:
        >>> args = parser.parse_args(["--config", "config.yaml", "download", "two-sum"])
        >>> config = load_configuration(args)
        >>> print(config.output_dir)
        "./problems"
    """
    # Extract CLI arguments that override config
    cli_args = {}

    if args.output_dir:
        cli_args["output_dir"] = str(args.output_dir)

    if hasattr(args, "format"):
        cli_args["default_format"] = args.format

    # Load config with proper precedence
    config = Config.load(
        config_file=args.config if args.config else None,
        cli_args=cli_args if cli_args else None,
    )

    return config


def setup_logging_from_args(args: argparse.Namespace, config: Config):
    """
    Set up logging based on command-line arguments and configuration.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance

    Example:
        >>> args = parser.parse_args(["--verbose", "download", "two-sum"])
        >>> config = Config()
        >>> setup_logging_from_args(args, config)
    """
    # Determine log level
    if args.verbose:
        log_level = "DEBUG"
    else:
        log_level = config.log_level

    # Determine log file
    log_file = (
        args.log_file if args.log_file else (Path(config.log_file) if config.log_file else None)
    )

    # Set up logging
    setup_logging(
        level=log_level,
        log_file=log_file,
        json_format=False,  # Use human-readable format for CLI
        console_output=True,
    )


def create_formatter(format_type: str):
    """
    Create an output formatter based on format type.

    Args:
        format_type: Format identifier (python, markdown, json)

    Returns:
        OutputFormatter instance

    Raises:
        ValueError: If format type is not supported

    Example:
        >>> formatter = create_formatter("python")
        >>> isinstance(formatter, PythonFormatter)
        True
    """
    format_type = format_type.lower()

    if format_type == "python":
        return PythonFormatter()
    elif format_type == "markdown":
        return MarkdownFormatter()
    elif format_type == "json":
        return JSONFormatter()
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def create_http_client(config: Config, logger) -> HTTPClient:
    """
    Create an HTTP client with retry and rate limiting.

    Args:
        config: Configuration instance
        logger: Logger instance

    Returns:
        Configured HTTPClient instance

    Example:
        >>> config = Config()
        >>> logger = get_logger(__name__)
        >>> http_client = create_http_client(config, logger)
    """
    # Create retry configuration
    retry_config = RetryConfig(
        max_retries=config.max_retries,
        initial_delay=config.initial_delay,
        max_delay=config.max_delay,
        exponential_base=config.exponential_base,
        jitter=config.jitter,
    )

    # Create rate limiter
    rate_limiter = RateLimiter(config.requests_per_second)

    # Create HTTP client
    http_client = HTTPClient(
        retry_config=retry_config,
        rate_limiter=rate_limiter,
        logger=logger,
    )

    return http_client


def execute_download_command(args: argparse.Namespace, config: Config, logger) -> int:
    """
    Execute the download command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance
        logger: Logger instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Create dependencies
        http_client = create_http_client(config, logger)
        client_factory = PlatformClientFactory(http_client, config, logger)
        platform_client = client_factory.create(args.platform)

        formatter = create_formatter(args.format)

        output_dir = Path(config.output_dir)
        repository = FileSystemRepository(
            base_path=output_dir,
            formatter=formatter,
            logger=logger,
        )

        # Create and execute command
        command = DownloadCommand(
            problem_id=args.problem_id,
            platform=args.platform,
            force=args.force,
            output_format=args.format,
            client=platform_client,
            repository=repository,
            formatter=formatter,
            logger=logger,
        )

        result = command.execute()

        # Print result message
        print(result.message)

        return 0 if result.success else 1

    except Exception as e:
        logger.exception(f"Unexpected error in download command: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def execute_batch_command(args: argparse.Namespace, config: Config, logger) -> int:
    """
    Execute the batch download command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance
        logger: Logger instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Create dependencies
        http_client = create_http_client(config, logger)
        client_factory = PlatformClientFactory(http_client, config, logger)
        platform_client = client_factory.create(args.platform)

        formatter = create_formatter(args.format)

        output_dir = Path(config.output_dir)
        repository = FileSystemRepository(
            base_path=output_dir,
            formatter=formatter,
            logger=logger,
        )

        # Create observers
        observers = [
            ConsoleProgressObserver(verbose=args.verbose if hasattr(args, "verbose") else False),
            LoggingObserver(logger),
        ]

        # Parse update mode
        update_mode = UpdateMode[args.mode.upper()]

        # Create and execute command
        command = BatchDownloadCommand(
            username=args.username,
            platform=args.platform,
            update_mode=update_mode,
            difficulty_filter=args.difficulty if hasattr(args, "difficulty") else None,
            topic_filter=args.topics if hasattr(args, "topics") else None,
            include_community=(
                args.include_community if hasattr(args, "include_community") else False
            ),
            output_format=args.format,
            limit=args.limit if hasattr(args, "limit") else None,
            client=platform_client,
            repository=repository,
            formatter=formatter,
            observers=observers,
            logger=logger,
        )

        result = command.execute()

        # Print result message (observers already printed progress)
        if not result.success:
            print(f"\n{result.message}", file=sys.stderr)

        return 0 if result.success else 1

    except Exception as e:
        logger.exception(f"Unexpected error in batch command: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def execute_list_command(args: argparse.Namespace, config: Config, logger) -> int:
    """
    Execute the list command.

    Args:
        args: Parsed command-line arguments
        config: Configuration instance
        logger: Logger instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Create dependencies
        formatter = create_formatter(config.default_format)

        output_dir = Path(config.output_dir)
        repository = FileSystemRepository(
            base_path=output_dir,
            formatter=formatter,
            logger=logger,
        )

        # Create and execute command
        command = ListCommand(
            platform=args.platform if hasattr(args, "platform") else None,
            difficulty_filter=args.difficulty if hasattr(args, "difficulty") else None,
            topic_filter=args.topics if hasattr(args, "topics") else None,
            sort_by=args.sort_by if hasattr(args, "sort_by") else "id",
            reverse=args.reverse if hasattr(args, "reverse") else False,
            repository=repository,
            logger=logger,
        )

        result = command.execute()

        # Print result message
        print(result.message)

        # Print problem list if successful
        if result.success and result.data:
            print()
            print("Problems:")
            print("-" * 80)
            for problem in result.data:
                print(
                    f"{problem.id:30} | {problem.title:40} | "
                    f"{problem.difficulty.level:8} | {problem.acceptance_rate:5.1f}%"
                )

        return 0 if result.success else 1

    except Exception as e:
        logger.exception(f"Unexpected error in list command: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI application.

    This function:
    1. Parses command-line arguments
    2. Loads configuration from all sources
    3. Sets up logging
    4. Creates and executes the appropriate command
    5. Returns an exit code

    Args:
        argv: Optional list of command-line arguments (for testing)
              If None, uses sys.argv[1:]

    Returns:
        Exit code (0 for success, non-zero for failure)

    Example:
        >>> exit_code = main(["download", "two-sum", "--platform", "leetcode"])
        >>> print(exit_code)
        0
    """
    # Parse arguments
    parser = create_main_parser()
    args = parser.parse_args(argv)

    # Load configuration
    config = load_configuration(args)

    # Set up logging
    setup_logging_from_args(args, config)
    logger = get_logger(__name__)

    logger.info(f"Starting crawler CLI with command: {args.command}")
    logger.debug(f"Configuration: {config.to_dict()}")

    # Execute appropriate command
    try:
        if args.command == "download":
            return execute_download_command(args, config, logger)
        elif args.command == "batch":
            return execute_batch_command(args, config, logger)
        elif args.command == "list":
            return execute_list_command(args, config, logger)
        else:
            logger.error(f"Unknown command: {args.command}")
            print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
