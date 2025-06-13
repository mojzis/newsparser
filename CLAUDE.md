# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

When working on this project, please maintain a neutral, professional tone:
- Avoid exclamation marks and overly enthusiastic language
- Skip flattery and proclamations like "you are absolutely right"
- Focus on factual, concise responses
- Use simple confirmations like "done" or "completed" rather than celebratory language
- Provide technical details when relevant, but keep explanations brief

## MVP Development Principles

**IMPORTANT: This project follows MVP/startup methodology. Keep everything super simple:**
- Focus only on the task at hand
- Always do minimal implementation
- No extra features or "nice-to-haves"
- Things will change soon - don't over-engineer
- Prioritize working code over perfect code
- Avoid premature optimization
- Skip edge cases unless explicitly required
- No additional abstractions beyond what's needed

## Phase Planning Requirement

Before proceeding with any new phase or significant feature implementation:
1. Create a detailed phase plan document outlining all tasks and implementation steps
2. Document the plan in the `plans/` directory with proper naming (e.g., `phase_3.md`)
3. Update the `plans/phases_overview.md` with any new phases or modifications
4. Get user approval for the plan before beginning implementation
5. Document implementation progress and decisions in the phase-specific file

### Task Implementation Guidelines

IMPORTANT: Each task within a phase should produce a testable CLI command:
- Tasks (e.g., 1.1, 1.2, 2.1) should each add a functional command
- Don't wait until phase completion to add commands
- Commands should demonstrate the specific functionality of that task
- Include the command syntax in the task plan (e.g., "Command: `nsp process-article <url>`")
- Test the command before marking the task complete
- Document example usage in commit messages
- **ALWAYS commit changes after completing a task or significant feature**

### Git Commit Guidelines

IMPORTANT: Commit changes after completing tasks:
- Use descriptive commit messages following existing patterns
- Include command examples in commit messages
- Add "🤖 Generated with [Claude Code](https://claude.ai/code)" footer
- Test functionality before committing
- Use `git add -A` to include new files
- Check `.gitignore` to avoid committing data files

### Notebook Development Guidelines

When working with Jupyter/marimo notebooks:
- **Never use `asyncio.run()`** - notebooks already run in an event loop
- Provide synchronous wrapper methods for async functionality (e.g., `get_stored_posts_sync()`)
- Use nest_asyncio if async calls are absolutely necessary
- Prefer CLI commands for complex async operations
- Document which features should use CLI vs notebook interface

## Project Overview

This is the Bluesky MCP Monitor project - a daily service that parses Bluesky for "mcp" mentions, evaluates content using Anthropic API, stores data in Parquet files on Cloudflare R2, and generates HTML reports with automated Bluesky posting.

## CLI Tool

The project provides a command-line interface accessible via the `nsp` command (short for "newsparser"). After installation with Poetry, all operations are performed using:

```bash
poetry run nsp <command> [options]
```

The CLI provides commands for data collection, search configuration, data exploration, and operational tasks.

## Commands

### Development Setup
```bash
# Install dependencies
poetry install

# Install development dependencies
poetry install --with dev

# Activate virtual environment
poetry shell
```

### Dependency Management

IMPORTANT: Always use Poetry to add new dependencies:
```bash
# Add a runtime dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Add with version constraints
poetry add "package-name>=1.0,<2.0"

# Update dependencies
poetry update
```

Never manually edit pyproject.toml to add dependencies. Using `poetry add` ensures:
- Latest compatible versions are installed
- Lock file is properly updated
- Dependency resolution is handled correctly
- Version constraints are properly set

### Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_models/test_post.py

# Run tests matching pattern
poetry run pytest -k "test_post"
```

### CLI Commands (Phase 2.5+)

#### Stage-Based Commands (New Architecture)
```bash
# Individual stages
poetry run nsp stages collect --date 2024-01-15 --max-posts 100 --search mcp_tag
poetry run nsp stages collect --date 2024-01-15 --no-expand-urls  # Skip URL expansion
poetry run nsp stages fetch --date 2024-01-15
poetry run nsp stages evaluate --date 2024-01-15
poetry run nsp stages report --date 2024-01-15

# Run all stages in sequence
poetry run nsp stages run-all --date 2024-01-15 --max-posts 100 --search mcp_tag
poetry run nsp stages run-all --date 2024-01-15 --no-expand-urls  # Skip URL expansion

