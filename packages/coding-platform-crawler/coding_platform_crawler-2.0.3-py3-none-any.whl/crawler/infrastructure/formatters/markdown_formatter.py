"""Markdown file formatter for problems."""

from typing import Optional

from crawler.application.interfaces.formatter import OutputFormatter
from crawler.domain.entities import Problem, Submission


class MarkdownFormatter(OutputFormatter):
    """
    Format problems as Markdown files.

    This formatter creates well-structured Markdown documents with:
    - Proper heading hierarchy
    - Code blocks for examples and solutions
    - Tables for metadata
    - Clear section separation

    The output is designed to be:
    - Readable in any Markdown viewer
    - Compatible with GitHub/GitLab rendering
    - Easy to navigate with table of contents
    """

    def format_problem(self, problem: Problem, submission: Optional[Submission] = None) -> str:
        """
        Format a problem as a Markdown file.

        Args:
            problem: The problem entity to format
            submission: Optional submission entity to include

        Returns:
            str: Formatted Markdown content

        Example output:
            # Two Sum

            **Difficulty:** Easy
            **Platform:** leetcode
            **Topics:** Array, Hash Table
            **Acceptance Rate:** 49.1%

            ## Description

            Given an array of integers nums and an integer target...

            ## Examples

            ### Example 1

            **Input:** `nums = [2,7,11,15], target = 9`
            **Output:** `[0,1]`
            **Explanation:** nums[0] + nums[1] == 9

            ## Solution

            **Language:** Python
            **Runtime:** 52 ms
            **Memory:** 15.2 MB

            ```python
            def twoSum(nums, target):
                pass
            ```
        """
        lines = []

        # Add title
        lines.append(f"# {problem.title}")
        lines.append("")

        # Add metadata
        lines.append(f"**Difficulty:** {problem.difficulty.level}")
        lines.append(f"**Platform:** {problem.platform}")

        if problem.topics:
            lines.append(f"**Topics:** {', '.join(problem.topics)}")

        lines.append(f"**Acceptance Rate:** {problem.acceptance_rate:.1f}%")
        lines.append("")

        # Add description
        lines.append("## Description")
        lines.append("")
        lines.append(problem.description)
        lines.append("")

        # Add constraints
        if problem.constraints:
            lines.append("## Constraints")
            lines.append("")
            for constraint in problem.constraints:
                lines.append(f"- {constraint.text}")
            lines.append("")

        # Add examples
        if problem.examples:
            lines.append("## Examples")
            lines.append("")

            for i, example in enumerate(problem.examples, 1):
                lines.append(f"### Example {i}")
                lines.append("")
                lines.append(f"**Input:** `{example.input}`")
                lines.append("")
                lines.append(f"**Output:** `{example.output}`")
                lines.append("")

                if example.explanation:
                    lines.append(f"**Explanation:** {example.explanation}")
                    lines.append("")

        # Add hints
        if problem.hints:
            lines.append("## Hints")
            lines.append("")
            for i, hint in enumerate(problem.hints, 1):
                lines.append(f"{i}. {hint}")
            lines.append("")

        # Add submission
        if submission:
            lines.append("## Solution")
            lines.append("")
            lines.append(f"**Language:** {submission.language}")
            lines.append(f"**Runtime:** {submission.runtime}")
            lines.append(f"**Memory:** {submission.memory}")

            if submission.percentiles:
                lines.append(f"**Runtime Percentile:** {submission.percentiles.runtime:.1f}%")
                lines.append(f"**Memory Percentile:** {submission.percentiles.memory:.1f}%")

            lines.append("")

            # Determine language for code block
            lang = submission.language.lower()
            if lang == "c++":
                lang = "cpp"
            elif lang == "c#":
                lang = "csharp"

            lines.append(f"```{lang}")
            lines.append(submission.code)
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def get_file_extension(self) -> str:
        """
        Get the file extension for Markdown files.

        Returns:
            str: "md"
        """
        return "md"
