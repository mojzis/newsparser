# Phase 3: Content Processing Pipeline

## Overview
Phase 3 focuses on implementing article extraction and AI evaluation using the Anthropic API. This phase builds on the Bluesky data collection from Phase 2 and adds intelligent content processing to evaluate the relevance and quality of linked articles.

## Objectives
- Extract articles from links found in Bluesky posts
- Evaluate article content for MCP relevance using Anthropic API
- Generate summaries and topic identification
- Implement robust error handling and rate limiting
- Store processed article data alongside post data

## Architecture

### Component Overview
```
BlueskyPost (from Phase 2)
    ↓
LinkExtractor
    ↓
ArticleFetcher (httpx)
    ↓
ContentExtractor
    ↓
AnthropicEvaluator
    ↓
ArticleEvaluation (stored to R2)
```

### Data Flow
1. **Input**: BlueskyPost objects with extracted links
2. **Article Fetching**: Download content from URLs using httpx
3. **Content Extraction**: Parse HTML and extract meaningful text
4. **AI Evaluation**: Send to Anthropic API for relevance scoring and analysis
5. **Output**: ArticleEvaluation objects for storage

## Technical Implementation

### 1. Dependencies
Add to `pyproject.toml`:
```toml
httpx = "^0.25.0"              # HTTP client for article fetching
beautifulsoup4 = "^4.12.0"     # HTML parsing
anthropic = "^0.34.0"          # Anthropic API client
readability-lxml = "^0.8.1"    # Content extraction
html2text = "^2020.1.16"       # HTML to Markdown conversion
```

### 2. Data Models

#### ArticleEvaluation Model
```python
class ArticleEvaluation(BaseModel):
    url: HttpUrl
    title: str | None = None
    content_summary: str = Field(max_length=1000)
    relevance_score: float = Field(ge=0.0, le=1.0)
    key_topics: list[str] = Field(default_factory=list)
    evaluation_timestamp: datetime
    extraction_success: bool
    evaluation_success: bool
    error_message: str | None = None
    
    # Metadata
    word_count: int | None = None
    language: str | None = None
    domain: str
```

#### ProcessingResult Model
```python
class ProcessingResult(BaseModel):
    post_id: str
    articles: list[ArticleEvaluation]
    processing_timestamp: datetime
    total_links: int
    successful_extractions: int
    successful_evaluations: int
```

### 3. Core Components

#### ArticleFetcher
```python
class ArticleFetcher:
    """Fetches article content from URLs with error handling."""
    
    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.max_retries = max_retries
    
    async def fetch_article(self, url: str) -> ArticleContent | None:
        """Fetch and extract content from URL."""
        # Implementation with retry logic and error handling
```

#### ContentExtractor  
```python
class ContentExtractor:
    """Extracts and converts content from HTML to Markdown."""
    
    def extract_content(self, html: str, url: str) -> ExtractedContent:
        """Extract title, content as Markdown, and metadata from HTML."""
        # Implementation using readability-lxml and html2text for Markdown conversion
```

#### AnthropicEvaluator
```python
class AnthropicEvaluator:
    """Evaluates article content using Anthropic API."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def evaluate_article(self, content: ExtractedContent) -> EvaluationResult:
        """Evaluate article for MCP relevance and extract insights."""
        # Implementation with CSV response parsing for token efficiency
```

#### ContentProcessor
```python
class ContentProcessor:
    """Main orchestrator for content processing pipeline."""
    
    def __init__(self, settings: Settings):
        self.fetcher = ArticleFetcher()
        self.extractor = ContentExtractor()
        self.evaluator = AnthropicEvaluator(settings.anthropic_api_key)
        
    async def process_post(self, post: BlueskyPost) -> ProcessingResult:
        """Process all links in a post through the full pipeline."""
```

### 4. Anthropic API Integration

#### Evaluation Prompt Template
```python
EVALUATION_PROMPT = """
Analyze this article for relevance to Model Context Protocol (MCP):

Title: {title}
Content (Markdown): {content}

Please evaluate and respond in CSV format (no headers):
relevance_score,topic1,topic2,topic3,summary

Requirements:
- relevance_score: Float 0.0-1.0 
- topic1,topic2,topic3: Main topics (use "none" if <3 topics)
- summary: Concise summary (max 250 words)
- include text in ""

Example: 0.85,"mcp","ai-tools","integration","Article discusses MCP implementation for AI tools..."
"""
```

#### Rate Limiting Strategy
- Implement exponential backoff for API calls
- Respect Anthropic API rate limits (configurable)
- Queue management for batch processing
- Circuit breaker pattern for API failures

### 5. Error Handling

