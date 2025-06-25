# Bluesky MCP Monitor

A daily service that monitors Bluesky for Model Context Protocol (MCP) mentions, analyzes content quality using AI, and generates comprehensive reports.

## Overview

The Bluesky MCP Monitor is an automated system designed to track conversations and developments around the Model Context Protocol (MCP) on the Bluesky social network. The system provides valuable insights into community engagement, content quality, and emerging trends in the MCP ecosystem.

## How It Works

The monitor operates through a multi-stage processing pipeline:

1. **Collect**: Searches Bluesky for posts containing MCP-related keywords and hashtags
2. **Fetch**: Extracts and retrieves content from URLs found in collected posts
3. **Evaluate**: Uses advanced AI to analyze article quality, relevance, and categorization
4. **Report**: Generates HTML reports and automatically posts summaries back to Bluesky

## Key Features

- **Intelligent Content Analysis**: AI-powered evaluation of articles for relevance and quality
- **Automated URL Processing**: Expands shortened URLs and fetches full article content
- **Historical Data Storage**: Maintains 7-day rolling archives in efficient Parquet format
- **Interactive Analytics**: Web-based DuckDB query interface for data exploration
- **Cloud Storage**: Seamless integration with Cloudflare R2 for scalable data storage
- **Daily Automation**: Fully automated daily execution with comprehensive error handling

## Data Pipeline

The system processes data through fault-tolerant stages, storing intermediate results as individual markdown files for reliability. Each stage can be run independently or as part of a complete pipeline, making the system robust and maintainable.

## Use Cases

- Track MCP adoption and community growth
- Identify high-quality content and thought leaders
- Monitor emerging trends and discussions
- Analyze engagement patterns and content distribution
- Research community sentiment and feedback

Built with Python, leveraging the Anthropic API for content evaluation and modern data tools for storage and analysis.

## System Statistics

- **[Content Analytics](/content_stats.html)**: Explore post languages, authors, article types, and trending topics
- **[Project Statistics](/project_stats.html)**: View technical metrics, file counts, and system performance data