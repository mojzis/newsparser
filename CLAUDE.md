# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

When working on this project, please maintain a neutral, professional tone:
- Avoid exclamation marks and overly enthusiastic language
- Skip flattery and proclamations like "you are absolutely right"
- Focus on factual, concise responses
- Use simple confirmations like "done" or "completed" rather than celebratory language
- Provide technical details when relevant, but keep explanations brief

## Code Review

When you finish a coding task in this repo, run the `python-review` skill over the changed Python before reporting done.

Exception: if you are a subagent inside an orchestrated workflow (cf/cml — e.g. a dev, check, or fix agent), do NOT run the review skill. Those workflows have a dedicated review step; running it in other steps duplicates the review and slows the run.

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
- **For marimo notebooks**: See `MARIMO_RULES.md` for specific marimo conventions

### 🚨 CRITICAL MARIMO RULE - NEVER VIOLATE

**BEFORE writing ANY marimo cell, check:**
1. Are you putting `mo.md()`, `mo.ui.table()`, or ANY display function inside `if`, `try`, `for`, `while`, or `with` blocks?
2. If YES → STOP! You must prepare content inside control blocks, then display OUTSIDE them.

**Template pattern:**
```python
@app.cell
def _(mo):
    # Prepare content inside control blocks
    if condition:
        content = "success message"
    else:
        content = "error message"
    
    # Display OUTSIDE control blocks, BEFORE return
    mo.md(content)
    return
```

**Use notebooks/TEMPLATE.py as starting point for new marimo notebooks.**

## Project Overview

This is the Bluesky MCP Monitor project - a daily service that parses Bluesky for "mcp" mentions, evaluates content using Anthropic API, stores data in Parquet files on Cloudflare R2, and generates HTML reports with automated Bluesky posting.

## CLI Tool

The project provides a command-line interface accessible via the `nsp` command (short for "newsparser"). After installation with uv (`uv sync`), all operations are performed using:

```bash
uv run nsp <command> [options]
```

The CLI provides commands for data collection, search configuration, data exploration, and operational tasks.

## Commands

### Development Setup
```bash
# Install dependencies (runtime + dev; the dev group syncs by default)
uv sync

# Run a command in the project environment
uv run <command>

# Or activate the virtualenv directly
source .venv/bin/activate
```

### Dependency Management

IMPORTANT: Always use uv to add new dependencies:
```bash
# Add a runtime dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Add with version constraints
uv add "package-name>=1.0,<2.0"

# Update the lock file to latest compatible versions
uv lock --upgrade
```

Never manually edit pyproject.toml to add dependencies. Using `uv add` ensures:
- Latest compatible versions are installed
- Lock file is properly updated
- Dependency resolution is handled correctly
- Version constraints are properly set

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_models/test_post.py

# Run tests matching pattern
uv run pytest -k "test_post"
```

### CLI Commands (Phase 2.5+)

The CLI has been restructured for clarity:
- **`nsp`** - New stage-based architecture (recommended)
- **`onsp`** - Legacy commands (for backward compatibility)

#### Stage-Based Commands (Primary Interface)
```bash
# Top-level convenience commands
uv run nsp collect --date 2024-01-15 --max-posts 100 --search mcp_tag
uv run nsp collect --date 2024-01-15 --no-expand-urls  # Skip URL expansion
uv run nsp fetch --date 2024-01-15
uv run nsp evaluate --date 2024-01-15
uv run nsp report --date 2024-01-15

# Run all stages in sequence (most common usage)
uv run nsp run-all --date 2024-01-15 --max-posts 100 --search mcp_tag
uv run nsp run-all --date 2024-01-15 --no-expand-urls  # Skip URL expansion

# Show stage status
uv run nsp status --date 2024-01-15

# Detailed stage management (via 'stages' subcommand)
uv run nsp stages collect --date 2024-01-15 --max-posts 100 --search mcp_tag
uv run nsp stages run-all --date 2024-01-15 --max-posts 100 --search mcp_tag
uv run nsp stages status --date 2024-01-15          # Show stage progression
uv run nsp stages list-files collect --limit 10    # List files in stage
uv run nsp stages clean fetch --date 2024-01-15    # Clean stage data
```

#### Legacy Commands (Backward Compatibility)
```bash
# Access legacy functionality via 'onsp' command
uv run onsp collect --date 2024-01-15 --search mcp_tools --max-posts 200
uv run onsp list-searches
uv run onsp validate-config
uv run onsp status --date 2024-01-15
uv run onsp list-posts --limit 10
uv run onsp notebook
```

### Code Quality
```bash
# Format code with ruff
uv run ruff format .

# Lint and fix code issues
uv run ruff check . --fix

# Type checking with ty (alpha version)
uv run ty check src/
```

### Code Search Guidelines

When searching for code in this project:
- **Always search within the `src/` directory** to avoid irrelevant results from data, content, and output directories
- Use the Grep tool with `path: "src"` parameter to limit scope
- Use the Glob tool with patterns like `src/**/*.py` for file discovery

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

### Key Components

- **Data Models**: Pydantic models for posts and article evaluations with strict validation
- **Storage**: Cloudflare R2 interface using boto3 (S3-compatible) + Local stage-based storage
- **Configuration**: Environment-based settings using pydantic-settings
- **Stage-Based Processing**: Individual markdown files for fault-tolerant processing
- **URL Expansion**: Automatically resolves shortened URLs (bit.ly, tinyurl, youtu.be, etc.) to final destinations
- **Intelligent Retry Logic**: Permanent HTTP errors (403, 404, 410) are not retried, saving time and resources
- **Data Formats**: 
  - Legacy: Daily Parquet files organized as `data/YYYY/MM/DD/posts.parquet`
  - New: Individual markdown files in `stages/{stage_name}/YYYY-MM-DD/*.md`
- **Reports**: HTML reports stored as `reports/YYYY/MM/DD/report.html`
- **Notebooks**: Marimo notebooks for analytics and statistics in `notebooks/` directory

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

