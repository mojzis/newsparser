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
    import numpy as np
    return Path, datetime, mo, np, pd, timedelta, yaml


@app.cell
def _(mo):
    mo.md(
        """
    # Post Popularity Analysis

    This notebook analyzes Bluesky posts collected by the MCP Monitor to understand engagement patterns and popularity metrics.
    """
    )
    return


@app.cell
def _(Path, datetime, pd, timedelta, yaml):
    def load_posts(days_back: int = 7) -> pd.DataFrame:
        """Load posts from the last N days into a dataframe."""
        base_path = Path("stages/collect")
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

                                # Extract engagement metrics
                                engagement = frontmatter.get('engagement', {})

                                # Parse created_at timestamp
                                created_at = frontmatter.get('created_at', '')
                                if created_at:
                                    if created_at.endswith('+00:00'):
                                        created_at = datetime.fromisoformat(created_at.replace('+00:00', 'Z').rstrip('Z'))
                                    else:
                                        created_at = datetime.fromisoformat(created_at.rstrip('Z'))
                                else:
                                    created_at = datetime.now()

                                # Create record
                                record = {
                                    'date': current_date,
                                    'post_id': frontmatter.get('id', ''),
                                    'author': frontmatter.get('author', ''),
                                    'created_at': created_at,
                                    'hour_of_day': created_at.hour,
                                    'day_of_week': created_at.strftime('%A'),
                                    'likes': engagement.get('likes', 0),
                                    'reposts': engagement.get('reposts', 0),
                                    'replies': engagement.get('replies', 0),
                                    'total_engagement': engagement.get('likes', 0) + engagement.get('reposts', 0) + engagement.get('replies', 0),
                                    'urls_count': len(frontmatter.get('urls', [])),
                                    'has_urls': len(frontmatter.get('urls', [])) > 0,
                                    'text_length': len(frontmatter.get('text', '')),
                                    'file_path': str(md_file)
                                }
                                records.append(record)

                    except Exception as e:
                        print(f"Error loading {md_file}: {e}")

            current_date += timedelta(days=1)

        # Create dataframe
        posts_data = pd.DataFrame(records)

        # Convert date column to datetime if records exist
        if not posts_data.empty:
            posts_data['date'] = pd.to_datetime(posts_data['date'])

        return posts_data

    return (load_posts,)


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

    Select how many days of posts to analyze:

    {days_slider}
    """)
    return (days_slider,)


@app.cell
def _(days_slider, load_posts, mo):
    # Load the data
    posts_data = load_posts(days_back=days_slider.value)

    mo.md(f"""
    ### Data Loaded

    - **Total posts:** {len(posts_data)}
    - **Date range:** {posts_data['date'].min().strftime('%Y-%m-%d') if not posts_data.empty else 'N/A'} to {posts_data['date'].max().strftime('%Y-%m-%d') if not posts_data.empty else 'N/A'}
    - **Unique authors:** {posts_data['author'].nunique() if not posts_data.empty else 0}
    - **Total engagement:** {posts_data['total_engagement'].sum() if not posts_data.empty else 0:,}
    """)
    return (posts_data,)


@app.cell
def _(mo):
    mo.md("""## Engagement Overview""")
    return


@app.cell
def _(mo, pd, posts_data):
    # Calculate engagement statistics
    engagement_stats = {
        'Metric': ['Total Likes', 'Total Reposts', 'Total Replies', 'Avg Likes per Post', 'Avg Reposts per Post', 'Avg Replies per Post'],
        'Value': [
            posts_data['likes'].sum(),
            posts_data['reposts'].sum(),
            posts_data['replies'].sum(),
            round(posts_data['likes'].mean(), 2),
            round(posts_data['reposts'].mean(), 2),
            round(posts_data['replies'].mean(), 2)
        ]
    }

    engagement_df = pd.DataFrame(engagement_stats)

    mo.ui.table(
        engagement_df,
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo):
    mo.md("""## Top Posts by Engagement""")
    return


@app.cell
def _(mo, posts_data):
    # Get top posts by total engagement
    top_posts = posts_data.nlargest(20, 'total_engagement')[
        ['author', 'created_at', 'likes', 'reposts', 'replies', 'total_engagement', 'has_urls']
    ]

    mo.ui.table(
        top_posts,
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo):
    mo.md("""## Author Analysis""")
    return


