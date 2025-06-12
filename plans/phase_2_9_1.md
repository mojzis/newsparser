# Phase 2.9.1: URL Extraction and Deduplication

## Overview
Extract unique URLs from Bluesky posts and maintain a centralized URL registry file on R2 to ensure we only process each URL once across all data collection runs.

## Objectives
- Extract URLs from all collected posts
- Maintain a global URL registry on R2
- Track URL metadata (first seen, publish date, source post)
- Ensure URL uniqueness across all collection runs

## URL Registry Structure
Single Parquet file: `urls/url_registry.parquet`

Schema:
- url: string (primary key)
- first_seen: timestamp
- published_date: timestamp (nullable)
- first_post_id: string
- first_post_author: string
- times_seen: int32
- last_updated: timestamp
```

## Tasks

### Task 1: URL Registry Model (1.1)
- Create Pydantic model for URL registry
- Add URL entry model with metadata fields
- Keep it simple - just essential fields
- **Command**: `nsp url-stats` - Show registry statistics

### Task 2: R2 URL Registry Manager (2.1)
- Add methods to R2Storage for URL registry operations
- Download registry at start of collection
- Upload registry after updates
- Handle missing registry (first run)
- **Command**: `nsp url-sync` - Download/upload registry manually

### Task 3: URL Extraction Enhancement (3.1)
- Enhance BlueskyDataCollector to extract URLs during collection
- Check against registry before adding
- Update registry with new URLs only
- Store registry updates after collection
- **Command**: `nsp collect --track-urls` - Enable URL tracking

### Task 4: URL Listing and Search (4.1)
- Add CLI commands to explore URL registry
- List all URLs with metadata
- Search URLs by domain
- Show URL statistics
- **Command**: `nsp url-list --domain example.com` - List/search URLs

## Implementation Notes
- Load URL registry into pandas DataFrame for fast lookups
- Use parquet for efficient storage and schema enforcement
- Simple deduplication using DataFrame operations
- Don't extract publish dates from articles yet (Phase 3)
- Focus on collecting URL occurrence data

## Success Criteria
- URLs extracted from all posts during collection
- Registry maintained on R2 with proper sync
- No duplicate URL processing across runs
- CLI commands to inspect registry

## Future Enhancements (NOT NOW)
- Extract publish date from article content
- Track all posts mentioning each URL
- URL categorization
- Parquet format for better performance
- URL validation and normalization