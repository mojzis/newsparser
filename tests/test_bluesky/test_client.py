from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from atproto import models
from atproto.exceptions import AtProtocolError

from src.bluesky.client import BlueskyClient
from src.config.settings import Settings
from src.models.post import BlueskyPost


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
def mock_settings_no_credentials():
    """Create mock settings without Bluesky credentials."""
    return Settings(
        r2_access_key_id="test_key",
        r2_secret_access_key="test_secret",
        r2_bucket_name="test-bucket",
        r2_endpoint_url="https://test.r2.cloudflarestorage.com",
    )


@pytest.fixture
def bluesky_client(mock_settings):
    """Create BlueskyClient instance."""
    return BlueskyClient(mock_settings)


@pytest.fixture
def mock_post_data():
    """Create mock atproto post data."""
    # Create mock post record
    record = Mock()
    record.text = "Check out this MCP tool: https://example.com"
    record.created_at = "2024-01-15T10:30:00Z"
    record.facets = [Mock(features=[Mock(uri="https://example.com")])]

    # Create mock author
    author = Mock()
    author.handle = "user.bsky.social"

    # Create mock post
    post = Mock()
    post.uri = "at://did:plc:example/app.bsky.feed.post/123"
    post.record = record
    post.author = author
    post.like_count = 5
    post.repost_count = 2
    post.reply_count = 1

    # Create mock feed view post
    feed_post = Mock(spec=models.AppBskyFeedDefs.FeedViewPost)
    feed_post.post = post

    return feed_post


class TestBlueskyClientInit:
    def test_init_with_settings(self, mock_settings):
        """Test BlueskyClient initialization."""
        client = BlueskyClient(mock_settings)
        assert client.settings == mock_settings
        assert client.client is None
        assert not client._session_active

    def test_init_without_credentials(self, mock_settings_no_credentials):
        """Test initialization without credentials still works."""
        client = BlueskyClient(mock_settings_no_credentials)
        assert client.settings == mock_settings_no_credentials
        assert client.client is None


