import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from pathlib import Path
    from datetime import datetime, date, timedelta
    import yaml
    import json
    from typing import List, Dict, Any
    return Path, datetime, mo, pd, timedelta, yaml


@app.cell
def _(mo):
    mo.md(
        """
    # Evaluated Content Analysis

    This notebook loads evaluated content from the MCP Monitor project and provides tools for analysis.
    """
    )
    return


@app.cell
def _(Path, datetime, pd, timedelta, yaml):
    def load_evaluated_content(days_back: int = 7) -> pd.DataFrame:
        """Load evaluated content from the last N days into a dataframe."""
        base_path = Path("stages/evaluate")
        records = []

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)

        # Scan each day
        current_date = start_date
        while current_date <= end_date:
            date_dir = base_path / current_date.strftime("%Y-%m-%d")

            if date_dir.exists():
                for md_file in date_dir.glob("*.md"):
                    try:
                        # Read the markdown file
                        with open(md_file, 'r') as f:
                            content = f.read()

                        # Extract frontmatter
                        if content.startswith('---'):
                            parts = content.split('---', 2)
                            if len(parts) >= 3:
                                frontmatter = yaml.safe_load(parts[1])

                                # Extract evaluation data
                                evaluation = frontmatter.get('evaluation', {})

                                # Create record
                                record = {
                                    'date': current_date,
                                    'url': frontmatter.get('url', ''),
                                    'title': frontmatter.get('title', ''),
                                    'domain': frontmatter.get('domain', ''),
                                    'is_mcp_related': evaluation.get('is_mcp_related', False),
                                    'relevance_score': evaluation.get('relevance_score', 0.0),
                                    'key_topics': evaluation.get('key_topics', []),
                                    'perex': evaluation.get('perex', ''),
                                    'summary': evaluation.get('summary', ''),
                                    'found_in_posts': len(frontmatter.get('found_in_posts', [])),
                                    'file_path': str(md_file)
                                }
                                records.append(record)

                    except Exception as e:
                        print(f"Error loading {md_file}: {e}")

            current_date += timedelta(days=1)

        # Create dataframe
        df = pd.DataFrame(records)

        # Convert date column to datetime if records exist
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])

        return df

    return (load_evaluated_content,)


@app.cell
def _(mo):
    days_slider = mo.ui.slider(
        start=1, 
        stop=30, 
        value=7,
        label="Days to look back"
    )

    mo.md(f"""
    ## Load Data

    Select how many days of evaluated content to load:

    {days_slider}
    """)
    return (days_slider,)


@app.cell
def _(days_slider, load_evaluated_content, mo):
    # Load the data
    evaluated_content = load_evaluated_content(days_back=days_slider.value)

    mo.md(f"""
    ### Data Loaded

    - **Total records:** {len(evaluated_content)}
    - **Date range:** {evaluated_content['date'].min().strftime('%Y-%m-%d') if not evaluated_content.empty else 'N/A'} to {evaluated_content['date'].max().strftime('%Y-%m-%d') if not evaluated_content.empty else 'N/A'}
    - **MCP-related articles:** {evaluated_content['is_mcp_related'].sum() if not evaluated_content.empty else 0}
    - **Unique domains:** {evaluated_content['domain'].nunique() if not evaluated_content.empty else 0}
    """)
    return (evaluated_content,)


@app.cell
def _(mo):
    mo.md("""## Data Preview""")
    return


@app.cell
def _(evaluated_content, mo):
    mo.ui.table(
        evaluated_content,
        selection=None,
        pagination=True,
        page_size=30
    )
    return


@app.cell
def _(evaluated_content, mo):
    kt = (
        evaluated_content.loc[lambda x: x["is_mcp_related"]]
        [["url","key_topics"]]
        .explode("key_topics")
        .groupby("key_topics", as_index=False)
        .agg(num_urls=("url","nunique"))
        .sort_values("num_urls", ascending=False)
    )
    mo.ui.table(kt,page_size=30)
    return


