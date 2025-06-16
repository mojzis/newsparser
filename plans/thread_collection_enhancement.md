# Thread Collection Enhancement Plan

## Overview
Enhance the Bluesky MCP Monitor to collect entire threads instead of individual posts, extracting URLs from all posts in each thread and maintaining thread relationship data.

## Current State Analysis
- **Current approach**: Collects individual posts via search API
- **Available API**: atproto provides `get_post_thread(uri, depth, parentHeight)` method
- **Post model**: `BlueskyPost` stores individual post data
- **Stage architecture**: Collection happens in `CollectStage` class

## Proposed Changes

### 1. Post Model Enhancement (`src/models/post.py`)
- Add `thread_root_uri: Optional[str]` field to link posts to their thread starter  
- Add `thread_position: Optional[str]` field (values: "root", "reply", "nested_reply")
- Add `parent_post_uri: Optional[str]` field for direct parent reference
- Add `thread_depth: Optional[int]` field to indicate reply nesting level

### 2. Thread Collection Service (`src/bluesky/thread_collector.py`)
New service class for thread-specific operations:
- `collect_thread_from_post(post_uri)` - Fetch complete thread using atproto's `get_post_thread`
- `extract_thread_posts(thread_response)` - Parse thread structure into individual posts
- `collect_threads_from_search(search_results)` - Get threads for all search result posts
- Handle thread deduplication (avoid collecting same thread multiple times)

### 3. Bluesky Client Enhancement (`src/bluesky/client.py`)  
- Add `get_thread_by_uri(uri, depth=6, parent_height=80)` method
- Add thread structure parsing logic to convert atproto thread response to post models
- Handle thread traversal (parents and replies)

### 4. Collection Stage Enhancement (`src/stages/collect.py`)
- Add `collect_threads: bool = False` parameter to enable thread collection mode
- When enabled: for each search result post, fetch its complete thread
- Deduplicate threads to avoid processing same thread multiple times
- Store all thread posts with proper relationship metadata

### 5. URL Extraction Enhancement
- Extract URLs from ALL posts in each thread (not just search result post)
- Track which specific post in thread contained each URL
- Maintain URL-to-post mapping for better content attribution

### 6. Configuration Options
Add to search definitions in `src/config/searches.yaml`:
```yaml
collect_full_threads: true  # Enable thread collection for this search
max_thread_depth: 6        # How deep to go in replies  
max_parent_height: 80      # How far up parent chain
```

### 7. CLI Command Enhancement
Update `nsp collect` command:
- Add `--threads/--no-threads` flag to enable/disable thread collection
- Add `--max-thread-depth` and `--max-parent-height` options
- Update help text to explain thread collection behavior

## Implementation Steps

1. **Phase 1**: Enhance Post model with thread relationship fields
2. **Phase 2**: Create ThreadCollector service with basic thread fetching  
3. **Phase 3**: Integrate ThreadCollector into existing CollectStage
4. **Phase 4**: Add configuration options and CLI flags
5. **Phase 5**: Update URL extraction to work across thread posts
6. **Phase 6**: Add deduplication logic and performance optimizations

## Benefits
- **Richer context**: Capture full conversations around MCP topics
- **More URLs**: Find URLs mentioned in replies that might be missed otherwise  
- **Better relationships**: Track which posts are responses to which
- **Future analytics**: Enable thread-level analysis and reporting

## File Changes Required
- `src/models/post.py` - Add thread relationship fields
- `src/bluesky/thread_collector.py` - New thread collection service  
- `src/bluesky/client.py` - Add thread fetching methods
- `src/stages/collect.py` - Integrate thread collection
- `src/config/searches.py` - Add thread collection config options
- `src/cli/stage_commands.py` - Add CLI flags
- `tests/` - Add comprehensive tests for thread functionality
- `plans/thread_collection_enhancement.md` - Document this plan

## Considerations
- **Rate limiting**: Thread collection will increase API calls significantly
- **Storage**: More posts per search = larger storage requirements  
- **Performance**: Need efficient deduplication to avoid processing same threads
- **Backward compatibility**: Ensure existing single-post collection still works

## Implementation Status
- [x] Plan documented
- [x] Phase 1: Post model enhancement
- [x] Phase 2: ThreadCollector service  
- [x] Phase 3: Integration with CollectStage
- [x] Phase 4: CLI flags and configuration options
- [ ] Phase 5: URL extraction enhancement (already working - URLs extracted from all thread posts)
- [ ] Phase 6: Performance optimizations
- [ ] Phase 7: Tests and documentation

## Implementation Details

### Completed Features
1. **Enhanced Post Model** (`src/models/post.py`):
   - Added `thread_root_uri`, `thread_position`, `thread_depth`, `parent_post_uri` fields
   - Added helper methods: `is_thread_root()`, `is_reply()`, `set_thread_metadata()`
   - Added `ThreadPosition` type with "root", "reply", "nested_reply" values

2. **ThreadCollector Service** (`src/bluesky/thread_collector.py`):
   - `collect_thread_from_post()` - Fetch complete thread for any post URI
   - `collect_threads_from_search()` - Get threads for multiple search results with deduplication
   - Thread traversal using BFS algorithm
   - Rate limiting and error handling

3. **Enhanced Bluesky Client** (`src/bluesky/client.py`):
   - Added `get_thread_by_uri()` method using atproto's `get_post_thread`
   - Added `get_threads_for_posts()` convenience method
   - Integrated with ThreadCollector service

4. **CollectStage Integration** (`src/stages/collect.py`):
   - Added thread collection parameters to constructor
   - Modified `collect_posts()` to optionally fetch complete threads
   - Enhanced markdown frontmatter to include thread metadata
   - Maintains backward compatibility with single-post collection

5. **CLI Commands**:
   - Added `--threads/--no-threads` flag to `nsp collect` and `nsp run-all`
   - Added `--max-thread-depth` and `--max-parent-height` options
   - Updated help text and command descriptions
   - Both convenience commands (`nsp collect`) and stage commands (`nsp stages collect`) support thread options

### Usage Examples
```bash
# Collect individual posts (default behavior)
poetry run nsp collect --search mcp_tag --max-posts 50

# Collect entire threads
poetry run nsp collect --search mcp_tag --max-posts 50 --threads

# Collect threads with custom depth settings
poetry run nsp collect --search mcp_tag --max-posts 50 --threads --max-thread-depth 3 --max-parent-height 20

# Run all stages with thread collection
poetry run nsp run-all --search mcp_tag --threads
```

### Thread Data Structure
Each post now includes thread relationship data in its markdown frontmatter:
```yaml
thread:
  root_uri: "at://did:plc:example/app.bsky.feed.post/abc123"
  position: "reply"  # or "root" or "nested_reply"
  depth: 1
  parent_uri: "at://did:plc:example/app.bsky.feed.post/parent456"
```