class TestBlueskyClientAuthentication:
    @pytest.mark.asyncio
    async def test_authenticate_success(self, bluesky_client):
        """Test successful authentication."""
        with patch("src.bluesky.client.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await bluesky_client.authenticate()

            assert result is True
            assert bluesky_client.client == mock_client
            assert bluesky_client._session_active is True
            mock_client.login.assert_called_once_with(
                "test.bsky.social", "test-app-password"
            )

    @pytest.mark.asyncio
    async def test_authenticate_no_credentials(self, mock_settings_no_credentials):
        """Test authentication fails without credentials."""
        client = BlueskyClient(mock_settings_no_credentials)

        result = await client.authenticate()

        assert result is False
        assert client.client is None
        assert not client._session_active

    @pytest.mark.asyncio
    async def test_authenticate_api_error(self, bluesky_client):
        """Test authentication fails with API error."""
        with patch("src.bluesky.client.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.login.side_effect = AtProtocolError("Invalid credentials")
            mock_client_class.return_value = mock_client

            result = await bluesky_client.authenticate()

            assert result is False
            assert not bluesky_client._session_active

    @pytest.mark.asyncio
    async def test_authenticate_unexpected_error(self, bluesky_client):
        """Test authentication fails with unexpected error."""
        with patch("src.bluesky.client.AsyncClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Network error")

            result = await bluesky_client.authenticate()

            assert result is False
            assert not bluesky_client._session_active

    @pytest.mark.asyncio
    async def test_close(self, bluesky_client):
        """Test closing client session."""
        # Set up authenticated client
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True

        await bluesky_client.close()

        assert not bluesky_client._session_active
        bluesky_client.client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_client(self, bluesky_client):
        """Test closing when no client exists."""
        await bluesky_client.close()  # Should not raise error
        assert not bluesky_client._session_active


class TestBlueskyClientContextManager:
    @pytest.mark.asyncio
    async def test_async_context_manager_success(self, bluesky_client):
        """Test async context manager with successful auth."""
        with patch.object(
            bluesky_client, "authenticate", return_value=True
        ) as mock_auth, patch.object(bluesky_client, "close") as mock_close:
            async with bluesky_client as client:
                assert client == bluesky_client

            mock_auth.assert_called_once()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_with_exception(self, bluesky_client):
        """Test async context manager cleanup on exception."""
        with patch.object(bluesky_client, "authenticate", return_value=True):
            with patch.object(bluesky_client, "close") as mock_close:
                with pytest.raises(ValueError):
                    async with bluesky_client:
                        raise ValueError("Test error")

                mock_close.assert_called_once()


class TestBlueskyClientPostConversion:
    def test_convert_post_to_model(self, bluesky_client, mock_post_data):
        """Test converting atproto post data to BlueskyPost model."""
        result = bluesky_client._convert_post_to_model(mock_post_data)

        assert isinstance(result, BlueskyPost)
        assert result.id == "at://did:plc:example/app.bsky.feed.post/123"
        assert result.author == "user.bsky.social"
        assert result.content == "Check out this MCP tool: https://example.com"
        assert result.created_at == datetime(
            2024, 1, 15, 10, 30, 0, tzinfo=UTC
        )
        assert len(result.links) == 1
        assert str(result.links[0]) == "https://example.com/"
        assert result.engagement_metrics.likes == 5
        assert result.engagement_metrics.reposts == 2
        assert result.engagement_metrics.replies == 1

    def test_convert_post_missing_engagement(self, bluesky_client, mock_post_data):
        """Test converting post with missing engagement metrics."""
        # Remove engagement metrics
        del mock_post_data.post.like_count
        del mock_post_data.post.repost_count
        del mock_post_data.post.reply_count

        result = bluesky_client._convert_post_to_model(mock_post_data)

        assert result.engagement_metrics.likes == 0
        assert result.engagement_metrics.reposts == 0
        assert result.engagement_metrics.replies == 0

    def test_convert_post_no_facets(self, bluesky_client, mock_post_data):
        """Test converting post without facets (no links)."""
        mock_post_data.post.record.facets = None

        result = bluesky_client._convert_post_to_model(mock_post_data)

        assert len(result.links) == 0


class TestBlueskyClientSearch:
    @pytest.mark.asyncio
    async def test_search_posts_success(self, bluesky_client, mock_post_data):
        """Test successful post search."""
        # Set up authenticated client
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True

        # Mock search response
        mock_response = Mock()
        mock_response.posts = [mock_post_data]
        mock_response.cursor = "next_cursor_123"
        bluesky_client.client.app.bsky.feed.search_posts.return_value = mock_response

        posts, cursor = await bluesky_client.search_posts("mcp", limit=10)

        assert len(posts) == 1
        assert isinstance(posts[0], BlueskyPost)
        assert cursor == "next_cursor_123"

        bluesky_client.client.app.bsky.feed.search_posts.assert_called_once_with(
            params={"q": "mcp", "limit": 10, "cursor": None}
        )

    @pytest.mark.asyncio
    async def test_search_posts_not_authenticated(self, bluesky_client):
        """Test search fails when not authenticated."""
        with pytest.raises(RuntimeError, match="Client not authenticated"):
            await bluesky_client.search_posts("mcp")

    @pytest.mark.asyncio
    async def test_search_posts_api_error(self, bluesky_client):
        """Test search handles API error gracefully."""
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True
        bluesky_client.client.app.bsky.feed.search_posts.side_effect = AtProtocolError(
            "API error"
        )

        posts, cursor = await bluesky_client.search_posts("mcp")

        assert posts == []
        assert cursor is None

    @pytest.mark.asyncio
    async def test_search_posts_conversion_error(self, bluesky_client, mock_post_data):
        """Test search handles post conversion errors gracefully."""
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True

        # Create invalid post data that will cause conversion error
        invalid_post = Mock()
        invalid_post.post.uri = None  # This will cause conversion to fail

        mock_response = Mock()
        mock_response.posts = [mock_post_data, invalid_post]  # One valid, one invalid
        mock_response.cursor = None
        bluesky_client.client.app.bsky.feed.search_posts.return_value = mock_response

        posts, cursor = await bluesky_client.search_posts("mcp")

        # Should only return the valid post, invalid one skipped
        assert len(posts) == 1
        assert isinstance(posts[0], BlueskyPost)

    @pytest.mark.asyncio
    async def test_search_mcp_mentions(self, bluesky_client, mock_post_data):
        """Test MCP-specific search."""
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True

        mock_response = Mock()
        mock_response.posts = [mock_post_data]
        mock_response.cursor = None
        bluesky_client.client.app.bsky.feed.search_posts.return_value = mock_response

        posts, cursor = await bluesky_client.search_mcp_mentions(limit=5)

        assert len(posts) == 1
        bluesky_client.client.app.bsky.feed.search_posts.assert_called_once_with(
            params={"q": "mcp", "limit": 5, "cursor": None}
        )

    @pytest.mark.asyncio
    async def test_get_recent_mcp_posts_pagination(
        self, bluesky_client, mock_post_data
    ):
        """Test getting recent MCP posts with pagination."""
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True

        # Mock multiple pages of results
        first_response = Mock()
        first_response.posts = [mock_post_data]
        first_response.cursor = "cursor_page_2"

        second_response = Mock()
        second_response.posts = [mock_post_data]
        second_response.cursor = None  # No more pages

        bluesky_client.client.app.bsky.feed.search_posts.side_effect = [
            first_response,
            second_response,
        ]

        # Mock asyncio.sleep to avoid actual delays in tests
        with patch("asyncio.sleep"):
            posts = await bluesky_client.get_recent_mcp_posts(max_posts=50)

        assert len(posts) == 2
        assert bluesky_client.client.app.bsky.feed.search_posts.call_count == 2

    @pytest.mark.asyncio
    async def test_get_recent_mcp_posts_max_limit(self, bluesky_client, mock_post_data):
        """Test max_posts limit is respected."""
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True

        mock_response = Mock()
        mock_response.posts = [mock_post_data]
        mock_response.cursor = "has_more"
        bluesky_client.client.app.bsky.feed.search_posts.return_value = mock_response

        with patch("asyncio.sleep"):
            posts = await bluesky_client.get_recent_mcp_posts(max_posts=1)

        assert len(posts) == 1
        # Should only make one call since we reached max_posts
        assert bluesky_client.client.app.bsky.feed.search_posts.call_count == 1

    @pytest.mark.asyncio
    async def test_get_recent_mcp_posts_no_results(self, bluesky_client):
        """Test getting recent posts when no results found."""
        bluesky_client.client = AsyncMock()
        bluesky_client._session_active = True

        mock_response = Mock()
        mock_response.posts = []
        mock_response.cursor = None
        bluesky_client.client.app.bsky.feed.search_posts.return_value = mock_response

        posts = await bluesky_client.get_recent_mcp_posts(max_posts=10)

        assert len(posts) == 0