@app.cell
def _(mo, posts_data):
    # Analyze authors by engagement
    author_stats = posts_data.groupby('author').agg({
        'post_id': 'count',
        'likes': ['sum', 'mean'],
        'reposts': ['sum', 'mean'],
        'replies': ['sum', 'mean'],
        'total_engagement': ['sum', 'mean']
    }).round(2)

    # Flatten column names
    author_stats.columns = ['posts', 'total_likes', 'avg_likes', 'total_reposts', 'avg_reposts', 
                            'total_replies', 'avg_replies', 'total_engagement', 'avg_engagement']

    # Sort by total engagement
    author_stats = author_stats.sort_values('total_engagement', ascending=False).head(20)

    mo.ui.table(
        author_stats.reset_index(),
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo):
    mo.md("""## Time Analysis""")
    return


@app.cell
def _(mo, posts_data):
    # Analyze by hour of day
    hourly_stats = posts_data.groupby('hour_of_day').agg({
        'post_id': 'count',
        'total_engagement': 'mean'
    }).round(2)

    hourly_stats.columns = ['posts', 'avg_engagement']
    hourly_stats = hourly_stats.reset_index()

    mo.ui.table(
        hourly_stats,
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo, posts_data):
    # Analyze by day of week
    daily_stats = posts_data.groupby('day_of_week').agg({
        'post_id': 'count',
        'total_engagement': 'mean'
    }).round(2)

    daily_stats.columns = ['posts', 'avg_engagement']

    # Reorder by weekday
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_stats = daily_stats.reindex(weekday_order, fill_value=0)

    mo.ui.table(
        daily_stats.reset_index(),
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo):
    mo.md("""## Content Analysis""")
    return


@app.cell
def _(mo, posts_data):
    # Analyze posts with URLs vs without
    url_analysis = posts_data.groupby('has_urls').agg({
        'post_id': 'count',
        'likes': 'mean',
        'reposts': 'mean',
        'replies': 'mean',
        'total_engagement': 'mean'
    }).round(2)

    url_analysis.index = ['No URLs', 'Has URLs']
    url_analysis.columns = ['posts', 'avg_likes', 'avg_reposts', 'avg_replies', 'avg_engagement']

    mo.ui.table(
        url_analysis.reset_index(),
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo, np, pd, posts_data):
    # Analyze by text length
    posts_with_length = posts_data.copy()
    posts_with_length['length_category'] = pd.cut(
        posts_with_length['text_length'], 
        bins=[0, 100, 200, 300, np.inf],
        labels=['Short (<100)', 'Medium (100-200)', 'Long (200-300)', 'Very Long (>300)']
    )

    length_stats = posts_with_length.groupby('length_category').agg({
        'post_id': 'count',
        'total_engagement': 'mean'
    }).round(2)

    length_stats.columns = ['posts', 'avg_engagement']

    mo.ui.table(
        length_stats.reset_index(),
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo):
    mo.md("""## Engagement Distribution""")
    return


@app.cell
def _(mo, pd, posts_data):
    # Calculate engagement percentiles
    percentiles = [0, 25, 50, 75, 90, 95, 99, 100]
    engagement_dist = posts_data['total_engagement'].describe(percentiles=[p/100 for p in percentiles[1:-1]])

    dist_df = pd.DataFrame({
        'Statistic': engagement_dist.index,
        'Value': engagement_dist.values.round(2)
    })

    mo.ui.table(
        dist_df,
        selection=None,
        pagination=False
    )
    return


@app.cell
def _(mo):
    mo.md("""## Filters""")
    return


@app.cell
def _(mo, posts_data):
    # Create filter controls
    min_engagement = mo.ui.slider(
        start=0,
        stop=int(posts_data['total_engagement'].max()) if not posts_data.empty else 100,
        step=1,
        value=0,
        label="Minimum total engagement"
    )

    # Get unique authors for dropdown
    authors = ["All"] + sorted(posts_data['author'].unique().tolist())
    author_filter = mo.ui.dropdown(
        options=authors,
        value="All",
        label="Filter by author"
    )

    mo.hstack([min_engagement, author_filter])
    return author_filter, min_engagement


@app.cell
def _(author_filter, min_engagement, mo, posts_data):
    # Apply filters
    filtered_posts = posts_data.copy()

    if min_engagement.value > 0:
        filtered_posts = filtered_posts[filtered_posts['total_engagement'] >= min_engagement.value]

    if author_filter.value != "All":
        filtered_posts = filtered_posts[filtered_posts['author'] == author_filter.value]

    mo.md(f"""
    ### Filtered Results

    Showing **{len(filtered_posts)}** of {len(posts_data)} posts
    """)

    mo.ui.table(
        filtered_posts[['author', 'created_at', 'likes', 'reposts', 'replies', 'total_engagement', 'has_urls']].head(30),
        selection=None,
        pagination=True,
        page_size=20
    )
    return


if __name__ == "__main__":
    app.run()
