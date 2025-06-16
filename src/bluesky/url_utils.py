"""Utilities for handling Bluesky URLs and AT protocol URIs."""

import re
from typing import Optional
from urllib.parse import urlparse


def is_bluesky_post_url(url: str) -> bool:
    """
    Check if URL is a Bluesky post reference.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL points to a Bluesky post
    """
    if not url:
        return False
    
    # Pattern: https://bsky.app/profile/[handle]/post/[id]
    bluesky_pattern = r'^https?://bsky\.app/profile/[^/]+/post/[^/]+/?$'
    return bool(re.match(bluesky_pattern, url))


def extract_post_uri_from_url(url: str) -> Optional[str]:
    """
    Extract AT protocol URI from Bluesky URL.
    
    Args:
        url: Bluesky post URL (e.g., https://bsky.app/profile/handle.bsky.social/post/abc123)
        
    Returns:
        AT protocol URI (e.g., at://did:plc:xyz/app.bsky.feed.post/abc123) or None if invalid
    """
    if not is_bluesky_post_url(url):
        return None
    
    try:
        # Parse URL: https://bsky.app/profile/handle.bsky.social/post/abc123
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) != 4 or path_parts[0] != 'profile' or path_parts[2] != 'post':
            return None
        
        handle = path_parts[1]
        post_id = path_parts[3]
        
        # For now, we'll return a special format that the Bluesky client can handle
        # The atproto library can resolve handles to DIDs automatically
        return f"at://{handle}/app.bsky.feed.post/{post_id}"
        
    except Exception:
        return None


def extract_handle_and_post_id(url: str) -> Optional[tuple[str, str]]:
    """
    Extract handle and post ID from Bluesky URL.
    
    Args:
        url: Bluesky post URL
        
    Returns:
        Tuple of (handle, post_id) or None if invalid
    """
    if not is_bluesky_post_url(url):
        return None
    
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) != 4 or path_parts[0] != 'profile' or path_parts[2] != 'post':
            return None
        
        handle = path_parts[1]
        post_id = path_parts[3]
        
        return handle, post_id
        
    except Exception:
        return None


def clean_bluesky_urls_from_links(links: list[str]) -> tuple[list[str], list[str]]:
    """
    Separate Bluesky post URLs from other URLs.
    
    Args:
        links: List of URLs
        
    Returns:
        Tuple of (non_bluesky_urls, bluesky_urls)
    """
    bluesky_urls = []
    other_urls = []
    
    for url in links:
        if is_bluesky_post_url(str(url)):
            bluesky_urls.append(url)
        else:
            other_urls.append(url)
    
    return other_urls, bluesky_urls