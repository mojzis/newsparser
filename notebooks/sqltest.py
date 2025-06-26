import marimo

__generated_with = "0.13.15"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import duckdb
    from pathlib import Path
    from datetime import date
    import pandas as pd

    return Path, duckdb, mo, pd


@app.cell
def _(mo):
    mo.md("# SQL Query Test for DuckDB R2")


@app.cell
def _(Path, duckdb):
    # Create DuckDB connection
    conn = duckdb.connect()

    # Check for available parquet files in stages/evaluate
    evaluate_dir = Path("stages/evaluate")

    # Find the most recent date with data
    dates_with_data = []
    if evaluate_dir.exists():
        for date_dir in evaluate_dir.iterdir():
            if date_dir.is_dir() and list(date_dir.glob("*.md")):
                dates_with_data.append(date_dir.name)

    dates_with_data.sort(reverse=True)
    latest_date = dates_with_data[0] if dates_with_data else None

    print(f"Latest date with data: {latest_date}")
    return conn, latest_date


@app.cell
def _(Path, conn, latest_date):
    # Load parquet files if they exist
    parquet_dir = Path("parquet")
    tables_loaded = []

    if latest_date and parquet_dir.exists():
        # Try to load by-run-date files
        stages = [
            ('collect', 'posts'),
            ('fetch', 'fetched'),
            ('evaluate', 'evaluated')
        ]

        for stage, table_name in stages:
            by_run_date_dir = parquet_dir / stage / "by-run-date"
            if by_run_date_dir.exists():
                # Look for the most recent file
                parquet_files = list(by_run_date_dir.glob(f"{latest_date}_last_7_days.parquet"))
                if parquet_files:
                    parquet_file = parquet_files[0]
                    try:
                        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{parquet_file}')")
                        tables_loaded.append((table_name, parquet_file))
                        print(f"✅ Loaded {table_name} from {parquet_file}")
                    except Exception as e:
                        print(f"❌ Failed to load {table_name}: {e}")

    # Show loaded tables
    if tables_loaded:
        print("\nLoaded tables:")
        for table, file in tables_loaded:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  - {table}: {count} rows")
    else:
        print("⚠️ No tables loaded. Some queries may fail.")

    return (tables_loaded,)


@app.cell
def _(mo):
    mo.md("## Testing All Queries")


