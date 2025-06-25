# HTML Source Files

This directory contains the HTML source files for the project's web interfaces.

## Files

### Query Tools
- **`duckdb-query-tool.html`** - Basic DuckDB WASM query interface for local files
- **`duckdb-query-tool-r2.html`** - Enhanced version with R2 storage support

### Documentation
- **`metadata-example.html`** - Interactive parquet schema documentation viewer

### Templates
- **`about-template.html`** - Template for rendering the about page from markdown with navigation menu

## Publishing

The query tool and about page are automatically published to the output directory during the build process:

```bash
# Render about page manually
poetry run nsp stages render-about

# Generate statistics page manually
poetry run nsp stages render-stats

# Publish query tool manually
poetry run nsp stages publish

# Or as part of the full pipeline
poetry run nsp run-all
```

Published files:
- `output/about.html` - About page rendered from markdown
- `output/query/duckdb.html` - DuckDB query interface (R2-enabled version)
- `output/stats.html` - Project statistics page generated from marimo notebook (`notebooks/stats.py`)

## Navigation

All generated pages now include a consistent navigation header with:
- **Home** - Links to the main homepage (index.html)
- **Query** - Links to the DuckDB query interface (query/duckdb.html)
- **Stats** - Links to the project statistics page (stats.html)
- **About** - Links to the about page (about.html)

The navigation automatically highlights the current page and is responsive for mobile devices.

## Development

All JavaScript is currently embedded within the HTML files for simplicity. The files are self-contained and include:

- DuckDB WASM integration
- CSS styling
- Interactive JavaScript functionality
- Navigation header with consistent styling
- No external dependencies (except CDN-loaded DuckDB WASM)

## Structure

The HTML files follow this general structure:
- HTML markup with semantic structure
- Embedded CSS for styling
- Embedded JavaScript modules using ES6 imports
- CDN-loaded dependencies (DuckDB WASM)

This approach keeps everything in a single file for easy deployment and reduces complexity.