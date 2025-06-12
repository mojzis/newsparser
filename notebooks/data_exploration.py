import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        r"""
    # Bluesky MCP Monitor - Data Exploration

    This notebook allows you to explore the collected Bluesky posts data stored in Cloudflare R2.

    ## Setup
    Make sure you have your R2 credentials configured in your environment variables.
    """
    )
    return


@app.cell
def _():
    # Import required libraries
    import asyncio
    import json
    from datetime import date, datetime, timedelta
    from typing import List

    import pandas as pd

    # Import our modules
    from src.bluesky.collector import BlueskyDataCollector
    from src.config.settings import get_settings
    from src.models.post import BlueskyPost


    return BlueskyDataCollector, date, datetime, get_settings, pd


@app.cell
def _(BlueskyDataCollector, get_settings, mo):
    # Initialize settings and collector
    settings = get_settings()
    collector = BlueskyDataCollector(settings)

    # Check credentials
    if not settings.has_bluesky_credentials:
        mo.md("⚠️ **Warning**: Bluesky credentials not configured. Data collection will not work.")
    else:
        mo.md("✅ **Settings loaded**: Ready to explore data")
    return collector, settings


@app.cell
def _(date, mo):
    # Date selector for exploration
    target_date_input = mo.ui.date(value=date.today(), label="Select date to explore:")
    target_date_input
    return (target_date_input,)


@app.cell
def _(collector, mo, target_date_input):
    # Check if data exists for selected date
    selected_date = target_date_input.value

    data_exists = collector.check_stored_data(selected_date)

    if data_exists:
        mo.md(f"✅ **Data found** for {selected_date}")
    else:
        mo.md(f"❌ **No data found** for {selected_date}. Try collecting data first or select a different date.")
    return data_exists, selected_date


@app.cell
def _(collector, data_exists, mo, selected_date):
    # Load posts for selected date
    if data_exists:
        posts = collector.get_stored_posts_sync(selected_date)

        if posts:
            mo.md(f"📊 **Loaded {len(posts)} posts** for {selected_date}")
        else:
            mo.md("⚠️ Data file exists but no posts could be loaded.")
            posts = []
    else:
        posts = []
        mo.md("No posts to display.")
    return (posts,)


@app.cell
def _(mo, pd, posts):
    # Convert posts to DataFrame for analysis
    if posts:
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'author': post.author,
                'content': post.content,
                'created_at': post.created_at,
                'likes': post.engagement_metrics.likes,
                'reposts': post.engagement_metrics.reposts,
                'replies': post.engagement_metrics.replies,
                'total_engagement': post.engagement_metrics.likes + post.engagement_metrics.reposts + post.engagement_metrics.replies,
                'has_links': len(post.links) > 0,
                'link_count': len(post.links),
                'content_length': len(post.content),
                'tags': ', '.join(post.tags) if post.tags else '',
                'tag_count': len(post.tags),
                'has_tags': len(post.tags) > 0,
            })

        df = pd.DataFrame(posts_data)
        mo.md(f"📈 **DataFrame created** with {len(df)} rows and {len(df.columns)} columns")
    else:
        df = pd.DataFrame()
        mo.md("No data to convert to DataFrame.")
    return (df,)


@app.cell
def _(df, mo):
    # Display basic statistics
    if not df.empty:
        stats_table = mo.ui.table(
            data={
                "Metric": [
                    "Total Posts",
                    "Unique Authors", 
                    "Avg Content Length",
                    "Posts with Links",
                    "Total Likes",
                    "Total Reposts", 
                    "Total Replies",
                    "Most Active Author",
                    "Highest Engagement Post"
                ],
                "Value": [
                    len(df),
                    df['author'].nunique(),
                    f"{df['content_length'].mean():.1f} chars",
                    f"{df['has_links'].sum()} ({df['has_links'].mean()*100:.1f}%)",
                    df['likes'].sum(),
                    df['reposts'].sum(),
                    df['replies'].sum(),
                    df['author'].value_counts().index[0] if len(df) > 0 else "N/A",
                    df.loc[df['total_engagement'].idxmax(), 'author'] if len(df) > 0 else "N/A"
                ]
            },
            label="📊 Data Overview"
        )
        stats_table
    else:
        mo.md("No statistics to display.")
    return


