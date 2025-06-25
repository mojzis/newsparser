# DuckDB Parquet Query Tool

A web-based SQL query interface for analyzing Bluesky MCP Monitor parquet files using DuckDB WASM.

## Features

- **Client-side processing** - All queries run in your browser, no server required
- **Multi-file support** - Load collect, fetch, and evaluate parquet files simultaneously
- **Interactive SQL editor** - Write and execute custom SQL queries
- **Predefined queries** - Common analysis queries organized by category
- **Export results** - Download query results as CSV files
- **Quick stats** - See row counts for loaded tables

## Usage

1. **Open the tool**: Simply open `duckdb-query-tool.html` in a modern web browser

2. **Load parquet files**: Click "Choose Parquet Files" and select one or more parquet files:
   - Files containing "collect" in the name → loaded as `collect` table
   - Files containing "fetch" in the name → loaded as `fetch` table
   - Files containing "evaluate" in the name → loaded as `evaluate` table

3. **Run queries**: 
   - Select from example queries dropdown, or
   - Write custom SQL in the editor
   - Click "Run Query" or press Ctrl+Enter

4. **Export results**: Click "Export CSV" to download query results

## Example Queries

### Basic Exploration
```sql
-- Show all loaded tables
SHOW TABLES;

-- Preview data
SELECT * FROM collect LIMIT 10;
```

### Collect Stage Analysis
```sql
-- Most engaged posts
SELECT 
    author,
    content,
    engagement_metrics_likes + engagement_metrics_reposts as total_engagement
FROM collect
ORDER BY total_engagement DESC
LIMIT 20;

-- Thread analysis
SELECT 
    thread_position,
    COUNT(*) as count,
    AVG(engagement_metrics_likes) as avg_likes
FROM collect
WHERE thread_position IS NOT NULL
GROUP BY thread_position;
```

### Fetch Stage Analysis
```sql
-- Success rate by domain
SELECT 
    domain,
    COUNT(*) as total,
    SUM(CASE WHEN fetch_status = 'success' THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN fetch_status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM fetch
GROUP BY domain
HAVING COUNT(*) > 5
ORDER BY success_rate DESC;
```

### Evaluate Stage Analysis
```sql
-- MCP-related content by relevance
SELECT 
    title,
    relevance_score,
    perex,
    key_topics
FROM evaluate
WHERE is_mcp_related = true
ORDER BY relevance_score DESC
LIMIT 20;

-- Content type distribution
SELECT 
    content_type,
    COUNT(*) as count,
    ROUND(AVG(relevance_score), 3) as avg_relevance
FROM evaluate
GROUP BY content_type
ORDER BY count DESC;
```

### Cross-Stage Analysis
```sql
-- Authors sharing the most MCP-related content
SELECT 
    c.author,
    COUNT(DISTINCT e.url) as mcp_articles_shared,
    AVG(e.relevance_score) as avg_relevance
FROM collect c
JOIN fetch f ON f.url = ANY(c.links)
JOIN evaluate e ON e.url = f.url
WHERE e.is_mcp_related = true
GROUP BY c.author
HAVING COUNT(DISTINCT e.url) > 2
ORDER BY mcp_articles_shared DESC;
```

## Technical Details

- Uses DuckDB WASM from jsDelivr CDN
- Runs entirely in the browser using WebAssembly
- Supports standard SQL with DuckDB extensions
- Handles parquet files up to available browser memory

## R2 Integration

The enhanced version (`duckdb-query-tool-r2.html`) includes support for loading parquet files directly from Cloudflare R2:

### Setup
1. Ensure your R2 bucket has public read access for the parquet files
2. Use the R2 public URL format: `https://your-bucket.r2.dev`

### Usage
1. Enter your R2 base URL (e.g., `https://mcp.r2.dev`)
2. Select a date to load the corresponding `_last_7_days.parquet` files
3. Click "Load from R2" to fetch all three stage files

### Benefits
- No need to download files locally
- Always access the latest data
- Efficient HTTP range requests via DuckDB
- Works seamlessly with local files

## Future Enhancements

- Query history and saved queries
- Data visualization
- Schema browser
- Automatic R2 file discovery