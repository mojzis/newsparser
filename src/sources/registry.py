"""Single source of truth for which source names exist and how to build them."""

from collections.abc import Callable

from src.bluesky.client import BlueskyClient
from src.config.settings import Settings
from src.sources.base import Source
from src.sources.bluesky import BlueskySource
from src.sources.hackernews import HackerNewsSource

# Each factory takes the shared (settings, bluesky_client) and returns a Source.
# Sources that don't need them (e.g. HackerNewsSource) simply ignore the args.
SourceFactory = Callable[[Settings, BlueskyClient], Source]

SOURCE_FACTORIES: dict[str, SourceFactory] = {
    "bluesky": lambda settings, bluesky_client: BlueskySource(
        settings, client=bluesky_client
    ),
    "hackernews": lambda _settings, _bluesky_client: HackerNewsSource(),
}

KNOWN_SOURCES: frozenset[str] = frozenset(SOURCE_FACTORIES)
