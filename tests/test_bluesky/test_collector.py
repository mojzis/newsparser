from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.bluesky.collector import BlueskyDataCollector
from src.config.settings import Settings
from src.models.post import BlueskyPost, EngagementMetrics


@pytest.fixture
def mock_settings():
    """Create mock settings with credentials."""
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
def sample_posts():
    """Create sample BlueskyPost instances."""
    return [
        BlueskyPost(
            id="post1",
            author="user1.bsky.social",
            content="Check out this MCP tool",
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            links=["https://example.com"],
            engagement_metrics=EngagementMetrics(likes=5, reposts=2, replies=1),
        ),
        BlueskyPost(
            id="post2",
            author="user2.bsky.social",
            content="MCP integration is great",
            created_at=datetime(2024, 1, 15, 11, 0, 0),
            links=[],
            engagement_metrics=EngagementMetrics(likes=3, reposts=1, replies=0),
        ),
    ]


@pytest.fixture
def collector(mock_settings):
    """Create BlueskyDataCollector instance."""
    return BlueskyDataCollector(mock_settings)


class TestBlueskyDataCollectorInit:
    def test_init(self, mock_settings):
        """Test collector initialization."""
        collector = BlueskyDataCollector(mock_settings)

        assert collector.settings == mock_settings
        assert collector.bluesky_client is not None
        assert collector.r2_client is not None


