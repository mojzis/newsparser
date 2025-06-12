# Phase 4: Data Storage & Management

## Overview
Phase 4 focuses on transitioning from JSON to Parquet format for all data storage, enabling efficient querying and analysis of collected data. While we've already implemented Parquet storage for URL registry and evaluations, the posts data is still stored as JSON.

## Current Status

### Already Implemented ✅
- URL registry stored as Parquet (`urls/url_registry.parquet`)
- Article evaluations stored as Parquet (`data/YYYY/MM/DD/evaluations.parquet`)
- FileManager with proper path structure
- R2Client with upload/download capabilities

### Not Yet Implemented ❌
- Posts still stored as JSON (`data/YYYY/MM/DD/posts.json`)
- No unified data retrieval API
- No data validation layer
- No query optimization
- No data integrity checks

## Objectives
- Convert posts storage from JSON to Parquet format
- Implement efficient data retrieval and querying
- Add data validation and integrity checks
- Create unified data access layer
- Optimize for analytics and report generation

## Technical Implementation

### 1. Convert Posts Storage to Parquet

#### Update BlueskyDataCollector
```python
async def _store_posts(self, posts: list[BlueskyPost], target_date: date) -> bool:
    """Store posts as Parquet file instead of JSON."""
    # Convert posts to DataFrame
    posts_data = [post.model_dump() for post in posts]
    df = pd.DataFrame(posts_data)
    
    # Handle nested fields (links, tags, engagement_metrics)
    # Store as Parquet with proper schema
```

#### Schema Considerations
- Flatten engagement_metrics into separate columns
- Convert links list to separate table or JSON column
- Ensure datetime columns are properly typed
- Handle nullable fields appropriately

### 2. Data Models for Storage

#### Create Dedicated Storage Models
```python
class StoredPost(BaseModel):
    """Optimized model for Parquet storage."""
    id: str
    author: str
    content: str
    created_at: datetime
    language: str
    
    # Flattened engagement metrics
    likes_count: int
    reposts_count: int
    replies_count: int
    
    # Links as JSON string for Parquet compatibility
    links_json: str
    tags_json: str
```

### 3. Data Access Layer

#### Create DataStore Class
```python
class DataStore:
    """Unified data access for all stored data."""
    
    def __init__(self, r2_client: R2Client):
        self.r2_client = r2_client
    
    async def get_posts_for_date(self, target_date: date) -> pd.DataFrame:
        """Retrieve posts as DataFrame."""
    
    async def get_evaluations_for_date(self, target_date: date) -> pd.DataFrame:
        """Retrieve evaluations as DataFrame."""
    
    async def get_combined_data(self, target_date: date) -> pd.DataFrame:
        """Join posts with evaluations on URL."""
    
    async def query_posts(self, start_date: date, end_date: date, 
                         filters: dict) -> pd.DataFrame:
        """Query posts across date range with filters."""
```

### 4. Migration Strategy

#### Backward Compatibility
- Check for both `.json` and `.parquet` files
- Automatically convert JSON to Parquet on read
- Provide migration command to convert historical data

#### Migration Command
```bash
nsp migrate-to-parquet --start-date 2024-01-01 --end-date 2024-12-31
```

## Implementation Tasks

### Task 1: Update Posts Storage ✅
- [x] Modify `store_posts` to save as Parquet
- [x] Update `get_stored_posts` to read Parquet with JSON fallback
- [x] Handle nested data structures (links, tags, engagement_metrics as JSON strings)
- [x] Ensure proper datetime handling
- [x] Update tests to expect Parquet format

### Task 1.1: CLI Command for Migration
- [ ] Add migration command to convert JSON to Parquet
- [ ] Support date range selection
- [ ] Show progress during migration
- [ ] Verify data integrity after conversion
**Command**: `nsp migrate-to-parquet [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]`

### Task 2: Create Storage Models
- [ ] Define StoredPost model for Parquet
- [ ] Define StoredEvaluation model
- [ ] Create conversion methods from domain models
- [ ] Add validation for storage constraints
- [ ] Test model conversions

### Task 3: Implement Data Access Layer
- [ ] Create DataStore class
- [ ] Implement posts retrieval methods
- [ ] Implement evaluations retrieval methods
- [ ] Add join operations for combined data
- [ ] Create query builder for complex filters

### Task 4: Add Data Validation
- [ ] Implement schema validation on write
- [ ] Add data integrity checks
- [ ] Create validation reports
- [ ] Handle schema evolution
- [ ] Test edge cases

### Task 5: Query Optimization
- [ ] Add indexing strategy for common queries
- [ ] Implement data partitioning by date
- [ ] Create materialized views for reports
- [ ] Add caching layer for frequent queries
- [ ] Performance benchmarking

### Task 6: Update Existing Commands
- [ ] Update `list-posts` to use Parquet
- [ ] Update `status` command
- [ ] Update notebook to use new data layer
- [ ] Ensure backward compatibility
- [ ] Update documentation

## Data Schema

### Posts Parquet Schema
```
id: string (required)
author: string (required)
content: string (required)
created_at: timestamp (required)
language: string (required)
likes_count: int32 (required)
reposts_count: int32 (required)
replies_count: int32 (required)
links_json: string (nullable) # JSON array
tags_json: string (nullable) # JSON array
search_source: string (required) # Which search definition found this
```

### Evaluations Parquet Schema
```
url: string (required)
is_mcp_related: boolean (required)
relevance_score: float64 (required)
summary: string (required)
key_topics_json: string (nullable) # JSON array
title: string (nullable)
author: string (nullable)
published_date: timestamp (nullable)
evaluated_at: timestamp (required)
word_count: int32 (required)
truncated: boolean (required)
error: string (nullable)
```

## Performance Considerations

### Expected Improvements
- 5-10x faster data loading vs JSON
- 50-80% storage size reduction
- Efficient columnar queries
- Better memory usage for large datasets

### Query Patterns to Optimize
1. Daily report generation (posts + evaluations join)
2. Date range queries for trending analysis
3. Author activity analysis
4. URL performance tracking
5. Language distribution queries

## Testing Strategy

### Unit Tests
- Parquet schema validation
- Data conversion accuracy
- Query correctness
- Migration logic

### Integration Tests
- Full data pipeline with Parquet
- R2 upload/download with compression
- Cross-date querying
- Data integrity verification

### Performance Tests
- Load testing with 10K+ posts
- Query performance benchmarks
- Memory usage profiling
- Concurrent access patterns

## Success Criteria

### Functional Requirements
- All posts stored in Parquet format
- Backward compatible with JSON data
- Fast query performance (<1s for daily data)
- Data integrity maintained

### Technical Requirements
- 90%+ test coverage
- <500ms query time for daily reports
- 50%+ storage reduction vs JSON
- Support for 1M+ posts per month

## Risk Mitigation

### Data Loss Prevention
- Keep JSON backups during transition
- Implement checksum validation
- Test migration on copy first
- Incremental migration approach

### Performance Risks
- Monitor query patterns
- Add indexes as needed
- Implement query caching
- Use data partitioning

## Next Steps
After Phase 4 completion, the system will have efficient data storage enabling:
- Fast report generation (Phase 5)
- Complex analytics queries
- Historical trend analysis
- Scalable data management