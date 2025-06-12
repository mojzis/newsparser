import marimo

__generated_with = "0.10.6"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    return (mo,)


@app.cell
def __():
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
def __():
    # Import required libraries
    import asyncio
    import json
    from datetime import date, datetime, timedelta
    from typing import List
    
    import pandas as pd
    from rich.console import Console
    from rich.table import Table
    
    # Import our modules
    from src.bluesky.collector import BlueskyDataCollector
    from src.config.settings import get_settings
    from src.models.post import BlueskyPost
    
    console = Console()
    return BlueskyDataCollector, BlueskyPost, Console, List, Table, asyncio, console, date, datetime, get_settings, json, pd, timedelta


@app.cell
def __():
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
def __():
    # Date selector for exploration
    target_date_input = mo.ui.date(value=date.today(), label="Select date to explore:")
    target_date_input
    return (target_date_input,)


@app.cell
def __():
    # Check if data exists for selected date
    selected_date = target_date_input.value
    
    data_exists = collector.check_stored_data(selected_date)
    
    if data_exists:
        mo.md(f"✅ **Data found** for {selected_date}")
    else:
        mo.md(f"❌ **No data found** for {selected_date}. Try collecting data first or select a different date.")
    return data_exists, selected_date


@app.cell
def __():
    # Load posts for selected date
    if data_exists:
        posts = asyncio.run(collector.get_stored_posts(selected_date))
        
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
def __():
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
            })
        
        df = pd.DataFrame(posts_data)
        mo.md(f"📈 **DataFrame created** with {len(df)} rows and {len(df.columns)} columns")
    else:
        df = pd.DataFrame()
        mo.md("No data to convert to DataFrame.")
    return df, posts_data


@app.cell
def __():
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
    return (stats_table,)


@app.cell
def __():
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
    return author_table, author_table_data, top_authors


@app.cell
def __():
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
    return engagement_stats, engagement_table, engagement_table_data


@app.cell
def __():
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
    return top_posts, top_posts_data, top_posts_table


@app.cell
def __():
    # Content analysis
    if not df.empty:
        # Analyze content characteristics
        content_stats = {
            "Average Length": f"{df['content_length'].mean():.1f} characters",
            "Median Length": f"{df['content_length'].median():.1f} characters", 
            "Shortest Post": f"{df['content_length'].min()} characters",
            "Longest Post": f"{df['content_length'].max()} characters",
            "Posts with Links": f"{df['has_links'].sum()} ({df['has_links'].mean()*100:.1f}%)",
            "Total Links": df['link_count'].sum()
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
    return content_stats, content_table, content_table_data


@app.cell
def __():
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
def __():
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
            display_columns = ['author', 'content', 'total_engagement', 'likes', 'reposts', 'replies', 'has_links']
            
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
    return display_columns, display_df, filtered_df, filtered_table, filtered_table_data


@app.cell
def __():
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
def __():
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
    return export_button, export_df, filename, timestamp


@app.cell
def __():
    # Data collection interface
    mo.md("""
    ## 🔄 Data Collection
    
    Use the CLI commands to collect new data:
    
    ```bash
    # Collect posts for today
    poetry run newsparser collect
    
    # Collect posts for a specific date
    poetry run newsparser collect --date 2024-01-15
    
    # Check data status
    poetry run newsparser status --date 2024-01-15
    
    # List posts
    poetry run newsparser list-posts --date 2024-01-15 --limit 10
    ```
    
    Or collect data directly from this notebook (if credentials are configured):
    """)
    return


@app.cell
def __():
    # Collection interface
    if settings.has_bluesky_credentials:
        collect_date = mo.ui.date(value=date.today(), label="Date to collect:")
        max_posts_input = mo.ui.number(start=1, stop=500, value=100, label="Max posts:")
        
        mo.hstack([collect_date, max_posts_input])
    else:
        mo.md("⚠️ Configure Bluesky credentials to enable data collection.")
    return collect_date, max_posts_input


@app.cell
def __():
    # Collection button
    if settings.has_bluesky_credentials:
        collect_button = mo.ui.button(label="🔄 Collect Data")
        
        if collect_button.value:
            mo.md("🔄 **Collecting data...** This may take a moment.")
            
            try:
                posts_count, success = asyncio.run(
                    collector.collect_and_store(
                        target_date=collect_date.value,
                        max_posts=max_posts_input.value
                    )
                )
                
                if success:
                    mo.md(f"✅ **Successfully collected** {posts_count} posts for {collect_date.value}")
                else:
                    mo.md(f"⚠️ **Collected** {posts_count} posts but storage failed")
                    
            except Exception as e:
                mo.md(f"❌ **Collection failed:** {str(e)}")
        
        collect_button
    else:
        mo.md("Configure credentials to enable data collection.")
    return (collect_button,)


if __name__ == "__main__":
    app.run()