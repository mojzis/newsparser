import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("# Bluesky MCP Monitor - Content Analysis")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    from pathlib import Path
    from datetime import datetime, date, timedelta
    from collections import Counter
    
    return Counter, Path, datetime, mo, pd


@app.cell
def _(Path):
    # Define parquet directories
    parquet_dir = Path("parquet")
    collect_dir = parquet_dir / "collect" / "by-run-date"
    evaluate_dir = parquet_dir / "evaluate" / "by-run-date"
    
    return collect_dir, evaluate_dir


@app.cell
def _(collect_dir, evaluate_dir, mo):
    mo.md(f"""
    ## Data Sources
    
    Analyzing content from the latest parquet files:
    - **Posts**: `{collect_dir}`
    - **Evaluations**: `{evaluate_dir}`
    """)


@app.cell
def _(collect_dir, pd):
    # Load latest collect data
    collect_files = list(collect_dir.glob("*.parquet"))
    latest_collect_file = max(collect_files, key=lambda x: x.stat().st_mtime)
    posts_df = pd.read_parquet(latest_collect_file)
    
    return posts_df,


@app.cell
def _(evaluate_dir, pd):
    # Load latest evaluate data
    evaluate_files = list(evaluate_dir.glob("*.parquet"))
    latest_evaluate_file = max(evaluate_files, key=lambda x: x.stat().st_mtime)
    articles_df = pd.read_parquet(latest_evaluate_file)
    
    return articles_df,


@app.cell
def _(mo, posts_df):
    mo.md(f"""
    ### Post Language Distribution
    
    Analysis of {len(posts_df):,} collected posts by detected language family.
    """)


@app.cell
def _(posts_df):
    # Analyze post languages
    language_counts = posts_df['language'].value_counts()
    language_percentages = (language_counts / len(posts_df) * 100).round(1)
    
    return language_counts, language_percentages


@app.cell
def _(language_counts, language_percentages, mo, pd):
    language_df = pd.DataFrame({
        'Language': language_counts.head(10).index,
        'Posts': language_counts.head(10).values,
        'Percentage': language_percentages.head(10).values
    })
    
    mo.ui.table(language_df)


@app.cell
def _(mo, posts_df):
    mo.md(f"""
    ### Top Bluesky Authors
    
    Most active authors in the {len(posts_df):,} collected posts.
    """)


@app.cell
def _(posts_df):
    # Analyze top authors
    author_counts = posts_df['author'].value_counts()
    
    return author_counts,


@app.cell
def _(author_counts, mo, pd):
    author_df = pd.DataFrame({
        'Author': author_counts.head(15).index,
        'Posts': author_counts.head(15).values
    })
    
    mo.ui.table(author_df)


@app.cell
def _(mo, posts_df):
    mo.md(f"""
    ### Engagement Metrics
    
    Post engagement patterns across {len(posts_df):,} posts.
    """)


@app.cell
def _(posts_df):
    # Calculate engagement statistics
    engagement_cols = ['engagement_metrics_likes', 'engagement_metrics_reposts', 'engagement_metrics_replies']
    available_cols = [col for col in engagement_cols if col in posts_df.columns]
    
    engagement_stats = posts_df[available_cols].describe()
    total_engagement = posts_df[available_cols].sum().sum()
    
    return engagement_stats, total_engagement


@app.cell
def _(engagement_stats, mo, pd, posts_df, total_engagement):
    likes_avg = engagement_stats.loc['mean', 'engagement_metrics_likes'] if 'engagement_metrics_likes' in engagement_stats.columns else 0
    reposts_avg = engagement_stats.loc['mean', 'engagement_metrics_reposts'] if 'engagement_metrics_reposts' in engagement_stats.columns else 0
    replies_avg = engagement_stats.loc['mean', 'engagement_metrics_replies'] if 'engagement_metrics_replies' in engagement_stats.columns else 0
    posts_with_engagement = (posts_df[posts_df[engagement_stats.columns].sum(axis=1) > 0]).shape[0]
    
    engagement_summary_df = pd.DataFrame({
        'Metric': ['Total Interactions', 'Avg Likes/Post', 'Avg Reposts/Post', 'Avg Replies/Post', 'Posts with Engagement'],
        'Value': [f"{total_engagement:,}", f"{likes_avg:.1f}", f"{reposts_avg:.1f}", f"{replies_avg:.1f}", f"{posts_with_engagement:,}"]
    })
    
    mo.ui.table(engagement_summary_df)


