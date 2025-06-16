"""Tests for article fetcher."""
import pytest
from unittest.mock import Mock, AsyncMock
import httpx

from src.content.fetcher import ArticleFetcher
from src.content.models import ArticleContent, ContentError
from pydantic import ValidationError


class TestArticleFetcher:
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = ArticleFetcher(timeout=15.0, max_retries=2)
        assert fetcher.timeout == 15.0
        assert fetcher.max_retries == 2
        assert fetcher.retry_delay == 1.0
    
    def test_is_valid_url(self):
        """Test URL validation."""
        fetcher = ArticleFetcher()
        
        # Valid URLs
        assert fetcher._is_valid_url("https://example.com")
        assert fetcher._is_valid_url("http://example.com/path")
        assert fetcher._is_valid_url("https://subdomain.example.com/path?query=1")
        
        # Invalid URLs
        assert not fetcher._is_valid_url("ftp://example.com")
        assert not fetcher._is_valid_url("https://localhost")
        assert not fetcher._is_valid_url("https://127.0.0.1")
        assert not fetcher._is_valid_url("not-a-url")
        assert not fetcher._is_valid_url("")
    
    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        """Test that invalid URL validation."""
        fetcher = ArticleFetcher()
        
        # First test the validation function
        assert not fetcher._is_valid_url("invalid-url")
        
        # The fetch_article should handle invalid URLs
        result = await fetcher.fetch_article("invalid-url")
        assert isinstance(result, ContentError)
        assert result.error_type == "validation"
        assert "Invalid or unsafe URL" in result.error_message
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful article fetch."""
        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><head><title>Test</title></head><body>Content</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.reason_phrase = "OK"
        
        fetcher = ArticleFetcher()
        fetcher.client.get = AsyncMock(return_value=mock_response)
        
        result = await fetcher.fetch_article("https://example.com/article")
        
        assert isinstance(result, ArticleContent)
        assert str(result.url) == "https://example.com/article"
        assert result.status_code == 200
        assert "Test" in result.html
        assert result.headers["content-type"] == "text/html"
    
    @pytest.mark.asyncio
    async def test_http_error_returns_error(self):
        """Test that HTTP error returns ContentError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        mock_response.headers = {"content-type": "text/html"}
        
        fetcher = ArticleFetcher(max_retries=0)  # No retries for faster test
        fetcher.client.get = AsyncMock(return_value=mock_response)
        
        result = await fetcher.fetch_article("https://example.com/notfound")
        
        assert isinstance(result, ContentError)
        assert result.error_type == "permanent_http_error"
        assert "HTTP 404" in result.error_message
    
    @pytest.mark.asyncio
    async def test_timeout_returns_error(self):
        """Test that timeout returns ContentError."""
        fetcher = ArticleFetcher(max_retries=0)  # No retries for faster test
        fetcher.client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        
        result = await fetcher.fetch_article("https://example.com/slow")
        
        assert isinstance(result, ContentError)
        assert result.error_type == "timeout"
        assert "Timeout" in result.error_message
    
    @pytest.mark.asyncio
    async def test_network_error_returns_error(self):
        """Test that network error returns ContentError."""
        fetcher = ArticleFetcher(max_retries=0)  # No retries for faster test
        fetcher.client.get = AsyncMock(
            side_effect=httpx.NetworkError("Connection failed")
        )
        
        result = await fetcher.fetch_article("https://example.com/unreachable")
        
        assert isinstance(result, ContentError)
        assert result.error_type == "network"
        assert "Network error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_non_html_content_returns_error(self):
        """Test that non-HTML content returns ContentError."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        
        fetcher = ArticleFetcher()
        fetcher.client.get = AsyncMock(return_value=mock_response)
        
        result = await fetcher.fetch_article("https://example.com/api.json")
        
        assert isinstance(result, ContentError)
        assert result.error_type == "content_type"
        assert "Non-HTML content type" in result.error_message
    
    @pytest.mark.asyncio
    async def test_content_too_large_returns_error(self):
        """Test that content too large returns ContentError."""
        mock_response = Mock()
        mock_response.headers = {"content-length": "20000000"}  # 20MB
        
        fetcher = ArticleFetcher(max_content_size=1024)  # 1KB limit
        fetcher.client.get = AsyncMock(return_value=mock_response)
        
        result = await fetcher.fetch_article("https://example.com/large")
        
        assert isinstance(result, ContentError)
        assert result.error_type == "size"
        assert "Content too large" in result.error_message
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_empty_list(self):
        """Test fetching empty list returns empty list."""
        fetcher = ArticleFetcher()
        
        result = await fetcher.fetch_multiple([])
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_success(self):
        """Test fetching multiple URLs successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        
        fetcher = ArticleFetcher()
        fetcher.client.get = AsyncMock(return_value=mock_response)
        
        urls = [
            "https://example.com/1",
            "https://example.com/2",
        ]
        
        results = await fetcher.fetch_multiple(urls, max_concurrent=1)
        
        assert len(results) == 2
        assert all(isinstance(r, ArticleContent) for r in results)
        assert str(results[0].url) == "https://example.com/1"
        assert str(results[1].url) == "https://example.com/2"
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test fetcher as async context manager."""
        async with ArticleFetcher() as fetcher:
            assert isinstance(fetcher, ArticleFetcher)
            # The close method should be called automatically