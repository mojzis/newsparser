"""Tests for content extractor."""
import pytest
from datetime import datetime

from src.content.extractor import ContentExtractor
from src.content.models import ArticleContent, ContentError, ExtractedContent


class TestContentExtractor:
    def test_init(self):
        """Test extractor initialization."""
        extractor = ContentExtractor(min_content_length=50, max_content_length=1000)
        assert extractor.min_content_length == 50
        assert extractor.max_content_length == 1000
    
    def test_clean_html(self):
        """Test HTML cleaning."""
        extractor = ContentExtractor()
        
        dirty_html = """
        <html>
        <head><script>alert('test');</script></head>
        <body>
            <nav>Navigation</nav>
            <main>
                <h1>Title</h1>
                <p>Content paragraph</p>
            </main>
            <aside class="sidebar">Sidebar content</aside>
            <footer>Footer</footer>
        </body>
        </html>
        """
        
        cleaned = extractor._clean_html(dirty_html)
        
        # Script, nav, aside, footer should be removed
        assert "<script>" not in cleaned
        assert "Navigation" not in cleaned
        assert "Sidebar content" not in cleaned
        assert "Footer" not in cleaned
        
        # Main content should remain
        assert "Title" in cleaned
        assert "Content paragraph" in cleaned
    
    def test_extract_title_from_title_tag(self):
        """Test title extraction from title tag."""
        extractor = ContentExtractor()
        
        html = "<html><head><title>Test Article Title</title></head><body>Content</body></html>"
        title = extractor._extract_title(html)
        
        assert title == "Test Article Title"
    
    def test_extract_title_from_og_meta(self):
        """Test title extraction from Open Graph meta tag."""
        extractor = ContentExtractor()
        
        html = '''
        <html>
        <head>
            <meta property="og:title" content="Open Graph Title">
            <title>Regular Title</title>
        </head>
        <body>Content</body>
        </html>
        '''
        title = extractor._extract_title(html)
        
        assert title == "Open Graph Title"
    
    def test_extract_title_from_h1(self):
        """Test title extraction from h1 tag when no title tag."""
        extractor = ContentExtractor()
        
        html = "<html><body><h1>Main Heading</h1><p>Content</p></body></html>"
        title = extractor._extract_title(html)
        
        assert title == "Main Heading"
    
    def test_detect_language_english(self):
        """Test English language detection."""
        extractor = ContentExtractor()
        
        english_text = "The quick brown fox jumps over the lazy dog. This is a test article with many common English words and you can see that this has the and are but not all."
        language = extractor._detect_language(english_text)
        
        assert language == "en"
    
    def test_detect_language_unknown(self):
        """Test unknown language detection."""
        extractor = ContentExtractor()
        
        unknown_text = "Lorem ipsum dolor sit amet consectetur adipiscing elit"
        language = extractor._detect_language(unknown_text)
        
        assert language is None
    
    def test_extract_content_success(self):
        """Test successful content extraction."""
        extractor = ContentExtractor(min_content_length=10)
        
        html = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <article>
                <h1>Main Title</h1>
                <p>This is the main content of the article. It contains several sentences.</p>
                <p>Here is another paragraph with more content to make it substantial.</p>
            </article>
        </body>
        </html>
        """
        
        article_content = ArticleContent(
            url="https://example.com/article",
            html=html,
            status_code=200,
        )
        
        result = extractor.extract_content(article_content)
        
        assert isinstance(result, ExtractedContent)
        assert result.url == "https://example.com/article"
        assert result.title == "Test Article"
        assert "Main Title" in result.content_markdown
        assert "main content" in result.content_markdown
        assert result.word_count > 0
        assert result.language == "en"
        assert result.domain == "example.com"
    
    def test_extract_content_too_short(self):
        """Test extraction failure for content too short."""
        extractor = ContentExtractor(min_content_length=100)
        
        html = "<html><body><p>Short.</p></body></html>"
        
        article_content = ArticleContent(
            url="https://example.com/short",
            html=html,
            status_code=200,
        )
        
        result = extractor.extract_content(article_content)
        
        assert isinstance(result, ContentError)
        assert result.error_type == "extraction"
        assert "Content too short" in result.error_message
    
    def test_extract_content_readability_fails(self):
        """Test extraction failure when readability fails."""
        extractor = ContentExtractor()
        
        # Empty or invalid HTML
        html = "<html></html>"
        
        article_content = ArticleContent(
            url="https://example.com/empty",
            html=html,
            status_code=200,
        )
        
        result = extractor.extract_content(article_content)
        
        assert isinstance(result, ContentError)
        assert result.error_type == "extraction"
    
    def test_extract_content_truncation(self):
        """Test content truncation for very long content."""
        extractor = ContentExtractor(max_content_length=50)
        
        long_content = "This is a very long article. " * 100  # Make it long
        html = f"<html><body><article><p>{long_content}</p></article></body></html>"
        
        article_content = ArticleContent(
            url="https://example.com/long",
            html=html,
            status_code=200,
        )
        
        result = extractor.extract_content(article_content)
        
        assert isinstance(result, ExtractedContent)
        assert "[Content truncated...]" in result.content_markdown
        assert len(result.content_markdown) <= 50 + 50  # Some margin for truncation message
    
    def test_extract_multiple_empty_list(self):
        """Test extracting from empty list returns empty list."""
        extractor = ContentExtractor()
        
        result = extractor.extract_multiple([])
        
        assert result == []
    
    def test_extract_multiple_success(self):
        """Test extracting from multiple articles."""
        extractor = ContentExtractor(min_content_length=10)
        
        html1 = "<html><body><h1>Article 1</h1><p>Content for article one.</p></body></html>"
        html2 = "<html><body><h1>Article 2</h1><p>Content for article two.</p></body></html>"
        
        articles = [
            ArticleContent(
                url="https://example.com/1",
                html=html1,
                status_code=200,
            ),
            ArticleContent(
                url="https://example.com/2",
                html=html2,
                status_code=200,
            ),
        ]
        
        results = extractor.extract_multiple(articles)
        
        assert len(results) == 2
        assert all(isinstance(r, ExtractedContent) for r in results)
        assert "Article 1" in results[0].content_markdown
        assert "Article 2" in results[1].content_markdown
    
    def test_extract_content_exception_handling(self):
        """Test that exceptions during extraction are handled."""
        extractor = ContentExtractor()
        
        # Create malformed HTML that will cause readability to fail
        article_content = ArticleContent(
            url="https://example.com/error",
            html="<html><body>",  # Malformed HTML
            status_code=200,
        )
        
        result = extractor.extract_content(article_content)
        
        assert isinstance(result, ContentError)
        assert result.error_type in ["extraction", "extraction_exception"]