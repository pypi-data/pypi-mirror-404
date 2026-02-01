"""File system-based problem repository implementation."""

import json
from logging import Logger
from pathlib import Path
from typing import List, Optional

from crawler.application.interfaces.formatter import OutputFormatter
from crawler.application.interfaces.repository import ProblemRepository
from crawler.domain.entities import Problem, Submission
from crawler.domain.entities.enums import SubmissionStatus
from crawler.domain.exceptions import RepositoryException
from crawler.domain.value_objects import Constraint, Difficulty, Example, Percentiles


class FileSystemRepository(ProblemRepository):
    """
    File system-based implementation of ProblemRepository.

    This repository stores problems as files on the local file system with
    the following structure:

    base_path/
        platform/
            problem_id/
                solution.{ext}      # Formatted problem file
                metadata.json       # Problem metadata for reconstruction

    The metadata.json file contains all problem data in JSON format, allowing
    the problem to be reconstructed without parsing the formatted file.
    """

    def __init__(self, base_path: Path, formatter: OutputFormatter, logger: Logger):
        """
        Initialize the file system repository.

        Args:
            base_path: Root directory for storing problems
            formatter: Output formatter for generating problem files
            logger: Logger instance for logging operations
        """
        self.base_path = Path(base_path)
        self.formatter = formatter
        self.logger = logger

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, problem: Problem, submission: Optional[Submission] = None) -> None:
        """
        Save a problem and optionally its submission to the file system.

        Creates a directory structure: base_path/platform/problem_id/
        Writes two files:
        1. solution.{ext} - Formatted problem file
        2. metadata.json - Problem metadata for reconstruction

        Args:
            problem: The problem entity to save
            submission: Optional submission entity to save alongside the problem

        Raises:
            RepositoryException: If the save operation fails
        """
        try:
            # Create directory structure
            problem_dir = self.base_path / problem.platform / problem.id
            problem_dir.mkdir(parents=True, exist_ok=True)

            # Format and write the problem file
            content = self.formatter.format_problem(problem, submission)
            file_path = problem_dir / f"solution.{self.formatter.get_file_extension()}"
            file_path.write_text(content, encoding="utf-8")

            # Write metadata for reconstruction
            metadata = self._serialize_problem(problem, submission)
            metadata_path = problem_dir / "metadata.json"
            metadata_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            self.logger.info(f"Saved problem {problem.id} to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save problem {problem.id}: {e}")
            raise RepositoryException(f"Failed to save problem {problem.id}") from e

    def find_by_id(self, problem_id: str, platform: str) -> Optional[Problem]:
        """
        Find a problem by its ID and platform.

        Reads the metadata.json file and reconstructs the Problem entity.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name

        Returns:
            Optional[Problem]: The problem if found, None otherwise

        Raises:
            RepositoryException: If the retrieval operation fails
        """
        try:
            problem_dir = self.base_path / platform / problem_id
            metadata_path = problem_dir / "metadata.json"

            if not metadata_path.exists():
                return None

            # Read and deserialize metadata
            metadata_text = metadata_path.read_text(encoding="utf-8")
            metadata = json.loads(metadata_text)

            return self._deserialize_problem(metadata)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse metadata for {problem_id}: {e}")
            raise RepositoryException(f"Failed to parse metadata for {problem_id}") from e
        except Exception as e:
            self.logger.error(f"Failed to retrieve problem {problem_id}: {e}")
            raise RepositoryException(f"Failed to retrieve problem {problem_id}") from e

    def exists(self, problem_id: str, platform: str) -> bool:
        """
        Check if a problem exists in the repository.

        Checks for the existence of the problem directory and metadata file.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name

        Returns:
            bool: True if the problem exists, False otherwise
        """
        problem_dir = self.base_path / platform / problem_id
        metadata_path = problem_dir / "metadata.json"
        return metadata_path.exists()

    def list_all(self, platform: Optional[str] = None) -> List[Problem]:
        """
        List all problems in the repository, optionally filtered by platform.

        Scans the file system for problem directories and reconstructs
        Problem entities from metadata files.

        Args:
            platform: Optional platform name to filter by

        Returns:
            List[Problem]: List of all problems matching the filter

        Raises:
            RepositoryException: If the list operation fails
        """
        problems = []

        try:
            # Determine which platforms to scan
            if platform:
                platforms = [platform]
            else:
                # List all platform directories
                platforms = [p.name for p in self.base_path.iterdir() if p.is_dir()]

            # Scan each platform directory
            for plat in platforms:
                platform_dir = self.base_path / plat
                if not platform_dir.exists():
                    continue

                # Scan each problem directory
                for problem_dir in platform_dir.iterdir():
                    if not problem_dir.is_dir():
                        continue

                    # Try to load the problem
                    problem = self.find_by_id(problem_dir.name, plat)
                    if problem:
                        problems.append(problem)

            return problems

        except Exception as e:
            self.logger.error(f"Failed to list problems: {e}")
            raise RepositoryException("Failed to list problems") from e

    def delete(self, problem_id: str, platform: str) -> bool:
        """
        Delete a problem from the repository.

        Removes the entire problem directory including all files.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name

        Returns:
            bool: True if the problem was deleted, False if it didn't exist

        Raises:
            RepositoryException: If the delete operation fails
        """
        try:
            problem_dir = self.base_path / platform / problem_id

            if not problem_dir.exists():
                return False

            # Remove all files in the directory
            for file_path in problem_dir.iterdir():
                file_path.unlink()

            # Remove the directory
            problem_dir.rmdir()

            self.logger.info(f"Deleted problem {problem_id} from {platform}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete problem {problem_id}: {e}")
            raise RepositoryException(f"Failed to delete problem {problem_id}") from e

    def get_submission_timestamp(self, problem_id: str, platform: str) -> Optional[int]:
        """
        Get the timestamp of the stored submission for a problem.

        Reads the metadata.json file and extracts the submission timestamp
        if a submission exists.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name

        Returns:
            Optional[int]: Unix timestamp of the stored submission, or None if
                          the problem doesn't exist or has no submission

        Raises:
            RepositoryException: If the retrieval operation fails
        """
        try:
            problem_dir = self.base_path / platform / problem_id
            metadata_path = problem_dir / "metadata.json"

            if not metadata_path.exists():
                return None

            # Read and parse metadata
            metadata_text = metadata_path.read_text(encoding="utf-8")
            metadata = json.loads(metadata_text)

            # Check if submission exists in metadata
            if "submission" in metadata and metadata["submission"]:
                return metadata["submission"].get("timestamp")

            return None

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse metadata for {problem_id}: {e}")
            raise RepositoryException(f"Failed to parse metadata for {problem_id}") from e
        except Exception as e:
            self.logger.error(f"Failed to retrieve submission timestamp for {problem_id}: {e}")
            raise RepositoryException(
                f"Failed to retrieve submission timestamp for {problem_id}"
            ) from e

    def _serialize_problem(self, problem: Problem, submission: Optional[Submission] = None) -> dict:
        """
        Serialize a Problem entity to a dictionary for JSON storage.

        Args:
            problem: The problem entity to serialize
            submission: Optional submission entity to serialize

        Returns:
            dict: Serialized problem data
        """
        data = {
            "id": problem.id,
            "platform": problem.platform,
            "title": problem.title,
            "difficulty": problem.difficulty.level,
            "description": problem.description,
            "topics": problem.topics,
            "constraints": [{"text": c.text} for c in problem.constraints],
            "examples": [
                {"input": ex.input, "output": ex.output, "explanation": ex.explanation}
                for ex in problem.examples
            ],
            "hints": problem.hints,
            "acceptance_rate": problem.acceptance_rate,
        }

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
                "percentiles": (
                    {
                        "runtime": submission.percentiles.runtime,
                        "memory": submission.percentiles.memory,
                    }
                    if submission.percentiles
                    else None
                ),
            }

        return data

    def _deserialize_problem(self, data: dict) -> Problem:
        """
        Deserialize a Problem entity from a dictionary.

        Args:
            data: Serialized problem data

        Returns:
            Problem: Reconstructed problem entity
        """
        return Problem(
            id=data["id"],
            platform=data["platform"],
            title=data["title"],
            difficulty=Difficulty(data["difficulty"]),
            description=data["description"],
            topics=data["topics"],
            constraints=[Constraint(text=c["text"]) for c in data["constraints"]],
            examples=[
                Example(input=ex["input"], output=ex["output"], explanation=ex.get("explanation"))
                for ex in data["examples"]
            ],
            hints=data["hints"],
            acceptance_rate=data["acceptance_rate"],
        )
