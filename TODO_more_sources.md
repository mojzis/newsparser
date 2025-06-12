Yes, there are several other open sources you could integrate:
Additional Content Sources
Hacker News

API: Official JSON API (https://github.com/HackerNews/API)
Free: Yes, no rate limits mentioned
Search: Can search for "mcp" in titles/comments
Data: Stories, comments, user info, timestamps
Reliability: Very stable, well-documented

Reddit

API: Official Reddit API
Authentication: Requires app registration (free)
Rate Limits: 100 requests/minute for personal use
Search: Can search subreddits and posts for "mcp"
Considerations: More complex auth (OAuth2), stricter rate limits

Other Sources

GitHub: Search repositories, issues, discussions mentioning "mcp"
Dev.to: Has API for articles
Lobste.rs: RSS feeds available
Twitter/X: API exists but has restrictions and costs

Integration Approach
Could modify the system to:

Multi-source parsing: Extend Phase 2 to include HN/Reddit parsers
Source tagging: Add source field to data schema
Unified scoring: Anthropic evaluation across all sources
Source-specific reports: Separate sections in HTML output

Recommendation
Start with Hacker News - it's the easiest to integrate, has reliable API, and likely high-quality MCP discussions. Reddit could be Phase 7 addition.