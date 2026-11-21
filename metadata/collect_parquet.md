# Collect Stage Parquet File Documentation

## Overview

The collect stage parquet files contain Bluesky posts that match configured search criteria. These files are generated daily and contain the last 7 days of collected posts, organized by the date when the export was run.

**File Pattern**: `parquet/collect/by-run-date/{YYYY-MM-DD}_last_7_days.parquet`

## General Description

This dataset captures social media posts from Bluesky that mention or relate to MCP (Model Context Protocol) or other configured search terms. Each record represents a single post with its content, metadata, engagement metrics, and thread relationship information. Posts are collected via the Bluesky API and may include expanded thread context when thread collection is enabled.

## Column Definitions

### Core Post Information

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Unique identifier for the post (AT Protocol URI format) |
| `author` | string | Author handle/username (e.g., "user.bsky.social") |
| `content` | string | Full text content of the post |
| `created_at` | datetime (UTC) | Timestamp when the post was created on Bluesky |

### Extracted Data

| Column | Type | Description |
|--------|------|-------------|
| `links` | list[string] | URLs extracted from the post content |
| `tags` | list[string] | Hashtags extracted from post content (lowercase, without #) |
| `language` | string/category | Detected language type based on character analysis (e.g., "latin", "cjk", "arabic") |

### Engagement Metrics (Flattened)

| Column | Type | Description |
|--------|------|-------------|
| `engagement_metrics_likes` | int64 | Number of likes on the post |
| `engagement_metrics_reposts` | int64 | Number of reposts/reblogs |
| `engagement_metrics_replies` | int64 | Number of replies to the post |

### Thread Relationship Fields

| Column | Type | Description |
|--------|------|-------------|
| `thread_root_uri` | string (nullable) | URI of the root post in this thread |
| `thread_position` | string/category (nullable) | Position within thread: "root", "reply", or "nested_reply" |
| `parent_post_uri` | string (nullable) | URI of the direct parent post (for replies) |
| `thread_depth` | int64 (nullable) | Nesting level within the thread (0=root, 1=direct reply, etc.) |

### Metadata Fields

| Column | Type | Description |
|--------|------|-------------|
| `_file_path` | string | Source markdown file path where this record was stored |
| `_file_name` | string | Source markdown filename (e.g., "post_abc123.md") |

## Data Notes

- **Language Detection**: Uses character-based analysis to categorize text into language families (Latin, CJK, Arabic, etc.) rather than specific languages
- **Thread Collection**: When enabled, the collector will traverse up and down thread hierarchies to capture complete conversations
- **URL Expansion**: Links may be expanded from shortened URLs to their final destinations if URL expansion is enabled
- **Engagement Metrics**: Captured at collection time and may not reflect current values
- **Missing Content**: Some records may show "Content stored in markdown body" as a placeholder when loaded from markdown files

## Usage Examples

```python
import pandas as pd

# Load the parquet file
df = pd.read_parquet('parquet/collect/by-run-date/2024-01-15_last_7_days.parquet')

# Filter for posts with high engagement
high_engagement = df[df['engagement_metrics_likes'] > 10]

# Find posts in specific threads
thread_posts = df[df['thread_root_uri'].notna()]

# Get posts by language type
latin_posts = df[df['language'] == 'latin']
```