from datetime import date, datetime

from src.bluesky.client import BlueskyClient
from src.config.searches import SearchDefinition
from src.config.settings import Settings
from src.models.post import BlueskyPost
from src.storage.file_manager import FileManager
from src.storage.r2_client import R2Client
from src.utils.logging import get_logger
from src.utils.url_registry import URLRegistry

logger = get_logger(__name__)


class BlueskyDataCollector:
    """Service for collecting Bluesky posts and storing them."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the data collector.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.bluesky_client = BlueskyClient(settings)
        self.r2_client = R2Client(settings)

    async def collect_posts_by_definition(
        self, search_definition: SearchDefinition, target_date: date | None = None, max_posts: int = 100
    ) -> list[BlueskyPost]:
        """
        Collect posts using a search definition.

        Args:
            search_definition: SearchDefinition to use for collection
            target_date: Date to collect posts for (defaults to today)
            max_posts: Maximum number of posts to collect

        Returns:
            List of collected BlueskyPost instances
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Starting collection for {target_date} using definition '{search_definition.name}'")

        if not self.settings.has_bluesky_credentials:
            logger.error("Bluesky credentials not configured")
            return []

        try:
            async with self.bluesky_client as client:
                posts = await client.get_posts_by_definition(
                    search_definition=search_definition, max_posts=max_posts
                )

                # Filter posts by date if needed
                # Note: For now we collect recent posts regardless of date
                # In future phases we might want to filter by creation date

                logger.info(f"Collected {len(posts)} posts using definition '{search_definition.name}'")
                return posts

        except Exception as e:
            logger.exception(f"Failed to collect posts: {e}")
            return []

    async def collect_daily_posts(
        self, target_date: date | None = None, max_posts: int = 100
    ) -> list[BlueskyPost]:
        """
        Collect MCP-related posts for a specific date.
        
        Note: This method is deprecated. Use collect_posts_by_definition instead.

        Args:
            target_date: Date to collect posts for (defaults to today)
            max_posts: Maximum number of posts to collect

        Returns:
            List of collected BlueskyPost instances
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Starting collection for {target_date}")

        if not self.settings.has_bluesky_credentials:
            logger.error("Bluesky credentials not configured")
            return []

        try:
            async with self.bluesky_client as client:
                posts = await client.get_recent_mcp_posts(max_posts=max_posts)

                # Filter posts by date if needed
                # Note: For now we collect recent posts regardless of date
                # In future phases we might want to filter by creation date

                logger.info(f"Collected {len(posts)} posts")
                return posts

        except Exception as e:
            logger.exception(f"Failed to collect posts: {e}")
            return []

    async def store_posts(self, posts: list[BlueskyPost], target_date: date) -> bool:
        """
        Store collected posts to R2 storage.

        Args:
            posts: List of posts to store
            target_date: Date for organizing storage

        Returns:
            True if successful, False otherwise
        """
        if not posts:
            logger.warning("No posts to store")
            return True

        try:
            # Convert posts to JSON for storage
            posts_data = [post.model_dump() for post in posts]

            # Generate file path
            file_path = FileManager.get_posts_path(target_date)

            # For now, store as JSON (Phase 4 will convert to Parquet)
            json_path = file_path.replace(".parquet", ".json")

            # Store in R2
            import json

            json_data = json.dumps(posts_data, indent=2, default=str)
            success = self.r2_client.upload_bytes(
                json_data.encode("utf-8"), json_path, content_type="application/json"
            )

            if success:
                logger.info(f"Successfully stored {len(posts)} posts to {json_path}")
                return True
            logger.error(f"Failed to store posts to {json_path}")
            return False

        except Exception as e:
            logger.exception(f"Error storing posts: {e}")
            return False

    async def collect_and_store_by_definition(
        self, search_definition: SearchDefinition, target_date: date | None = None, 
        max_posts: int = 100, track_urls: bool = False
    ) -> tuple[int, bool]:
        """
        Collect and store posts using a search definition.

        Args:
            search_definition: SearchDefinition to use for collection
            target_date: Date to collect posts for
            max_posts: Maximum number of posts to collect
            track_urls: Whether to track URLs in registry

        Returns:
            Tuple of (number_of_posts_collected, storage_success)
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Starting collect and store operation for {target_date} using definition '{search_definition.name}'")

        # Collect posts
        posts = await self.collect_posts_by_definition(search_definition, target_date, max_posts)

        if not posts:
            logger.warning("No posts collected")
            return 0, True  # No posts to store is considered success

        # Track URLs if enabled
        if track_urls:
            await self._track_urls_from_posts(posts)

        # Store posts
        storage_success = await self.store_posts(posts, target_date)

        logger.info(
            f"Collection complete: {len(posts)} posts, "
            f"storage {'successful' if storage_success else 'failed'}"
        )

        return len(posts), storage_success
    
    async def _track_urls_from_posts(self, posts: list[BlueskyPost]) -> None:
        """
        Extract and track URLs from posts in the registry.
        
        Args:
            posts: List of posts to extract URLs from
        """
        try:
            # Download existing registry or create new one
            registry = self.r2_client.download_url_registry()
            if registry is None:
                registry = URLRegistry()
                logger.info("Created new URL registry")
            
            # Track URLs from each post
            new_urls = 0
            total_urls = 0
            
            for post in posts:
                for url in post.links:
                    total_urls += 1
                    is_new = registry.add_url(url, post.id, post.author)
                    if is_new:
                        new_urls += 1
            
            logger.info(f"Tracked {total_urls} URLs, {new_urls} new")
            
            # Upload updated registry
            if total_urls > 0:
                success = self.r2_client.upload_url_registry(registry)
                if not success:
                    logger.error("Failed to upload updated URL registry")
                    
        except Exception as e:
            logger.exception(f"Error tracking URLs: {e}")

    async def collect_and_store(
        self, target_date: date | None = None, max_posts: int = 100
    ) -> tuple[int, bool]:
        """
        Collect and store posts in one operation.
        
        Note: This method is deprecated. Use collect_and_store_by_definition instead.

        Args:
            target_date: Date to collect posts for
            max_posts: Maximum number of posts to collect

        Returns:
            Tuple of (number_of_posts_collected, storage_success)
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Starting collect and store operation for {target_date}")

        # Collect posts
        posts = await self.collect_daily_posts(target_date, max_posts)

        if not posts:
            logger.warning("No posts collected")
            return 0, True  # No posts to store is considered success

        # Store posts
        storage_success = await self.store_posts(posts, target_date)

        logger.info(
            f"Collection complete: {len(posts)} posts, "
            f"storage {'successful' if storage_success else 'failed'}"
        )

        return len(posts), storage_success

    async def get_stored_posts(self, target_date: date) -> list[BlueskyPost]:
        """
        Retrieve previously stored posts for a date.

        Args:
            target_date: Date to retrieve posts for

        Returns:
            List of BlueskyPost instances
        """
        try:
            # Generate file path (JSON for now)
            file_path = FileManager.get_posts_path(target_date)
            json_path = file_path.replace(".parquet", ".json")

            # Download from R2
            data = self.r2_client.download_bytes(json_path)
            if not data:
                logger.warning(f"No stored posts found for {target_date}")
                return []

            # Parse JSON and convert back to models
            import json

            posts_data = json.loads(data.decode("utf-8"))

            posts = []
            for post_data in posts_data:
                try:
                    # Handle datetime conversion
                    if isinstance(post_data.get("created_at"), str):
                        post_data["created_at"] = datetime.fromisoformat(
                            post_data["created_at"].replace("Z", "+00:00")
                        )

                    post = BlueskyPost.model_validate(post_data)
                    posts.append(post)
                except Exception as e:
                    logger.warning(f"Failed to parse stored post: {e}")
                    continue

            logger.info(f"Retrieved {len(posts)} stored posts for {target_date}")
            return posts

        except Exception as e:
            logger.exception(f"Error retrieving stored posts: {e}")
            return []

    def check_stored_data(self, target_date: date) -> bool:
        """
        Check if data exists for a specific date.

        Args:
            target_date: Date to check

        Returns:
            True if data exists, False otherwise
        """
        file_path = FileManager.get_posts_path(target_date)
        json_path = file_path.replace(".parquet", ".json")

        return self.r2_client.file_exists(json_path)

    def get_stored_posts_sync(self, target_date: date) -> list[BlueskyPost]:
        """
        Synchronous version of get_stored_posts for use in notebooks/synchronous contexts.
        
        Args:
            target_date: Date to retrieve posts for

        Returns:
            List of BlueskyPost instances
        """
        import asyncio
        
        try:
            # Check if we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, use nest_asyncio if available
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    return asyncio.run(self.get_stored_posts(target_date))
                except ImportError:
                    # nest_asyncio not available, use event loop directly
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.get_stored_posts(target_date))
                        return future.result()
            except RuntimeError:
                # No event loop running, we can use asyncio.run directly
                return asyncio.run(self.get_stored_posts(target_date))
        except Exception as e:
            logger.exception(f"Error in sync get_stored_posts: {e}")
            return []
