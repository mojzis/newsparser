# Bluesky MCP Monitor - Revised Implementation Phases

## Overview
This document outlines the revised implementation phases for the Bluesky MCP Monitor project. The system will parse Bluesky for "mcp" mentions, evaluate content using Anthropic API, store data in Parquet files on Cloudflare R2, and generate HTML reports with automated Bluesky posting.

## System Architecture
```
Bluesky API → Content Parser → Anthropic API → R2 Storage → Report Generator → Bluesky Publisher
```

## Technical Stack
- **Language**: Python 3.11+
- **Package Management**: Poetry
- **Bluesky**: atproto (official SDK)
- **HTTP Client**: httpx (article fetching)
- **Data Processing**: pandas, pyarrow
- **Storage**: boto3 (S3-compatible for Cloudflare R2)
- **HTML Generation**: Jinja2
- **Testing**: pytest, pytest-asyncio, pytest-mock, hypothesis
- **Configuration**: pydantic-settings

## Implementation Phases

### Phase 1: Core Infrastructure & Data Models
**Focus**: Local development foundation
- Set up project structure with Poetry dependency management
- Define Pydantic data models for posts and article evaluations
- Implement Cloudflare R2 storage interface using boto3
- Create configuration management with pydantic-settings
- Establish logging framework
- Write comprehensive unit tests with 90%+ coverage
- Create .env.example for local development

### Phase 2: Bluesky Integration
**Focus**: Reading and parsing Bluesky content
- Implement atproto client for authenticated access
- Create mention search functionality for "mcp" keywords
- Parse post content and extract links
- Handle rate limiting and pagination
- Implement retry logic and error handling
- Store raw post data for processing

### Phase 2.5: CLI Tools & Data Exploration
**Focus**: Developer tools and data visibility
- Create CLI commands for data collection operations (typer + rich)
- Implement interactive data exploration notebook (marimo)
- Add data export capabilities (CSV, JSON, Parquet)
- Build status checking and post listing tools
- Enable direct data collection from notebook interface
- Provide rich console output with formatting and feedback

### Phase 2.6: Configurable Search Queries
**Focus**: Flexible search with include/exclude terms
- Implement YAML-based search configuration system
- Create Lucene query builder with boolean logic support
- Add hashtag and keyword exclusion capabilities
- Enhance CLI with search definition selection
- Support multiple search scenarios and sorting options
- Provide query validation and configuration management tools

### Phase 2.9: Language Detection
**Focus**: Character-based language detection for multilingual content filtering
- Implement Unicode character range analysis for language detection
- Add language field to BlueskyPost model with backward compatibility
- Create filtering capabilities to exclude non-Latin posts (>30% threshold)
- Enhance CLI and notebook tools with language statistics and filtering
- Provide configurable thresholds and language classification options
- Ensure seamless integration with existing data collection workflows

### Phase 3: Content Processing Pipeline
**Focus**: Article extraction and AI evaluation
- Implement article fetching from extracted links
- Create content extraction logic (handling various website formats)
- Integrate Anthropic API for content evaluation
- Develop relevance scoring algorithm
- Extract key topics and generate summaries
- Handle failed extractions gracefully

### Phase 4: Data Storage & Management
**Focus**: Structured data persistence
- Implement daily Parquet file generation
- Create data models for efficient storage
- Develop R2 upload/download operations
- Implement data validation and integrity checks
- Create file structure: `data/YYYY/MM/DD/posts.parquet`
- Build data retrieval and query functions

### Phase 5: Report Generation
**Focus**: HTML report creation
- Design Jinja2 templates for the homepage and daily reports
- Implement report data aggregation
- Create visualizations and statistics
- Generate summary insights
- Output to R2: `reports/YYYY/MM/DD/report.html`
- Include top posts, key themes, and trends

### Phase 6: Bluesky Publishing
**Focus**: Automated content posting
- Implement post composition from report data
- Create engaging summary format
- Handle Bluesky post length limits
- Implement posting via atproto
- Add link to full HTML report
- Error handling for failed posts

### Phase 7: Automation & Deployment
**Focus**: GitHub Actions and production deployment
- Set up GitHub Actions workflow for daily execution
- Configure cron schedule (9 AM UTC)
- Implement secrets management
- Add manual trigger capability
- Create error notifications via GitHub issues
- Set up monitoring and alerting

### Phase 8: Enhancement & Optimization
**Focus**: Performance and feature improvements
- Implement caching for frequently accessed data
- Add historical data analysis
- Create trend detection algorithms
- Optimize Anthropic API usage
- Add data export capabilities
- Implement performance monitoring

## Data Schema

### Post Structure
- id: Unique identifier
- author: Bluesky handle
- content: Post text
- created_at: Timestamp
- links: List of extracted URLs
- engagement_metrics: Dictionary with likes, reposts, replies

### Article Evaluation
- url: Article URL
- title: Extracted title
- content_summary: AI-generated summary (max 1000 chars)
- relevance_score: Float between 0.0 and 1.0
- key_topics: List of identified topics
- evaluation_timestamp: When evaluated

## Testing Strategy
- Test-Driven Development (TDD) approach
- Unit tests for all components
- Integration tests for external APIs (mocked)
- End-to-end pipeline tests
- Property-based testing for data validation
- Minimum 90% code coverage target

## Storage Structure (Cloudflare R2)
```
bucket/
├── data/
│   └── YYYY/
│       └── MM/
│           └── DD/
│               ├── posts.parquet
│               └── articles.parquet
└── reports/
    └── YYYY/
        └── MM/
            └── DD/
                └── report.html
```

## Success Metrics
- Daily successful execution rate > 99%
- Average processing time < 5 minutes
- Relevant content identification accuracy > 85%
- Zero data loss incidents
- Clear and actionable daily reports

## Risk Mitigation
- API rate limit handling
- Graceful degradation for failed components
- Data backup strategies
- Error alerting and monitoring
- Regular dependency updates

---

**Note**: This phased approach allows for incremental development with each phase delivering working functionality. Local development and testing are prioritized in early phases, with automation deferred to Phase 7.