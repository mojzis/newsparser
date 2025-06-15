"""Fetch stage - fetches full content from URLs found in posts."""

from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional
import logging
import hashlib

from src.content.fetcher import ArticleFetcher
from src.content.extractor import ContentExtractor
from src.content.models import ArticleContent, ContentError
from src.stages.base import ProcessingStage
from src.stages.markdown import MarkdownFile, generate_file_id

logger = logging.getLogger(__name__)


class FetchStage(ProcessingStage):
    """Fetches full content from URLs found in posts."""
    
    def __init__(self, base_path: Path = Path("stages")):
        super().__init__("fetch", "collect", base_path)
        self.fetcher = ArticleFetcher()
        self.extractor = ContentExtractor()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.fetcher.close()
    
    def get_url_hash(self, url: str) -> str:
        """Generate a hash-based ID for a URL."""
        return generate_file_id(url, length=8)
    
    def get_url_filename(self, url: str) -> str:
        """Generate filename for a URL."""
        url_hash = self.get_url_hash(url)
        return f"url_{url_hash}.md"
    
    def get_output_path_for_url(self, target_date: date, url: str) -> Path:
        """Generate output path for a specific URL."""
        stage_dir = self.ensure_stage_dir(target_date)
        filename = self.get_url_filename(url)
        return stage_dir / filename
    
    async def fetch_and_extract_content(self, url: str) -> tuple[dict, str]:
        """
        Fetch and extract content from a URL.
        
        Returns:
            Tuple of (frontmatter_dict, content_string)
        """
        # Fetch content
        result = await self.fetcher.fetch_article(url)
        
        if isinstance(result, ContentError):
            # Handle fetch error
            frontmatter = {
                "url": url,
                "fetched_at": datetime.utcnow().isoformat() + 'Z',
                "fetch_status": "error",
                "error_type": result.error_type,
                "error_message": result.error_message,
                "stage": "fetched"
            }
            content = f"# Fetch Error\n\nFailed to fetch content: {result.error_message}"
            return frontmatter, content
        
        # Extract content
        try:
            extracted = self.extractor.extract_content(result)
            
            if isinstance(extracted, ContentError):
                # Handle extraction error
                frontmatter = {
                    "url": url,
                    "fetched_at": datetime.utcnow().isoformat() + 'Z',
                    "fetch_status": "error",
                    "error_type": extracted.error_type,
                    "error_message": extracted.error_message,
                    "stage": "fetched"
                }
                content = f"# Extraction Error\n\nFailed to extract content: {extracted.error_message}"
                return frontmatter, content
            
            # Success - create comprehensive frontmatter
            frontmatter = {
                "url": url,
                "fetched_at": datetime.utcnow().isoformat() + 'Z',
                "fetch_status": "success",
                "word_count": extracted.word_count,
                "title": extracted.title or "Untitled",
                "author": extracted.author,
                "domain": extracted.domain,
                "medium": extracted.medium,
                "language": extracted.language,
                "extraction_timestamp": extracted.extraction_timestamp.isoformat() + 'Z',
                "stage": "fetched"
            }
            
            # Use extracted markdown content
            content = f"# {extracted.title or 'Article'}\n\n{extracted.content_markdown}"
            return frontmatter, content
            
        except Exception as e:
            logger.error(f"Unexpected error extracting content from {url}: {e}")
            frontmatter = {
                "url": url,
                "fetched_at": datetime.utcnow().isoformat() + 'Z',
                "fetch_status": "error",
                "error_type": "extraction",
                "error_message": str(e),
                "stage": "fetched"
            }
            content = f"# Extraction Error\n\nUnexpected error: {str(e)}"
            return frontmatter, content
    
    async def process_item(self, input_path: Path, target_date: date) -> Optional[Path]:
        """Process a single post file and extract URLs.
        
        NOTE: This method is kept for backward compatibility but is not used
        in the new multi-day scanning approach.
        """
        try:
            # Load the post markdown file
            md_file = MarkdownFile.load(input_path)
            
            # Get URLs from frontmatter
            links = md_file.get_frontmatter_value("links", [])
            
            if not links:
                logger.debug(f"No links found in {input_path.name}")
                return None
            
            processed_urls = []
            
            # Process each URL
            for url in links:
                try:
                    # Check if we already processed this URL
                    output_path = self.get_output_path_for_url(target_date, url)
                    
                    if output_path.exists():
                        logger.debug(f"URL already fetched: {url}")
                        processed_urls.append(str(output_path))
                        continue
                    
                    # Fetch and extract content
                    frontmatter, content = await self.fetch_and_extract_content(url)
                    
                    # Add reference to the source post
                    frontmatter["found_in_posts"] = [md_file.get_frontmatter_value("id")]
                    
                    # Create and save markdown file
                    url_md = MarkdownFile(frontmatter, content)
                    url_md.save(output_path)
                    
                    processed_urls.append(str(output_path))
                    logger.info(f"Fetched and saved: {url} -> {output_path.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to process URL {url}: {e}")
            
            if processed_urls:
                return Path(processed_urls[0])  # Return first processed URL path
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to process {input_path}: {e}")
            return None
    
    async def run_fetch(self, days_back: int = 7) -> dict:
        """
        Run the fetch stage, scanning posts from the last N days for unfetched URLs.
        
        Args:
            days_back: Number of days to look back for posts (default: 7)
        
        Returns:
            Summary of fetch results
        """
        from datetime import timedelta
        
        logger.info(f"Running fetch stage, scanning posts from last {days_back} days")
        
        # Track all URLs we've already fetched across all dates
        fetched_urls = set()
        
        # First, scan all existing fetch stage files to know what we've already fetched
        fetch_base = self.base_path / self.stage_name
        if fetch_base.exists():
            for date_dir in fetch_base.iterdir():
                if date_dir.is_dir():
                    for md_file_path in date_dir.glob("*.md"):
                        try:
                            md = MarkdownFile.load(md_file_path)
                            url = md.get_frontmatter_value("url")
                            if url:
                                fetched_urls.add(url)
                        except Exception as e:
                            logger.debug(f"Error reading {md_file_path}: {e}")
        
        logger.info(f"Found {len(fetched_urls)} already fetched URLs")
        
        # Now scan posts from the last N days
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        processed_posts = 0
        skipped_posts = 0
        failed_posts = 0
        new_urls_fetched = 0
        total_urls_found = 0
        urls_by_date = {}
        
        async with self:  # Use async context manager
            # Scan each day in the range
            current_date = start_date
            while current_date <= end_date:
                # Check if collect stage has data for this date
                collect_dir = self.base_path / self.input_stage_name / current_date.strftime("%Y-%m-%d")
                
                if collect_dir.exists():
                    logger.info(f"Scanning posts from {current_date}")
                    
                    for input_path in collect_dir.glob("*.md"):
                        try:
                            # Load post to get URLs
                            md_file = MarkdownFile.load(input_path)
                            links = md_file.get_frontmatter_value("links", [])
                            post_id = md_file.get_frontmatter_value("id")
                            
                            if not links:
                                skipped_posts += 1
                                continue
                            
                            total_urls_found += len(links)
                            
                            # Process each URL
                            for url in links:
                                if url in fetched_urls:
                                    logger.debug(f"URL already fetched: {url}")
                                    continue
                                
                                try:
                                    # Determine which date directory to save in
                                    # Use the post's publication date
                                    post_created = md_file.get_frontmatter_value("created_at")
                                    if post_created:
                                        post_date = datetime.fromisoformat(post_created.replace('Z', '+00:00')).date()
                                    else:
                                        post_date = current_date
                                    
                                    # Ensure output directory exists
                                    self.ensure_stage_dir(post_date)
                                    
                                    # Get output path
                                    output_path = self.get_output_path_for_url(post_date, url)
                                    
                                    # Fetch and extract content
                                    frontmatter, content = await self.fetch_and_extract_content(url)
                                    
                                    # Track which posts this URL was found in
                                    if "found_in_posts" not in frontmatter:
                                        frontmatter["found_in_posts"] = []
                                    frontmatter["found_in_posts"].append(post_id)
                                    
                                    # Create and save markdown file
                                    url_md = MarkdownFile(frontmatter, content)
                                    url_md.save(output_path)
                                    
                                    fetched_urls.add(url)
                                    new_urls_fetched += 1
                                    
                                    # Track URLs by date
                                    date_str = str(post_date)
                                    if date_str not in urls_by_date:
                                        urls_by_date[date_str] = 0
                                    urls_by_date[date_str] += 1
                                    
                                    logger.info(f"Fetched new URL: {url} -> {output_path.name}")
                                    
                                except Exception as e:
                                    logger.error(f"Failed to fetch URL {url}: {e}")
                            
                            processed_posts += 1
                            
                        except Exception as e:
                            failed_posts += 1
                            logger.error(f"Failed to process {input_path}: {e}")
                
                current_date += timedelta(days=1)
        
        result = {
            "stage": self.stage_name,
            "days_scanned": days_back,
            "date_range": f"{start_date} to {end_date}",
            "processed_posts": processed_posts,
            "skipped_posts": skipped_posts,
            "failed_posts": failed_posts,
            "total_posts": processed_posts + skipped_posts + failed_posts,
            "total_urls_found": total_urls_found,
            "new_urls_fetched": new_urls_fetched,
            "previously_fetched": len(fetched_urls) - new_urls_fetched,
            "urls_by_date": urls_by_date
        }
        
        logger.info(f"Fetch stage completed: {result}")
        return result