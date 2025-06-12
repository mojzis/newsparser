from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models.post import BlueskyPost, EngagementMetrics


class TestEngagementMetrics:
    def test_valid_metrics(self):
        """Test creating valid engagement metrics."""
        metrics = EngagementMetrics(likes=10, reposts=5, replies=3)
        assert metrics.likes == 10
        assert metrics.reposts == 5
        assert metrics.replies == 3

    def test_zero_metrics(self):
        """Test that zero values are allowed."""
        metrics = EngagementMetrics(likes=0, reposts=0, replies=0)
        assert metrics.likes == 0
        assert metrics.reposts == 0
        assert metrics.replies == 0

    def test_negative_metrics_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EngagementMetrics(likes=-1, reposts=0, replies=0)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            EngagementMetrics(likes=0, reposts=-1, replies=0)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            EngagementMetrics(likes=0, reposts=0, replies=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    @given(
        likes=st.integers(min_value=0, max_value=1000000),
        reposts=st.integers(min_value=0, max_value=1000000),
        replies=st.integers(min_value=0, max_value=1000000),
    )
    def test_property_based_valid_metrics(self, likes, reposts, replies):
        """Property-based test for valid engagement metrics."""
        metrics = EngagementMetrics(likes=likes, reposts=reposts, replies=replies)
        assert metrics.likes == likes
        assert metrics.reposts == reposts
        assert metrics.replies == replies


class TestBlueskyPost:
    def test_valid_post(self):
        """Test creating a valid post."""
        now = datetime.utcnow()
        metrics = EngagementMetrics(likes=10, reposts=5, replies=3)
        post = BlueskyPost(
            id="123456",
            author="user.bsky.social",
            content="Check out this MCP tool: https://example.com",
            created_at=now,
            links=["https://example.com"],
            engagement_metrics=metrics,
        )

        assert post.id == "123456"
        assert post.author == "user.bsky.social"
        assert post.content == "Check out this MCP tool: https://example.com"
        assert post.created_at == now
        assert len(post.links) == 1
        assert str(post.links[0]) == "https://example.com/"
        assert post.engagement_metrics.likes == 10

    def test_empty_content_rejected(self):
        """Test that empty content is rejected."""
        now = datetime.utcnow()
        metrics = EngagementMetrics(likes=0, reposts=0, replies=0)

        with pytest.raises(ValidationError) as exc_info:
            BlueskyPost(
                id="123",
                author="user",
                content="",
                created_at=now,
                links=[],
                engagement_metrics=metrics,
            )
        assert "at least 1 character" in str(exc_info.value)

    def test_whitespace_only_content_rejected(self):
        """Test that whitespace-only content is rejected."""
        now = datetime.utcnow()
        metrics = EngagementMetrics(likes=0, reposts=0, replies=0)

        with pytest.raises(ValidationError) as exc_info:
            BlueskyPost(
                id="123",
                author="user",
                content="   \n\t  ",
                created_at=now,
                links=[],
                engagement_metrics=metrics,
            )
        assert "empty or whitespace only" in str(exc_info.value)

    def test_multiple_links(self):
        """Test post with multiple links."""
        now = datetime.utcnow()
        metrics = EngagementMetrics(likes=0, reposts=0, replies=0)
        post = BlueskyPost(
            id="123",
            author="user",
            content="Links: https://example.com https://test.com",
            created_at=now,
            links=["https://example.com", "https://test.com"],
            engagement_metrics=metrics,
        )

        assert len(post.links) == 2
        assert str(post.links[0]) == "https://example.com/"
        assert str(post.links[1]) == "https://test.com/"

    def test_no_links(self):
        """Test post with no links."""
        now = datetime.utcnow()
        metrics = EngagementMetrics(likes=0, reposts=0, replies=0)
        post = BlueskyPost(
            id="123",
            author="user",
            content="Just text, no links",
            created_at=now,
            links=[],
            engagement_metrics=metrics,
        )

        assert len(post.links) == 0

    def test_json_serialization(self):
        """Test JSON serialization of post."""
        now = datetime.utcnow()
        metrics = EngagementMetrics(likes=10, reposts=5, replies=3)
        post = BlueskyPost(
            id="123",
            author="user",
            content="Test post",
            created_at=now,
            links=["https://example.com"],
            engagement_metrics=metrics,
        )

        json_data = post.model_dump_json()
        assert isinstance(json_data, str)
        assert '"id":"123"' in json_data
        assert '"author":"user"' in json_data
        assert now.isoformat() in json_data
        assert "https://example.com/" in json_data

    def test_from_dict(self):
        """Test creating post from dictionary."""
        data = {
            "id": "123",
            "author": "user",
            "content": "Test post",
            "created_at": "2024-01-15T10:30:00",
            "links": ["https://example.com"],
            "engagement_metrics": {"likes": 10, "reposts": 5, "replies": 3},
        }

        post = BlueskyPost.model_validate(data)
        assert post.id == "123"
        assert post.author == "user"
        assert post.engagement_metrics.likes == 10

    @given(
        post_id=st.text(min_size=1, max_size=50),
        author=st.text(min_size=1, max_size=50),
        content=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        likes=st.integers(min_value=0, max_value=1000000),
        reposts=st.integers(min_value=0, max_value=1000000),
        replies=st.integers(min_value=0, max_value=1000000),
    )
    def test_property_based_valid_post(
        self, post_id, author, content, likes, reposts, replies
    ):
        """Property-based test for valid posts."""
        now = datetime.utcnow()
        metrics = EngagementMetrics(likes=likes, reposts=reposts, replies=replies)

        post = BlueskyPost(
            id=post_id,
            author=author,
            content=content,
            created_at=now,
            links=[],
            engagement_metrics=metrics,
        )

        assert post.id == post_id
        assert post.author == author
        assert post.content == content
        assert post.engagement_metrics.likes == likes