# Utility commands
poetry run nsp stages status --date 2024-01-15          # Show stage progression
poetry run nsp stages list-files collect --limit 10    # List files in stage
poetry run nsp stages clean fetch --date 2024-01-15    # Clean stage data

# Convenient top-level aliases
poetry run nsp collect-new --date 2024-01-15
poetry run nsp collect-new --date 2024-01-15 --no-expand-urls  # Skip URL expansion
poetry run nsp fetch-new --date 2024-01-15
poetry run nsp evaluate-new --date 2024-01-15
poetry run nsp report-new --date 2024-01-15
```

#### Legacy Commands (Original Architecture)
```bash
# Collect posts from Bluesky
poetry run nsp collect

# Collect for specific date with custom search
poetry run nsp collect --date 2024-01-15 --search mcp_tools --max-posts 200

# List available search definitions
poetry run nsp list-searches

# Validate search configuration
poetry run nsp validate-config

# Check data status
poetry run nsp status --date 2024-01-15

# List stored posts
poetry run nsp list-posts --limit 10

# Launch data exploration notebook
poetry run nsp notebook
```

### Code Quality
```bash
# Format code with ruff
poetry run ruff format .

# Lint and fix code issues
poetry run ruff check . --fix

# Type checking with ty (alpha version)
poetry run ty check src/
```

### Search Tools
```bash
# Fast code search with ag (The Silver Searcher) - preferred for complex searches
ag "pattern" --python  # Search in Python files only
ag "pattern" src/       # Search in specific directory
ag -l "pattern"         # List matching files only

# Alternative: ripgrep (rg) - also very fast
rg "pattern" --type py  # Search in Python files
rg "pattern" src/       # Search in specific directory
```

## Architecture

The project follows a phased implementation approach (see `plans/phases_overview.md`):

1. **Phase 1** (Completed): Core infrastructure with Pydantic models, R2 storage interface, and logging
2. **Phase 2** (Completed): Bluesky integration using atproto SDK
3. **Phase 2.5** (Completed): CLI tools and data exploration with typer and marimo
4. **Phase 2.6** (Completed): Configurable search queries with YAML configuration and Lucene syntax
5. **Phase 3**: Content processing with Anthropic API
6. **Phase 4**: Data storage in Parquet format
7. **Phase 5**: HTML report generation
8. **Phase 6**: Automated Bluesky publishing
9. **Phase 7**: GitHub Actions automation
10. **Phase 8**: Enhancements and optimization

### Key Components

- **Data Models**: Pydantic models for posts and article evaluations with strict validation
- **Storage**: Cloudflare R2 interface using boto3 (S3-compatible) + Local stage-based storage
- **Configuration**: Environment-based settings using pydantic-settings
- **Stage-Based Processing**: Individual markdown files for fault-tolerant processing
- **URL Expansion**: Automatically resolves shortened URLs (bit.ly, tinyurl, youtu.be, etc.) to final destinations
- **Data Formats**: 
  - Legacy: Daily Parquet files organized as `data/YYYY/MM/DD/posts.parquet`
  - New: Individual markdown files in `stages/{stage_name}/YYYY-MM-DD/*.md`
- **Reports**: HTML reports stored as `reports/YYYY/MM/DD/report.html`

### Stage-Based Directory Structure

```
stages/
├── collect/
│   └── 2024-12-06/
│       ├── post_abc123.md
│       ├── post_def456.md
│       └── ...
├── fetch/
│   └── 2024-12-06/
│       ├── url_hash1.md
│       ├── url_hash2.md
│       └── ...
├── evaluate/
│   └── 2024-12-06/
│       ├── url_hash1.md  # enhanced with evaluation
│       ├── url_hash2.md
│       └── ...
└── report/
    └── 2024-12-06/
        ├── report_meta.md
        └── report.html
```

### Testing Strategy

- TDD approach with 90%+ coverage target
- Property-based testing using Hypothesis for data validation
- Mocked external services (R2, Bluesky, Anthropic) for testing
- Integration tests using moto for AWS/S3 mocking

## Project Status

Phase 2.6 completed. The project now has:
- Complete Bluesky integration with configurable search queries
- YAML-based search configuration with include/exclude terms and Lucene syntax  
- CLI tools built with Click for operational tasks with search definition support
- Interactive data exploration notebook with marimo
- Query validation and configuration management tools
- Rich console formatting and comprehensive error handling

Next phase: Content processing with Anthropic API integration as outlined in the phases overview.