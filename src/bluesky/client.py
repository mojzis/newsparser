import asyncio
from datetime import datetime
from typing import Any, List, Optional

from atproto import AsyncClient, models
from atproto.exceptions import AtProtocolError

from src.bluesky.query_builders import QueryBuilderFactory
from src.config.searches import SearchDefinition
from src.config.settings import Settings
from src.models.post import BlueskyPost, EngagementMetrics
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BlueskyClient:
    """Client for interacting with Bluesky API using atproto."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize Bluesky client with settings.

        Args:
            settings: Application settings containing Bluesky credentials
        """
        self.settings = settings
        self.client: AsyncClient | None = None
        self._session_active = False

    async def authenticate(self) -> bool:
        """
        Authenticate with Bluesky using handle and app password.

        Returns:
            True if authentication successful, False otherwise
        """
        if not self.settings.bluesky_handle or not self.settings.bluesky_app_password:
            logger.error("Bluesky credentials not configured")
            return False

        try:
            self.client = AsyncClient()
            await self.client.login(
                self.settings.bluesky_handle, self.settings.bluesky_app_password
            )
            self._session_active = True
            logger.info(f"Successfully authenticated as {self.settings.bluesky_handle}")
            return True

        except AtProtocolError as e:
            logger.exception(f"Authentication failed: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected authentication error: {e}")
            return False

    async def close(self) -> None:
        """Close the client session."""
        if self.client:
            # AsyncClient from atproto doesn't have a close method
            # Just reset our session state
            self._session_active = False
            self.client = None
            logger.info("Bluesky client session closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated before making requests."""
        if not self._session_active or not self.client:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

    def _convert_post_to_model(
        self, post_data: Any
    ) -> BlueskyPost:
        """
        Convert atproto post data to our BlueskyPost model.

        Args:
            post_data: Raw post data from atproto (could be FeedViewPost or PostView)

        Returns:
            BlueskyPost model instance
        """
        # Handle different post data structures
        if hasattr(post_data, 'post'):
            # FeedViewPost structure
            post = post_data.post
        else:
            # Direct PostView structure
            post = post_data

        # Extract engagement metrics
        engagement = EngagementMetrics(
            likes=getattr(post, "like_count", 0) or 0,
            reposts=getattr(post, "repost_count", 0) or 0,
            replies=getattr(post, "reply_count", 0) or 0,
        )

        # Extract links from post content
        links = []
        if hasattr(post.record, "facets") and post.record.facets:
            for facet in post.record.facets:
                for feature in facet.features:
                    if hasattr(feature, "uri"):
                        links.append(feature.uri)

        # Handle datetime conversion
        created_at = post.record.created_at
        if isinstance(created_at, str):
            # Parse ISO format datetime string
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        # Validate content is not empty
        content = post.record.text or ""
        if not content.strip():
            raise ValueError("Post content is empty or whitespace only")

        return BlueskyPost(
            id=post.uri,
            author=post.author.handle,
            content=content,
            created_at=created_at,
            links=links,
            engagement_metrics=engagement,
        )

    async def search_posts(
        self, query: str, limit: int = 25, cursor: str | None = None, sort: str = "latest"
    ) -> tuple[list[BlueskyPost], str | None]:
        """
        Search for posts containing specific keywords.

        Args:
            query: Search query string (Lucene syntax supported)
            limit: Maximum number of posts to return (default 25)
            cursor: Pagination cursor for next batch
            sort: Sort order ("latest" or "top")

        Returns:
            Tuple of (posts list, next_cursor)
        """
        self._ensure_authenticated()

        try:
            params = {
                "q": query,
                "limit": limit,
                "sort": sort,
            }
            
            if cursor:
                params["cursor"] = cursor

            response = await self.client.app.bsky.feed.search_posts(params=params)

            posts = []
            for post_data in response.posts:
                try:
                    post_model = self._convert_post_to_model(post_data)
                    posts.append(post_model)
                except Exception as e:
                    # Try to get URI for logging, but handle different post structures
                    try:
                        if hasattr(post_data, 'post'):
                            uri = post_data.post.uri
                        elif hasattr(post_data, 'uri'):
                            uri = post_data.uri
                        else:
                            uri = "unknown"
                        logger.warning(f"Failed to convert post {uri}: {e}")
                    except:
                        logger.warning(f"Failed to convert post (unknown URI): {e}")
                    continue

            next_cursor = getattr(response, "cursor", None)
            logger.info(f"Found {len(posts)} posts for query: {query}")

            return posts, next_cursor

        except AtProtocolError as e:
            logger.exception(f"Search failed: {e}")
            return [], None
        except Exception as e:
            logger.exception(f"Unexpected search error: {e}")
            return [], None

    async def search_by_definition(
        self, search_definition: SearchDefinition, limit: int = 25, cursor: str | None = None
    ) -> tuple[list[BlueskyPost], str | None]:
        """
        Search for posts using a search definition.

        Args:
            search_definition: SearchDefinition containing query parameters
            limit: Maximum number of posts to return
            cursor: Pagination cursor for next batch

        Returns:
            Tuple of (posts list, next_cursor)
        """
        try:
            # Build query using appropriate builder
            builder = QueryBuilderFactory.create(search_definition.query_syntax)
            query = builder.build_query(search_definition)
            
            # Validate query
            is_valid, error_msg = builder.validate_query(query)
            if not is_valid:
                raise ValueError(f"Invalid query: {error_msg}")
            
            logger.info(f"Searching with definition '{search_definition.name}' using {search_definition.query_syntax} syntax: {query}")
            
            return await self.search_posts(
                query=query,
                limit=limit,
                cursor=cursor,
                sort=search_definition.sort
            )
            
        except Exception as e:
            logger.error(f"Failed to search with definition '{search_definition.name}': {e}")
            return [], None

    async def search_mcp_mentions(
        self, limit: int = 25, cursor: str | None = None
    ) -> tuple[list[BlueskyPost], str | None]:
        """
        Search for posts mentioning "mcp" or related terms.
        
        Note: This method is deprecated. Use search_by_definition instead.

        Args:
            limit: Maximum number of posts to return
            cursor: Pagination cursor for next batch

        Returns:
            Tuple of (posts list, next_cursor)
        """
        # Search for "mcp" keyword - kept for backward compatibility
        return await self.search_posts("mcp", limit=limit, cursor=cursor)

    async def get_posts_by_definition(
        self, search_definition: SearchDefinition, max_posts: int = 100
    ) -> list[BlueskyPost]:
        """
        Get posts using a search definition, handling pagination.

        Args:
            search_definition: SearchDefinition to use for search
            max_posts: Maximum number of posts to collect

        Returns:
            List of BlueskyPost instances
        """
        all_posts = []
        cursor = None

        while len(all_posts) < max_posts:
            batch_size = min(25, max_posts - len(all_posts))
            posts, next_cursor = await self.search_by_definition(
                search_definition, limit=batch_size, cursor=cursor
            )

            if not posts:
                break

            all_posts.extend(posts)
            cursor = next_cursor

            if not cursor:
                break

            # Add small delay to respect rate limits
            await asyncio.sleep(0.5)

        logger.info(f"Collected {len(all_posts)} posts using definition '{search_definition.name}'")
        return all_posts

    async def get_recent_mcp_posts(self, max_posts: int = 100) -> list[BlueskyPost]:
        """
        Get recent posts mentioning MCP, handling pagination.
        
        Note: This method is deprecated. Use get_posts_by_definition instead.

        Args:
            max_posts: Maximum number of posts to collect

        Returns:
            List of BlueskyPost instances
        """
        all_posts = []
        cursor = None

        while len(all_posts) < max_posts:
            batch_size = min(25, max_posts - len(all_posts))
            posts, next_cursor = await self.search_mcp_mentions(
                limit=batch_size, cursor=cursor
            )

            if not posts:
                break

            all_posts.extend(posts)
            cursor = next_cursor

            if not cursor:
                break

            # Add small delay to respect rate limits
            await asyncio.sleep(0.5)

        logger.info(f"Collected {len(all_posts)} MCP-related posts")
        return all_posts
    
    async def get_thread_by_uri(
        self, 
        uri: str, 
        depth: int = 6, 
        parent_height: int = 80
    ) -> Optional[Any]:
        """
        Get thread data for a specific post URI.
        
        Args:
            uri: Post URI to fetch thread for
            depth: How deep to go in replies (default 6)
            parent_height: How far up parent chain (default 80)
            
        Returns:
            Thread response from atproto, or None if failed
        """
        self._ensure_authenticated()
        
        try:
            params = models.AppBskyFeedGetPostThread.Params(
                uri=uri,
                depth=depth,
                parent_height=parent_height
            )
            
            response = await self.client.app.bsky.feed.get_post_thread(params)
            logger.info(f"Successfully fetched thread for URI: {uri}")
            return response
            
        except AtProtocolError as e:
            logger.error(f"Failed to fetch thread for {uri}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching thread for {uri}: {e}")
            return None
    
    async def get_threads_for_posts(
        self, 
        posts: List[BlueskyPost], 
        depth: int = 6, 
        parent_height: int = 80
    ) -> List[BlueskyPost]:
        """
        Get complete threads for a list of posts.
        
        Args:
            posts: List of posts to fetch threads for
            depth: Thread depth to fetch
            parent_height: Parent chain height to fetch
            
        Returns:
            List of all posts from all threads (deduplicated)
        """
        from src.bluesky.thread_collector import ThreadCollector
        
        self._ensure_authenticated()
        
        try:
            collector = ThreadCollector(self.client)
            thread_posts = await collector.collect_threads_from_search(
                posts, depth, parent_height
            )
            
            logger.info(f"Collected {len(thread_posts)} posts from {len(posts)} initial posts")
            return thread_posts
            
        except Exception as e:
            logger.exception(f"Error collecting threads: {e}")
            return posts  # Return original posts if thread collection fails
