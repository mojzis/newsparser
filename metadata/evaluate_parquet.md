# Evaluate Stage Parquet File Documentation

## Overview

The evaluate stage parquet files contain AI-powered evaluations of articles found in Bluesky posts. These files are generated daily and contain the last 7 days of evaluated content, organized by the date when the export was run.

**File Pattern**: `parquet/evaluate/by-run-date/{YYYY-MM-DD}_last_7_days.parquet`

## General Description

This dataset contains evaluation results from analyzing fetched articles using the Anthropic API. Each record represents an article that was successfully fetched and then evaluated for relevance to MCP (Model Context Protocol) and other criteria. The evaluation includes content classification, quality scoring, summaries, and extracted metadata. Only successfully fetched URLs are evaluated.

## Column Definitions

### Core Evaluation Results

| Column | Type | Description |
|--------|------|-------------|
| `url` | string | The article URL that was evaluated |
| `is_mcp_related` | boolean | Whether the article is related to MCP (Model Context Protocol) |
| `relevance_score` | float64 | Relevance score from 0.0 to 1.0 (1.0 = highly relevant) |
| `summary` | string | Brief summary of the article (10-500 characters) |
| `perex` | string | Witty, engaging summary for display (10-200 characters) |
| `key_topics` | list[string] | Key topics discussed in the article |

### Content Classification

| Column | Type | Description |
|--------|------|-------------|
| `content_type` | string/category | Type of content: "video", "newsletter", "article", "blog post", "product update", or "invite" |
| `language` | string | Language code of the content (e.g., "en", "es", "fr", "ja") |

### Article Metadata

| Column | Type | Description |
|--------|------|-------------|
| `title` | string (nullable) | Article title |
| `author` | string (nullable) | Article author |
| `medium` | string (nullable) | Publication medium/platform |
| `domain` | string | Domain of the article (e.g., "example.com") |
| `published_date` | datetime (nullable) | When the article was published |

### Processing Metadata

| Column | Type | Description |
|--------|------|-------------|
| `evaluated_at` | datetime (UTC) | Timestamp when the evaluation was performed |
| `word_count` | int64 | Number of words in the article |
| `truncated` | boolean | Whether content was truncated before evaluation (for very long articles) |
| `error` | string (nullable) | Error message if evaluation failed |

### File Metadata

| Column | Type | Description |
|--------|------|-------------|
| `_file_path` | string | Source markdown file path where this record was stored |
| `_file_name` | string | Source markdown filename (e.g., "url_hash123.md") |

## Data Notes

- **Evaluation Model**: Uses Anthropic's Claude API to analyze article content
- **Relevance Scoring**: Based on content analysis, not just keyword matching
- **Content Types**: Automatically detected based on content patterns and metadata
- **Language Detection**: More accurate than URL fetch stage as it's based on full content analysis
- **Truncation**: Very long articles may be truncated to fit API limits, indicated by the `truncated` flag
- **Key Topics**: Extracted topics are normalized and may include technical terms, product names, and concepts
- **Perex**: Designed to be an engaging, tweet-length summary suitable for social media sharing
- **Published Date**: Extracted when available from article metadata, may be null for some content

## Usage Examples

```python
import pandas as pd

# Load the parquet file
df = pd.read_parquet('parquet/evaluate/by-run-date/2024-01-15_last_7_days.parquet')

# Get MCP-related articles
mcp_articles = df[df['is_mcp_related'] == True]

# Find highly relevant content
highly_relevant = df[df['relevance_score'] > 0.8]

# Analyze by content type
content_type_counts = df['content_type'].value_counts()

# Get articles by language
english_articles = df[df['language'] == 'en']

# Find long-form content
long_articles = df[df['word_count'] > 2000]

# Extract articles with specific topics
ai_articles = df[df['key_topics'].apply(lambda topics: 'artificial intelligence' in [t.lower() for t in topics])]
```

## Relationship to Other Stages

This dataset builds upon the fetch stage results. Each record here corresponds to a successfully fetched URL from the fetch stage. URLs that failed to fetch or had errors will not appear in this dataset. The evaluation adds semantic understanding and classification to the raw content extracted during the fetch stage.