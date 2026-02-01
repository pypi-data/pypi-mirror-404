"""
CLI commands package.

This package contains all CLI command implementations following the Command pattern.
"""

from .base import Command, CommandResult
from .batch import BatchDownloadCommand
from .download import DownloadCommand

__all__ = ["Command", "CommandResult", "BatchDownloadCommand", "DownloadCommand"]
