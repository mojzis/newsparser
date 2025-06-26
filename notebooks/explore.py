import marimo

__generated_with = "0.13.15"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent / "src"))

    from config.settings import Settings
    from storage.r2_client import R2Client

    return R2Client, Settings, mo, pd


@app.cell
def _(mo):
    mo.md("""# Data Exploration Notebook""")
    return


@app.cell
def _(R2Client, Settings, mo):
    settings = Settings()
    r2_client = R2Client(settings)
    mo.md("✅ R2 client initialized")
    return (r2_client,)


@app.cell
def _(mo, r2_client):
    posts_files = r2_client.list_files("posts/by-run-date/", max_keys=20)
    fetched_files = r2_client.list_files("fetched/by-run-date/", max_keys=20)
    evaluated_files = r2_client.list_files("evaluated/by-run-date/", max_keys=20)

    posts_files.sort(reverse=True)
    fetched_files.sort(reverse=True)
    evaluated_files.sort(reverse=True)

    mo.md(f"""
    ## Available Files

    **Posts**: {len(posts_files)} files  
    **Fetched**: {len(fetched_files)} files  
    **Evaluated**: {len(evaluated_files)} files

    ### Recent Files:
    {chr(10).join(['- ' + f for f in (posts_files[:3] + fetched_files[:3] + evaluated_files[:3])])}
    """)
    return evaluated_files, fetched_files, posts_files


@app.cell
def _(evaluated_files, fetched_files, mo, pd, posts_files, r2_client):
    import tempfile

    datasets = {}
    file_sets = [
        ("posts", posts_files[:1]),
        ("fetched", fetched_files[:1]),
        ("evaluated", evaluated_files[:1])
    ]

    for category, files in file_sets:
        if files:
            key = files[0]
            with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
                r2_client.download_file(key, tmp.name)
                df_temp = pd.read_parquet(tmp.name)
                datasets[category] = {
                    'df': df_temp,
                    'file': key,
                    'shape': df_temp.shape
                }

    summary_parts = ["## Loaded Datasets"]
    for dataset_name, dataset_info in datasets.items():
        summary_parts.append(f"**{dataset_name.title()}**: {dataset_info['shape'][0]} rows × {dataset_info['shape'][1]} columns")
        summary_parts.append(f"  - File: `{dataset_info['file']}`")

    mo.md(chr(10).join(summary_parts))
    return (datasets,)


@app.cell
def _(datasets, mo):
    if 'posts' in datasets:
        posts_df = datasets['posts']['df']
        posts_table = mo.ui.table(
            posts_df.head(15),
            selection="multi",
            label="Posts Data"
        )
        posts_table
    else:
        mo.md("Posts data not available")
    return


@app.cell
def _(datasets, mo):
    if 'fetched' in datasets:
        fetched_df = datasets['fetched']['df']
        fetched_table = mo.ui.table(
            fetched_df.head(15),
            selection="multi",
            label="Fetched Articles Data"
        )
        fetched_table
    else:
        mo.md("Fetched data not available")
    return


@app.cell
def _(datasets, mo):
    if 'evaluated' in datasets:
        evaluated_df = datasets['evaluated']['df']
        evaluated_table = mo.ui.table(
            evaluated_df.head(15),
            selection="multi",
            label="Evaluated Content Data"
        )
        evaluated_table
    else:
        mo.md("Evaluated data not available")
    return


@app.cell
def _(datasets, mo):
    analysis_parts = ["## Quick Analysis"]

    for dataset_name, dataset_info in datasets.items():
        df_analysis = dataset_info['df']
        analysis_parts.append(f"### {dataset_name.title()} Dataset")
        analysis_parts.append(f"- **Rows**: {df_analysis.shape[0]:,}")
        analysis_parts.append(f"- **Columns**: {df_analysis.shape[1]}")
        analysis_parts.append(f"- **Memory**: {df_analysis.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
        analysis_parts.append("")

    mo.md(chr(10).join(analysis_parts))
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## Usage Instructions

    ### Available DataFrames:
    - `posts_df` - Recent posts data
    - `fetched_df` - Recent fetched articles data  
    - `evaluated_df` - Recent evaluated content data

    ### Example Operations:
    ```python
    # Filter posts by language
    english_posts = posts_df[posts_df['language'] == 'en']

    # Find MCP-related content
    mcp_content = evaluated_df[evaluated_df['is_mcp_related'] == True]

    # Check engagement metrics
    high_engagement = posts_df[posts_df['engagement_metrics_likes'] > 10]

    # Explore URL domains
    top_domains = fetched_df['domain'].value_counts().head(10)
    ```

    Add new cells below to explore the data!
    """
    )
    return


if __name__ == "__main__":
    app.run()
