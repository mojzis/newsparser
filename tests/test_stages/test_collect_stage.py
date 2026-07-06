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

        assert stage.sources["bluesky"]._client is stage.bluesky_client

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
                stage.sources["bluesky"],
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


class TestCollectStageMultipleSources:
    def test_default_sources_is_bluesky_only(self, mock_settings):
        stage = CollectStage(settings=mock_settings)

        assert stage.source_names == ["bluesky"]
        assert set(stage.sources.keys()) == {"bluesky"}

    def test_hackernews_only_skips_bluesky_client(self, mock_settings):
        """When bluesky isn't configured, no Bluesky source is built."""
        stage = CollectStage(settings=mock_settings, sources=["hackernews"])

        assert set(stage.sources.keys()) == {"hackernews"}
        assert "bluesky" not in stage.sources

    @pytest.mark.asyncio
    async def test_collect_posts_aggregates_multiple_sources(
        self, mock_settings, sample_post
    ):
        """Posts from every configured source are aggregated into one list."""
        hn_post = BlueskyPost(
            id="hn_123",
            author="hnuser",
            content="Show HN: something",
            created_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC),
            engagement_metrics=EngagementMetrics(likes=5, reposts=0, replies=2),
            source="hackernews",
        )
        stage = CollectStage(
            settings=mock_settings,
            expand_urls=False,
            expand_references=False,
            collect_threads=False,
            sources=["bluesky", "hackernews"],
        )

        with (
            patch.object(
                stage.sources["bluesky"],
                "search",
                new=AsyncMock(return_value=[sample_post]),
            ),
            patch.object(
                stage.sources["hackernews"],
                "search",
                new=AsyncMock(return_value=[hn_post]),
            ),
            patch.object(
                stage.bluesky_client,
                "authenticate",
                new=AsyncMock(return_value=True),
            ),
        ):
            result = await stage.collect_posts(date(2024, 1, 15))

        assert result == [sample_post, hn_post]

    @pytest.mark.asyncio
    async def test_thread_and_expansion_only_applied_to_bluesky_posts(
        self, mock_settings, sample_post
    ):
        """Bluesky-only post-processing must not run on non-Bluesky posts."""
        hn_post = BlueskyPost(
            id="hn_456",
            author="hnuser",
            content="Ask HN: anything",
            created_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0),
            source="hackernews",
        )
        stage = CollectStage(
            settings=mock_settings,
            expand_urls=False,
            expand_references=True,
            max_reference_depth=1,
            collect_threads=False,
            sources=["bluesky", "hackernews"],
        )

        with (
            patch.object(
                stage.sources["bluesky"],
                "search",
                new=AsyncMock(return_value=[sample_post]),
            ),
            patch.object(
                stage.sources["hackernews"],
                "search",
                new=AsyncMock(return_value=[hn_post]),
            ),
            patch.object(
                stage.bluesky_client,
                "authenticate",
                new=AsyncMock(return_value=True),
            ),
            patch.object(
                stage,
                "_expand_post_references",
                new=AsyncMock(return_value=[sample_post]),
            ) as mock_expand_references,
        ):
            result = await stage.collect_posts(date(2024, 1, 15))

        # Only the bluesky post is passed into reference expansion.
        mock_expand_references.assert_called_once_with([sample_post], depth=0)
        assert result == [sample_post, hn_post]

    @pytest.mark.asyncio
    async def test_hackernews_only_does_not_check_bluesky_credentials(
        self, sample_post
    ):
        """Credential check is skipped entirely when bluesky isn't configured."""
        settings = Settings(
            r2_access_key_id="test_key",
            r2_secret_access_key="test_secret",
            r2_bucket_name="test-bucket",
            r2_endpoint_url="https://test.r2.cloudflarestorage.com",
        )
        hn_post = BlueskyPost(
            id="hn_789",
            author="hnuser",
            content="Some HN story",
            created_at=datetime(2024, 1, 15, 13, 0, 0, tzinfo=UTC),
            engagement_metrics=EngagementMetrics(likes=0, reposts=0, replies=0),
            source="hackernews",
        )
        stage = CollectStage(settings=settings, sources=["hackernews"])

        with patch.object(
            stage.sources["hackernews"],
            "search",
            new=AsyncMock(return_value=[hn_post]),
        ):
            result = await stage.collect_posts(date(2024, 1, 15))

        assert result == [hn_post]
