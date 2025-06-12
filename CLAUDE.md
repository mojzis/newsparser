# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

When working on this project, please maintain a neutral, professional tone:
- Avoid exclamation marks and overly enthusiastic language
- Skip flattery and proclamations like "you are absolutely right"
- Focus on factual, concise responses
- Use simple confirmations like "done" or "completed" rather than celebratory language
- Provide technical details when relevant, but keep explanations brief

## Phase Planning Requirement

Before proceeding with any new phase or significant feature implementation:
1. Create a detailed phase plan document outlining all tasks and implementation steps
2. Document the plan in the `plans/` directory with proper naming (e.g., `phase_3.md`)
3. Update the `plans/phases_overview.md` with any new phases or modifications
4. Get user approval for the plan before beginning implementation
5. Document implementation progress and decisions in the phase-specific file

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
- **Storage**: Cloudflare R2 interface using boto3 (S3-compatible)
- **Configuration**: Environment-based settings using pydantic-settings
- **Data Format**: Daily Parquet files organized as `data/YYYY/MM/DD/posts.parquet`
- **Reports**: HTML reports stored as `reports/YYYY/MM/DD/report.html`

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