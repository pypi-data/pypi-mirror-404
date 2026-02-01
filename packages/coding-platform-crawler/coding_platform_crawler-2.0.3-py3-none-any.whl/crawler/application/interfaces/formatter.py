"""Output formatter interface for multi-format support."""

from abc import ABC, abstractmethod
from typing import Optional

from crawler.domain.entities import Problem, Submission


class OutputFormatter(ABC):
    """
    Abstract interface for output formatting.

    This interface defines the contract for formatting problems and submissions
    into different output formats, enabling the Strategy pattern for multi-format
    support. Each concrete implementation handles a specific output format.

    Formatters are responsible for:
    - Converting domain entities to formatted text
    - Preserving all essential information
    - Applying format-specific styling and structure
    - Providing the appropriate file extension

    Examples of concrete implementations:
    - PythonFormatter (generates .py files with comments)
    - MarkdownFormatter (generates .md files)
    - JSONFormatter (generates .json files)
    - HTMLFormatter (future - generates .html files)
    """

    @abstractmethod
    def format_problem(self, problem: Problem, submission: Optional[Submission] = None) -> str:
        """
        Format a problem and optional submission into a string.

        Args:
            problem: The problem entity to format
            submission: Optional submission entity to include in the output

        Returns:
            str: The formatted output as a string, ready to be written to a file

        Example:
            >>> formatter = PythonFormatter()
            >>> problem = Problem(id="two-sum", title="Two Sum", ...)
            >>> submission = Submission(code="def twoSum(...):", ...)
            >>> output = formatter.format_problem(problem, submission)
            >>> print(output[:50])
            'Problem: Two Sum, Difficulty: Easy, Platform: leetcode'

        Note:
            The formatted output should include:
            - Problem title and metadata (difficulty, platform, topics)
            - Problem description
            - Constraints
            - Examples with explanations
            - Hints (if available)
            - Submission code (if provided)
            - Submission metadata (runtime, memory, percentiles if available)

            The exact structure and styling depends on the format, but all
            essential information should be preserved.
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Get the file extension for this formatter.

        Returns:
            str: The file extension without the leading dot (e.g., "py", "md", "json")

        Example:
            >>> formatter = PythonFormatter()
            >>> print(formatter.get_file_extension())
            "py"
            >>>
            >>> formatter = MarkdownFormatter()
            >>> print(formatter.get_file_extension())
            "md"

        Note:
            The extension is used by the repository to determine the output
            filename. For example, a problem with ID "two-sum" formatted with
            PythonFormatter would be saved as "two-sum.py".
        """
        pass
