# Bluesky MCP Monitor - Project Specification

## Overview
Daily service that parses Bluesky for "mcp" mentions, evaluates content using Anthropic API, stores data in Parquet files on Cloudflare R2, and generates HTML reports with automated Bluesky posting.

## System Architecture
```
GitHub Actions (Daily) → Bluesky API → Content Parser → Anthropic API → R2 Storage → Report Generator → Bluesky Publisher
```

## Technical Stack
- **Runtime**: GitHub Actions (daily cron)
- **Language**: Python 3.11+
- **Bluesky**: atproto (official SDK)
- **HTTP Client**: httpx (article fetching)
- **Data Processing**: pandas, pyarrow
- **Storage**: boto3 (S3-compatible for Cloudflare R2)
- **HTML Generation**: Jinja2
- **Testing**: pytest, pytest-asyncio, pytest-mock
- **Configuration**: pydantic-settings

## Implementation Phases

### Phase 1: Core Infrastructure & Data Models
- Define Pydantic data structures for posts, articles, evaluations
- Set up Cloudflare R2 interface using boto3
- GitHub Actions environment setup
- Logging framework

### Phase 2: Bluesky Integration
- Implement atproto client for mention parsing
- Rate limiting and error handling
- Authentication management

### Phase 3: Content Processing Pipeline
- Article extraction from links
- Anthropic API integration for evaluation
- Content scoring and categorization

### Phase 4: Storage & Retrieval
- Daily Parquet file generation
- R2 operations and data validation
- File structure: `data/YYYY/MM/DD/posts.parquet`

### Phase 5: Report Generation
- HTML template system with Jinja2
- Daily summary compilation
- Output to R2: `reports/YYYY/MM/DD/report.html`

### Phase 6: Publishing & Automation
- Bluesky post composition via atproto
- GitHub Actions workflow completion
- Error handling and notifications

## Data Schema
```python
# Post structure
{
    "id": str,
    "author": str, 
    "content": str,
    "created_at": datetime,
    "links": List[str],
    "engagement_metrics": dict
}

# Article evaluation
{
    "url": str,
    "title": str,
    "content_summary": str,
    "relevance_score": float,
    "key_topics": List[str],
    "evaluation_timestamp": datetime
}
```

## Testing Requirements
- High test coverage with meaningful tests
- TDD approach for data validation, API clients, scoring algorithms
- Unit tests for components
- Integration tests for external APIs
- End-to-end pipeline testing with mocks
- Property-based testing for data validation

## GitHub Actions Configuration
- Daily execution at 9 AM UTC
- Manual trigger capability
- Secrets: Bluesky credentials, Anthropic API key, R2 credentials
- Error notifications via GitHub issues

## Storage Structure (Cloudflare R2)
- Daily data: `data/YYYY/MM/DD/posts.parquet`, `articles.parquet`
- Reports: `reports/YYYY/MM/DD/report.html`
- S3-compatible API using boto3

---

**Instructions for Claude Code**: Please build this system following the phased approach. Present detailed implementation plans before each major phase for confirmation. Prioritize meaningful test coverage and ask for confirmation on technical decisions. The system should be stateless and optimized for GitHub Actions execution.
