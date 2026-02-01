"""
Base Command interface for implementing the command pattern in the CLI.

This module defines the abstract Command class and CommandResult dataclass
that all CLI commands must implement. The Command pattern encapsulates
CLI operations as objects, making them easier to test, extend, and compose.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CommandResult:
    """
    Encapsulates the result of a command execution.

    Attributes:
        success: Whether the command executed successfully
        message: Human-readable message describing the result
        data: Optional data returned by the command
        error: Optional error information if the command failed
    """

    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[Exception] = None

    def __post_init__(self):
        """Validate CommandResult invariants."""
        if self.success and self.error is not None:
            raise ValueError("Successful result cannot have an error")
        if not self.success and self.error is None:
            raise ValueError("Failed result must have an error")


class Command(ABC):
    """
    Abstract base class for all CLI commands.

    The Command pattern allows us to encapsulate CLI operations as objects,
    providing benefits such as:
    - Easier testing through dependency injection
    - Consistent error handling across commands
    - Ability to queue, log, or undo commands
    - Clear separation between command parsing and execution

    Subclasses must implement the execute() method to define the command's
    behavior.
    """

    @abstractmethod
    def execute(self) -> CommandResult:
        """
        Execute the command and return the result.

        This method should contain the main logic of the command. It should
        handle all errors gracefully and return a CommandResult indicating
        success or failure.

        Returns:
            CommandResult: The result of the command execution

        Raises:
            Should not raise exceptions - all errors should be caught and
            returned in the CommandResult
        """
        pass
