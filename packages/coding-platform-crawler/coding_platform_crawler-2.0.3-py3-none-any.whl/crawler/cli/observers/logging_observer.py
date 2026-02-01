"""Logging observer for recording download progress to logs."""

import logging
from typing import Optional

from crawler.application.interfaces.observer import DownloadObserver, DownloadStats
from crawler.domain.entities import Problem


class LoggingObserver(DownloadObserver):
    """
    Logging-based observer that records download progress to application logs.

    This observer provides persistent logging of download operations by recording:
    - Start of batch downloads with total count
    - Progress updates for each downloaded problem
    - Skip events with reasons
    - Error events with exception details
    - Completion statistics

    The observer follows the logging level guidelines from Requirements 1.4:
    - INFO: Normal progress updates, start/complete events
    - WARNING: Skip events (informational but noteworthy)
    - ERROR: Download failures and exceptions
    - DEBUG: Detailed diagnostic information

    Unlike ConsoleProgressObserver which provides real-time visual feedback,
    LoggingObserver creates a permanent record suitable for:
    - Auditing download operations
    - Debugging issues after the fact
    - Monitoring automated batch downloads
    - Integration with log aggregation systems

    Example:
        >>> import logging
        >>> logger = logging.getLogger("crawler.batch")
        >>> observer = LoggingObserver(logger)
        >>> observer.on_start(150)
        # Logs: [INFO] Starting batch download of 150 problems

        >>> problem = Problem(id="two-sum", title="Two Sum", ...)
        >>> observer.on_progress(1, 150, problem)
        # Logs: [INFO] Downloaded problem 1/150: Two Sum (two-sum)

        >>> observer.on_skip(problem, "Already exists")
        # Logs: [WARNING] Skipped problem: Two Sum (two-sum) - Already exists

        >>> observer.on_error(problem, Exception("Network timeout"))
        # Logs: [ERROR] Failed to download problem: Two Sum (two-sum) - Network timeout

        >>> stats = DownloadStats(total=150, downloaded=145, skipped=3, failed=2, duration=120.5)
        >>> observer.on_complete(stats)
        # Logs: [INFO] Batch download complete: 145/150 downloaded, 3 skipped, 2 failed (120.5s)

    Attributes:
        logger: Logger instance for recording events
        _start_time: Timestamp when the download started (for duration calculation)
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the logging observer.

        Args:
            logger: Logger instance to use for recording events.
                   If None, creates a logger named "crawler.observer"
        """
        self.logger = logger or logging.getLogger("crawler.observer")
        self._start_time: Optional[float] = None

    def on_start(self, total: int) -> None:
        """
        Called when a download batch starts.

        Logs an INFO message indicating the start of the batch download
        and the total number of problems to download.

        Args:
            total: Total number of problems to download
        """
        import time

        self._start_time = time.time()

        self.logger.info(
            f"Starting batch download of {total} problems",
            extra={"extra_fields": {"total_problems": total, "event": "batch_start"}},
        )

    def on_progress(self, current: int, total: int, problem: Problem) -> None:
        """
        Called when a problem is successfully downloaded.

        Logs an INFO message with the current progress, problem title, and ID.

        Args:
            current: Current progress (number of problems processed so far)
            total: Total number of problems to download
            problem: The problem that was just downloaded
        """
        percentage = (current / total * 100) if total > 0 else 0

        self.logger.info(
            f"Downloaded problem {current}/{total}: {problem.title} ({problem.id})",
            extra={
                "extra_fields": {
                    "event": "problem_downloaded",
                    "problem_id": problem.id,
                    "problem_title": problem.title,
                    "platform": problem.platform,
                    "difficulty": problem.difficulty.level,
                    "current": current,
                    "total": total,
                    "percentage": round(percentage, 1),
                }
            },
        )

    def on_skip(self, problem: Problem, reason: str) -> None:
        """
        Called when a problem is skipped.

        Logs a WARNING message indicating which problem was skipped and why.
        Skip events are logged at WARNING level because they represent
        deviations from the normal download flow that may warrant attention.

        Args:
            problem: The problem that was skipped
            reason: Human-readable reason for skipping
        """
        self.logger.warning(
            f"Skipped problem: {problem.title} ({problem.id}) - {reason}",
            extra={
                "extra_fields": {
                    "event": "problem_skipped",
                    "problem_id": problem.id,
                    "problem_title": problem.title,
                    "platform": problem.platform,
                    "skip_reason": reason,
                }
            },
        )

    def on_error(self, problem: Problem, error: Exception) -> None:
        """
        Called when an error occurs while downloading a problem.

        Logs an ERROR message with the problem details and exception information.
        The exception traceback is automatically included by the logging framework.

        Args:
            problem: The problem that failed to download
            error: The exception that was raised
        """
        self.logger.error(
            f"Failed to download problem: {problem.title} ({problem.id}) - {str(error)}",
            extra={
                "extra_fields": {
                    "event": "problem_failed",
                    "problem_id": problem.id,
                    "problem_title": problem.title,
                    "platform": problem.platform,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            },
            exc_info=True,  # Include exception traceback
        )

    def on_complete(self, stats: DownloadStats) -> None:
        """
        Called when a download batch completes.

        Logs an INFO message with comprehensive statistics about the operation:
        - Total number of problems
        - Number downloaded successfully
        - Number skipped
        - Number failed
        - Total duration
        - Success rate

        Args:
            stats: Statistics about the completed operation
        """
        # Calculate success rate
        success_rate = (stats.downloaded / stats.total * 100) if stats.total > 0 else 0

        # Format duration
        duration_str = self._format_duration(stats.duration)

        self.logger.info(
            f"Batch download complete: {stats.downloaded}/{stats.total} downloaded, "
            f"{stats.skipped} skipped, {stats.failed} failed ({duration_str})",
            extra={
                "extra_fields": {
                    "event": "batch_complete",
                    "total": stats.total,
                    "downloaded": stats.downloaded,
                    "skipped": stats.skipped,
                    "failed": stats.failed,
                    "duration_seconds": stats.duration,
                    "success_rate": round(success_rate, 1),
                }
            },
        )

        # Log additional details at DEBUG level
        self.logger.debug(
            f"Batch download details: success_rate={success_rate:.1f}%, "
            f"duration={stats.duration:.2f}s",
            extra={
                "extra_fields": {
                    "event": "batch_details",
                    "success_rate": round(success_rate, 1),
                    "duration_seconds": stats.duration,
                }
            },
        )

    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to a human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "2m 30.5s", "45.2s", "1h 5m 30s")

        Examples:
            >>> observer = LoggingObserver()
            >>> observer._format_duration(45.2)
            '45.2s'
            >>> observer._format_duration(150.5)
            '2m 30.5s'
            >>> observer._format_duration(3665.0)
            '1h 1m 5.0s'
        """
        if seconds < 60:
            return f"{seconds:.1f}s"

        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60

        if minutes < 60:
            return f"{minutes}m {remaining_seconds:.1f}s"

        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"