@app.cell
def _(conn, mo):
    # Define all test queries
    queries = [
        ("Show all tables", "SHOW TABLES;"),
        ("First 10 posts", "SELECT id, author, CAST(created_at AS VARCHAR) as created_at, content, engagement_metrics_likes, engagement_metrics_reposts, engagement_metrics_replies, language FROM posts LIMIT 10;"),
        ("Failed fetches", "SELECT url, fetch_status, error_type, title, CAST(fetched_at AS VARCHAR) as fetched_at FROM fetched WHERE fetch_status = 'error' LIMIT 10;"),
        ("MCP-related content", "SELECT url, title, content_type, is_mcp_related, relevance_score, CAST(evaluated_at AS VARCHAR) as evaluated_at FROM evaluated WHERE is_mcp_related = true LIMIT 10;"),
        ("Top posters", "SELECT author, COUNT(*) as post_count FROM posts GROUP BY author ORDER BY post_count DESC LIMIT 20;"),
        ("Posts per day", "SELECT CAST(DATE(created_at) AS VARCHAR) as date, COUNT(*) as posts FROM posts GROUP BY DATE(created_at) ORDER BY DATE(created_at);"),
        ("Popular hashtags", "SELECT tag, COUNT(*) as count FROM (SELECT UNNEST(tags) as tag FROM posts) GROUP BY tag ORDER BY count DESC LIMIT 20;"),
        ("Top domains", "SELECT domain, COUNT(*) as count, AVG(word_count) as avg_words FROM fetched WHERE fetch_status = 'success' GROUP BY domain ORDER BY count DESC LIMIT 20;"),
        ("Error breakdown", "SELECT error_type, COUNT(*) as count FROM fetched WHERE fetch_status = 'error' GROUP BY error_type ORDER BY count DESC;"),
        ("Content types", "SELECT content_type, COUNT(*) as count FROM evaluated GROUP BY content_type ORDER BY count DESC;"),
        ("Languages", "SELECT language, COUNT(*) as count FROM evaluated GROUP BY language ORDER BY count DESC;"),
        ("Top MCP content", "SELECT title, relevance_score, perex FROM evaluated WHERE is_mcp_related = true ORDER BY relevance_score DESC LIMIT 10;"),
        ("Authors sharing MCP content", "SELECT p.author, COUNT(DISTINCT e.url) as mcp_articles FROM posts p JOIN fetched f ON f.url = ANY(p.links) JOIN evaluated e ON e.url = f.url WHERE e.is_mcp_related = true GROUP BY p.author ORDER BY mcp_articles DESC LIMIT 20;")
    ]
    
    # Test all queries and collect results
    results = []
    
    for i, (name, query) in enumerate(queries, 1):
        try:
            result = conn.execute(query).fetchall()
            if len(result) > 0:
                results.append(f"✅ **Query {i}: {name}**\n   - Query: `{query}`\n   - Success: {len(result)} rows returned\n")
            else:
                results.append(f"⚪ **Query {i}: {name}**\n   - Query: `{query}`\n   - Success: 0 rows returned\n")
        except Exception as e:
            results.append(f"❌ **Query {i}: {name}**\n   - Query: `{query}`\n   - Error: {str(e)}\n")
    
    # Prepare summary
    total_queries = len(queries)
    successful_queries = len([r for r in results if r.startswith("✅") or r.startswith("⚪")])
    failed_queries = total_queries - successful_queries
    
    summary = f"""## Query Test Results

**Summary**: {successful_queries}/{total_queries} queries successful, {failed_queries} failed

{chr(10).join(results)}"""
    
    # CORRECT PATTERN: mo.md() OUTSIDE control blocks, BEFORE return
    mo.md(summary)
    return


@app.cell
def _(conn, mo, tables_loaded):
    # Schema inspection
    schema_info = []
    
    try:
        for table_name_iter, _ in tables_loaded:
            try:
                # Get column information
                columns_info = conn.execute(f"DESCRIBE {table_name_iter}").fetchall()
                schema_info.append(f"### Table: {table_name_iter}")
                for col in columns_info:
                    schema_info.append(f"- **{col[0]}**: {col[1]}")
                schema_info.append("")  # Empty line between tables
            except Exception as e:
                schema_info.append(f"### Table: {table_name_iter}")
                schema_info.append(f"- Error: {e}")
                schema_info.append("")
        
        content = "## Table Schemas\n\n" + "\n".join(schema_info)
    except Exception as e:
        content = f"## Table Schemas\n\nError inspecting schemas: {e}"
    
    # CORRECT PATTERN: mo.md() OUTSIDE try/except, BEFORE return
    mo.md(content)
    return


@app.cell  
def _(conn, mo):
    # Show some sample data from each table
    sample_data = []
    tables = ["posts", "fetched", "evaluated"]
    
    try:
        for table in tables:
            try:
                # Get first 3 rows as sample
                result = conn.execute(f"SELECT * FROM {table} LIMIT 3").df()
                sample_data.append(f"### Sample data from {table} ({len(result)} rows shown)")
                sample_data.append("```")
                sample_data.append(result.to_string())
                sample_data.append("```")
                sample_data.append("")
            except Exception as e:
                sample_data.append(f"### Sample data from {table}")
                sample_data.append(f"Error: {e}")
                sample_data.append("")
        
        content = "## Sample Data\n\n" + "\n".join(sample_data)
    except Exception as e:
        content = f"## Sample Data\n\nError getting sample data: {e}"
    
    # CORRECT PATTERN: mo.md() OUTSIDE try/except, BEFORE return
    mo.md(content)
    return


if __name__ == "__main__":
    app.run()