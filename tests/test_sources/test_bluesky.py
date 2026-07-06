from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.config.searches import SearchDefinition
from src.config.settings import Settings
from src.models.post import BlueskyPost, EngagementMetrics
from src.sources.bluesky import BlueskySource


@pytest.fixture
def mock_settings():
    """Create mock settings with Bluesky credentials."""
    return Settings(
        r2_access_key_id="test_key",
        r2_secret_access_key="test_secret",
        r2_bucket_name="test-bucket",
        r2_endpoint_url="https://test.r2.cloudflarestorage.com",
        bluesky_handle="test.bsky.social",
        bluesky_app_password="test-app-password",
    )


@pytest.fixture
def search_definition():
    return SearchDefinition(
        name="mcp_mentions",
        description="MCP mentions",
        include_terms=["mcp"],
    )


@pytest.fixture
def sample_posts():
    return [
        BlueskyPost(
            id="at://did:plc:example/app.bsky.feed.post/123",
            author="user.bsky.social",
            content="Check out this MCP tool",
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0),
        )
    ]


class TestBlueskySource:
    def test_name(self, mock_settings):
        source = BlueskySource(mock_settings)
        assert source.name == "bluesky"

    @pytest.mark.asyncio
    async def test_search_returns_bluesky_stamped_posts(
        self, mock_settings, search_definition, sample_posts
    ):
        """search() returns posts from get_posts_by_definition, stamped as bluesky."""
        with patch("src.sources.bluesky.BlueskyClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_posts_by_definition.return_value = sample_posts
            mock_client_class.return_value = mock_client

            source = BlueskySource(mock_settings)
            result = await source.search(search_definition, max_posts=10)

            assert result == sample_posts
            assert all(post.source == "bluesky" for post in result)
            mock_client.get_posts_by_definition.assert_called_once_with(
                search_definition=search_definition, max_posts=10
            )
            mock_client.__aenter__.assert_called_once()
            mock_client.__aexit__.assert_called_once()
