"""LeetCode adapter for converting API responses to domain models."""

import json
import logging
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from crawler.domain.entities import Problem, Submission
from crawler.domain.entities.enums import SubmissionStatus
from crawler.domain.value_objects import Constraint, Difficulty, Example, Percentiles

# Configure logger for this module
logger = logging.getLogger(__name__)


class LeetCodeAdapter:
    """Adapts LeetCode API responses to domain models.

    This adapter handles the conversion of LeetCode-specific API response
    formats to our domain entities (Problem, Submission). It isolates
    API-specific parsing logic from the rest of the application.

    Key responsibilities:
    - Parse HTML content to plain text
    - Extract and parse example test cases
    - Convert API response structures to domain entities
    - Handle missing or optional fields gracefully

    Example:
        >>> adapter = LeetCodeAdapter()
        >>> problem = adapter.adapt_problem(api_response)
        >>> print(problem.title)
        "Two Sum"
    """

    def adapt_problem(self, raw_data: Dict[str, Any]) -> Problem:
        """Convert LeetCode API response to Problem entity.

        Args:
            raw_data: Raw API response from LeetCode GraphQL API

        Returns:
            Problem entity with all fields populated

        Raises:
            KeyError: If required fields are missing from the response
            ValueError: If data validation fails

        Example:
            >>> response = {"data": {"question": {...}}}
            >>> problem = adapter.adapt_problem(response)
        """
        question = raw_data["data"]["question"]

        # Parse HTML content to plain text
        full_description = self._parse_html(question["content"])

        # Extract structured data from description
        parsed = self._extract_description_parts(full_description)

        # Parse acceptance rate from stats JSON
        acceptance_rate = self._parse_acceptance_rate(question.get("stats", "{}"))

        # Extract topic tags
        topics = [tag["name"] for tag in question.get("topicTags", [])]

        # Get hints (may be empty list)
        hints = question.get("hints", [])

        return Problem(
            id=question["titleSlug"],
            platform="leetcode",
            title=question["title"],
            difficulty=Difficulty(question["difficulty"]),
            description=parsed["description"],
            topics=topics,
            constraints=parsed["constraints"],
            examples=parsed["examples"],
            hints=hints,
            acceptance_rate=acceptance_rate,
        )

    def adapt_submission(self, raw_data: Dict[str, Any], problem_id: str = "unknown") -> Submission:
        """Convert LeetCode submission response to Submission entity.

        Args:
            raw_data: Raw API response from LeetCode submission API
            problem_id: The problem ID this submission belongs to (default: "unknown")

        Returns:
            Submission entity with all fields populated

        Raises:
            KeyError: If required fields are missing from the response
            ValueError: If data validation fails

        Example:
            >>> response = {"data": {"submissionDetails": {...}}}
            >>> submission = adapter.adapt_submission(response, "two-sum")
        """
        details = raw_data["data"]["submissionDetails"]

        # Map LeetCode status to our enum
        status = self._map_submission_status(details["statusDisplay"])

        # Parse percentiles if available
        percentiles = None
        if "runtimePercentile" in details and "memoryPercentile" in details:
            percentiles = Percentiles(
                runtime=float(details["runtimePercentile"]),
                memory=float(details["memoryPercentile"]),
            )

        # Convert timestamp string to integer
        timestamp = int(details["timestamp"])

        return Submission(
            id=details["id"],
            problem_id=problem_id,
            language=details["langName"],
            code=details["code"],
            status=status,
            runtime=details["runtime"],
            memory=details["memory"],
            timestamp=timestamp,
            percentiles=percentiles,
        )

    def _parse_html(self, html: str) -> str:
        """Extract plain text from HTML content.

        Uses BeautifulSoup to parse HTML and extract text content,
        removing all HTML tags while preserving line breaks.

        Args:
            html: HTML string to parse

        Returns:
            Plain text content with HTML tags removed

        Example:
            >>> html = "<p>Hello <code>world</code></p>"
            >>> adapter._parse_html(html)
            "Hello world"
        """
        if not html:
            return ""

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Extract text content
        text = soup.get_text()

        # Clean up whitespace while preserving newlines
        # Replace multiple spaces (but not newlines) with single space
        lines = text.split("\n")
        cleaned_lines = [re.sub(r"[ \t]+", " ", line.strip()) for line in lines]
        text = "\n".join(line for line in cleaned_lines if line)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def _extract_description_parts(self, full_text: str) -> Dict[str, Any]:
        """Extract description, examples, and constraints from full text.

        LeetCode descriptions contain everything in one text block:
        - Main problem description
        - Examples (Example 1:, Example 2:, etc.)
        - Constraints (Constraints:)
        - Follow-up questions

        This method intelligently splits them into separate components.

        Args:
            full_text: Complete problem description text

        Returns:
            Dictionary with 'description', 'examples' (List[Example]), and 'constraints' (List[Constraint])

        Example:
            >>> text = "Given an array... Example 1: Input: [1,2] Output: [2,1] Constraints: 1 <= n <= 100"
            >>> result = adapter._extract_description_parts(text)
            >>> result['description']
            "Given an array..."
            >>> len(result['examples'])
            1
            >>> len(result['constraints'])
            1
        """
        # Find where examples start
        example_match = re.search(r"\bExample\s+1:", full_text)
        constraints_match = re.search(r"\bConstraints?:", full_text, re.IGNORECASE)

        # Extract main description (before examples)
        if example_match:
            description = full_text[: example_match.start()].strip()
        elif constraints_match:
            description = full_text[: constraints_match.start()].strip()
        else:
            description = full_text.strip()

        # Extract examples with error handling
        examples = []
        if example_match:
            try:
                # Determine where examples section ends
                if constraints_match:
                    examples_text = full_text[example_match.start() : constraints_match.start()]
                else:
                    examples_text = full_text[example_match.start() :]

                examples = self._parse_examples_from_text(examples_text)
                logger.info(f"Successfully parsed {len(examples)} examples")
            except Exception as e:
                # Log warning and continue with empty list (Requirement 4.5)
                logger.warning(f"Failed to parse examples: {e}", exc_info=True)
                examples = []

        # Extract constraints with error handling
        constraints = []
        if constraints_match:
            try:
                constraints_text = full_text[constraints_match.start() :]

                # Remove "Constraints:" prefix
                constraints_text = re.sub(
                    r"^Constraints?:\s*", "", constraints_text, flags=re.IGNORECASE
                )

                # Remove "Follow-up:" and everything after it
                follow_up_match = re.search(r"\bFollow-?up:", constraints_text, re.IGNORECASE)
                if follow_up_match:
                    constraints_text = constraints_text[: follow_up_match.start()]

                constraints_text = constraints_text.strip()

                # Parse constraints into structured list
                constraints = self._parse_constraints_from_text(constraints_text)
                logger.info(f"Successfully parsed {len(constraints)} constraints")
            except Exception as e:
                # Log warning and continue with empty list (Requirement 4.6)
                logger.warning(f"Failed to parse constraints: {e}", exc_info=True)
                constraints = []

        return {"description": description, "examples": examples, "constraints": constraints}

    def _parse_examples_from_text(self, examples_text: str) -> List[Example]:
        """Parse examples from the examples section of description.

        Examples in LeetCode follow this pattern:
        Example 1:
        Input: nums = [2,7,11,15], target = 9
        Output: [0,1]
        Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

        Enhanced to handle edge cases:
        - Examples without "Example N:" prefix (just "Example:")
        - Multi-line input/output (preserves newlines)
        - Malformed examples (skips instead of crashing)
        - Logs warnings for skipped examples

        Args:
            examples_text: Text containing all examples

        Returns:
            List of Example value objects

        Example:
            >>> text = "Example 1: Input: [1,2] Output: [2,1] Explanation: Reversed"
            >>> examples = adapter._parse_examples_from_text(text)
            >>> examples[0].input
            "[1,2]"
        """
        # Handle None and empty strings
        if not examples_text:
            return []

        try:
            examples = []

            # Split by "Example N:" or "Example:" pattern (handles both numbered and unnumbered)
            # Use lookahead to keep the delimiter for better error messages
            example_blocks = re.split(r"(?=\bExample(?:\s+\d+)?:)", examples_text)

            for block_idx, block in enumerate(example_blocks):
                if not block.strip():
                    continue

                # Remove the "Example N:" or "Example:" prefix for cleaner processing
                block_content = re.sub(r"^\bExample(?:\s+\d+)?:\s*", "", block, flags=re.IGNORECASE)

                if not block_content.strip():
                    continue

                try:
                    # Extract Input, Output, and Explanation
                    # Use DOTALL to handle multi-line content
                    # Use non-greedy matching to stop at the next field
                    input_match = re.search(
                        r"Input:\s*(.+?)(?=\s*(?:Output:|Explanation:|Example(?:\s+\d+)?:|$))",
                        block_content,
                        re.DOTALL | re.IGNORECASE,
                    )
                    output_match = re.search(
                        r"Output:\s*(.+?)(?=\s*(?:Explanation:|Example(?:\s+\d+)?:|$))",
                        block_content,
                        re.DOTALL | re.IGNORECASE,
                    )
                    explanation_match = re.search(
                        r"Explanation:\s*(.+?)(?=\s*(?:Example(?:\s+\d+)?:|$))",
                        block_content,
                        re.DOTALL | re.IGNORECASE,
                    )

                    # Validate that we have both Input and Output
                    if not input_match or not output_match:
                        # Log warning for malformed example (Requirement 4.5)
                        missing_fields = []
                        if not input_match:
                            missing_fields.append("Input")
                        if not output_match:
                            missing_fields.append("Output")

                        logger.warning(
                            f"Skipping malformed example (missing {', '.join(missing_fields)}): "
                            f"{block_content[:100]}..."
                        )
                        continue

                    # Extract and clean the text, preserving internal newlines
                    input_text = input_match.group(1).strip()
                    output_text = output_match.group(1).strip()
                    explanation_text = (
                        explanation_match.group(1).strip() if explanation_match else None
                    )

                    # Create Example object with validation
                    examples.append(
                        Example(input=input_text, output=output_text, explanation=explanation_text)
                    )

                except (ValueError, AttributeError) as e:
                    # Skip this example if validation fails or regex fails (Requirement 4.5)
                    logger.warning(
                        f"Skipping example due to validation error: {e}. "
                        f"Block content: {block_content[:100]}..."
                    )
                    continue

            return examples

        except Exception as e:
            # Catch-all for unexpected errors - return empty list for robustness (Requirement 4.5)
            logger.error(f"Unexpected error parsing examples: {e}", exc_info=True)
            return []

    def _parse_constraints_from_text(self, constraints_text: str) -> List[Constraint]:
        """Parse constraints from the constraints section.

        Handles multiple constraint formats:
        - Newline-separated constraints (most common)
        - Bullet-pointed lists (•, -, *)
        - Numbered lists (1., 2., etc.)

        Edge cases handled:
        - Empty constraints (returns empty list)
        - Multi-line constraints (preserves complete text)
        - Trailing periods (normalized)
        - Bullet point markers (removed)

        Args:
            constraints_text: Text containing all constraints

        Returns:
            List of Constraint value objects

        Example:
            >>> text = "1 <= n <= 100\\n-10^4 <= nums[i] <= 10^4"
            >>> constraints = adapter._parse_constraints_from_text(text)
            >>> len(constraints)
            2
        """
        if not constraints_text or not constraints_text.strip():
            return []

        try:
            constraints = []

            # Strategy 1: Split by newlines (most common format)
            lines = constraints_text.split("\n")
            for line in lines:
                cleaned = self._clean_constraint_text(line)
                if cleaned:
                    try:
                        constraints.append(Constraint(text=cleaned))
                    except ValueError:
                        continue

            # If we got constraints, return them
            if constraints:
                return constraints

            # Strategy 2: Try splitting by bullet points (for inline bullets)
            if "•" in constraints_text:
                parts = constraints_text.split("•")
                for part in parts:
                    cleaned = self._clean_constraint_text(part)
                    if cleaned:
                        try:
                            constraints.append(Constraint(text=cleaned))
                        except ValueError:
                            continue
                if constraints:
                    return constraints

            # Strategy 3: Fallback - treat entire text as single constraint
            cleaned = self._clean_constraint_text(constraints_text)
            if cleaned:
                try:
                    constraints.append(Constraint(text=cleaned))
                except ValueError:
                    pass

            return constraints

        except Exception as e:
            # Log error and return empty list for robustness (Requirement 4.6)
            logger.error(f"Unexpected error parsing constraints: {e}", exc_info=True)
            return []

    def _clean_constraint_text(self, text: str) -> str:
        """Clean constraint text by removing formatting artifacts.

        Removes:
        - Leading/trailing whitespace
        - Bullet point markers (•, -, *) at the start
        - Numbered list markers (1., 2., etc.) at the start
        - Trailing periods (normalized)

        Preserves:
        - Internal whitespace and newlines
        - Special characters in constraint expressions
        - Numeric ranges

        Args:
            text: Raw constraint text

        Returns:
            Cleaned constraint text, or empty string if invalid

        Example:
            >>> adapter._clean_constraint_text("• 1 <= n <= 100.")
            "1 <= n <= 100"
        """
        if not text:
            return ""

        # Strip leading/trailing whitespace
        cleaned = text.strip()

        # Remove bullet point markers at the start
        cleaned = re.sub(r"^[•\-\*]\s+", "", cleaned)

        # Remove numbered list markers at the start (e.g., "1. ", "2. ")
        cleaned = re.sub(r"^\d+\.\s+", "", cleaned)

        # Remove trailing period if present
        # Only remove if it's the very last character after stripping
        if cleaned.endswith("."):
            cleaned = cleaned[:-1].strip()

        return cleaned

    def _parse_acceptance_rate(self, stats_json: str) -> float:
        """Parse acceptance rate from stats JSON string.

        Args:
            stats_json: JSON string containing problem statistics

        Returns:
            Acceptance rate as a float (0-100)

        Example:
            >>> stats = '{"acRate": "49.1%"}'
            >>> adapter._parse_acceptance_rate(stats)
            49.1
        """
        if not stats_json:
            return 0.0

        try:
            stats = json.loads(stats_json)
            ac_rate_str = stats.get("acRate", "0%")

            # Remove '%' and convert to float
            ac_rate = float(ac_rate_str.rstrip("%"))

            return ac_rate
        except (json.JSONDecodeError, ValueError, KeyError):
            return 0.0

    def _map_submission_status(self, status_display: str) -> SubmissionStatus:
        """Map LeetCode status string to SubmissionStatus enum.

        Args:
            status_display: Status string from LeetCode API

        Returns:
            Corresponding SubmissionStatus enum value

        Example:
            >>> adapter._map_submission_status("Accepted")
            SubmissionStatus.ACCEPTED
        """
        status_map = {
            "Accepted": SubmissionStatus.ACCEPTED,
            "Wrong Answer": SubmissionStatus.WRONG_ANSWER,
            "Time Limit Exceeded": SubmissionStatus.TIME_LIMIT_EXCEEDED,
            "Memory Limit Exceeded": SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
            "Runtime Error": SubmissionStatus.RUNTIME_ERROR,
            "Compile Error": SubmissionStatus.COMPILE_ERROR,
        }

        return status_map.get(status_display, SubmissionStatus.RUNTIME_ERROR)
