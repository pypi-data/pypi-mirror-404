"""Platform client interface for multi-platform support."""

from abc import ABC, abstractmethod
from typing import Dict, List

from crawler.domain.entities import Problem, Submission


class PlatformClient(ABC):
    """
    Abstract interface for platform-specific API clients.

    This interface defines the contract that all platform clients must implement,
    enabling the Strategy pattern for multi-platform support. Each concrete
    implementation handles platform-specific API communication and data formats.

    Implementations should handle:
    - Authentication with the platform
    - API request formatting and response parsing
    - Platform-specific error handling
    - Rate limiting and retry logic (via HTTPClient)

    Examples of concrete implementations:
    - LeetCodeClient
    - HackerRankClient (future)
    - CodeChefClient (future)
    - CodeforcesClient (future)
    """

    @abstractmethod
    def fetch_problem(self, problem_id: str) -> Problem:
        """
        Fetch a single problem by its identifier.

        Args:
            problem_id: The platform-specific problem identifier
                       (e.g., "two-sum" for LeetCode, "fizzbuzz" for HackerRank)

        Returns:
            Problem: The fetched problem entity with all metadata

        Raises:
            ProblemNotFoundException: If the problem doesn't exist
            NetworkException: If the network request fails
            AuthenticationException: If authentication is required but not provided

        Example:
            >>> client = LeetCodeClient(...)
            >>> problem = client.fetch_problem("two-sum")
            >>> print(problem.title)
            "Two Sum"
        """
        pass

    @abstractmethod
    def fetch_solved_problems(self, username: str, limit: int = None) -> List[Problem]:
        """
        Fetch all problems solved by a specific user.

        Args:
            username: The platform-specific username
            limit: Optional maximum number of problems to fetch (default: None = all)

        Returns:
            List[Problem]: List of all problems the user has solved (up to limit)

        Raises:
            UserNotFoundException: If the user doesn't exist
            NetworkException: If the network request fails
            AuthenticationException: If authentication is required but not provided

        Example:
            >>> client = LeetCodeClient(...)
            >>> problems = client.fetch_solved_problems("john_doe")
            >>> print(f"Solved {len(problems)} problems")
            "Solved 150 problems"

            >>> # Fetch only recent 50 problems
            >>> problems = client.fetch_solved_problems("john_doe", limit=50)
            >>> print(f"Fetched {len(problems)} problems")
            "Fetched 50 problems"
        """
        pass

    @abstractmethod
    def fetch_submission(self, problem_id: str, username: str) -> Submission:
        """
        Fetch the last accepted submission for a problem by a user.

        Args:
            problem_id: The platform-specific problem identifier
            username: The platform-specific username

        Returns:
            Submission: The last accepted submission with code and metadata

        Raises:
            SubmissionNotFoundException: If no accepted submission exists
            NetworkException: If the network request fails
            AuthenticationException: If authentication is required but not provided

        Example:
            >>> client = LeetCodeClient(...)
            >>> submission = client.fetch_submission("two-sum", "john_doe")
            >>> print(submission.language)
            "python3"
        """
        pass

    @abstractmethod
    def fetch_community_solutions(self, problem_id: str, limit: int = 10) -> List[Submission]:
        """
        Fetch top community solutions for a problem.

        Args:
            problem_id: The platform-specific problem identifier
            limit: Maximum number of solutions to fetch (default: 10)

        Returns:
            List[Submission]: List of community submissions, typically sorted by
                            popularity or performance

        Raises:
            ProblemNotFoundException: If the problem doesn't exist
            NetworkException: If the network request fails

        Example:
            >>> client = LeetCodeClient(...)
            >>> solutions = client.fetch_community_solutions("two-sum", limit=5)
            >>> print(f"Found {len(solutions)} community solutions")
            "Found 5 community solutions"
        """
        pass

    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with the platform using provided credentials.

        Args:
            credentials: Platform-specific authentication credentials
                        (e.g., {"session_token": "..."} for LeetCode,
                         {"api_key": "..."} for HackerRank)

        Returns:
            bool: True if authentication succeeded, False otherwise

        Raises:
            AuthenticationException: If authentication fails
            NetworkException: If the network request fails

        Example:
            >>> client = LeetCodeClient(...)
            >>> success = client.authenticate({"session_token": "abc123"})
            >>> print(f"Authenticated: {success}")
            "Authenticated: True"

        Note:
            Some platforms may not require explicit authentication for public data.
            In such cases, this method may be a no-op that returns True.
        """
        pass
