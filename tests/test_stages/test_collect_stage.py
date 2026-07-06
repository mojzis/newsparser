from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.config.settings import Settings
from src.models.post import BlueskyPost, EngagementMetrics
from src.stages.collect import CollectStage


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
def sample_post():
    return BlueskyPost(
        id="at://did:plc:example/app.bsky.feed.post/123",
        author="user.bsky.social",
        content="Check out this MCP tool",
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0),
    )


class TestPostToMarkdown:
    def test_frontmatter_includes_source(self, mock_settings, sample_post):
        """post_to_markdown includes the post's source in frontmatter."""
        stage = CollectStage(settings=mock_settings, expand_references=False)

        md_file = stage.post_to_markdown(sample_post, date(2024, 1, 15))

        assert md_file.frontmatter["source"] == "bluesky"


class TestCollectPostsUsesSource:
    def test_bluesky_source_shares_collect_stage_client(self, mock_settings):
        """BlueskySource is wired to reuse CollectStage's client (single login)."""
        stage = CollectStage(settings=mock_settings)

        assert stage.bluesky_source._client is stage.bluesky_client

    @pytest.mark.asyncio
    async def test_collect_posts_uses_bluesky_source_for_search(
        self, mock_settings, sample_post
    ):
        """collect_posts() obtains search results via BlueskySource."""
        stage = CollectStage(
            settings=mock_settings,
            expand_urls=False,
            expand_references=False,
            collect_threads=False,
        )

        with (
            patch.object(
                stage.bluesky_source,
                "search",
                new=AsyncMock(return_value=[sample_post]),
            ) as mock_search,
            patch.object(
                stage.bluesky_client,
                "authenticate",
                new=AsyncMock(return_value=True),
            ) as mock_authenticate,
        ):
            result = await stage.collect_posts(date(2024, 1, 15))

        assert result == [sample_post]
        mock_search.assert_called_once_with(stage.search_definition, stage.max_posts)
        # Only one authenticated session should be opened for the whole collect run.
        mock_authenticate.assert_called_once()
