"""JSON file formatter for problems."""

import json
from typing import Optional

from crawler.application.interfaces.formatter import OutputFormatter
from crawler.domain.entities import Problem, Submission


class JSONFormatter(OutputFormatter):
    """
    Format problems as JSON files.

    This formatter creates structured JSON documents that:
    - Preserve all problem data
    - Are machine-readable
    - Can be easily parsed by other tools
    - Support round-trip serialization

    The output is designed to be:
    - Valid JSON
    - Pretty-printed for readability
    - Compatible with JSON parsers
    - Suitable for data exchange
    """

    def format_problem(self, problem: Problem, submission: Optional[Submission] = None) -> str:
        """
        Format a problem as a JSON file.

        Args:
            problem: The problem entity to format
            submission: Optional submission entity to include

        Returns:
            str: Formatted JSON content

        Example output:
            {
              "id": "two-sum",
              "platform": "leetcode",
              "title": "Two Sum",
              "difficulty": "Easy",
              "description": "Given an array...",
              "topics": ["Array", "Hash Table"],
              "constraints": [
                {"text": "2 <= nums.length <= 10^4"},
                {"text": "-10^9 <= nums[i] <= 10^9"}
              ],
              "constraints_text": "2 <= nums.length <= 10^4\\n-10^9 <= nums[i] <= 10^9",
              "examples": [
                {
                  "input": "nums = [2,7,11,15], target = 9",
                  "output": "[0,1]",
                  "explanation": "nums[0] + nums[1] == 9"
                }
              ],
              "hints": ["Use a hash map"],
              "acceptance_rate": 49.1,
              "submission": {
                "id": "sub-123",
                "language": "Python",
                "code": "def twoSum(nums, target):\\n    pass",
                "runtime": "52 ms",
                "memory": "15.2 MB"
              }
            }
        """
        data = {
            "id": problem.id,
            "platform": problem.platform,
            "title": problem.title,
            "difficulty": problem.difficulty.level,
            "description": problem.description,
            "topics": problem.topics,
            "constraints": [{"text": constraint.text} for constraint in problem.constraints],
            "constraints_text": problem.constraints_text,  # Backward compatibility
            "examples": [
                {"input": ex.input, "output": ex.output, "explanation": ex.explanation}
                for ex in problem.examples
            ],
            "hints": problem.hints,
            "acceptance_rate": problem.acceptance_rate,
        }

        # Add submission if available
        if submission:
            data["submission"] = {
                "id": submission.id,
                "problem_id": submission.problem_id,
                "language": submission.language,
                "code": submission.code,
                "status": submission.status.value,
                "runtime": submission.runtime,
                "memory": submission.memory,
                "timestamp": submission.timestamp,
            }

            if submission.percentiles:
                data["submission"]["percentiles"] = {
                    "runtime": submission.percentiles.runtime,
                    "memory": submission.percentiles.memory,
                }

        # Pretty-print JSON with 2-space indentation
        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_file_extension(self) -> str:
        """
        Get the file extension for JSON files.

        Returns:
            str: "json"
        """
        return "json"
