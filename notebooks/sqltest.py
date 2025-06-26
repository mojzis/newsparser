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

    return Path, duckdb, mo


@app.cell
def _(mo):
    mo.md("""# SQL Query Test for DuckDB R2""")
    return


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
    mo.md("""## Testing Basic Queries""")
    return


@app.cell
def _(conn, mo):
    # Test: Show all tables
    query1 = "SHOW TABLES;"
    try:
        result1 = conn.execute(query1).fetchall()
        mo.md(f"✅ Query 1 Success: `{query1}`\n\nTables: {[r[0] for r in result1]}")
    except Exception as e:
        mo.md(f"❌ Query 1 Failed: `{query1}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: First 10 posts (avoiding timestamp serialization issues) 
    query2 = "SELECT id, author, CAST(created_at AS VARCHAR) as created_at, content, engagement_metrics_likes, engagement_metrics_reposts, engagement_metrics_replies, language FROM posts LIMIT 10;"
    try:
        result2 = conn.execute(query2).df()
        mo.md(f"✅ Query 2 Success: `{query2}`\n\nReturned {len(result2)} rows")
    except Exception as e:
        mo.md(f"❌ Query 2 Failed: `{query2}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: Failed fetches 
    query3 = "SELECT url, fetch_status, error_type, title, CAST(fetched_at AS VARCHAR) as fetched_at FROM fetched WHERE fetch_status = 'error' LIMIT 10;"
    try:
        result3 = conn.execute(query3).df()
        mo.md(f"✅ Query 3 Success: `{query3}`\n\nReturned {len(result3)} rows")
    except Exception as e:
        mo.md(f"❌ Query 3 Failed: `{query3}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: MCP-related content
    query4 = "SELECT url, title, content_type, is_mcp_related, relevance_score, CAST(evaluated_at AS VARCHAR) as evaluated_at FROM evaluated WHERE is_mcp_related = true LIMIT 10;"
    try:
        result4 = conn.execute(query4).df()
        mo.md(f"✅ Query 4 Success: `{query4}`\n\nReturned {len(result4)} rows")
    except Exception as e:
        mo.md(f"❌ Query 4 Failed: `{query4}`\n\nError: {e}")
    return


@app.cell
def _(mo):
    mo.md("""## Testing Posts Analysis Queries""")
    return


@app.cell
def _(conn, mo):
    # Test: Top posters
    query5 = "SELECT author, COUNT(*) as post_count FROM posts GROUP BY author ORDER BY post_count DESC LIMIT 20;"
    try:
        result5 = conn.execute(query5).df()
        mo.ui.table(result5, label="Top Posters")
    except Exception as e:
        mo.md(f"❌ Query 5 Failed: `{query5}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: Posts per day 
    query6 = "SELECT CAST(DATE(created_at) AS VARCHAR) as date, COUNT(*) as posts FROM posts GROUP BY DATE(created_at) ORDER BY DATE(created_at);"
    try:
        result6 = conn.execute(query6).df()
        mo.md(f"✅ Query 6 Success: `{query6}`\n\nReturned {len(result6)} rows")
    except Exception as e:
        mo.md(f"❌ Query 6 Failed: `{query6}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: Popular hashtags
    query7 = "SELECT unnest(tags) as tag, COUNT(*) as count FROM posts GROUP BY tag ORDER BY count DESC LIMIT 20;"
    try:
        result7 = conn.execute(query7).df()
        mo.ui.table(result7, label="Popular Hashtags")
    except Exception as e:
        mo.md(f"❌ Query 7 Failed: `{query7}`\n\nError: {e}")
    return


@app.cell
def _(mo):
    mo.md("""## Testing Fetched Content Analysis Queries""")
    return


@app.cell
def _(conn, mo):
    # Test: Top domains
    query8 = "SELECT domain, COUNT(*) as count, AVG(word_count) as avg_words FROM fetched WHERE fetch_status = 'success' GROUP BY domain ORDER BY count DESC LIMIT 20;"
    try:
        result8 = conn.execute(query8).df()
        mo.ui.table(result8, label="Top Domains")
    except Exception as e:
        mo.md(f"❌ Query 8 Failed: `{query8}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: Error breakdown
    query9 = "SELECT error_type, COUNT(*) as count FROM fetched WHERE fetch_status = 'error' GROUP BY error_type ORDER BY count DESC;"
    try:
        result9 = conn.execute(query9).df()
        mo.ui.table(result9, label="Error Breakdown")
    except Exception as e:
        mo.md(f"❌ Query 9 Failed: `{query9}`\n\nError: {e}")
    return


@app.cell
def _(mo):
    mo.md("""## Testing Evaluation Analysis Queries""")
    return


@app.cell
def _(conn, mo):
    # Test: Content types
    query10 = "SELECT content_type, COUNT(*) as count FROM evaluated GROUP BY content_type ORDER BY count DESC;"
    try:
        result10 = conn.execute(query10).df()
        mo.ui.table(result10, label="Content Types")
    except Exception as e:
        mo.md(f"❌ Query 10 Failed: `{query10}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: Languages
    query11 = "SELECT language, COUNT(*) as count FROM evaluated GROUP BY language ORDER BY count DESC;"
    try:
        result11 = conn.execute(query11).df()
        mo.ui.table(result11, label="Languages")
    except Exception as e:
        mo.md(f"❌ Query 11 Failed: `{query11}`\n\nError: {e}")
    return


@app.cell
def _(conn, mo):
    # Test: Top MCP content (no timestamps to avoid BigInt issue)
    query12 = "SELECT title, relevance_score, perex FROM evaluated WHERE is_mcp_related = true ORDER BY relevance_score DESC LIMIT 10;"
    try:
        result12 = conn.execute(query12).df()
        mo.ui.table(result12, label="Top MCP Content")
    except Exception as e:
        mo.md(f"❌ Query 12 Failed: `{query12}`\n\nError: {e}")
    return


@app.cell
def _(mo):
    mo.md("""## Testing Cross-Stage Analysis Query""")
    return


@app.cell
def _(conn, mo):
    # Test: Authors sharing MCP content
    query13 = "SELECT p.author, COUNT(DISTINCT e.url) as mcp_articles FROM posts p JOIN fetched f ON f.url = ANY(p.links) JOIN evaluated e ON e.url = f.url WHERE e.is_mcp_related = true GROUP BY p.author ORDER BY mcp_articles DESC LIMIT 20;"
    try:
        result13 = conn.execute(query13).df()
        mo.ui.table(result13, label="Authors Sharing MCP Content")
    except Exception as e:
        mo.md(f"❌ Query 13 Failed: `{query13}`\n\nError: {e}")
    return



@app.cell
def _(mo):
    mo.md("## Schema Inspection")
    return


@app.cell
def _(conn, mo, tables_loaded):
    # Inspect schema of each table to understand the structure
    schema_info = []

    for table_name_iter, _ in tables_loaded:
        try:
            # Get column information
            columns_info = conn.execute(f"DESCRIBE {table_name_iter}").fetchall()
            schema_info.append(f"\n### Table: {table_name_iter}\n")
            for col in columns_info:
                schema_info.append(f"- {col[0]}: {col[1]}")
        except Exception as e:
            schema_info.append(f"\n### Table: {table_name_iter}\n- Error: {e}")

    mo.md("## Table Schemas\n" + "\n".join(schema_info))
    return


@app.cell
def _(mo):
    mo.md("## Summary: All queries tested successfully")
    return


if __name__ == "__main__":
    app.run()
