"""URL expansion utilities for resolving shortened URLs."""

import asyncio
import logging
from typing import Optional, Set
from urllib.parse import urlparse

import httpx
from pydantic import HttpUrl

logger = logging.getLogger(__name__)

# Common URL shortener domains
SHORTENER_DOMAINS = {
    "bit.ly", "bitly.com", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "short.link", "tiny.cc", "is.gd", "buff.ly", "ift.tt", "dlvr.it",
    "fb.me", "amzn.to", "youtu.be", "linkedin.com/posts", "lnkd.in",
    "rebrand.ly", "cutt.ly", "bl.ink", "short.lnk", "v.gd", "x.co",
    "po.st", "shor.by", "switchy.io", "smallseotools.com"
}


class URLExpander:
    """Expands shortened URLs to their final destinations."""
    
    def __init__(
        self,
        timeout: float = 10.0,
        max_redirects: int = 10,
        user_agent: str = "Mozilla/5.0 (compatible; URLExpander/1.0)"
    ):
        """
        Initialize URL expander.
        
        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
            user_agent: User agent string for requests
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.user_agent = user_agent
        
        # Cache for expanded URLs to avoid repeated requests
        self._cache: dict[str, str] = {}
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": user_agent},
            follow_redirects=False,  # We'll handle redirects manually
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def is_shortened_url(self, url: str) -> bool:
        """
        Check if a URL appears to be from a known shortener service.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be shortened
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix if present
            if domain.startswith("www."):
                domain = domain[4:]
            
            return domain in SHORTENER_DOMAINS
        except Exception:
            return False
    
    async def expand_url(self, url: str) -> str:
        """
        Expand a single URL to its final destination.
        
        Args:
            url: URL to expand
            
        Returns:
            Final expanded URL, or original URL if expansion fails
        """
        # Check cache first
        if url in self._cache:
            return self._cache[url]
        
        # If not a known shortener, return as-is
        if not self.is_shortened_url(url):
            self._cache[url] = url
            return url
        
        try:
            final_url = await self._follow_redirects(url)
            self._cache[url] = final_url
            logger.debug(f"Expanded {url} -> {final_url}")
            return final_url
        except Exception as e:
            logger.warning(f"Failed to expand URL {url}: {e}")
            # Return original URL if expansion fails
            self._cache[url] = url
            return url
    
    async def _follow_redirects(self, url: str) -> str:
        """
        Follow redirects to find the final URL.
        
        Args:
            url: Starting URL
            
        Returns:
            Final URL after following redirects
        """
        current_url = url
        redirect_count = 0
        
        while redirect_count < self.max_redirects:
            try:
                response = await self.client.head(current_url)
                
                # Check for redirect status codes
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        break
                    
                    # Handle relative URLs
                    if location.startswith("/"):
                        parsed = urlparse(current_url)
                        location = f"{parsed.scheme}://{parsed.netloc}{location}"
                    elif not location.startswith(("http://", "https://")):
                        # Relative to current path
                        parsed = urlparse(current_url)
                        base = f"{parsed.scheme}://{parsed.netloc}"
                        if parsed.path:
                            base += "/" + "/".join(parsed.path.split("/")[:-1])
                        location = f"{base}/{location}"
                    
                    current_url = location
                    redirect_count += 1
                    logger.debug(f"Redirect {redirect_count}: {current_url}")
                else:
                    # No more redirects
                    break
                    
            except httpx.HTTPStatusError:
                # Some services return errors for HEAD requests, try GET
                try:
                    response = await self.client.get(
                        current_url, 
                        headers={"Range": "bytes=0-0"}  # Minimal request
                    )
                    # Same redirect logic as above
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if location:
                            current_url = location
                            redirect_count += 1
                            continue
                except Exception:
                    break
                break
            except Exception as e:
                logger.debug(f"Error following redirect from {current_url}: {e}")
                break
        
        if redirect_count >= self.max_redirects:
            logger.warning(f"Maximum redirects ({self.max_redirects}) reached for {url}")
        
        return current_url
    
    async def expand_urls(self, urls: list[str]) -> list[str]:
        """
        Expand multiple URLs concurrently.
        
        Args:
            urls: List of URLs to expand
            
        Returns:
            List of expanded URLs in the same order
        """
        if not urls:
            return []
        
        # Expand URLs concurrently
        tasks = [self.expand_url(url) for url in urls]
        expanded = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        results = []
        for i, result in enumerate(expanded):
            if isinstance(result, Exception):
                logger.warning(f"Failed to expand URL {urls[i]}: {result}")
                results.append(urls[i])  # Use original URL
            else:
                results.append(result)
        
        return results


async def expand_url(url: str) -> str:
    """
    Convenience function to expand a single URL.
    
    Args:
        url: URL to expand
        
    Returns:
        Expanded URL
    """
    async with URLExpander() as expander:
        return await expander.expand_url(url)


async def expand_urls(urls: list[str]) -> list[str]:
    """
    Convenience function to expand multiple URLs.
    
    Args:
        urls: List of URLs to expand
        
    Returns:
        List of expanded URLs
    """
    async with URLExpander() as expander:
        return await expander.expand_urls(urls)