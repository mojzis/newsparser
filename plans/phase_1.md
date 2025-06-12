# Phase 1: Core Infrastructure & Data Models

## Overview
Phase 1 establishes the foundational components of the Bluesky MCP Monitor system, including data models, storage interfaces, environment configuration, and logging infrastructure for local development.

## Goals
- Define clear and validated data structures using Pydantic
- Set up reliable Cloudflare R2 storage interface
- Configure local development environment
- Implement comprehensive logging for monitoring and debugging

## Implementation Plan

### 1. Project Structure Setup
```
newsparser/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── post.py          # Bluesky post models
│   │   ├── article.py       # Article evaluation models
│   │   └── common.py        # Shared types and utilities
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── r2_client.py     # Cloudflare R2 interface
│   │   └── file_manager.py  # File path utilities
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py      # Configuration management
│   └── utils/
│       ├── __init__.py
│       └── logging.py       # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_models/
│   ├── test_storage/
│   └── test_utils/
├── pyproject.toml           # Poetry configuration
├── poetry.lock
├── pytest.ini
└── .env.example
```

### 2. Data Models (Pydantic)

#### Post Model
- Define BlueskyPost model with fields: id, author, content, created_at, links, engagement_metrics
- EngagementMetrics sub-model with likes, reposts, replies counts
- Validation for non-empty content and positive engagement metrics
- Support for multiple article links per post

#### Article Model
- ArticleEvaluation model with url, title, content_summary, relevance_score, key_topics, evaluation_timestamp
- Relevance score bounded between 0.0 and 1.0
- Content summary with maximum length constraint
- Key topics as a non-empty list of strings

### 3. Cloudflare R2 Interface

#### R2 Client
- S3-compatible client using boto3 with Cloudflare R2 endpoints
- Core operations: upload_file, download_file, file_exists, list_files
- Proper error handling and retry logic
- Support for both binary and text file operations
- Path management for organized storage structure

#### File Manager
- Utility functions for generating consistent file paths
- Date-based directory structure (data/YYYY/MM/DD/)
- Support for different file types (parquet, html, json)
- Path validation and sanitization

### 4. Configuration Management

#### Settings
- Pydantic Settings class for environment variable management
- Required R2 credentials and configuration
- Optional placeholders for future integrations (Bluesky, Anthropic)
- Application-level settings (log level, environment)
- Support for .env file in local development

### 5. Logging Framework

#### Logging Configuration
- Structured logging with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Console output with timestamp, logger name, level, and message
- Logger factory function for consistent setup across modules
- Support for module-specific loggers
- Configuration through settings

## Testing Strategy

### Unit Tests
- **Models**: Validate all Pydantic models with edge cases
- **Storage**: Mock boto3 client for R2 operations
- **Configuration**: Test settings loading and validation
- **Logging**: Verify proper logger setup

### Integration Tests
- R2 client with localstack or moto for S3 mocking
- End-to-end file upload/download operations
- Configuration loading from environment variables

### Test Coverage Goals
- Minimum 90% coverage for Phase 1 components
- 100% coverage for data validation logic
- Property-based testing for model validation using Hypothesis

## Dependencies (Poetry)

### Core Dependencies
- pydantic: Data validation and settings management
- pydantic-settings: Environment variable configuration
- boto3: AWS SDK for Cloudflare R2 (S3-compatible)
- pandas: Data manipulation (for future phases)
- pyarrow: Parquet file support

### Development Dependencies
- pytest: Testing framework
- pytest-asyncio: Async test support
- pytest-mock: Mocking utilities
- pytest-cov: Coverage reporting
- moto: AWS service mocking
- hypothesis: Property-based testing
- black: Code formatting
- ruff: Linting
- mypy: Type checking

## Deliverables
1. Complete project structure with all Phase 1 modules
2. Fully tested data models with validation
3. Working R2 storage interface with error handling
4. Local development environment configuration
5. Comprehensive logging setup
6. 90%+ test coverage for all Phase 1 components

## Success Criteria
- All Pydantic models validate data correctly
- R2 client can upload/download files successfully
- Local environment runs without configuration issues
- Logging provides clear visibility into system operations
- Tests pass with high coverage
- Code follows Python best practices and is well-documented

## Next Steps
After Phase 1 completion, we'll be ready to:
- Integrate with Bluesky API (Phase 2)
- Implement content processing pipeline (Phase 3)
- Begin storing daily data in Parquet format (Phase 4)
- Add GitHub Actions for automation (future phase)