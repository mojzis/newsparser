"""Minimal protocol for post sources."""

from typing import Protocol

from src.config.searches import SearchDefinition
from src.models.post import BlueskyPost


class Source(Protocol):
    """A source that can search for posts matching a search definition."""

    name: str

    async def search(
        self, search_definition: SearchDefinition, max_posts: int
    ) -> list[BlueskyPost]:
        """Search this source for posts matching the given search definition."""
        ...