@app.cell
def _(evaluated_content, mo):
        # Filter to MCP-related content
    mcp_df = evaluated_content[evaluated_content['is_mcp_related']].copy()

    mo.md(f"""
    ### MCP Articles by Relevance Score

    Found **{len(mcp_df)}** MCP-related articles with average relevance score of **{mcp_df['relevance_score'].mean():.3f}**
    """)
    return (mcp_df,)


@app.cell
def _(mcp_df, mo):
        # Sort by relevance score
    top_articles = mcp_df.nlargest(20, 'relevance_score')[['title', 'domain', 'relevance_score', 'perex']]

    mo.ui.table(
        top_articles,
        selection=None,
        pagination=False
    )

    return


@app.cell
def _(evaluated_content, mo):
        # Aggregate by domain
    domain_stats = evaluated_content.groupby('domain').agg({
        'url': 'count',
        'is_mcp_related': 'sum',
        'relevance_score': 'mean'
    }).round(3)

    domain_stats.columns = ['total_articles', 'mcp_articles', 'avg_relevance']
    domain_stats = domain_stats.sort_values('mcp_articles', ascending=False).head(15)

    mo.ui.table(
        domain_stats.reset_index(),
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(evaluated_content, mo):
    mo.md("## Time Series Analysis")

    if not evaluated_content.empty and len(evaluated_content) > 0:
        # Aggregate by date
        daily_stats = evaluated_content.groupby(evaluated_content['date'].dt.date).agg({
            'url': 'count',
            'is_mcp_related': 'sum',
            'relevance_score': lambda x: x[evaluated_content.loc[x.index, 'is_mcp_related']].mean() if any(evaluated_content.loc[x.index, 'is_mcp_related']) else 0
        }).round(3)

        daily_stats.columns = ['total_articles', 'mcp_articles', 'avg_mcp_relevance']
        daily_stats = daily_stats.reset_index()
        daily_stats.columns = ['date', 'total_articles', 'mcp_articles', 'avg_mcp_relevance']

        mo.ui.table(
            daily_stats,
            selection=None,
            pagination=False
        )
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## Advanced Filtering

    Use these controls to filter the dataset:
    """
    )
    return


@app.cell
def _(evaluated_content, mo):
        # Create filter controls
    mcp_only = mo.ui.checkbox(label="MCP-related only", value=False)
    min_relevance = mo.ui.slider(
        start=0.0,
        stop=1.0,
        step=0.1,
        value=0.0,
        label="Minimum relevance score"
    )

    # Get unique domains for dropdown
    domains = ["All"] + sorted(evaluated_content['domain'].unique().tolist())
    domain_filter = mo.ui.dropdown(
        options=domains,
        value="All",
        label="Filter by domain"
    )

    mo.hstack([
        mo.vstack([mcp_only, min_relevance]),
        domain_filter
    ])
    return domain_filter, mcp_only, min_relevance


@app.cell
def _(domain_filter, evaluated_content, mcp_only, min_relevance, mo):
    # Apply filters
    filtered_df = evaluated_content.copy()

    if mcp_only.value:
        filtered_df = filtered_df[filtered_df['is_mcp_related']]

    if min_relevance.value > 0:
        filtered_df = filtered_df[filtered_df['relevance_score'] >= min_relevance.value]

    if domain_filter.value != "All":
        filtered_df = filtered_df[filtered_df['domain'] == domain_filter.value]

    mo.md(f"""
    ### Filtered Results

    Showing **{len(filtered_df)}** of {len(evaluated_content)} articles
    """)

    mo.ui.table(
        filtered_df[['date', 'title', 'domain', 'is_mcp_related', 'relevance_score', 'perex']].head(20),
        selection=None,
        pagination=True,
        page_size=30
    )
    return


if __name__ == "__main__":
    app.run()
