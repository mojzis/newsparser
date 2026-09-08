"""Bluesky implementation of the Source protocol."""

import logging

from src.bluesky.client import BlueskyClient
from src.config.searches import SearchDefinition
from src.config.settings import Settings
from src.models.post import BlueskyPost

logger = logging.getLogger(__name__)


class BlueskySource:
    """Searches Bluesky for posts matching a search definition.

    The post's `source` field is set via its model default ("bluesky"); this
    class does not stamp it explicitly.
    """

    name = "bluesky"

    def __init__(self, settings: Settings, client: BlueskyClient | None = None) -> None:
        """
        Args:
            settings: Application settings containing Bluesky credentials.
            client: Optional already-authenticated client to reuse (e.g. when a
                caller needs the same session for other calls). If omitted, a
                new client is created and its async context is managed
                internally for the duration of `search`.
        """
        self.settings = settings
        self._client = client

    async def search(
        self, search_definition: SearchDefinition, max_posts: int
    ) -> list[BlueskyPost]:
        """Search Bluesky for posts matching the search definition."""
        if self._client is not None:
            return await self._client.get_posts_by_definition(
                search_definition=search_definition, max_posts=max_posts
            )

        async with BlueskyClient(self.settings) as client:
            return await client.get_posts_by_definition(
                search_definition=search_definition, max_posts=max_posts
            )
