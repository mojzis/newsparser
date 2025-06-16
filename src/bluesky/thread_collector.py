"""Thread collection service for fetching complete Bluesky threads."""

import asyncio
from typing import Any, Dict, List, Optional, Set
from collections import deque

from atproto import AsyncClient, models
from atproto.exceptions import AtProtocolError

from src.models.post import BlueskyPost, ThreadPosition
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ThreadCollector:
    """Service for collecting complete Bluesky threads."""
    
    def __init__(self, client: AsyncClient):
        """
        Initialize thread collector with authenticated atproto client.
        
        Args:
            client: Authenticated AsyncClient instance
        """
        self.client = client
        self._collected_threads: Set[str] = set()  # Track processed thread roots
    
    async def collect_thread_from_post(
        self, 
        post_uri: str, 
        depth: int = 6, 
        parent_height: int = 80
    ) -> List[BlueskyPost]:
        """
        Fetch complete thread for a given post URI.
        
        Args:
            post_uri: URI of any post in the thread
            depth: How deep to go in replies (default 6)
            parent_height: How far up parent chain (default 80)
            
        Returns:
            List of BlueskyPost instances for all posts in the thread
        """
        try:
            logger.info(f"Fetching thread for post: {post_uri}")
            
            # Get thread data from atproto
            params = models.AppBskyFeedGetPostThread.Params(
                uri=post_uri,
                depth=depth,
                parent_height=parent_height
            )
            
            response = await self.client.app.bsky.feed.get_post_thread(params)
            
            # Extract all posts from thread structure
            posts = self._extract_thread_posts(response.thread)
            
            # Mark this thread as collected
            if posts:
                root_uri = self._find_thread_root_uri(posts)
                if root_uri:
                    self._collected_threads.add(root_uri)
            
            logger.info(f"Extracted {len(posts)} posts from thread")
            return posts
            
        except AtProtocolError as e:
            logger.error(f"Failed to fetch thread for {post_uri}: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error fetching thread for {post_uri}: {e}")
            return []
    
    async def collect_threads_from_search(
        self, 
        search_posts: List[BlueskyPost], 
        depth: int = 6, 
        parent_height: int = 80
    ) -> List[BlueskyPost]:
        """
        Collect complete threads for all posts from search results.
        
        Args:
            search_posts: Posts found via search
            depth: Thread depth to fetch
            parent_height: Parent chain height to fetch
            
        Returns:
            List of all posts from all threads (deduplicated)
        """
        all_thread_posts = []
        processed_roots = set()
        
        for post in search_posts:
            # Skip if we've already processed this thread
            potential_root = post.thread_root_uri or post.id
            if potential_root in processed_roots:
                continue
            
            # Fetch complete thread
            thread_posts = await self.collect_thread_from_post(
                post.id, depth, parent_height
            )
            
            if thread_posts:
                # Find actual root URI and mark as processed
                root_uri = self._find_thread_root_uri(thread_posts)
                if root_uri:
                    processed_roots.add(root_uri)
                
                all_thread_posts.extend(thread_posts)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.3)
        
        logger.info(f"Collected {len(all_thread_posts)} total posts from {len(processed_roots)} threads")
        return all_thread_posts
    
    def _extract_thread_posts(self, thread_view: Any) -> List[BlueskyPost]:
        """
        Extract all posts from atproto thread structure.
        
        Args:
            thread_view: Thread response from atproto
            
        Returns:
            List of BlueskyPost instances with thread metadata
        """
        posts = []
        
        # Use BFS to traverse thread structure
        queue = deque([(thread_view, None, 0)])  # (view, parent_uri, depth)
        root_uri = None
        
        while queue:
            current_view, parent_uri, depth = queue.popleft()
            
            try:
                # Extract post data
                if hasattr(current_view, 'post'):
                    post_data = current_view.post
                    post = self._convert_thread_post_to_model(post_data, parent_uri, depth)
                    
                    # Set root URI (first post we encounter is the root)
                    if root_uri is None:
                        root_uri = post.id
                        post.set_thread_metadata(post.id, "root", 0)
                    else:
                        # Determine position based on depth and parent
                        position = "reply" if depth == 1 else "nested_reply"
                        post.set_thread_metadata(root_uri, position, depth, parent_uri)
                    
                    posts.append(post)
                    
                    # Add replies to queue
                    if hasattr(current_view, 'replies') and current_view.replies:
                        for reply in current_view.replies:
                            queue.append((reply, post.id, depth + 1))
                
            except Exception as e:
                logger.warning(f"Failed to parse thread post at depth {depth}: {e}")
                continue
        
        return posts
    
    def _convert_thread_post_to_model(
        self, 
        post_data: Any, 
        parent_uri: Optional[str], 
        depth: int
    ) -> BlueskyPost:
        """
        Convert atproto post data to BlueskyPost model with thread context.
        
        Args:
            post_data: Raw post data from atproto
            parent_uri: URI of parent post (if any)
            depth: Thread depth level
            
        Returns:
            BlueskyPost instance
        """
        # Use similar logic to the main client's conversion
        # but include thread-specific context
        
        from src.bluesky.client import BlueskyClient
        
        # Create a temporary client instance to use its conversion method
        # This is not ideal but reuses existing logic
        temp_client = BlueskyClient.__new__(BlueskyClient)
        
        # Convert using existing logic
        post = temp_client._convert_post_to_model(post_data)
        
        return post
    
    def _find_thread_root_uri(self, posts: List[BlueskyPost]) -> Optional[str]:
        """
        Find the root URI from a list of thread posts.
        
        Args:
            posts: List of posts from a thread
            
        Returns:
            URI of the root post, or None if not found
        """
        for post in posts:
            if post.thread_position == "root" or post.thread_depth == 0:
                return post.id
        
        # Fallback: return first post's thread_root_uri or its own URI
        if posts:
            return posts[0].thread_root_uri or posts[0].id
        
        return None
    
    def has_collected_thread(self, root_uri: str) -> bool:
        """
        Check if a thread has already been collected.
        
        Args:
            root_uri: URI of the thread root
            
        Returns:
            True if thread was already collected
        """
        return root_uri in self._collected_threads
    
    def reset_collection_cache(self) -> None:
        """Reset the cache of collected threads."""
        self._collected_threads.clear()