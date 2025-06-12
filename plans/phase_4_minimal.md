# Phase 4: Minimal Implementation Plan

## What's Already Done ✅
- Parquet dependencies installed (pandas, pyarrow)
- URL registry using Parquet
- Article evaluations stored as Parquet
- FileManager with proper paths
- R2Client with upload/download

## What Actually Needs to Be Done ❌
1. **Convert posts from JSON to Parquet storage**
   - Currently stored as `posts.json`
   - Need to store as `posts.parquet`

## Minimal Implementation Tasks

### Task 1: Update Posts Storage (MVP)
```python
# In BlueskyDataCollector._store_posts()
# Current: Stores as JSON
# New: Store as Parquet using pandas

# Simple approach:
posts_data = [post.model_dump() for post in posts]
df = pd.DataFrame(posts_data)

# Handle lists/dicts as JSON strings for Parquet compatibility
df['links'] = df['links'].apply(lambda x: json.dumps(x))
df['tags'] = df['tags'].apply(lambda x: json.dumps(x))
df['engagement_metrics'] = df['engagement_metrics'].apply(lambda x: json.dumps(x))

# Save as Parquet
df.to_parquet(temp_file, index=False)
```

### Task 2: Update Posts Retrieval
```python
# In BlueskyDataCollector.get_stored_posts()
# Read Parquet instead of JSON
df = pd.read_parquet(temp_file)

# Convert JSON strings back to lists/dicts
df['links'] = df['links'].apply(json.loads)
df['tags'] = df['tags'].apply(json.loads)
df['engagement_metrics'] = df['engagement_metrics'].apply(json.loads)

# Convert to BlueskyPost models
```

### Task 3: Backward Compatibility
- Check for both `.json` and `.parquet` files
- If only JSON exists, read it (existing functionality)
- Always save new data as Parquet

## Implementation Steps

1. **Update `_store_posts` method**
   - Convert posts to DataFrame
   - Handle nested fields as JSON strings
   - Save as Parquet

2. **Update `get_stored_posts` method**
   - Try reading Parquet first
   - Fall back to JSON if needed
   - Convert DataFrame back to models

3. **Update `check_stored_data` method**
   - Check for either `.parquet` or `.json`

4. **Test the changes**
   - Ensure existing JSON files still work
   - Verify new Parquet files are created
   - Check data integrity

## Estimated Time: 1-2 hours

This minimal approach:
- Achieves the core goal of Parquet storage
- Maintains backward compatibility
- Doesn't require new models or complex migrations
- Uses existing pandas/pyarrow capabilities
- Follows MVP principles

## Benefits
- Smaller file sizes (50-80% reduction)
- Faster loading (5-10x improvement)
- Better for analytics in Phase 5
- No breaking changes