# DuckDB WASM Query Interface Plan

## Overview
Create a web-based query interface using DuckDB WASM to analyze parquet files from the Bluesky MCP Monitor project.

## Architecture

### Phase 1: Local File Support
- Load parquet files from local filesystem
- Support for all three stage files (collect, fetch, evaluate)
- Interactive SQL query interface

### Phase 2: R2 Integration (Future)
- Direct loading from Cloudflare R2 URLs
- HTTP range requests for efficient querying
- Authentication/CORS setup

## Technical Components

### 1. Core DuckDB Setup
- Use jsDelivr CDN for DuckDB WASM
- Initialize async DuckDB instance
- Handle worker setup and cleanup

### 2. File Management
- File picker for local parquet files
- Automatic detection of file type (collect/fetch/evaluate)
- Register files with meaningful table names

### 3. Query Interface
- SQL editor with syntax highlighting (CodeMirror or Monaco)
- Query execution with timing
- Result display in table format
- Export results as CSV/JSON

### 4. Predefined Queries
Organized by stage with examples like:

**Collect Stage:**
- Most engaged posts
- Posts by language
- Thread analysis
- Hashtag frequency

**Fetch Stage:**
- Success/error rates
- Most shared domains
- Content length distribution
- Error analysis

**Evaluate Stage:**
- MCP-related content
- High relevance articles
- Content type breakdown
- Language distribution

### 5. Data Visualization (Optional)
- Simple charts using Chart.js
- Engagement trends
- Domain distribution
- Error rates over time

## User Interface Layout

```
+----------------------------------+
|        DuckDB Query Tool         |
+----------------------------------+
| [Load Files] | Active Tables: [] |
+----------------------------------+
| Predefined Queries:              |
| [Dropdown menu with examples]    |
+----------------------------------+
| SQL Editor:                      |
| +------------------------------+ |
| |                              | |
| | SELECT * FROM collect       | |
| | LIMIT 10;                    | |
| |                              | |
| +------------------------------+ |
| [Run Query] [Clear] [Export]     |
+----------------------------------+
| Results:                         |
| +------------------------------+ |
| | Table view of query results  | |
| +------------------------------+ |
| Rows: X | Time: Yms             |
+----------------------------------+
```

## Implementation Steps

1. **Basic HTML Structure**
   - Responsive layout
   - Clean, minimal design
   - Loading indicators

2. **DuckDB Integration**
   - Async initialization
   - Error handling
   - Memory management

3. **File Loading**
   - Multiple file selection
   - Progress indicators
   - Table registration

4. **Query Execution**
   - Async query handling
   - Result formatting
   - Error display

5. **Example Queries**
   - Categorized by use case
   - Copy-to-editor functionality
   - Query explanations

## Security Considerations

- Client-side only (no server required)
- CORS handling for R2 integration
- No credential storage in code

## Performance Optimizations

- Lazy loading of DuckDB WASM
- Efficient result pagination
- Query result caching
- Worker thread utilization

## Future Enhancements

1. **R2 Integration**
   - Direct S3-compatible API access
   - Signed URL generation
   - Automatic file discovery

2. **Advanced Features**
   - Query history
   - Saved queries
   - Schema browser
   - Join builder UI

3. **Collaboration**
   - Shareable query links
   - Export query results
   - Embedded visualizations