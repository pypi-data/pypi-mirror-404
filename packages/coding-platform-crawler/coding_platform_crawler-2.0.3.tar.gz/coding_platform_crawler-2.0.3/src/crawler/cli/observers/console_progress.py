"""Console progress observer for displaying real-time download progress."""

import sys
from typing import Optional

from crawler.application.interfaces.observer import DownloadObserver, DownloadStats
from crawler.domain.entities import Problem


class ConsoleProgressObserver(DownloadObserver):
    """
    Console-based progress observer that displays real-time progress during batch downloads.

    This observer provides visual feedback to users by displaying:
    - A progress bar showing overall completion
    - Current problem being downloaded
    - Statistics at completion (total, downloaded, skipped, failed)

    The implementation uses simple text-based progress display that works in any terminal
    without requiring external dependencies like tqdm or rich.

    Example:
        >>> observer = ConsoleProgressObserver()
        >>> observer.on_start(150)
        Starting download of 150 problems...

        >>> problem = Problem(id="two-sum", title="Two Sum", ...)
        >>> observer.on_progress(1, 150, problem)
        [1/150] (0.7%) Downloaded: Two Sum

        >>> observer.on_complete(stats)

        Download complete!
        ================================================================================
        Total: 150 | Downloaded: 145 | Skipped: 3 | Failed: 2
        Duration: 2m 0.5s
        ================================================================================

    Attributes:
        verbose: If True, display detailed messages for skips and errors
        _start_time: Timestamp when the download started (for duration calculation)
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the console progress observer.

        Args:
            verbose: If True, display detailed messages for skips and errors.
                    If False, only show progress and final statistics.
        """
        self.verbose = verbose
        self._start_time: Optional[float] = None

    def on_start(self, total: int) -> None:
        """
        Called when a download batch starts.

        Displays a message indicating the start of the download operation
        and the total number of problems to download.

        Args:
            total: Total number of problems to download
        """
        import time

        self._start_time = time.time()

        print(f"\nStarting download of {total} problems...")
        print("=" * 80)
        sys.stdout.flush()

    def on_progress(self, current: int, total: int, problem: Problem) -> None:
        """
        Called when a problem is successfully downloaded.

        Displays a progress indicator showing:
        - Current position and total (e.g., [1/150])
        - Percentage complete
        - Problem title

        Args:
            current: Current progress (number of problems processed so far)
            total: Total number of problems to download
            problem: The problem that was just downloaded
        """
        percentage = (current / total * 100) if total > 0 else 0

        # Create a simple text-based progress bar
        bar_width = 40
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        # Display progress with problem title
        print(f"\r[{current}/{total}] {bar} {percentage:5.1f}% | {problem.title}", end="")
        sys.stdout.flush()

        # Print newline every 10 items or at the end for better readability
        if current % 10 == 0 or current == total:
            print()  # Move to next line
            sys.stdout.flush()

    def on_skip(self, problem: Problem, reason: str) -> None:
        """
        Called when a problem is skipped.

        If verbose mode is enabled, displays a message indicating which problem
        was skipped and why.

        Args:
            problem: The problem that was skipped
            reason: Human-readable reason for skipping
        """
        if self.verbose:
            print(f"\n  ⊘ Skipped: {problem.title} ({reason})")
            sys.stdout.flush()

    def on_error(self, problem: Problem, error: Exception) -> None:
        """
        Called when an error occurs while downloading a problem.

        Displays an error message with the problem title and error details.
        This is always shown regardless of verbose mode since errors are important.

        Args:
            problem: The problem that failed to download
            error: The exception that was raised
        """
        print(f"\n  ✗ Error downloading {problem.title}: {str(error)}")
        sys.stdout.flush()

    def on_complete(self, stats: DownloadStats) -> None:
        """
        Called when a download batch completes.

        Displays final statistics including:
        - Total number of problems
        - Number downloaded successfully
        - Number skipped
        - Number failed
        - Total duration

        Args:
            stats: Statistics about the completed operation
        """
        print("\n")
        print("=" * 80)
        print("Download complete!")
        print("=" * 80)

        # Display statistics
        print(
            f"Total: {stats.total} | "
            f"Downloaded: {stats.downloaded} | "
            f"Skipped: {stats.skipped} | "
            f"Failed: {stats.failed}"
        )

        # Format duration
        duration_str = self._format_duration(stats.duration)
        print(f"Duration: {duration_str}")

        # Display success rate
        if stats.total > 0:
            success_rate = stats.downloaded / stats.total * 100
            print(f"Success rate: {success_rate:.1f}%")

        print("=" * 80)
        sys.stdout.flush()

    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to a human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "2m 30.5s", "45.2s", "1h 5m 30s")

        Examples:
            >>> observer = ConsoleProgressObserver()
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
