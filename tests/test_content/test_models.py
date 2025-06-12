"""Tests for content processing models."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.content.models import ArticleContent, ContentError, ExtractedContent


class TestExtractedContent:
    def test_valid_extracted_content(self):
        """Test creating valid extracted content."""
        content = ExtractedContent(
            url="https://example.com/article",
            title="Test Article",
            content_markdown="# Test\n\nThis is a test article.",
            word_count=6,
            language="en",
            domain="example.com",
        )
        
        assert str(content.url) == "https://example.com/article"
        assert content.title == "Test Article"
        assert content.word_count == 6
        assert content.language == "en"
        assert content.domain == "example.com"
        assert isinstance(content.extraction_timestamp, datetime)
    
    def test_minimal_extracted_content(self):
        """Test creating minimal extracted content."""
        content = ExtractedContent(
            url="https://example.com/article",
            content_markdown="Content",
            word_count=1,
            domain="example.com",
        )
        
        assert content.title is None
        assert content.language is None
        assert content.word_count == 1
    
    def test_negative_word_count_fails(self):
        """Test that negative word count fails validation."""
        with pytest.raises(ValidationError):
            ExtractedContent(
                url="https://example.com/article",
                content_markdown="Content",
                word_count=-1,
                domain="example.com",
            )
    
    def test_invalid_url_fails(self):
        """Test that invalid URL fails validation."""
        with pytest.raises(ValidationError):
            ExtractedContent(
                url="not-a-url",
                content_markdown="Content",
                word_count=1,
                domain="example.com",
            )


class TestArticleContent:
    def test_valid_article_content(self):
        """Test creating valid article content."""
        content = ArticleContent(
            url="https://example.com/article",
            html="<html><body>Test</body></html>",
            status_code=200,
            headers={"content-type": "text/html"},
        )
        
        assert str(content.url) == "https://example.com/article"
        assert content.html == "<html><body>Test</body></html>"
        assert content.status_code == 200
        assert content.headers == {"content-type": "text/html"}
        assert isinstance(content.fetch_timestamp, datetime)
    
    def test_minimal_article_content(self):
        """Test creating minimal article content."""
        content = ArticleContent(
            url="https://example.com/article",
            html="<html>Test</html>",
            status_code=200,
        )
        
        assert content.headers == {}
        assert isinstance(content.fetch_timestamp, datetime)


class TestContentError:
    def test_valid_content_error(self):
        """Test creating valid content error."""
        error = ContentError(
            url="https://example.com/article",
            error_type="fetch",
            error_message="Connection timeout",
        )
        
        assert str(error.url) == "https://example.com/article"
        assert error.error_type == "fetch"
        assert error.error_message == "Connection timeout"
        assert isinstance(error.timestamp, datetime)
    
    def test_content_error_serialization(self):
        """Test content error can be serialized to JSON."""
        error = ContentError(
            url="https://example.com/article",
            error_type="fetch",
            error_message="Connection timeout",
        )
        
        json_data = error.model_dump()
        assert str(json_data["url"]) == "https://example.com/article"
        assert json_data["error_type"] == "fetch"
        assert json_data["error_message"] == "Connection timeout"