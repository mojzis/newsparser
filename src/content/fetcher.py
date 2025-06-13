"""Article fetching client using httpx."""
import asyncio
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import HttpUrl

from src.content.models import ArticleContent, ContentError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ArticleFetcher:
    """Fetches article content from URLs with error handling and retry logic."""
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_content_size: int = 10 * 1024 * 1024,  # 10MB
    ) -> None:
        """
        Initialize the article fetcher.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            max_content_size: Maximum content size to download
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_content_size = max_content_size
        
        # Headers to mimic a real browser
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=self.headers,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self) -> "ArticleFetcher":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and safe to fetch."""
        try:
            parsed = urlparse(url)
            return all([
                parsed.scheme in ("http", "https"),
                parsed.netloc,
                not parsed.netloc.startswith("localhost"),
                not parsed.netloc.startswith("127.0.0.1"),
                not parsed.netloc.startswith("0.0.0.0"),
            ])
        except Exception:
            return False
    
    async def fetch_article(self, url: str | HttpUrl) -> ArticleContent | ContentError:
        """
        Fetch article content from URL with retries.
        
        Args:
            url: URL to fetch
            
        Returns:
            ArticleContent on success, ContentError on failure
        """
        url_str = str(url)
        
        if not self._is_valid_url(url_str):
            return ContentError(
                url=url,
                error_type="validation",
                error_message=f"Invalid or unsafe URL: {url_str}",
            )
        
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Fetching {url_str} (attempt {attempt + 1})")
                
                response = await self.client.get(url_str)
                
                # Check content length
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.max_content_size:
                    return ContentError(
                        url=url,
                        error_type="size",
                        error_message=f"Content too large: {content_length} bytes",
                    )
                
                # Check if response is HTML-like
                content_type = response.headers.get("content-type", "").lower()
                if not any(ct in content_type for ct in ["text/html", "application/xhtml"]):
                    return ContentError(
                        url=url,
                        error_type="content_type",
                        error_message=f"Non-HTML content type: {content_type}",
                    )
                
                # Handle non-2xx status codes
                if response.status_code >= 400:
                    # Don't retry permanent errors
                    permanent_errors = {401, 403, 404, 410, 451}  # Unauthorized, Forbidden, Not Found, Gone, Unavailable For Legal Reasons
                    
                    if response.status_code in permanent_errors:
                        logger.warning(
                            f"HTTP {response.status_code} for {url_str} - permanent error, not retrying"
                        )
                        return ContentError(
                            url=url,
                            error_type="permanent_http_error",
                            error_message=f"HTTP {response.status_code}: {response.reason_phrase} (permanent)",
                        )
                    
                    # Retry transient errors (5xx, 429, 408, etc.)
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            f"HTTP {response.status_code} for {url_str}, "
                            f"retrying in {delay}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    
                    return ContentError(
                        url=url,
                        error_type="http_error",
                        error_message=f"HTTP {response.status_code}: {response.reason_phrase}",
                    )
                
                # Check actual content size
                content = response.text
                if len(content.encode("utf-8")) > self.max_content_size:
                    return ContentError(
                        url=url,
                        error_type="size",
                        error_message="Content exceeds size limit after download",
                    )
                
                logger.info(f"Successfully fetched {url_str} ({len(content)} chars)")
                
                return ArticleContent(
                    url=url,
                    html=content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    fetch_timestamp=datetime.utcnow(),
                )
            
            except httpx.TimeoutException:
                error_msg = f"Timeout after {self.timeout}s"
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Timeout for {url_str}, retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                
                return ContentError(
                    url=url,
                    error_type="timeout",
                    error_message=error_msg,
                )
            
            except httpx.NetworkError as e:
                error_msg = f"Network error: {e}"
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Network error for {url_str}, retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                
                return ContentError(
                    url=url,
                    error_type="network",
                    error_message=error_msg,
                )
            
            except Exception as e:
                logger.exception(f"Unexpected error fetching {url_str}: {e}")
                return ContentError(
                    url=url,
                    error_type="unexpected",
                    error_message=f"Unexpected error: {e}",
                )
        
        # This should never be reached
        return ContentError(
            url=url,
            error_type="unknown",
            error_message="Unknown error after all retries",
        )
    
    async def fetch_multiple(
        self, urls: list[str | HttpUrl], max_concurrent: int = 5
    ) -> list[ArticleContent | ContentError]:
        """
        Fetch multiple articles concurrently.
        
        Args:
            urls: List of URLs to fetch
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of ArticleContent or ContentError objects
        """
        if not urls:
            return []
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url: str | HttpUrl) -> ArticleContent | ContentError:
            async with semaphore:
                return await self.fetch_article(url)
        
        logger.info(f"Fetching {len(urls)} articles with max {max_concurrent} concurrent")
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ContentError(
                        url=urls[i],
                        error_type="exception",
                        error_message=f"Exception during fetch: {result}",
                    )
                )
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if isinstance(r, ArticleContent))
        logger.info(f"Fetched {successful}/{len(urls)} articles successfully")
        
        return processed_results