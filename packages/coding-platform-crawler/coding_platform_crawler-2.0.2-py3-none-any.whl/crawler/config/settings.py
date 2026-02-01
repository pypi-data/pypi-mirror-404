"""Configuration settings for the crawler application.

This module provides comprehensive configuration management with support for:
- Environment variables
- YAML/JSON configuration files
- Command-line argument overrides
- Default values

Configuration precedence (highest to lowest):
1. CLI arguments
2. Environment variables
3. Config file
4. Defaults
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class Config:
    """Configuration for the crawler application.

    Supports loading configuration from multiple sources with clear precedence:
    CLI > ENV > Config File > Defaults

    Attributes:
        # LeetCode configuration
        leetcode_graphql_url: LeetCode GraphQL API endpoint
        leetcode_session_token: Optional session token for authentication
        leetcode_username: LeetCode username

        # Future platform credentials (extensible)
        hackerrank_api_key: HackerRank API key (for future use)
        codechef_username: CodeChef username (for future use)
        codechef_password: CodeChef password (for future use)
        codeforces_api_key: Codeforces API key (for future use)
        codeforces_api_secret: Codeforces API secret (for future use)

        # Rate limiting configuration
        requests_per_second: Rate limit for API requests

        # Retry configuration
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay for exponential backoff (seconds)
        max_delay: Maximum delay for exponential backoff (seconds)
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to retry delays

        # Output configuration
        output_dir: Base directory for downloaded problems
        default_format: Default output format (python, markdown, json)

        # Logging configuration
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """

    # LeetCode configuration
    leetcode_graphql_url: str = "https://leetcode.com/graphql"
    leetcode_session_token: Optional[str] = None
    leetcode_csrf_token: Optional[str] = None
    leetcode_username: Optional[str] = None

    # Future platform credentials (extensible for Phase 3)
    hackerrank_api_key: Optional[str] = None
    codechef_username: Optional[str] = None
    codechef_password: Optional[str] = None
    codeforces_api_key: Optional[str] = None
    codeforces_api_secret: Optional[str] = None

    # Rate limiting configuration
    requests_per_second: float = 2.0

    # Retry configuration
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    # Output configuration
    output_dir: str = "./problems"
    default_format: str = "python"

    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @classmethod
    def from_defaults(cls) -> "Config":
        """Create a Config instance with default values.

        Returns:
            Config instance with all default values
        """
        return cls()

    @classmethod
    def from_env(cls, base_config: Optional["Config"] = None) -> "Config":
        """Load configuration from environment variables.

        Environment variables should be prefixed with CRAWLER_ and use uppercase.
        For example: CRAWLER_LEETCODE_SESSION_TOKEN

        Args:
            base_config: Optional base configuration to override

        Returns:
            Config instance with values from environment variables
        """
        if base_config is None:
            base_config = cls()

        # Create a dictionary of current values
        config_dict = {
            # LeetCode
            "leetcode_graphql_url": os.getenv(
                "CRAWLER_LEETCODE_GRAPHQL_URL", base_config.leetcode_graphql_url
            ),
            "leetcode_session_token": os.getenv(
                "CRAWLER_LEETCODE_SESSION_TOKEN", base_config.leetcode_session_token
            ),
            "leetcode_csrf_token": os.getenv(
                "CRAWLER_LEETCODE_CSRF_TOKEN", base_config.leetcode_csrf_token
            ),
            "leetcode_username": os.getenv(
                "CRAWLER_LEETCODE_USERNAME", base_config.leetcode_username
            ),
            # Future platforms
            "hackerrank_api_key": os.getenv(
                "CRAWLER_HACKERRANK_API_KEY", base_config.hackerrank_api_key
            ),
            "codechef_username": os.getenv(
                "CRAWLER_CODECHEF_USERNAME", base_config.codechef_username
            ),
            "codechef_password": os.getenv(
                "CRAWLER_CODECHEF_PASSWORD", base_config.codechef_password
            ),
            "codeforces_api_key": os.getenv(
                "CRAWLER_CODEFORCES_API_KEY", base_config.codeforces_api_key
            ),
            "codeforces_api_secret": os.getenv(
                "CRAWLER_CODEFORCES_API_SECRET", base_config.codeforces_api_secret
            ),
            # Rate limiting
            "requests_per_second": float(
                os.getenv("CRAWLER_REQUESTS_PER_SECOND", str(base_config.requests_per_second))
            ),
            # Retry configuration
            "max_retries": int(os.getenv("CRAWLER_MAX_RETRIES", str(base_config.max_retries))),
            "initial_delay": float(
                os.getenv("CRAWLER_INITIAL_DELAY", str(base_config.initial_delay))
            ),
            "max_delay": float(os.getenv("CRAWLER_MAX_DELAY", str(base_config.max_delay))),
            "exponential_base": float(
                os.getenv("CRAWLER_EXPONENTIAL_BASE", str(base_config.exponential_base))
            ),
            "jitter": os.getenv("CRAWLER_JITTER", str(base_config.jitter)).lower()
            in ("true", "1", "yes"),
            # Output configuration
            "output_dir": os.getenv("CRAWLER_OUTPUT_DIR", base_config.output_dir),
            "default_format": os.getenv("CRAWLER_DEFAULT_FORMAT", base_config.default_format),
            # Logging configuration
            "log_level": os.getenv("CRAWLER_LOG_LEVEL", base_config.log_level),
            "log_file": os.getenv("CRAWLER_LOG_FILE", base_config.log_file),
        }

        return cls(**config_dict)

    @classmethod
    def from_file(cls, file_path: Path, base_config: Optional["Config"] = None) -> "Config":
        """Load configuration from a YAML or JSON file.

        Args:
            file_path: Path to configuration file (.yaml, .yml, or .json)
            base_config: Optional base configuration to override

        Returns:
            Config instance with values from file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or invalid
        """
        if base_config is None:
            base_config = cls()

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Determine file format
        suffix = file_path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            if not YAML_AVAILABLE:
                raise ValueError("YAML support requires PyYAML. Install with: pip install pyyaml")
            with open(file_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f)
        elif suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
        else:
            raise ValueError(
                f"Unsupported config file format: {suffix}. "
                "Supported formats: .yaml, .yml, .json"
            )

        if not isinstance(file_config, dict):
            raise ValueError("Configuration file must contain a dictionary/object")

        # Merge with base config
        config_dict = {
            # LeetCode
            "leetcode_graphql_url": file_config.get(
                "leetcode_graphql_url", base_config.leetcode_graphql_url
            ),
            "leetcode_session_token": file_config.get(
                "leetcode_session_token", base_config.leetcode_session_token
            ),
            "leetcode_csrf_token": file_config.get(
                "leetcode_csrf_token", base_config.leetcode_csrf_token
            ),
            "leetcode_username": file_config.get(
                "leetcode_username", base_config.leetcode_username
            ),
            # Future platforms
            "hackerrank_api_key": file_config.get(
                "hackerrank_api_key", base_config.hackerrank_api_key
            ),
            "codechef_username": file_config.get(
                "codechef_username", base_config.codechef_username
            ),
            "codechef_password": file_config.get(
                "codechef_password", base_config.codechef_password
            ),
            "codeforces_api_key": file_config.get(
                "codeforces_api_key", base_config.codeforces_api_key
            ),
            "codeforces_api_secret": file_config.get(
                "codeforces_api_secret", base_config.codeforces_api_secret
            ),
            # Rate limiting
            "requests_per_second": file_config.get(
                "requests_per_second", base_config.requests_per_second
            ),
            # Retry configuration
            "max_retries": file_config.get("max_retries", base_config.max_retries),
            "initial_delay": file_config.get("initial_delay", base_config.initial_delay),
            "max_delay": file_config.get("max_delay", base_config.max_delay),
            "exponential_base": file_config.get("exponential_base", base_config.exponential_base),
            "jitter": file_config.get("jitter", base_config.jitter),
            # Output configuration
            "output_dir": file_config.get("output_dir", base_config.output_dir),
            "default_format": file_config.get("default_format", base_config.default_format),
            # Logging configuration
            "log_level": file_config.get("log_level", base_config.log_level),
            "log_file": file_config.get("log_file", base_config.log_file),
        }

        return cls(**config_dict)

    @classmethod
    def from_cli_args(
        cls, args: Dict[str, Any], base_config: Optional["Config"] = None
    ) -> "Config":
        """Load configuration from command-line arguments.

        Args:
            args: Dictionary of command-line arguments
            base_config: Optional base configuration to override

        Returns:
            Config instance with values from CLI arguments
        """
        if base_config is None:
            base_config = cls()

        # Only override values that are explicitly provided in args
        config_dict = {
            # LeetCode
            "leetcode_graphql_url": args.get(
                "leetcode_graphql_url", base_config.leetcode_graphql_url
            ),
            "leetcode_session_token": args.get(
                "leetcode_session_token", base_config.leetcode_session_token
            ),
            "leetcode_csrf_token": args.get("leetcode_csrf_token", base_config.leetcode_csrf_token),
            "leetcode_username": args.get("leetcode_username", base_config.leetcode_username),
            # Future platforms
            "hackerrank_api_key": args.get("hackerrank_api_key", base_config.hackerrank_api_key),
            "codechef_username": args.get("codechef_username", base_config.codechef_username),
            "codechef_password": args.get("codechef_password", base_config.codechef_password),
            "codeforces_api_key": args.get("codeforces_api_key", base_config.codeforces_api_key),
            "codeforces_api_secret": args.get(
                "codeforces_api_secret", base_config.codeforces_api_secret
            ),
            # Rate limiting
            "requests_per_second": args.get("requests_per_second", base_config.requests_per_second),
            # Retry configuration
            "max_retries": args.get("max_retries", base_config.max_retries),
            "initial_delay": args.get("initial_delay", base_config.initial_delay),
            "max_delay": args.get("max_delay", base_config.max_delay),
            "exponential_base": args.get("exponential_base", base_config.exponential_base),
            "jitter": args.get("jitter", base_config.jitter),
            # Output configuration
            "output_dir": args.get("output_dir", base_config.output_dir),
            "default_format": args.get("default_format", base_config.default_format),
            # Logging configuration
            "log_level": args.get("log_level", base_config.log_level),
            "log_file": args.get("log_file", base_config.log_file),
        }

        return cls(**config_dict)

    @classmethod
    def load(
        cls, config_file: Optional[Path] = None, cli_args: Optional[Dict[str, Any]] = None
    ) -> "Config":
        """Load configuration with proper precedence: CLI > ENV > Config File > Defaults.

        This is the recommended way to load configuration as it applies the correct
        precedence order automatically.

        Args:
            config_file: Optional path to configuration file
            cli_args: Optional dictionary of CLI arguments

        Returns:
            Config instance with values from all sources, properly prioritized

        Example:
            >>> config = Config.load(
            ...     config_file=Path("config.yaml"),
            ...     cli_args={"leetcode_username": "john_doe"}
            ... )
        """
        # Start with defaults
        config = cls.from_defaults()

        # Apply config file if provided
        if config_file is not None and config_file.exists():
            config = cls.from_file(config_file, base_config=config)

        # Apply environment variables
        config = cls.from_env(base_config=config)

        # Apply CLI arguments (highest precedence)
        if cli_args is not None:
            config = cls.from_cli_args(cli_args, base_config=config)

        return config

    def get_platform_credentials(self, platform: str) -> Dict[str, Optional[str]]:
        """Get credentials for a specific platform.

        Args:
            platform: Platform name (leetcode, hackerrank, codechef, codeforces)

        Returns:
            Dictionary of credentials for the platform

        Raises:
            ValueError: If platform is not supported
        """
        platform = platform.lower()

        if platform == "leetcode":
            return {
                "session_token": self.leetcode_session_token,
                "csrf_token": self.leetcode_csrf_token,
                "username": self.leetcode_username,
            }
        elif platform == "hackerrank":
            return {
                "api_key": self.hackerrank_api_key,
            }
        elif platform == "codechef":
            return {
                "username": self.codechef_username,
                "password": self.codechef_password,
            }
        elif platform == "codeforces":
            return {
                "api_key": self.codeforces_api_key,
                "api_secret": self.codeforces_api_secret,
            }
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            # LeetCode
            "leetcode_graphql_url": self.leetcode_graphql_url,
            "leetcode_session_token": self.leetcode_session_token,
            "leetcode_csrf_token": self.leetcode_csrf_token,
            "leetcode_username": self.leetcode_username,
            # Future platforms
            "hackerrank_api_key": self.hackerrank_api_key,
            "codechef_username": self.codechef_username,
            "codechef_password": self.codechef_password,
            "codeforces_api_key": self.codeforces_api_key,
            "codeforces_api_secret": self.codeforces_api_secret,
            # Rate limiting
            "requests_per_second": self.requests_per_second,
            # Retry configuration
            "max_retries": self.max_retries,
            "initial_delay": self.initial_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter,
            # Output configuration
            "output_dir": self.output_dir,
            "default_format": self.default_format,
            # Logging configuration
            "log_level": self.log_level,
            "log_file": self.log_file,
        }