@app.cell
def _(df, mo):
    # Top authors by post count
    if not df.empty:
        top_authors = df['author'].value_counts().head(10)

        author_table_data = {
            "Author": top_authors.index.tolist(),
            "Post Count": top_authors.values.tolist()
        }

        author_table = mo.ui.table(
            data=author_table_data,
            label="👥 Top Authors by Post Count"
        )
        author_table
    else:
        mo.md("No author data to display.")
    return


@app.cell
def _(df, mo):
    # Popular tags analysis
    if not df.empty and df['tag_count'].sum() > 0:
        # Flatten all tags and count occurrences
        all_tags = []
        for tags_str in df['tags']:
            if tags_str:  # If tags string is not empty
                all_tags.extend(tags_str.split(', '))
        
        if all_tags:
            from collections import Counter
            tag_counts = Counter(all_tags)
            top_tags = tag_counts.most_common(10)
            
            tag_table_data = {
                "Tag": [f"#{tag}" for tag, count in top_tags],
                "Usage Count": [count for tag, count in top_tags],
                "Percentage": [f"{(count/len(df))*100:.1f}%" for tag, count in top_tags]
            }
            
            tag_table = mo.ui.table(
                data=tag_table_data,
                label="🏷️ Most Popular Tags"
            )
            tag_table
        else:
            mo.md("No tags found in the dataset.")
    else:
        mo.md("No tag data to display.")
    return


@app.cell
def _(df, mo):
    # Engagement analysis
    if not df.empty:
        engagement_stats = df[['likes', 'reposts', 'replies', 'total_engagement']].describe()

        engagement_table_data = {
            "Metric": engagement_stats.index.tolist(),
            "Likes": engagement_stats['likes'].round(2).tolist(),
            "Reposts": engagement_stats['reposts'].round(2).tolist(), 
            "Replies": engagement_stats['replies'].round(2).tolist(),
            "Total": engagement_stats['total_engagement'].round(2).tolist()
        }

        engagement_table = mo.ui.table(
            data=engagement_table_data,
            label="📈 Engagement Statistics"
        )
        engagement_table
    else:
        mo.md("No engagement data to display.")
    return


@app.cell
def _(df, mo):
    # Most engaging posts
    if not df.empty and len(df) > 0:
        top_posts = df.nlargest(5, 'total_engagement')[['author', 'content', 'total_engagement', 'likes', 'reposts', 'replies']]

        top_posts_data = {
            "Author": top_posts['author'].tolist(),
            "Content (truncated)": [content[:80] + "..." if len(content) > 80 else content for content in top_posts['content'].tolist()],
            "Total": top_posts['total_engagement'].tolist(),
            "❤️": top_posts['likes'].tolist(),
            "🔄": top_posts['reposts'].tolist(),
            "💬": top_posts['replies'].tolist()
        }

        top_posts_table = mo.ui.table(
            data=top_posts_data,
            label="🔥 Most Engaging Posts"
        )
        top_posts_table
    else:
        mo.md("No post engagement data to display.")
    return


@app.cell
def _(df, mo):
    # Content analysis
    if not df.empty:
        # Analyze content characteristics
        content_stats = {
            "Average Length": f"{df['content_length'].mean():.1f} characters",
            "Median Length": f"{df['content_length'].median():.1f} characters", 
            "Shortest Post": f"{df['content_length'].min()} characters",
            "Longest Post": f"{df['content_length'].max()} characters",
            "Posts with Links": f"{df['has_links'].sum()} ({df['has_links'].mean()*100:.1f}%)",
            "Total Links": df['link_count'].sum(),
            "Posts with Tags": f"{df['has_tags'].sum()} ({df['has_tags'].mean()*100:.1f}%)",
            "Total Tags": df['tag_count'].sum(),
            "Average Tags per Post": f"{df['tag_count'].mean():.1f}"
        }

        content_table_data = {
            "Metric": list(content_stats.keys()),
            "Value": list(content_stats.values())
        }

        content_table = mo.ui.table(
            data=content_table_data,
            label="📝 Content Analysis"
        )
        content_table
    else:
        mo.md("No content analysis to display.")
    return


@app.cell
def _(df, mo):
    # Raw data explorer
    if not df.empty:
        mo.md("## 🔍 Raw Data Explorer")

        # Add filters
        author_filter = mo.ui.multiselect(
            options=sorted(df['author'].unique().tolist()),
            label="Filter by authors:"
        )

        min_engagement = mo.ui.slider(
            start=0, 
            stop=int(df['total_engagement'].max()) if len(df) > 0 else 100,
            value=0,
            label="Minimum engagement:"
        )

        mo.hstack([author_filter, min_engagement])
    else:
        mo.md("No data to explore.")
    return author_filter, min_engagement