class TestBlueskyDataCollectorCollectPosts:
    @pytest.mark.asyncio
    async def test_collect_daily_posts_success(self, collector, sample_posts):
        """Test successful post collection."""
        with patch("src.bluesky.collector.BlueskyClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_recent_mcp_posts.return_value = sample_posts
            mock_client_class.return_value = mock_client

            # Create new collector with mocked client
            test_collector = BlueskyDataCollector(collector.settings)

            result = await test_collector.collect_daily_posts(
                target_date=date(2024, 1, 15), max_posts=50
            )

            assert len(result) == 2
            assert all(isinstance(post, BlueskyPost) for post in result)

    @pytest.mark.asyncio
    async def test_collect_daily_posts_no_credentials(
        self, mock_settings_no_credentials
    ):
        """Test collection fails without credentials."""
        collector = BlueskyDataCollector(mock_settings_no_credentials)

        result = await collector.collect_daily_posts()

        assert result == []

    @pytest.mark.asyncio
    async def test_collect_daily_posts_default_date(self, collector, sample_posts):
        """Test collection with default date (today)."""
        with patch("src.bluesky.collector.BlueskyClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_recent_mcp_posts.return_value = sample_posts
            mock_client_class.return_value = mock_client

            with patch("src.bluesky.collector.date") as mock_date:
                mock_date.today.return_value = date(2024, 1, 15)

                test_collector = BlueskyDataCollector(collector.settings)
                result = await test_collector.collect_daily_posts()

                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_collect_daily_posts_exception(self, collector):
        """Test collection handles exceptions gracefully."""
        with patch.object(
            collector.bluesky_client,
            "__aenter__",
            side_effect=Exception("Connection failed"),
        ):
            result = await collector.collect_daily_posts()

            assert result == []


class TestBlueskyDataCollectorStorePosts:
    @pytest.mark.asyncio
    async def test_store_posts_success(self, collector, sample_posts):
        """Test successful post storage."""
        target_date = date(2024, 1, 15)

        with patch.object(
            collector.r2_client, "upload_bytes", return_value=True
        ) as mock_upload:
            result = await collector.store_posts(sample_posts, target_date)

            assert result is True
            mock_upload.assert_called_once()

            # Check the call arguments
            call_args = mock_upload.call_args
            assert call_args[0][1] == "data/2024/01/15/posts.json"  # file path
            assert call_args[1]["content_type"] == "application/json"

    @pytest.mark.asyncio
    async def test_store_posts_empty_list(self, collector):
        """Test storing empty post list."""
        result = await collector.store_posts([], date(2024, 1, 15))

        assert result is True  # Empty list is considered success

    @pytest.mark.asyncio
    async def test_store_posts_upload_failure(self, collector, sample_posts):
        """Test storage failure during upload."""
        with patch.object(collector.r2_client, "upload_bytes", return_value=False):
            result = await collector.store_posts(sample_posts, date(2024, 1, 15))

            assert result is False

    @pytest.mark.asyncio
    async def test_store_posts_exception(self, collector, sample_posts):
        """Test storage handles exceptions."""
        with patch.object(
            collector.r2_client, "upload_bytes", side_effect=Exception("Upload failed")
        ):
            result = await collector.store_posts(sample_posts, date(2024, 1, 15))

            assert result is False


class TestBlueskyDataCollectorCollectAndStore:
    @pytest.mark.asyncio
    async def test_collect_and_store_success(self, collector, sample_posts):
        """Test successful collect and store operation."""
        target_date = date(2024, 1, 15)

        with patch.object(collector, "collect_daily_posts", return_value=sample_posts):
            with patch.object(collector, "store_posts", return_value=True):
                count, success = await collector.collect_and_store(
                    target_date, max_posts=50
                )

                assert count == 2
                assert success is True

    @pytest.mark.asyncio
    async def test_collect_and_store_no_posts(self, collector):
        """Test collect and store with no posts found."""
        with patch.object(collector, "collect_daily_posts", return_value=[]):
            count, success = await collector.collect_and_store()

            assert count == 0
            assert success is True  # No posts to store is success

    @pytest.mark.asyncio
    async def test_collect_and_store_storage_failure(self, collector, sample_posts):
        """Test collect and store with storage failure."""
        with patch.object(collector, "collect_daily_posts", return_value=sample_posts):
            with patch.object(collector, "store_posts", return_value=False):
                count, success = await collector.collect_and_store()

                assert count == 2
                assert success is False

    @pytest.mark.asyncio
    async def test_collect_and_store_default_date(self, collector, sample_posts):
        """Test collect and store with default date."""
        with patch.object(
            collector, "collect_daily_posts", return_value=sample_posts
        ) as mock_collect, patch.object(collector, "store_posts", return_value=True):
            with patch("src.bluesky.collector.date") as mock_date:
                mock_date.today.return_value = date(2024, 1, 15)

                await collector.collect_and_store()

                # Verify collect_daily_posts was called with today's date
                mock_collect.assert_called_once_with(date(2024, 1, 15), 100)


class TestBlueskyDataCollectorRetrievePosts:
    @pytest.mark.asyncio
    async def test_get_stored_posts_success(self, collector, sample_posts):
        """Test successful retrieval of stored posts."""
        target_date = date(2024, 1, 15)

        # Create JSON data as it would be stored
        import json

        stored_data = [post.model_dump() for post in sample_posts]
        json_data = json.dumps(stored_data, default=str).encode("utf-8")

        with patch.object(
            collector.r2_client, "download_bytes", return_value=json_data
        ):
            result = await collector.get_stored_posts(target_date)

            assert len(result) == 2
            assert all(isinstance(post, BlueskyPost) for post in result)
            assert result[0].id == "post1"
            assert result[1].id == "post2"

    @pytest.mark.asyncio
    async def test_get_stored_posts_not_found(self, collector):
        """Test retrieval when no data exists."""
        with patch.object(collector.r2_client, "download_bytes", return_value=None):
            result = await collector.get_stored_posts(date(2024, 1, 15))

            assert result == []

    @pytest.mark.asyncio
    async def test_get_stored_posts_invalid_json(self, collector):
        """Test retrieval with invalid JSON data."""
        with patch.object(
            collector.r2_client, "download_bytes", return_value=b"invalid json"
        ):
            result = await collector.get_stored_posts(date(2024, 1, 15))

            assert result == []

    @pytest.mark.asyncio
    async def test_get_stored_posts_invalid_post_data(self, collector):
        """Test retrieval with invalid post data."""
        # Create JSON with invalid post data
        import json

        invalid_data = [{"id": "test", "invalid": "data"}]  # Missing required fields
        json_data = json.dumps(invalid_data).encode("utf-8")

        with patch.object(
            collector.r2_client, "download_bytes", return_value=json_data
        ):
            result = await collector.get_stored_posts(date(2024, 1, 15))

            assert result == []  # Invalid posts should be skipped

    @pytest.mark.asyncio
    async def test_get_stored_posts_exception(self, collector):
        """Test retrieval handles exceptions."""
        with patch.object(
            collector.r2_client,
            "download_bytes",
            side_effect=Exception("Download failed"),
        ):
            result = await collector.get_stored_posts(date(2024, 1, 15))

            assert result == []


class TestBlueskyDataCollectorCheckData:
    def test_check_stored_data_exists(self, collector):
        """Test checking for existing data."""
        with patch.object(collector.r2_client, "file_exists", return_value=True):
            result = collector.check_stored_data(date(2024, 1, 15))

            assert result is True

    def test_check_stored_data_not_exists(self, collector):
        """Test checking for non-existent data."""
        with patch.object(collector.r2_client, "file_exists", return_value=False):
            result = collector.check_stored_data(date(2024, 1, 15))

            assert result is False

    def test_check_stored_data_correct_path(self, collector):
        """Test that correct path is used for checking."""
        with patch.object(
            collector.r2_client, "file_exists", return_value=True
        ) as mock_exists:
            collector.check_stored_data(date(2024, 1, 15))

            mock_exists.assert_called_once_with("data/2024/01/15/posts.json")
