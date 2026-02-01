# Coding Platform Crawler

[![Tests](https://github.com/prakharmishra04/extensible-leetcode-crawler/workflows/Tests/badge.svg)](https://github.com/prakharmishra04/extensible-leetcode-crawler/actions)
[![Pre-commit](https://github.com/prakharmishra04/extensible-leetcode-crawler/workflows/Pre-commit%20Checks/badge.svg)](https://github.com/prakharmishra04/extensible-leetcode-crawler/actions)
[![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)](htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.8--3.12-blue)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A well-architected Python toolkit for downloading and managing coding problems from LeetCode with extensible support for additional platforms. Built with clean architecture principles, comprehensive testing, and SOLID design patterns.

## Features

- 🎯 Download individual problems with full descriptions and your submissions
- 📦 Batch download all your solved problems at once
- 📋 List and filter problems by difficulty and topics
- 🔄 Smart update modes: skip existing, update changed, or force overwrite
- 📝 Multiple output formats: Python, Markdown, or JSON
- 🏗️ Extensible architecture: Easy to add support for new platforms
- ⚙️ Flexible configuration: CLI args, environment variables, or config files
- 🔁 Robust error handling: Automatic retries with exponential backoff
- 🧪 Comprehensive tests: 89% code coverage with 617 tests (unit + integration)

## Quick Start

> **Looking for the simple script-based version?** Check out [v1-scripts/](v1-scripts/) for standalone Python scripts that work without installation. Perfect for quick one-off downloads!

### 1. Install the Package

```bash
# Option A: Install as a package (recommended for end users)
pip install -e .
# This installs: requests, beautifulsoup4, lxml, pyyaml, rich
# Plus the 'crawler' CLI command

# Option B: Install dependencies only (if you want to run without installing)
pip install -r requirements.txt
# Then use: python -m crawler.cli.main

# Option C: Install with development tools (for contributors)
pip install -e ".[dev]"
# This installs everything including pytest, black, flake8, mypy, etc.
```

After installation with Option A or C, you get a convenient `crawler` command!

### 2. Set Up Configuration

**Option A: Using Config File (Recommended)**

```bash
# Copy the template
cp my-config.yaml.example my-config.yaml

# Edit my-config.yaml and add your credentials
# (This file is gitignored for security)
```

Get your LeetCode session cookies:

1. Open https://leetcode.com (logged in) → Press F12
1. Application tab → Cookies → https://leetcode.com
1. Copy `LEETCODE_SESSION` and `csrftoken` values
1. Paste them into `my-config.yaml`

**Option B: Using Environment Variables**

```bash
export CRAWLER_LEETCODE_SESSION_TOKEN='your-session-token'
export CRAWLER_LEETCODE_CSRF_TOKEN='your-csrf-token'
export CRAWLER_LEETCODE_USERNAME='your-username'
```

### 3. Download Your First Problem

```bash
# If installed with pip install -e .
crawler download two-sum --platform leetcode

# Or without installation
python -m crawler.cli.main download two-sum --platform leetcode
```

Your problem is now in `./problems/leetcode/two-sum/solution.py` with your actual submission code!

## Usage

> **Note:** All examples below use the `crawler` command (after `pip install -e .`). If you haven't installed the package, replace `crawler` with `python -m crawler.cli.main`.

### Download a Single Problem

```bash
# Download with your submission
crawler download two-sum --platform leetcode

# Force re-download
crawler download two-sum --platform leetcode --force

# Download as Markdown
crawler download two-sum --platform leetcode --format markdown
```

### Batch Download All Solved Problems

```bash
# Download all your solutions
crawler batch your-username --platform leetcode

# Update only newer submissions
crawler batch your-username --platform leetcode --mode update

# Download only Easy problems
crawler batch your-username --platform leetcode --difficulty Easy

# Download only recent 50 problems
crawler batch your-username --platform leetcode --mode skip --limit 50
```

### List Downloaded Problems

```bash
# List all problems
crawler list

# List only Medium problems
crawler list --difficulty Medium

# List problems sorted by difficulty
crawler list --sort-by difficulty
```

## Configuration

Configuration priority (highest to lowest):

1. **CLI arguments** - Override everything
1. **Environment variables** - Override config files
1. **Config file** (`my-config.yaml` or `config.yaml`) - Base configuration

### Option 1: Config File (Recommended)

```bash
# Copy the template
cp my-config.yaml.example my-config.yaml
```

Edit `my-config.yaml`:

```yaml
# LeetCode credentials
leetcode_session_token: "your-token"
leetcode_csrf_token: "your-csrf"
leetcode_username: "your-username"

# Output configuration
output_dir: "./problems"
default_format: "python"  # Options: python, markdown, json

# Rate limiting
requests_per_second: 2.0

# Retry configuration
max_retries: 3
initial_delay: 1.0
max_delay: 60.0
exponential_base: 2.0
jitter: true

# Logging
log_level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
log_file: "./logs/crawler.log"
```

> **Security Note:** `my-config.yaml` is gitignored to protect your credentials. Never commit this file!

### Option 2: Environment Variables

```bash
# Authentication
export CRAWLER_LEETCODE_SESSION_TOKEN='your-token'
export CRAWLER_LEETCODE_CSRF_TOKEN='your-csrf'
export CRAWLER_LEETCODE_USERNAME='your-username'

# Output
export CRAWLER_OUTPUT_DIR='./problems'
export CRAWLER_DEFAULT_FORMAT='python'

# Rate limiting
export CRAWLER_REQUESTS_PER_SECOND='2.0'

# Retry configuration
export CRAWLER_MAX_RETRIES='3'
export CRAWLER_INITIAL_DELAY='1.0'
export CRAWLER_MAX_DELAY='60.0'

# Logging
export CRAWLER_LOG_LEVEL='INFO'
export CRAWLER_LOG_FILE='./logs/crawler.log'
```

### Option 3: CLI Arguments

```bash
# Override config with CLI args
crawler download two-sum --platform leetcode --format markdown --output-dir ./my-problems
```

## Output Structure

```
problems/
└── leetcode/
    ├── two-sum/
    │   ├── solution.py          # Your solution with submission code
    │   └── metadata.json        # Problem metadata
    └── add-two-numbers/
        ├── solution.py
        └── metadata.json
```

## Architecture

The crawler follows clean architecture with clear separation of concerns:

```
CLI Layer → Application Layer → Domain Layer → Infrastructure Layer
```

- **Domain Layer**: Entities (Problem, Submission), Value Objects (Difficulty, Example)
- **Application Layer**: Use cases (FetchProblem, BatchDownload, ListProblems)
- **Infrastructure Layer**: Platform clients, HTTP, file I/O, formatters
- **CLI Layer**: Command handlers, argument parsing, console output

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## Development

### Setup Development Environment

**Automated setup (recommended):**

```bash
# Linux/macOS
./scripts/setup-dev.sh

# Windows PowerShell
.\scripts\setup-dev.ps1

# Windows Command Prompt
scripts\setup-dev.bat
```

These scripts will:

1. Install the package in development mode
1. Install all dev dependencies
1. Set up git hooks (pre-commit, pre-push, commit-msg)
1. Run initial code quality checks

**Manual setup:**

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Set up git hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg

# Run checks on all files
pre-commit run --all-files
```

### Git Hooks (Automatic Quality Checks)

Once set up, git hooks run automatically:

**On `git commit`:**

- Code formatting (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Security scanning (bandit)
- Commit message validation (Conventional Commits)

**On `git push`:**

- Full test suite execution
- Prevents pushing broken code

See [docs/CI_CD.md](docs/CI_CD.md) for complete CI/CD documentation.

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/crawler --cov-report=html

# Specific tests
pytest tests/unit/
pytest tests/integration/

# Watch mode (requires pytest-watch)
ptw
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/

# Run all checks
pre-commit run --all-files
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Maintain >80% test coverage

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines.

## Extending the Crawler

The architecture makes it easy to add new platforms. See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete guide on adding support for HackerRank, CodeChef, Codeforces, etc.

## Troubleshooting

**"Authentication required"**

- Set `CRAWLER_LEETCODE_SESSION_TOKEN` and `CRAWLER_LEETCODE_CSRF_TOKEN`
- Get fresh cookies from your browser (they expire after 2-4 weeks)

**"No accepted submissions found"**

- You haven't solved this problem yet on LeetCode
- Check the problem ID is correct (use URL slug like "two-sum")

**"Rate limit exceeded"**

- Reduce `requests_per_second` in config
- Wait a few seconds and try again

## Security

⚠️ **Important**: Never commit credentials to version control

- **Use `my-config.yaml`** for local credentials (already gitignored)
- **Use environment variables** for CI/CD or shared environments
- **Rotate session tokens regularly** (they expire after 2-4 weeks)
- **Never commit** `config.yaml`, `config.json`, or `my-config.yaml`

The `.gitignore` is configured to protect these files, but always double-check before committing!

## License

For personal use only. Respect LeetCode's Terms of Service and rate limits.

## Version History

### v2 (Current) - Clean Architecture

The main project with extensible architecture, comprehensive testing, and multi-platform support.

**Installation:**

```bash
pip install -e .
crawler download two-sum --platform leetcode
```

### v1 - Simple Scripts

Standalone Python scripts that work without installation. Perfect for quick downloads and users who prefer simplicity over architecture.

**Usage:**

```bash
python v1-scripts/batch_download_solutions.py
```

See [v1-scripts/README.md](v1-scripts/README.md) for v1 documentation and [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for complete project overview.

**When to use which version:**

- **Use v2** if you want a proper CLI tool, extensible architecture, and plan to use it regularly
- **Use v1** if you just need a quick one-off download or prefer simple scripts

## Acknowledgments

Built with Python 3.8+, following SOLID principles and clean architecture patterns.
