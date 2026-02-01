"""Domain enumerations"""

from enum import Enum


class SubmissionStatus(Enum):
    """Submission status enumeration"""

    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILE_ERROR = "Compile Error"


class UpdateMode(Enum):
    """Update mode for batch downloads"""

    SKIP = "skip"  # Skip existing files
    UPDATE = "update"  # Update if newer submission exists
    FORCE = "force"  # Always overwrite