#### Failure Categories
1. **Network Errors**: Timeout, connection issues
2. **Content Extraction Errors**: Invalid HTML, blocked content
3. **API Errors**: Rate limits, authentication, service unavailable
4. **Validation Errors**: Invalid content format, parsing failures

#### Recovery Strategies
- Retry with exponential backoff
- Fallback to basic extraction methods
- Graceful degradation (store partial results)
- Error aggregation and reporting

### 6. Storage Integration

#### File Structure Extension
```
data/YYYY/MM/DD/
├── posts.json              # Raw posts (Phase 2)
├── articles.json           # Article evaluations (Phase 3)
└── processing_summary.json # Daily processing stats
```

## Implementation Tasks

### Task 1: Core Infrastructure
- [x] Create article fetching client with httpx
- [x] Implement content extraction using readability
- [x] Add HTML to Markdown conversion with html2text
- [x] Set up basic error handling and logging
- [x] Create unit tests for core components

### Task 1.1: CLI Command for Content Processing
- [x] Add CLI command to test article fetching and extraction
- [x] Support single URL processing with output display  
- [x] Show fetched content, extracted markdown, and metadata
- [x] Handle errors gracefully with user-friendly messages
**Command**: `nsp process-article <url> [--show-content] [--verbose]`

### Task 2: Anthropic Integration
- [ ] Add anthropic dependency and client setup
- [ ] Implement evaluation prompts with CSV response format
- [ ] Create CSV response parsing and validation
- [ ] Create rate limiting and retry logic
- [ ] Test API integration with mock responses

### Task 3: Data Models & Validation
- [ ] Define ArticleEvaluation Pydantic model
- [ ] Create ProcessingResult model
- [ ] Implement data validation and serialization
- [ ] Add model tests with property-based testing

### Task 4: Pipeline Orchestration
- [ ] Create ContentProcessor main class
- [ ] Implement end-to-end processing workflow
- [ ] Add batch processing capabilities
- [ ] Create integration tests

### Task 5: Storage & Persistence
- [ ] Extend R2Client for article data storage
- [ ] Implement daily file organization
- [ ] Add data retrieval and querying
- [ ] Create storage tests

### Task 6: CLI Integration
- [ ] Add process command to CLI
- [ ] Implement processing status and monitoring
- [ ] Add data exploration for articles
- [ ] Update notebook with article analysis

### Task 7: Error Handling & Monitoring
- [ ] Implement comprehensive error handling
- [ ] Add processing metrics and statistics
- [ ] Create error reporting and logging
- [ ] Build retry and recovery mechanisms

## Configuration

### Settings Extension
```python
class Settings(BaseSettings):
    # Existing settings...
    
    # Anthropic API
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-haiku-20240307")
    anthropic_max_tokens: int = Field(default=1000)
    
    # Article Processing
    article_fetch_timeout: float = Field(default=30.0)
    article_max_retries: int = Field(default=3)
    max_concurrent_requests: int = Field(default=5)
    
    # Content Extraction
    min_content_length: int = Field(default=100)
    max_content_length: int = Field(default=50000)
```

## Testing Strategy

### Unit Tests
- ArticleFetcher with mocked HTTP responses
- ContentExtractor with sample HTML files
- AnthropicEvaluator with mocked API responses
- Data model validation and serialization

### Integration Tests
- End-to-end pipeline with real content
- API integration with rate limiting
- Storage operations with moto mocking
- Error handling scenarios

### Performance Tests
- Concurrent processing load testing
- Memory usage monitoring
- API rate limit validation

## Success Criteria

### Functional Requirements
- Successfully fetch and process articles from Bluesky post links
- Generate accurate relevance scores using Anthropic API
- Handle errors gracefully with appropriate fallbacks
- Store processed data in structured format

### Performance Requirements
- Process 100 articles in under 10 minutes
- Maintain <5% failure rate for article fetching
- Respect Anthropic API rate limits without errors
- Use <500MB memory during processing

### Quality Requirements
- 90%+ test coverage for new components
- Clear error messages and logging
- Comprehensive documentation
- Robust error recovery

## Risk Mitigation

### API Dependencies
- **Risk**: Anthropic API rate limits or outages
- **Mitigation**: Implement retry logic, fallback processing, queue management

### Content Extraction
- **Risk**: Websites blocking automated access
- **Mitigation**: Respect robots.txt, implement user agent rotation, graceful fallbacks

### Data Quality
- **Risk**: Poor content extraction affecting AI evaluation
- **Mitigation**: Content validation, extraction quality metrics, manual review tools

### Cost Management
- **Risk**: High Anthropic API costs
- **Mitigation**: Content filtering, batch processing, model selection optimization

## Next Steps
Upon completion of Phase 3, the system will have intelligent content processing capabilities. Phase 4 will focus on structured data storage using Parquet files for efficient querying and analysis.