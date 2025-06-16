"""Tests for article evaluation models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.evaluation import ArticleEvaluation


class TestArticleEvaluation:
    """Test ArticleEvaluation model."""
    
    def test_evaluation_creation(self):
        """Test creating an evaluation with all fields."""
        now = datetime.now()
        evaluation = ArticleEvaluation(
            url="https://example.com/article",
            is_mcp_related=True,
            relevance_score=0.85,
            summary="Article about MCP tools and integration",
            perex="A comprehensive guide to understanding Model Context Protocol (MCP) and its integration with AI tools.",
            key_topics=["MCP", "AI tools", "integration"],
            content_type="article",
            language="en",
            title="Understanding MCP",
            author="John Doe",
            medium="Tech Blog",
            domain="example.com",
            published_date=now,
            evaluated_at=now,
            word_count=1500,
            truncated=False
        )
        
        assert str(evaluation.url) == "https://example.com/article"
        assert evaluation.is_mcp_related is True
        assert evaluation.relevance_score == 0.85
        assert evaluation.summary == "Article about MCP tools and integration"
        assert len(evaluation.key_topics) == 3
        assert evaluation.word_count == 1500
        assert evaluation.truncated is False
        assert evaluation.error is None
    
    def test_evaluation_minimal(self):
        """Test creating evaluation with minimal required fields."""
        now = datetime.now()
        evaluation = ArticleEvaluation(
            url="https://example.com",
            is_mcp_related=False,
            relevance_score=0.0,
            summary="Not related to MCP",
            perex="This article discusses general technology topics but does not mention MCP or related protocols.",
            content_type="article",
            language="en",
            domain="example.com",
            evaluated_at=now,
            word_count=100
        )
        
        assert evaluation.title is None
        assert evaluation.author is None
        assert evaluation.medium is None
        assert evaluation.published_date is None
        assert evaluation.key_topics == []
        assert evaluation.truncated is False
        assert evaluation.error is None
    
    def test_evaluation_with_error(self):
        """Test evaluation with error."""
        now = datetime.now()
        evaluation = ArticleEvaluation(
            url="https://example.com",
            is_mcp_related=False,
            relevance_score=0.0,
            summary="Error: Failed to fetch",  # Minimum 10 chars
            perex="Unable to retrieve article content due to access errors.",
            content_type="article",
            language="en",
            domain="example.com",
            evaluated_at=now,
            word_count=0,
            error="Failed to fetch article: 404 Not Found"
        )
        
        assert evaluation.error == "Failed to fetch article: 404 Not Found"
        assert evaluation.relevance_score == 0.0
        assert evaluation.is_mcp_related is False
    
    def test_evaluation_validation(self):
        """Test evaluation validation."""
        now = datetime.now()
        
        # Invalid relevance score (too high)
        with pytest.raises(ValidationError):
            ArticleEvaluation(
                url="https://example.com",
                is_mcp_related=True,
                relevance_score=1.5,  # > 1.0
                summary="Test",
                perex="Test perex for validation test case.",
                content_type="article",
                language="en",
                domain="example.com",
                evaluated_at=now,
                word_count=100
            )
        
        # Invalid relevance score (negative)
        with pytest.raises(ValidationError):
            ArticleEvaluation(
                url="https://example.com",
                is_mcp_related=True,
                relevance_score=-0.5,  # < 0.0
                summary="Test",
                perex="Test perex for negative score validation.",
                content_type="article",
                language="en",
                domain="example.com",
                evaluated_at=now,
                word_count=100
            )
        
        # Summary too short
        with pytest.raises(ValidationError):
            ArticleEvaluation(
                url="https://example.com",
                is_mcp_related=True,
                relevance_score=0.5,
                summary="Short",  # < 10 chars
                perex="Test perex for short summary validation.",
                content_type="article",
                language="en",
                domain="example.com",
                evaluated_at=now,
                word_count=100
            )
        
        # Invalid URL
        with pytest.raises(ValidationError):
            ArticleEvaluation(
                url="not-a-url",
                is_mcp_related=True,
                relevance_score=0.5,
                summary="Test summary",
                perex="Test perex for invalid URL validation.",
                content_type="article",
                language="en",
                domain="example.com",
                evaluated_at=now,
                word_count=100
            )
    
    def test_evaluation_serialization(self):
        """Test evaluation serialization."""
        now = datetime.now()
        evaluation = ArticleEvaluation(
            url="https://example.com/article",
            is_mcp_related=True,
            relevance_score=0.75,
            summary="Test article about MCP",
            perex="A test article exploring MCP concepts and practical applications for testing purposes.",
            key_topics=["MCP", "testing"],
            content_type="article",
            language="en",
            domain="example.com",
            evaluated_at=now,
            word_count=500
        )
        
        # Test dict serialization
        data = evaluation.model_dump()
        assert str(data["url"]) == "https://example.com/article"
        assert data["is_mcp_related"] is True
        assert data["relevance_score"] == 0.75
        assert len(data["key_topics"]) == 2
        
        # Test JSON serialization
        json_data = evaluation.model_dump_json()
        assert '"is_mcp_related":true' in json_data
        assert '"relevance_score":0.75' in json_data