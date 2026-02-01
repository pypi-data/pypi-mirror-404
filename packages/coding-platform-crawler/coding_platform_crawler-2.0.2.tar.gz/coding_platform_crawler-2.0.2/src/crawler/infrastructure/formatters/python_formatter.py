"""Python file formatter for problems."""

from typing import Optional

from crawler.application.interfaces.formatter import OutputFormatter
from crawler.domain.entities import Problem, Submission

from .text_utils import wrap_text


class PythonFormatter(OutputFormatter):
    """Format problems as Python files with comments.

    This formatter creates Python files with the problem description,
    constraints, examples, and hints as comments, followed by the
    user's submission code if available.

    The output format is designed to be:
    - Readable as documentation
    - Executable as Python code
    - Compatible with Python syntax highlighting
    """

    def format_problem(self, problem: Problem, submission: Optional[Submission] = None) -> str:
        """Format a problem as a Python file with comments.

        Args:
            problem: The problem entity to format
            submission: Optional submission entity to include

        Returns:
            str: Formatted Python file content
        """
        lines = []

        # Add docstring header with structured format
        lines.append('"""')
        lines.append(f"LeetCode Problem #{problem.id}: {problem.title}")
        lines.append(f"Difficulty: {problem.difficulty.level}")

        if problem.topics:
            lines.append(f"Topics: {', '.join(problem.topics)}")

        lines.append("")

        # Add submission info if available
        if submission:
            lines.append("My Last Accepted Submission:")
            lines.append(f"Language: {submission.language}")
            runtime_pct = (
                f"{submission.percentiles.runtime:.1f}" if submission.percentiles else "None"
            )
            memory_pct = (
                f"{submission.percentiles.memory:.1f}" if submission.percentiles else "None"
            )
            lines.append(f"Runtime: {submission.runtime} (beats {runtime_pct}%)")
            lines.append(f"Memory: {submission.memory} (beats {memory_pct}%)")
            lines.append("")

        # Add main problem description (now clean, without examples/constraints)
        lines.append("Problem Description:")
        wrapped_desc = wrap_text(problem.description, width=75)
        lines.append(wrapped_desc)

        # Add examples (now properly structured from domain entity)
        if problem.examples:
            lines.append("")
            for i, example in enumerate(problem.examples, 1):
                lines.append(f"Example {i}:")
                lines.append(f"Input: {example.input}")
                lines.append(f"Output: {example.output}")
                if example.explanation:
                    lines.append(f"Explanation: {example.explanation}")
                if i < len(problem.examples):  # Add blank line between examples
                    lines.append("")

        # Add constraints (now properly structured from domain entity)
        if problem.constraints:
            lines.append("")
            lines.append("Constraints:")

            # Iterate over structured Constraint objects
            for constraint in problem.constraints:
                # Each constraint is already cleaned and validated
                lines.append(f"• {constraint.text}")

        lines.append('"""')
        lines.append("")

        # Add submission code if available
        if submission:
            lines.append(submission.code)
        else:
            # Add placeholder function
            lines.append("# TODO: Implement solution")
            lines.append("")

        # Add test harness
        lines.append("")
        lines.append('if __name__ == "__main__":')
        lines.append("    # Test cases")
        lines.append("    solution = Solution()")
        lines.append("    # Add your test cases here")
        lines.append("    pass")

        return "\n".join(lines)

    def get_file_extension(self) -> str:
        """Get the file extension for Python files.

        Returns:
            str: "py"
        """
        return "py"
