"""Domain exceptions for the crawler.

This module defines the exception hierarchy for all crawler errors,
providing clear error messages and context for different failure scenarios.
"""

from typing import Any, Optional


class CrawlerException(Exception):
    """Base exception for all crawler errors."""

    pass


class NetworkException(CrawlerException):
    """Raised when network operations fail.

    Attributes:
        url: The URL that failed (if applicable)
        status_code: HTTP status code (if applicable)
    """

    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        """Initialize network exception.

        Args:
            message: Error message describing the failure
            url: The URL that failed (optional)
            status_code: HTTP status code (optional)
        """
        self.url = url
        self.status_code = status_code
        super().__init__(message)


class ProblemNotFoundException(CrawlerException):
    """Raised when a problem cannot be found.

    Attributes:
        problem_id: The problem identifier that was not found
        platform: The platform where the problem was searched
    """

    def __init__(self, problem_id: str, platform: str):
        """Initialize problem not found exception.

        Args:
            problem_id: The problem identifier
            platform: The platform name
        """
        self.problem_id = problem_id
        self.platform = platform
        super().__init__(f"Problem '{problem_id}' not found on {platform}")


class AuthenticationException(CrawlerException):
    """Raised when authentication fails.

    Attributes:
        platform: The platform where authentication failed
        reason: The reason for authentication failure
    """

    def __init__(self, platform: str, reason: str):
        """Initialize authentication exception.

        Args:
            platform: The platform name
            reason: The reason for failure
        """
        self.platform = platform
        self.reason = reason
        super().__init__(f"Authentication failed for {platform}: {reason}")


class UnsupportedPlatformException(CrawlerException):
    """Raised when an unsupported platform is requested.

    Attributes:
        platform: The unsupported platform name
    """

    def __init__(self, platform: str):
        """Initialize unsupported platform exception.

        Args:
            platform: The platform name
        """
        self.platform = platform
        super().__init__(f"Platform '{platform}' is not supported")


class ValidationException(CrawlerException):
    """Raised when data validation fails.

    Attributes:
        field: The field that failed validation
        value: The invalid value
        reason: The reason for validation failure
    """

    def __init__(self, field: str, value: Any, reason: str):
        """Initialize validation exception.

        Args:
            field: The field name
            value: The invalid value
            reason: The reason for failure
        """
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for {field}='{value}': {reason}")


class RepositoryException(CrawlerException):
    """Raised when repository operations fail."""

    pass


# CLI-specific exceptions


class CommandException(CrawlerException):
    """Base exception for CLI command errors."""

    pass


class CommandValidationException(CommandException):
    """Raised when command argument validation fails.

    Attributes:
        command: The command name
        argument: The argument that failed validation
        reason: The reason for validation failure
    """

    def __init__(self, command: str, argument: str, reason: str):
        """Initialize command validation exception.

        Args:
            command: The command name (e.g., "download", "batch", "list")
            argument: The argument that failed validation
            reason: The reason for failure
        """
        self.command = command
        self.argument = argument
        self.reason = reason
        super().__init__(f"Invalid argument '{argument}' for command '{command}': {reason}")


class ConfigurationException(CrawlerException):
    """Raised when configuration loading or validation fails.

    Attributes:
        config_source: The configuration source (e.g., "file", "env", "cli")
        reason: The reason for configuration failure
    """

    def __init__(self, config_source: str, reason: str):
        """Initialize configuration exception.

        Args:
            config_source: The configuration source
            reason: The reason for failure
        """
        self.config_source = config_source
        self.reason = reason
        super().__init__(f"Configuration error from {config_source}: {reason}")


class CommandExecutionException(CommandException):
    """Raised when command execution fails unexpectedly.

    Attributes:
        command: The command name
        reason: The reason for execution failure
        original_exception: The original exception that caused the failure
    """

    def __init__(self, command: str, reason: str, original_exception: Optional[Exception] = None):
        """Initialize command execution exception.

        Args:
            command: The command name
            reason: The reason for failure
            original_exception: The original exception (optional)
        """
        self.command = command
        self.reason = reason
        self.original_exception = original_exception
        super().__init__(f"Command '{command}' execution failed: {reason}")
