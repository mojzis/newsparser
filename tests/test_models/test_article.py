from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models.article import ArticleEvaluation


class TestArticleEvaluation:
    def test_valid_evaluation(self):
        """Test creating a valid article evaluation."""
        eval = ArticleEvaluation(
            url="https://example.com/article",
            title="MCP Tools Overview",
            content_summary="An overview of Model Context Protocol tools",
            relevance_score=0.85,
            key_topics=["MCP", "AI tools", "integration"],
        )

        assert str(eval.url) == "https://example.com/article"
        assert eval.title == "MCP Tools Overview"
        assert eval.content_summary == "An overview of Model Context Protocol tools"
        assert eval.relevance_score == 0.85
        assert eval.key_topics == ["MCP", "AI tools", "integration"]
        assert isinstance(eval.evaluation_timestamp, datetime)

    def test_optional_title(self):
        """Test that title is optional."""
        eval = ArticleEvaluation(
            url="https://example.com",
            title=None,
            content_summary="Summary without title",
            relevance_score=0.5,
            key_topics=["MCP"],
        )

        assert eval.title is None

    def test_empty_summary_rejected(self):
        """Test that empty summary is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                title="Title",
                content_summary="",
                relevance_score=0.5,
                key_topics=["MCP"],
            )
        assert "empty or whitespace only" in str(exc_info.value)

    def test_whitespace_only_summary_rejected(self):
        """Test that whitespace-only summary is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                title="Title",
                content_summary="   \n\t  ",
                relevance_score=0.5,
                key_topics=["MCP"],
            )
        assert "empty or whitespace only" in str(exc_info.value)

    def test_summary_max_length(self):
        """Test summary maximum length constraint."""
        long_summary = "x" * 501
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                title="Title",
                content_summary=long_summary,
                relevance_score=0.5,
                key_topics=["MCP"],
            )
        assert "at most 500 characters" in str(exc_info.value)

    def test_relevance_score_bounds(self):
        """Test relevance score bounds (0.0 to 1.0)."""
        # Test minimum bound
        eval_min = ArticleEvaluation(
            url="https://example.com",
            content_summary="Summary",
            relevance_score=0.0,
            key_topics=["MCP"],
        )
        assert eval_min.relevance_score == 0.0

        # Test maximum bound
        eval_max = ArticleEvaluation(
            url="https://example.com",
            content_summary="Summary",
            relevance_score=1.0,
            key_topics=["MCP"],
        )
        assert eval_max.relevance_score == 1.0

        # Test below minimum
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                content_summary="Summary",
                relevance_score=-0.1,
                key_topics=["MCP"],
            )
        assert "greater than or equal to 0" in str(exc_info.value)

        # Test above maximum
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                content_summary="Summary",
                relevance_score=1.1,
                key_topics=["MCP"],
            )
        assert "less than or equal to 1" in str(exc_info.value)

    def test_empty_topics_list_rejected(self):
        """Test that empty topics list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                content_summary="Summary",
                relevance_score=0.5,
                key_topics=[],
            )
        assert "at least 1 item" in str(exc_info.value)

    def test_whitespace_topics_cleaned(self):
        """Test that whitespace topics are cleaned."""
        eval = ArticleEvaluation(
            url="https://example.com",
            content_summary="Summary",
            relevance_score=0.5,
            key_topics=["  MCP  ", "\tAI tools\n", "integration"],
        )

        assert eval.key_topics == ["MCP", "AI tools", "integration"]

    def test_empty_string_topics_rejected(self):
        """Test that empty string topics are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                content_summary="Summary",
                relevance_score=0.5,
                key_topics=["MCP", "", "AI"],
            )
        assert "At least one non-empty topic is required" in str(exc_info.value)

    def test_whitespace_only_topics_rejected(self):
        """Test that whitespace-only topics are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleEvaluation(
                url="https://example.com",
                content_summary="Summary",
                relevance_score=0.5,
                key_topics=["   ", "\t\n"],
            )
        assert "At least one non-empty topic is required" in str(exc_info.value)

    def test_default_timestamp(self):
        """Test that evaluation_timestamp has a default value."""
        before = datetime.utcnow()
        eval = ArticleEvaluation(
            url="https://example.com",
            content_summary="Summary",
            relevance_score=0.5,
            key_topics=["MCP"],
        )
        after = datetime.utcnow()

        assert before <= eval.evaluation_timestamp <= after

    def test_custom_timestamp(self):
        """Test setting a custom timestamp."""
        custom_time = datetime(2024, 1, 15, 10, 30, 0)
        eval = ArticleEvaluation(
            url="https://example.com",
            content_summary="Summary",
            relevance_score=0.5,
            key_topics=["MCP"],
            evaluation_timestamp=custom_time,
        )

        assert eval.evaluation_timestamp == custom_time

    def test_json_serialization(self):
        """Test JSON serialization."""
        eval = ArticleEvaluation(
            url="https://example.com/article",
            title="Title",
            content_summary="Summary",
            relevance_score=0.75,
            key_topics=["MCP", "AI"],
        )

        json_data = eval.model_dump_json()
        assert isinstance(json_data, str)
        assert '"url":"https://example.com/article"' in json_data
        assert '"title":"Title"' in json_data
        assert '"relevance_score":0.75' in json_data

    def test_from_dict(self):
        """Test creating evaluation from dictionary."""
        data = {
            "url": "https://example.com",
            "title": "MCP Article",
            "content_summary": "Article about MCP",
            "relevance_score": 0.9,
            "key_topics": ["MCP", "tools"],
            "evaluation_timestamp": "2024-01-15T10:30:00",
        }

        eval = ArticleEvaluation.model_validate(data)
        assert eval.title == "MCP Article"
        assert eval.relevance_score == 0.9
        assert eval.key_topics == ["MCP", "tools"]

    @given(
        summary=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        num_topics=st.integers(min_value=1, max_value=10),
    )
    def test_property_based_valid_evaluation(self, summary, score, num_topics):
        """Property-based test for valid evaluations."""
        topics = [f"topic_{i}" for i in range(num_topics)]

        eval = ArticleEvaluation(
            url="https://example.com",
            content_summary=summary,
            relevance_score=score,
            key_topics=topics,
        )

        assert eval.content_summary == summary
        assert eval.relevance_score == score
        assert len(eval.key_topics) == num_topics
