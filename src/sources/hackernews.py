"""Hacker News (Algolia) implementation of the Source protocol."""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import HttpUrl

from src.config.searches import SearchDefinition
from src.models.post import BlueskyPost, EngagementMetrics

logger = logging.getLogger(__name__)

ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HackerNewsSource:
    """Searches Hacker News stories (via the free Algolia API) for a search definition.

    MVP: only `include_terms` are used to build the query (joined with spaces);
    `exclude_terms` are ignored since the Algolia endpoint has no per-source
    exclusion syntax here.
    """

    name = "hackernews"

    async def search(
        self, search_definition: SearchDefinition, max_posts: int
    ) -> list[BlueskyPost]:
        """Search Hacker News for stories matching the search definition."""
        query = " ".join(search_definition.include_terms)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    ALGOLIA_SEARCH_URL,
                    params={"query": query, "tags": "story", "hitsPerPage": max_posts},
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            logger.exception("Failed to search Hacker News")
            return []

        posts = []
        for hit in data.get("hits", []):
            post = self._hit_to_post(hit)
            if post is not None:
                posts.append(post)
        return posts

    def _hit_to_post(self, hit: dict[str, Any]) -> BlueskyPost | None:
        """Map a single Algolia hit to a BlueskyPost, or None if it can't be mapped."""
        title = hit.get("title")
        if not title or not title.strip():
            return None

        object_id = hit.get("objectID")
        url = hit.get("url")

        try:
            return BlueskyPost(
                id=f"hn_{object_id}",
                author=hit.get("author") or "unknown",
                content=title,
                created_at=datetime.fromtimestamp(hit["created_at_i"], tz=UTC),
                links=[HttpUrl(url)] if url else [],
                engagement_metrics=EngagementMetrics(
                    likes=hit.get("points") or 0,
                    reposts=0,
                    replies=hit.get("num_comments") or 0,
                ),
                source="hackernews",
            )
        except Exception:
            logger.exception(f"Failed to map Hacker News hit {object_id}")
            return None
