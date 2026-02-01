"""Problem repository interface for data persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional

from crawler.domain.entities import Problem, Submission


class ProblemRepository(ABC):
    """
    Abstract interface for problem persistence.

    This interface defines the contract for storing and retrieving problems,
    enabling the Repository pattern for data access. Concrete implementations
    can use different storage backends (file system, database, cloud storage).

    The repository abstracts away storage details, allowing the application
    layer to work with domain entities without knowing how they're persisted.

    Examples of concrete implementations:
    - FileSystemRepository (current implementation)
    - SQLiteRepository (future)
    - PostgreSQLRepository (future)
    - MongoDBRepository (future)
    """

    @abstractmethod
    def save(self, problem: Problem, submission: Optional[Submission] = None) -> None:
        """
        Save a problem and optionally its submission to the repository.

        Args:
            problem: The problem entity to save
            submission: Optional submission entity to save alongside the problem

        Raises:
            RepositoryException: If the save operation fails
            ValidationException: If the problem or submission is invalid

        Example:
            >>> repo = FileSystemRepository(...)
            >>> problem = Problem(id="two-sum", ...)
            >>> submission = Submission(id="sub-123", ...)
            >>> repo.save(problem, submission)

        Note:
            If a problem with the same ID and platform already exists,
            implementations should overwrite it. The behavior can be
            controlled by the caller using exists() before calling save().
        """
        pass

    @abstractmethod
    def find_by_id(self, problem_id: str, platform: str) -> Optional[Problem]:
        """
        Find a problem by its ID and platform.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name (e.g., "leetcode", "hackerrank")

        Returns:
            Optional[Problem]: The problem if found, None otherwise

        Raises:
            RepositoryException: If the retrieval operation fails

        Example:
            >>> repo = FileSystemRepository(...)
            >>> problem = repo.find_by_id("two-sum", "leetcode")
            >>> if problem:
            ...     print(problem.title)
            "Two Sum"

        Note:
            This method returns None if the problem doesn't exist, rather than
            raising an exception. This allows callers to easily check for
            existence without exception handling.
        """
        pass

    @abstractmethod
    def exists(self, problem_id: str, platform: str) -> bool:
        """
        Check if a problem exists in the repository.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name (e.g., "leetcode", "hackerrank")

        Returns:
            bool: True if the problem exists, False otherwise

        Raises:
            RepositoryException: If the check operation fails

        Example:
            >>> repo = FileSystemRepository(...)
            >>> if repo.exists("two-sum", "leetcode"):
            ...     print("Problem already downloaded")
            "Problem already downloaded"

        Note:
            This is a convenience method that can be implemented using
            find_by_id(), but concrete implementations may provide more
            efficient implementations (e.g., checking file existence).
        """
        pass

    @abstractmethod
    def list_all(self, platform: Optional[str] = None) -> List[Problem]:
        """
        List all problems in the repository, optionally filtered by platform.

        Args:
            platform: Optional platform name to filter by. If None, returns
                     problems from all platforms.

        Returns:
            List[Problem]: List of all problems matching the filter

        Raises:
            RepositoryException: If the list operation fails

        Example:
            >>> repo = FileSystemRepository(...)
            >>> all_problems = repo.list_all()
            >>> print(f"Total: {len(all_problems)}")
            "Total: 250"
            >>>
            >>> leetcode_problems = repo.list_all(platform="leetcode")
            >>> print(f"LeetCode: {len(leetcode_problems)}")
            "LeetCode: 150"

        Note:
            The returned list may be large for users with many solved problems.
            Implementations should consider lazy loading or pagination for
            better performance.
        """
        pass

    @abstractmethod
    def delete(self, problem_id: str, platform: str) -> bool:
        """
        Delete a problem from the repository.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name (e.g., "leetcode", "hackerrank")

        Returns:
            bool: True if the problem was deleted, False if it didn't exist

        Raises:
            RepositoryException: If the delete operation fails

        Example:
            >>> repo = FileSystemRepository(...)
            >>> deleted = repo.delete("two-sum", "leetcode")
            >>> if deleted:
            ...     print("Problem deleted successfully")
            "Problem deleted successfully"

        Note:
            This method returns False if the problem doesn't exist, rather than
            raising an exception. This makes it idempotent - calling it multiple
            times has the same effect as calling it once.
        """
        pass

    @abstractmethod
    def get_submission_timestamp(self, problem_id: str, platform: str) -> Optional[int]:
        """
        Get the timestamp of the stored submission for a problem.

        This method is used to determine if a newer submission exists on the
        platform, enabling smart UPDATE mode behavior that only re-downloads
        problems when there's a newer submission available.

        Args:
            problem_id: The platform-specific problem identifier
            platform: The platform name (e.g., "leetcode", "hackerrank")

        Returns:
            Optional[int]: Unix timestamp of the stored submission, or None if:
                          - The problem doesn't exist in the repository
                          - The problem exists but has no submission stored

        Raises:
            RepositoryException: If the retrieval operation fails

        Example:
            >>> repo = FileSystemRepository(...)
            >>> timestamp = repo.get_submission_timestamp("two-sum", "leetcode")
            >>> if timestamp:
            ...     print(f"Stored submission from: {timestamp}")
            "Stored submission from: 1640995200"
            >>>
            >>> # Problem without submission
            >>> timestamp = repo.get_submission_timestamp("new-problem", "leetcode")
            >>> print(timestamp)
            None

        Note:
            This method is specifically designed for UPDATE mode optimization.
            It allows checking if a re-download is needed without loading the
            entire problem entity, which is more efficient for large repositories.
        """
        pass
