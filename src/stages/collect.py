"""Collection stage - collects posts from Bluesky and stores as individual markdown files."""

from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional
import logging

from src.bluesky.client import BlueskyClient
from src.bluesky.url_utils import clean_bluesky_urls_from_links, extract_post_uri_from_url
from src.config.searches import SearchDefinition, SearchConfig
from src.config.settings import Settings
from src.models.post import BlueskyPost
from src.stages.base import InputStage
from src.stages.markdown import MarkdownFile, generate_file_id
from src.utils.url_expansion import URLExpander

logger = logging.getLogger(__name__)


class CollectStage(InputStage):
    """Collects posts from Bluesky and stores as individual markdown files."""
    
    def __init__(self, settings: Settings, search_definition: Optional[SearchDefinition] = None, 
                 max_posts: int = 100, expand_urls: bool = True, collect_threads: bool = False,
                 max_thread_depth: int = 6, max_parent_height: int = 80, base_path: Path = Path("stages"),
                 export_parquet: bool = True, expand_references: bool = True, max_reference_depth: int = 2):
        super().__init__("collect", base_path)
        self.settings = settings
        self.search_definition = search_definition or SearchConfig.get_default_config().searches["mcp_mentions"]
        self.max_posts = max_posts
        self.expand_urls = expand_urls
        self.collect_threads = collect_threads
        self.max_thread_depth = max_thread_depth
        self.max_parent_height = max_parent_height
        self.export_parquet = export_parquet
        self.expand_references = expand_references
        self.max_reference_depth = max_reference_depth
        self.processed_post_uris = set()  # Track processed posts to avoid duplication
        self.bluesky_client = BlueskyClient(settings)
    
    async def collect_posts(self, target_date: date) -> list[BlueskyPost]:
        """Collect posts from Bluesky matching search criteria."""
        collection_mode = "threads" if self.collect_threads else "posts"
        logger.info(f"Collecting {collection_mode} using '{self.search_definition.name}' search")
        
        if not self.settings.has_bluesky_credentials:
            logger.error("Bluesky credentials not configured")
            return []
        
        try:
            async with self.bluesky_client as client:
                # First, get initial search results
                search_posts = await client.get_posts_by_definition(
                    search_definition=self.search_definition,
                    max_posts=self.max_posts
                )
                
                if not search_posts:
                    logger.info("No posts found from search")
                    return []
                
                # If thread collection is enabled, fetch complete threads
                if self.collect_threads:
                    logger.info(f"Fetching complete threads for {len(search_posts)} search results")
                    posts = await client.get_threads_for_posts(
                        search_posts, 
                        depth=self.max_thread_depth,
                        parent_height=self.max_parent_height
                    )
                else:
                    posts = search_posts
                
                # Expand shortened URLs if enabled
                if self.expand_urls and posts:
                    posts = await self._expand_post_urls(posts)
                
                # Expand Bluesky post references if enabled
                if self.expand_references and posts:
                    posts = await self._expand_post_references(posts, depth=0)
                
                logger.info(f"Collected {len(posts)} total posts ({len(search_posts)} from search)")
                return posts
                
        except Exception as e:
            logger.error(f"Failed to collect posts: {e}")
            return []
    
    async def _expand_post_urls(self, posts: list[BlueskyPost]) -> list[BlueskyPost]:
        """Expand shortened URLs in collected posts."""
        logger.info("Expanding shortened URLs in collected posts...")
        
        async with URLExpander() as expander:
            expanded_posts = []
            
            for post in posts:
                if not post.links:
                    expanded_posts.append(post)
                    continue
                
                # Convert HttpUrl objects to strings for expansion
                original_urls = [str(link) for link in post.links]
                
                # Expand URLs
                expanded_urls = await expander.expand_urls(original_urls)
                
                # Check if any URLs were actually expanded
                if expanded_urls != original_urls:
                    # Create a new post with expanded URLs
                    from pydantic import HttpUrl
                    expanded_links = [HttpUrl(url) for url in expanded_urls]
                    
                    # Create new post dict and update links
                    post_dict = post.model_dump()
                    post_dict['links'] = expanded_links
                    
                    # Create new post instance
                    expanded_post = BlueskyPost(**post_dict)
                    expanded_posts.append(expanded_post)
                    
                    # Log expansions
                    for orig, expanded in zip(original_urls, expanded_urls):
                        if orig != expanded:
                            logger.info(f"Expanded URL: {orig} -> {expanded}")
                else:
                    expanded_posts.append(post)
            
        logger.info(f"URL expansion completed for {len(posts)} posts")
        return expanded_posts
    
    async def _expand_post_references(self, posts: list[BlueskyPost], depth: int) -> list[BlueskyPost]:
        """
        Expand Bluesky post references by fetching referenced posts.
        
        Args:
            posts: List of posts to process
            depth: Current recursion depth
            
        Returns:
            Expanded list of posts including referenced posts
        """
        if depth >= self.max_reference_depth:
            logger.debug(f"Reached maximum reference depth {self.max_reference_depth}")
            return posts
        
        logger.info(f"Expanding Bluesky post references (depth {depth})...")
        
        all_posts = []
        new_posts = []
        
        for post in posts:
            # Skip if we've already processed this post
            if post.id in self.processed_post_uris:
                logger.debug(f"Skipping duplicate post: {post.id}")
                continue
            
            # Mark this post as processed
            self.processed_post_uris.add(post.id)
            
            # Separate Bluesky URLs from other URLs
            original_links = [str(link) for link in post.links]
            non_bluesky_urls, bluesky_urls = clean_bluesky_urls_from_links(original_links)
            
            # Update post to only have non-Bluesky URLs
            if bluesky_urls:
                from pydantic import HttpUrl
                filtered_links = [HttpUrl(url) for url in non_bluesky_urls]
                
                # Create new post with filtered links
                post_dict = post.model_dump()
                post_dict['links'] = filtered_links
                post = BlueskyPost(**post_dict)
                
                logger.info(f"Removed {len(bluesky_urls)} Bluesky reference(s) from post {post.id}")
            
            all_posts.append(post)
            
            # Fetch referenced posts
            for bluesky_url in bluesky_urls:
                try:
                    referenced_post = await self._fetch_referenced_post(bluesky_url)
                    if referenced_post and referenced_post.id not in self.processed_post_uris:
                        new_posts.append(referenced_post)
                        logger.info(f"Fetched referenced post: {referenced_post.id}")
                except Exception as e:
                    logger.warning(f"Failed to fetch referenced post from {bluesky_url}: {e}")
        
        # Recursively expand references in new posts
        if new_posts:
            logger.info(f"Found {len(new_posts)} new referenced posts, expanding recursively")
            expanded_new = await self._expand_post_references(new_posts, depth + 1)
            all_posts.extend(expanded_new)
        
        logger.info(f"Reference expansion completed: {len(all_posts)} total posts")
        return all_posts
    
    async def _fetch_referenced_post(self, bluesky_url: str) -> Optional[BlueskyPost]:
        """
        Fetch a single referenced Bluesky post.
        
        Args:
            bluesky_url: Bluesky post URL
            
        Returns:
            BlueskyPost instance or None if fetch failed
        """
        try:
            post_uri = extract_post_uri_from_url(bluesky_url)
            if not post_uri:
                logger.warning(f"Failed to extract URI from Bluesky URL: {bluesky_url}")
                return None
            
            # Use the Bluesky client to fetch the post
            post_data = await self.bluesky_client.get_post_by_uri(post_uri)
            if not post_data:
                logger.debug(f"No post found for URI: {post_uri}")
                return None
            
            # Convert to our post model
            referenced_post = self.bluesky_client._convert_post_to_model(post_data)
            logger.debug(f"Successfully fetched referenced post: {referenced_post.id}")
            return referenced_post
            
        except Exception as e:
            logger.warning(f"Failed to fetch referenced post {bluesky_url}: {e}")
            return None
    
    def post_to_markdown(self, post: BlueskyPost, target_date: date) -> MarkdownFile:
        """Convert a BlueskyPost to a MarkdownFile."""
        # Extract post ID from AT protocol URI
        post_id = post.id
        if post_id.startswith("at://"):
            short_id = post_id.split("/")[-1]
        else:
            short_id = post_id
        
        # Create frontmatter
        frontmatter = {
            "id": post.id,
            "author": post.author,
            "created_at": post.created_at.isoformat(),
            "language": post.language.value,
            "engagement": {
                "likes": post.engagement_metrics.likes,
                "reposts": post.engagement_metrics.reposts,
                "replies": post.engagement_metrics.replies
            },
            "links": [str(link) for link in post.links],
            "tags": post.tags,
            "stage": "collected",
            "collected_at": datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add thread metadata if available
        if post.thread_root_uri is not None:
            frontmatter["thread"] = {
                "root_uri": post.thread_root_uri,
                "position": post.thread_position,
                "depth": post.thread_depth,
                "parent_uri": post.parent_post_uri
            }
        
        # Create content
        content = f"# Post Content\n\n{post.content}"
        
        return MarkdownFile(frontmatter, content)
    
    def get_post_filename(self, post: BlueskyPost) -> str:
        """Generate filename for a post."""
        # Extract short ID from AT protocol URI
        post_id = post.id
        if post_id.startswith("at://"):
            short_id = post_id.split("/")[-1]
        else:
            short_id = post_id
        
        return f"post_{short_id}.md"
    
    def get_inputs(self, target_date: date) -> Iterator[Path]:
        """
        Collection stage generates its own inputs by fetching from Bluesky.
        This method returns an empty iterator since we don't read files.
        """
        return iter([])
    
    def process_item(self, input_path: Path, target_date: date) -> Optional[Path]:
        """
        Not used for collection stage since we don't process files.
        Use run_collection() instead.
        """
        return None
    
    async def run_collection(self, target_date: Optional[date] = None) -> dict:
        """
        Run the collection stage. Posts are organized by their publication date.
        
        Returns:
            Summary of collection results including new vs updated stats
        """
        logger.info(f"Running collect stage")
        
        # Collect posts from Bluesky
        posts = await self.collect_posts(target_date or date.today())
        
        processed = 0
        failed = 0
        new_posts = 0
        updated_posts = 0
        
        # Group posts by their publication date
        from collections import defaultdict
        posts_by_date = defaultdict(list)
        
        for post in posts:
            post_date = post.created_at.date()
            posts_by_date[post_date].append(post)
        
        # Process posts organized by publication date
        for post_date, date_posts in posts_by_date.items():
            # Ensure output directory exists for this publication date
            stage_dir = self.ensure_stage_dir(post_date)
            
            for post in date_posts:
                try:
                    # Convert to markdown
                    md_file = self.post_to_markdown(post, post_date)
                    
                    # Generate filename and save
                    filename = self.get_post_filename(post)
                    output_path = stage_dir / filename
                    
                    # Check if post already exists
                    if output_path.exists():
                        # Read existing post to check for updates
                        existing_md = MarkdownFile.load(output_path)
                        existing_engagement = existing_md.frontmatter.get("engagement", {})
                        new_engagement = md_file.frontmatter.get("engagement", {})
                        
                        # Check if engagement metrics have changed
                        if (existing_engagement.get("likes") != new_engagement.get("likes") or
                            existing_engagement.get("reposts") != new_engagement.get("reposts") or
                            existing_engagement.get("replies") != new_engagement.get("replies")):
                            
                            # Update the post with new metrics
                            md_file.frontmatter["updated_at"] = datetime.utcnow().isoformat() + 'Z'
                            md_file.save(output_path)
                            updated_posts += 1
                            logger.debug(f"Updated post metrics: {filename}")
                        else:
                            logger.debug(f"Post unchanged: {filename}")
                    else:
                        # New post
                        md_file.save(output_path)
                        new_posts += 1
                        logger.debug(f"Saved new post to {output_path}")
                    
                    processed += 1
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to save post {post.id}: {e}")
        
        result = {
            "stage": self.stage_name,
            "run_date": date.today(),
            "processed": processed,
            "failed": failed,
            "total": len(posts),
            "new_posts": new_posts,
            "updated_posts": updated_posts,
            "posts_by_date": {str(d): len(p) for d, p in posts_by_date.items()}
        }
        
        logger.info(f"Collection completed: {result}")
        
        # Export to Parquet if enabled
        if self.export_parquet and processed > 0:
            from src.analytics.parquet_export import export_stage_to_parquet
            from src.models.post import BlueskyPost
            
            # Export all collected data as a single parquet file with 7 days of history
            run_date = date.today()
            await export_stage_to_parquet("collect", BlueskyPost, run_date, self.export_parquet, days_back=7, settings=self.settings)
        
        return result