@app.cell
def _(author_filter, df, min_engagement, mo):
    # Filtered data display
    if not df.empty:
        # Apply filters
        filtered_df = df.copy()

        if author_filter.value:
            filtered_df = filtered_df[filtered_df['author'].isin(author_filter.value)]

        if min_engagement.value > 0:
            filtered_df = filtered_df[filtered_df['total_engagement'] >= min_engagement.value]

        if len(filtered_df) > 0:
            # Display filtered results
            display_columns = ['author', 'content', 'total_engagement', 'likes', 'reposts', 'replies', 'has_links', 'tags', 'tag_count']

            # Truncate content for display
            display_df = filtered_df[display_columns].copy()
            display_df['content'] = display_df['content'].apply(
                lambda x: x[:100] + "..." if len(x) > 100 else x
            )

            filtered_table_data = {
                col: display_df[col].tolist() for col in display_df.columns
            }

            filtered_table = mo.ui.table(
                data=filtered_table_data,
                label=f"📊 Filtered Results ({len(filtered_df)} posts)"
            )
            filtered_table
        else:
            mo.md("❌ No posts match the current filters.")
    else:
        mo.md("No data to filter.")
    return (filtered_df,)


@app.cell
def _(df, mo):
    # Export options
    if not df.empty:
        mo.md("## 💾 Export Data")

        export_format = mo.ui.dropdown(
            options=["CSV", "JSON", "Parquet"],
            value="CSV",
            label="Export format:"
        )

        export_filtered = mo.ui.checkbox(
            label="Export only filtered data"
        )

        mo.hstack([export_format, export_filtered])
    else:
        mo.md("No data to export.")
    return export_filtered, export_format


@app.cell
def _(filtered_df):
    filtered_df
    return


@app.cell
def _(
    datetime,
    df,
    export_filtered,
    export_format,
    filtered_df,
    mo,
    selected_date,
):
    # Export functionality
    if not df.empty:
        export_button = mo.ui.button(label="📥 Export Data")

        if export_button.value:
            # Determine which data to export
            export_df = filtered_df if export_filtered.value and len(filtered_df) > 0 else df

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bluesky_mcp_posts_{selected_date}_{timestamp}"

            if export_format.value == "CSV":
                export_df.to_csv(f"{filename}.csv", index=False)
                mo.md(f"✅ **Exported** {len(export_df)} posts to `{filename}.csv`")
            elif export_format.value == "JSON":
                export_df.to_json(f"{filename}.json", orient="records", indent=2)
                mo.md(f"✅ **Exported** {len(export_df)} posts to `{filename}.json`")
            elif export_format.value == "Parquet":
                export_df.to_parquet(f"{filename}.parquet", index=False)
                mo.md(f"✅ **Exported** {len(export_df)} posts to `{filename}.parquet`")

        export_button
    else:
        mo.md("No data available for export.")
    return


@app.cell
def _(mo):
    # Data collection interface
    mo.md("""
    ## 🔄 Data Collection

    Use the CLI commands to collect new data:

    ```bash
    # Collect posts for today
    poetry run nsp collect

    # Collect posts for a specific date
    poetry run nsp collect --date 2024-01-15

    # Check data status
    poetry run nsp status --date 2024-01-15

    # List posts
    poetry run nsp list-posts --date 2024-01-15 --limit 10
    ```

    Or collect data directly from this notebook (if credentials are configured):
    """)
    return


@app.cell
def _(date, mo, settings):
    # Collection interface
    if settings.has_bluesky_credentials:
        collect_date = mo.ui.date(value=date.today(), label="Date to collect:")
        max_posts_input = mo.ui.number(start=1, stop=500, value=100, label="Max posts:")

        mo.hstack([collect_date, max_posts_input])
    else:
        mo.md("⚠️ Configure Bluesky credentials to enable data collection.")
    return collect_date, max_posts_input


@app.cell
def _(collect_date, max_posts_input, mo, settings):
    # Collection button
    if settings.has_bluesky_credentials:
        collect_button = mo.ui.button(label="🔄 Collect Data")

        if collect_button.value:
            mo.md("🔄 **Data collection disabled in notebook** - use CLI instead:")
            mo.md(f"```bash\npoetry run nsp collect --date {collect_date.value} --max-posts {max_posts_input.value}\n```")

        collect_button
    else:
        mo.md("Configure credentials to enable data collection.")
    return


if __name__ == "__main__":
    app.run()
