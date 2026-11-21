# Fetch Stage Parquet File Documentation

## Overview

The fetch stage parquet files contain results from fetching and extracting content from URLs found in collected Bluesky posts. These files are generated daily and contain the last 7 days of fetched URLs, organized by the date when the export was run.

**File Pattern**: `parquet/fetch/by-run-date/{YYYY-MM-DD}_last_7_days.parquet`

## General Description

This dataset captures the results of attempting to fetch and extract content from URLs shared in Bluesky posts. Each record represents one unique URL that was discovered in collected posts. The fetch process uses web scraping to extract article content, metadata, and convert HTML to clean text for further analysis. URLs that fail to fetch include error information for debugging.

## Column Definitions

### Core Fetch Information

| Column | Type | Description |
|--------|------|-------------|
| `url` | string | The URL that was fetched |
| `fetched_at` | datetime (UTC) | Timestamp when the fetch operation was performed |
| `fetch_status` | string/category | Status of fetch operation: "success" or "error" |
| `stage` | string | Processing stage (always "fetched" for this dataset) |

### Content Metadata (Success Cases)

| Column | Type | Description |
|--------|------|-------------|
| `word_count` | int64 (nullable) | Number of words in the extracted article content |
| `title` | string (nullable) | Article title extracted from the page |
| `author` | string (nullable) | Article author if detected |
| `domain` | string | Domain name extracted from the URL (e.g., "example.com") |
| `medium` | string (nullable) | Publication medium/platform if detected |
| `language` | string (nullable) | Detected language of the content |
| `extraction_timestamp` | datetime (nullable) | When content extraction was completed |

### Error Information (Failed Cases)

| Column | Type | Description |
|--------|------|-------------|
| `error_type` | string (nullable) | Category of error encountered (e.g., "HTTPError", "Timeout") |
| `error_message` | string (nullable) | Detailed error message for debugging |

### Post Relationship Fields

| Column | Type | Description |
|--------|------|-------------|
| `found_in_posts` | list[string] | List of post IDs where this URL was found |
| `found_in_posts_str` | string (nullable) | Comma-separated string of post IDs (for easier querying) |
| `found_in_posts_count` | int64 | Number of posts that contained this URL |

### Metadata Fields

| Column | Type | Description |
|--------|------|-------------|
| `_file_path` | string | Source markdown file path where this record was stored |
| `_file_name` | string | Source markdown filename (e.g., "url_hash123.md") |

## Data Notes

- **URL Deduplication**: Each unique URL is fetched only once, even if it appears in multiple posts
- **URL Expansion**: Shortened URLs (bit.ly, tinyurl, etc.) are automatically expanded to their final destinations
- **Permanent Failures**: HTTP errors like 403 (Forbidden), 404 (Not Found), and 410 (Gone) are not retried
- **Content Extraction**: Uses intelligent extraction to get clean article text, removing navigation, ads, and other non-content elements
- **Domain Field**: Always populated, extracted from the URL even if fetch fails
- **Word Count**: Only available for successfully fetched content
- **Language Detection**: Performed on the extracted content, may differ from the language of posts linking to it

## Usage Examples

```python
import pandas as pd

# Load the parquet file
df = pd.read_parquet('parquet/fetch/by-run-date/2024-01-15_last_7_days.parquet')

# Get successfully fetched articles
successful = df[df['fetch_status'] == 'success']

# Find long-form content
long_articles = df[df['word_count'] > 1000]

# Analyze errors
errors = df[df['fetch_status'] == 'error']
error_summary = errors.groupby('error_type').size()

# Find most shared URLs
popular_urls = df.nlargest(10, 'found_in_posts_count')

# Filter by domain
github_links = df[df['domain'].str.contains('github.com')]
```