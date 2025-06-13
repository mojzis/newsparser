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
                "published_date": extracted.published_date.isoformat() if extracted.published_date else None,
                "stage": "fetched"
            }
            
            # Use extracted markdown content
            content = f"# {extracted.title or 'Article'}\n\n{extracted.content}"
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
        """Process a single post file and extract URLs."""
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
    
    async def run_fetch(self, target_date: Optional[date] = None) -> dict:
        """
        Run the fetch stage for the specified date.
        
        Returns:
            Summary of fetch results
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Running fetch stage for {target_date}")
        
        # Ensure output directory exists
        self.ensure_stage_dir(target_date)
        
        # Process all posts from collect stage
        processed = 0
        skipped = 0
        failed = 0
        total_urls = 0
        
        async with self:  # Use async context manager
            for input_path in self.get_inputs(target_date):
                try:
                    # Load post to count URLs
                    md_file = MarkdownFile.load(input_path)
                    links = md_file.get_frontmatter_value("links", [])
                    total_urls += len(links)
                    
                    if not links:
                        skipped += 1
                        continue
                    
                    result = await self.process_item(input_path, target_date)
                    if result:
                        processed += 1
                    else:
                        skipped += 1
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to process {input_path}: {e}")
        
        result = {
            "stage": self.stage_name,
            "date": target_date,
            "processed_posts": processed,
            "skipped_posts": skipped,
            "failed_posts": failed,
            "total_posts": processed + skipped + failed,
            "total_urls": total_urls
        }
        
        logger.info(f"Fetch stage completed: {result}")
        return result