"""Download observer interface for progress tracking."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from crawler.domain.entities import Problem


@dataclass
class DownloadStats:
    """
    Statistics for a download operation.

    Attributes:
        total: Total number of problems to download
        downloaded: Number of problems successfully downloaded
        skipped: Number of problems skipped (already exist)
        failed: Number of problems that failed to download
        duration: Total duration of the operation in seconds
    """

    total: int
    downloaded: int
    skipped: int
    failed: int
    duration: float


class DownloadObserver(ABC):
    """
    Abstract interface for download progress observation.

    This interface defines the contract for observing download operations,
    enabling the Observer pattern for progress tracking. Concrete implementations
    can display progress in different ways (console, GUI, logs, metrics).

    The observer pattern decouples progress reporting from business logic,
    allowing multiple observers to track the same operation simultaneously.
    For example, you could have both a console progress bar and a logging
    observer active at the same time.

    Examples of concrete implementations:
    - ConsoleProgressObserver (displays progress bar in terminal)
    - LoggingObserver (logs progress to file)
    - MetricsObserver (future - sends metrics to monitoring system)
    - GUIObserver (future - updates GUI progress bar)
    """

    @abstractmethod
    def on_start(self, total: int) -> None:
        """
        Called when a download batch starts.

        Args:
            total: Total number of problems to download

        Example:
            >>> observer = ConsoleProgressObserver()
            >>> observer.on_start(150)
            # Displays: "Starting download of 150 problems..."

        Note:
            This is called once at the beginning of a batch download operation.
            Observers can use this to initialize progress bars, start timers,
            or log the start of the operation.
        """
        pass

    @abstractmethod
    def on_progress(self, current: int, total: int, problem: Problem) -> None:
        """
        Called when a problem is successfully downloaded.

        Args:
            current: Current progress (number of problems processed so far)
            total: Total number of problems to download
            problem: The problem that was just downloaded

        Example:
            >>> observer = ConsoleProgressObserver()
            >>> problem = Problem(id="two-sum", title="Two Sum", ...)
            >>> observer.on_progress(1, 150, problem)
            # Displays: "[1/150] Downloaded: Two Sum"

        Note:
            This is called after each successful download. Observers can use
            this to update progress bars, log progress, or display the current
            problem being processed.
        """
        pass

    @abstractmethod
    def on_skip(self, problem: Problem, reason: str) -> None:
        """
        Called when a problem is skipped.

        Args:
            problem: The problem that was skipped
            reason: Human-readable reason for skipping (e.g., "Already exists",
                   "Filtered by difficulty", "Filtered by topic")

        Example:
            >>> observer = ConsoleProgressObserver()
            >>> problem = Problem(id="two-sum", title="Two Sum", ...)
            >>> observer.on_skip(problem, "Already exists")
            # Displays: "Skipped: Two Sum (Already exists)"

        Note:
            This is called when a problem is intentionally skipped, not when
            an error occurs. Common reasons include:
            - Problem already exists (skip mode)
            - Problem filtered out by difficulty
            - Problem filtered out by topic
        """
        pass

    @abstractmethod
    def on_error(self, problem: Problem, error: Exception) -> None:
        """
        Called when an error occurs while downloading a problem.

        Args:
            problem: The problem that failed to download
            error: The exception that was raised

        Example:
            >>> observer = ConsoleProgressObserver()
            >>> problem = Problem(id="two-sum", title="Two Sum", ...)
            >>> error = NetworkException("Connection timeout")
            >>> observer.on_error(problem, error)
            # Displays: "Error downloading Two Sum: Connection timeout"

        Note:
            This is called when an error occurs during download. The batch
            download operation continues with the next problem after calling
            this method. Observers can use this to log errors, display warnings,
            or track failure statistics.
        """
        pass

    @abstractmethod
    def on_complete(self, stats: DownloadStats) -> None:
        """
        Called when a download batch completes.

        Args:
            stats: Statistics about the completed operation

        Example:
            >>> observer = ConsoleProgressObserver()
            >>> stats = DownloadStats(
            ...     total=150,
            ...     downloaded=145,
            ...     skipped=3,
            ...     failed=2,
            ...     duration=120.5
            ... )
            >>> observer.on_complete(stats)
            # Displays:
            # "Download complete!"
            # "Total: 150 | Downloaded: 145 | Skipped: 3 | Failed: 2"
            # "Duration: 2m 0.5s"

        Note:
            This is called once at the end of a batch download operation,
            regardless of whether all downloads succeeded or some failed.
            Observers can use this to display final statistics, close progress
            bars, or log the completion of the operation.
        """
        pass