@app.cell
def _(articles_df, mo):
    mo.md(f"""
    ### Article Content Analysis
    
    Analysis of {len(articles_df):,} evaluated articles.
    """)


@app.cell
def _(articles_df):
    # Analyze article content types
    content_type_counts = articles_df['content_type'].value_counts()
    
    return content_type_counts,


@app.cell
def _(content_type_counts, mo, pd):
    content_type_percentages = (content_type_counts / content_type_counts.sum() * 100).round(1)
    content_type_df = pd.DataFrame({
        'Content Type': content_type_counts.index,
        'Articles': content_type_counts.values,
        'Percentage': content_type_percentages.values
    })
    
    mo.ui.table(content_type_df)


@app.cell
def _(articles_df):
    # Analyze article languages
    article_language_counts = articles_df['language'].value_counts()
    
    return article_language_counts,


@app.cell
def _(article_language_counts, mo, pd):
    article_language_percentages = (article_language_counts / article_language_counts.sum() * 100).round(1)
    article_language_df = pd.DataFrame({
        'Language': article_language_counts.head(10).index,
        'Articles': article_language_counts.head(10).values,
        'Percentage': article_language_percentages.head(10).values
    })
    
    mo.ui.table(article_language_df)


@app.cell
def _(articles_df):
    # MCP relevance analysis
    mcp_related_count = articles_df['is_mcp_related'].sum()
    total_articles = len(articles_df)
    mcp_percentage = (mcp_related_count / total_articles * 100)
    
    avg_relevance = articles_df['relevance_score'].mean()
    high_relevance_count = (articles_df['relevance_score'] > 0.8).sum()
    
    return avg_relevance, high_relevance_count, mcp_percentage, mcp_related_count, total_articles


@app.cell
def _(avg_relevance, high_relevance_count, mcp_percentage, mcp_related_count, mo, pd, total_articles):
    mcp_relevance_df = pd.DataFrame({
        'Metric': ['MCP-related Articles', 'Total Articles', 'MCP Percentage', 'Avg Relevance Score', 'Highly Relevant (>0.8)'],
        'Value': [f"{mcp_related_count:,}", f"{total_articles:,}", f"{mcp_percentage:.1f}%", f"{avg_relevance:.3f}", f"{high_relevance_count:,}"]
    })
    
    mo.ui.table(mcp_relevance_df)


@app.cell
def _(Counter, articles_df):
    # Analyze key topics
    all_topics = []
    for topics_list in articles_df['key_topics'].dropna():
        if isinstance(topics_list, list):
            all_topics.extend([topic.lower() for topic in topics_list])
    
    topic_counter = Counter(all_topics)
    top_topics = topic_counter.most_common(20)
    
    return top_topics,


@app.cell
def _(mo, pd, top_topics):
    topics_df = pd.DataFrame(top_topics, columns=['Topic', 'Mentions'])
    
    mo.ui.table(topics_df)


@app.cell
def _(articles_df):
    # Analyze domains
    domain_counts = articles_df['domain'].value_counts()
    
    return domain_counts,


@app.cell
def _(domain_counts, mo, pd):
    domain_percentages = (domain_counts / domain_counts.sum() * 100).round(1)
    domains_df = pd.DataFrame({
        'Domain': domain_counts.head(15).index,
        'Articles': domain_counts.head(15).values,
        'Percentage': domain_percentages.head(15).values
    })
    
    mo.ui.table(domains_df)


@app.cell
def _(articles_df):
    # Word count analysis
    word_count_stats = articles_df['word_count'].describe()
    long_articles = (articles_df['word_count'] > 2000).sum()
    short_articles = (articles_df['word_count'] < 500).sum()
    
    return long_articles, short_articles, word_count_stats


@app.cell
def _(long_articles, mo, pd, short_articles, word_count_stats):
    word_length_df = pd.DataFrame({
        'Metric': ['Average Words', 'Median Words', 'Long Articles (>2000)', 'Short Articles (<500)', 'Longest Article'],
        'Value': [f"{word_count_stats['mean']:.0f}", f"{word_count_stats['50%']:.0f}", f"{long_articles:,}", f"{short_articles:,}", f"{word_count_stats['max']:.0f}"]
    })
    
    mo.ui.table(word_length_df)


@app.cell
def _(datetime, mo):
    mo.md(f"""
    ## Summary
    
    **Content analysis generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    This dashboard provides insights into the actual content collected and evaluated by the Bluesky MCP Monitor, including post languages, author activity, article types, and topic trends.
    """)


if __name__ == "__main__":
    app.run()