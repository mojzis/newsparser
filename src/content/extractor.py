"""Content extraction from HTML to Markdown."""
import re
from datetime import datetime
from urllib.parse import urlparse

import html2text
from bs4 import BeautifulSoup
from pydantic import HttpUrl
from readability import Document

from src.content.models import ArticleContent, ContentError, ExtractedContent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ContentExtractor:
    """Extracts and converts content from HTML to Markdown."""
    
    def __init__(
        self,
        min_content_length: int = 100,
        max_content_length: int = 50000,
    ) -> None:
        """
        Initialize the content extractor.
        
        Args:
            min_content_length: Minimum content length to consider valid
            max_content_length: Maximum content length to process
        """
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length
        
        # Configure html2text for clean Markdown output
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = True
        self.html2text.ignore_emphasis = False
        self.html2text.body_width = 0  # No line wrapping
        self.html2text.unicode_snob = True
        self.html2text.escape_snob = True
    
    def _clean_html(self, html: str) -> str:
        """Clean HTML by removing unwanted elements."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Remove comment elements
        for element in soup(string=lambda text: isinstance(text, str) and text.strip().startswith("<!--")):
            element.extract()
        
        # Remove navigation, sidebar, footer elements
        for element in soup.find_all(attrs={"class": re.compile(r"nav|sidebar|footer|menu|ad|advertisement", re.I)}):
            element.decompose()
        
        for element in soup.find_all(attrs={"id": re.compile(r"nav|sidebar|footer|menu|ad|advertisement", re.I)}):
            element.decompose()
        
        # Remove elements by tag that are typically not content
        for tag in soup(["nav", "aside", "footer", "header"]):
            tag.decompose()
        
        return str(soup)
    
    def _extract_author(self, html: str) -> str | None:
        """Extract author from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Try multiple author extraction methods
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[name="twitter:creator"]',
            '[rel="author"]',
            '.author',
            '.byline',
            '.writer',
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    author = element.get("content", "").strip()
                else:
                    author = element.get_text().strip()
                
                if author and len(author) > 1:
                    # Clean up author name
                    author = re.sub(r"^by\s+", "", author, flags=re.IGNORECASE)
                    author = re.sub(r"\s+", " ", author)
                    author = author[:100]  # Reasonable author name length
                    return author
        
        return None
    
    def _extract_medium(self, html: str) -> str | None:
        """Extract publication/medium name from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Try multiple medium extraction methods
        medium_selectors = [
            'meta[property="og:site_name"]',
            'meta[name="publisher"]',
            'meta[property="article:publisher"]',
            '.publication',
            '.site-name',
            '.brand',
        ]
        
        for selector in medium_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    medium = element.get("content", "").strip()
                else:
                    medium = element.get_text().strip()
                
                if medium and len(medium) > 1:
                    # Clean up medium name
                    medium = re.sub(r"\s+", " ", medium)
                    medium = medium[:100]  # Reasonable medium name length
                    return medium
        
        return None

    def _extract_title(self, html: str) -> str | None:
        """Extract title from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Try multiple title extraction methods
        title_selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            "title",
            "h1",
            ".title",
            "#title",
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    title = element.get("content", "").strip()
                else:
                    title = element.get_text().strip()
                
                if title and len(title) > 3:
                    # Clean up title
                    title = re.sub(r"\s+", " ", title)
                    title = title[:200]  # Reasonable title length
                    return title
        
        return None
    
    def _detect_language(self, text: str) -> str | None:
        """Basic language detection based on common patterns."""
        # Simple heuristic - could be enhanced with proper language detection
        text_sample = text[:1000].lower()
        
        # Common English words
        english_indicators = ["the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "was", "one", "our", "out", "day", "get", "has", "him", "his", "how", "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "its", "let", "put", "say", "she", "too", "use"]
        english_count = sum(1 for word in english_indicators if f" {word} " in text_sample)
        
        if english_count >= 5:
            return "en"
        
        return None
    
    def extract_content(self, article_content: ArticleContent, debug: bool = False) -> ExtractedContent | ContentError:
        """
        Extract content from ArticleContent and convert to Markdown.
        
        Args:
            article_content: ArticleContent object with HTML
            
        Returns:
            ExtractedContent on success, ContentError on failure
        """
        try:
            url_str = str(article_content.url)
            parsed_url = urlparse(url_str)
            domain = parsed_url.netloc
            
            logger.debug(f"Extracting content from {url_str}")
            
            if debug:
                # Analyze HTML structure for debugging
                soup = BeautifulSoup(article_content.html, "html.parser")
                
                # Count different elements
                debug_info = {
                    "total_html_length": len(article_content.html),
                    "title_tags": len(soup.find_all("title")),
                    "h1_tags": len(soup.find_all("h1")),
                    "p_tags": len(soup.find_all("p")),
                    "div_tags": len(soup.find_all("div")),
                    "article_tags": len(soup.find_all("article")),
                    "main_tags": len(soup.find_all("main")),
                    "content_classes": len(soup.find_all(attrs={"class": re.compile(r"content|article|post", re.I)})),
                }
                
                logger.info(f"HTML structure analysis: {debug_info}")
            
            # Use readability to extract main content
            doc = Document(article_content.html)
            title = doc.title()
            content_html = doc.summary()
            
            if debug:
                logger.info(f"Readability extracted title: '{title}'")
                logger.info(f"Readability content length: {len(content_html) if content_html else 0}")
                if content_html:
                    # Show first 200 chars of extracted HTML
                    preview = content_html[:200] + "..." if len(content_html) > 200 else content_html
                    logger.info(f"Readability HTML preview: {repr(preview)}")
            
            if not content_html or len(content_html.strip()) < 50:
                error_details = "Readability failed to extract meaningful content"
                if debug:
                    error_details += f" (extracted {len(content_html) if content_html else 0} chars)"
                return ContentError(
                    url=article_content.url,
                    error_type="extraction",
                    error_message=error_details,
                )
            
            # Clean the HTML
            cleaned_html = self._clean_html(content_html)
            
            # Convert to Markdown
            markdown_content = self.html2text.handle(cleaned_html).strip()
            
            if debug:
                logger.info(f"HTML2Text conversion result length: {len(markdown_content)}")
                if markdown_content:
                    preview = markdown_content[:200] + "..." if len(markdown_content) > 200 else markdown_content
                    logger.info(f"Markdown preview: {repr(preview)}")
            
            # Additional cleaning of Markdown
            # Remove excessive newlines
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
            
            # Remove empty lines with just spaces
            lines = markdown_content.split("\n")
            cleaned_lines = [line.rstrip() for line in lines]
            markdown_content = "\n".join(cleaned_lines)
            
            if debug:
                logger.info(f"Final cleaned markdown length: {len(markdown_content)}")
            
            # Check content length
            if len(markdown_content) < self.min_content_length:
                error_details = f"Content too short: {len(markdown_content)} characters (minimum: {self.min_content_length})"
                if debug and markdown_content:
                    error_details += f"\nActual content: {repr(markdown_content[:100])}"
                return ContentError(
                    url=article_content.url,
                    error_type="extraction",
                    error_message=error_details,
                )
            
            if len(markdown_content) > self.max_content_length:
                logger.warning(f"Content truncated for {url_str}: {len(markdown_content)} chars")
                markdown_content = markdown_content[:self.max_content_length] + "\n\n[Content truncated...]"
            
            # Try to extract a better title if readability didn't find one
            final_title = title
            if not final_title or len(final_title.strip()) < 3:
                extracted_title = self._extract_title(article_content.html)
                if extracted_title:
                    final_title = extracted_title
            
            # Count words (approximate)
            word_count = len(re.findall(r"\b\w+\b", markdown_content))
            
            # Detect language
            language = self._detect_language(markdown_content)
            
            # Extract author and medium
            author = self._extract_author(article_content.html)
            medium = self._extract_medium(article_content.html)
            
            logger.info(
                f"Extracted content from {url_str}: "
                f"{word_count} words, {len(markdown_content)} chars"
            )
            
            return ExtractedContent(
                url=article_content.url,
                title=final_title,
                content_markdown=markdown_content,
                word_count=word_count,
                language=language,
                domain=domain,
                author=author,
                medium=medium,
                extraction_timestamp=datetime.utcnow(),
            )
        
        except Exception as e:
            logger.exception(f"Failed to extract content from {article_content.url}: {e}")
            return ContentError(
                url=article_content.url,
                error_type="extraction_exception",
                error_message=f"Exception during extraction: {e}",
            )
    
    def extract_multiple(
        self, article_contents: list[ArticleContent]
    ) -> list[ExtractedContent | ContentError]:
        """
        Extract content from multiple ArticleContent objects.
        
        Args:
            article_contents: List of ArticleContent objects
            
        Returns:
            List of ExtractedContent or ContentError objects
        """
        if not article_contents:
            return []
        
        logger.info(f"Extracting content from {len(article_contents)} articles")
        
        results = []
        for article_content in article_contents:
            result = self.extract_content(article_content)
            results.append(result)
        
        successful = sum(1 for r in results if isinstance(r, ExtractedContent))
        logger.info(f"Extracted {successful}/{len(article_contents)} articles successfully")
        
        return results