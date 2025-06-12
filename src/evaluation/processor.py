"""Article evaluation processor with URL registry integration."""

from datetime import date, datetime
from typing import Optional
import tempfile
from pathlib import Path

import pandas as pd

from src.config.settings import Settings
from src.content.extractor import ContentExtractor
from src.content.fetcher import ArticleFetcher
from src.content.models import ContentError
from src.evaluation.anthropic_client import AnthropicEvaluator
from src.models.evaluation import ArticleEvaluation
from src.storage.file_manager import FileManager
from src.storage.r2_client import R2Client
from src.utils.logging import get_logger
from src.utils.url_registry import URLRegistry

logger = get_logger(__name__)


class EvaluationProcessor:
    """Processes articles for evaluation, managing URL registry and storage."""
    
    def __init__(self, settings: Settings):
        """Initialize processor with settings."""
        self.settings = settings
        self.r2_client = R2Client(settings)
        self.fetcher = ArticleFetcher()
        self.extractor = ContentExtractor()
        self.evaluator = AnthropicEvaluator(settings)
        
    async def evaluate_posts(
        self, 
        posts: list, 
        target_date: Optional[date] = None,
        force: bool = False
    ) -> tuple[int, int]:
        """
        Evaluate articles from posts, skipping already processed URLs.
        
        Args:
            posts: List of BlueskyPost objects with URLs
            target_date: Date for organizing storage (defaults to today)
            force: Force re-evaluation of already processed URLs
            
        Returns:
            Tuple of (new_evaluations, total_urls)
        """
        if target_date is None:
            target_date = date.today()
            
        # Download URL registry
        registry = self.r2_client.download_url_registry()
        if registry is None:
            registry = URLRegistry()
            logger.info("No URL registry found, creating new one")
        
        # Extract unique URLs from posts
        urls_to_process = []
        for post in posts:
            for url in post.links:
                url_str = str(url)
                
                # Skip if already evaluated (unless forced)
                if not force and registry.is_evaluated(url_str):
                    logger.debug(f"Skipping already evaluated URL: {url_str}")
                    continue
                    
                urls_to_process.append((url_str, post.id, post.author))
        
        if not urls_to_process:
            logger.info("No new URLs to process")
            return 0, len(registry.df)
        
        logger.info(f"Processing {len(urls_to_process)} new URLs")
        
        # Process each URL
        evaluations = []
        
        async with self.fetcher:
            for url, post_id, author in urls_to_process:
                try:
                    # Fetch article
                    logger.info(f"Fetching article: {url}")
                    fetch_result = await self.fetcher.fetch_article(url)
                    
                    if isinstance(fetch_result, ContentError):
                        logger.warning(f"Failed to fetch {url}: {fetch_result.error_message}")
                        # Still track in registry as attempted
                        registry.add_url(url, post_id, author)
                        continue
                    
                    # Extract content
                    extract_result = self.extractor.extract_content(fetch_result)
                    
                    if isinstance(extract_result, ContentError):
                        logger.warning(f"Failed to extract {url}: {extract_result.error_message}")
                        # Still track in registry as attempted
                        registry.add_url(url, post_id, author)
                        continue
                    
                    # Evaluate with Anthropic
                    logger.info(f"Evaluating article: {url}")
                    evaluation = self.evaluator.evaluate_article(extract_result, url)
                    evaluations.append(evaluation)
                    
                    # Add to registry and mark as evaluated
                    registry.add_url(url, post_id, author)
                    registry.mark_evaluated(
                        url,
                        evaluation.is_mcp_related,
                        evaluation.relevance_score
                    )
                    
                except Exception as e:
                    logger.exception(f"Error processing {url}: {e}")
                    # Still track in registry as attempted
                    registry.add_url(url, post_id, author)
        
        # Store evaluations if any
        if evaluations:
            success = await self._store_evaluations(evaluations, target_date)
            if not success:
                logger.error("Failed to store evaluations")
        
        # Upload updated registry
        if self.r2_client.upload_url_registry(registry):
            logger.info("Updated URL registry uploaded")
        else:
            logger.error("Failed to upload URL registry")
        
        return len(evaluations), len(registry.df)
    
    async def _store_evaluations(
        self, 
        evaluations: list[ArticleEvaluation], 
        target_date: date
    ) -> bool:
        """Store evaluations to R2."""
        try:
            # Convert evaluations to DataFrame
            eval_dicts = [eval.model_dump() for eval in evaluations]
            df = pd.DataFrame(eval_dicts)
            
            # Convert datetime columns
            datetime_cols = ['published_date', 'evaluated_at']
            for col in datetime_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Save to temporary parquet file
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
                df.to_parquet(tmp.name, index=False)
                tmp_path = Path(tmp.name)
                
                # Upload to R2
                file_path = FileManager.get_evaluations_path(target_date)
                success = self.r2_client.upload_file(
                    tmp_path,
                    file_path,
                    content_type="application/octet-stream"
                )
                
                # Clean up
                tmp_path.unlink()
                
                if success:
                    logger.info(f"Stored {len(evaluations)} evaluations to {file_path}")
                
                return success
                
        except Exception as e:
            logger.exception(f"Failed to store evaluations: {e}")
            return False
    
    def get_stored_evaluations(self, target_date: date) -> list[ArticleEvaluation]:
        """Retrieve stored evaluations for a date."""
        try:
            file_path = FileManager.get_evaluations_path(target_date)
            
            # Download to temp file
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
                if not self.r2_client.download_file(file_path, tmp.name):
                    logger.warning(f"No evaluations found for {target_date}")
                    return []
                
                # Read parquet
                df = pd.read_parquet(tmp.name)
                
                # Clean up
                Path(tmp.name).unlink()
                
                # Convert back to models
                evaluations = []
                for _, row in df.iterrows():
                    try:
                        eval_dict = row.to_dict()
                        
                        # Convert timestamps
                        for field in ['published_date', 'evaluated_at']:
                            if field in eval_dict and pd.notna(eval_dict[field]):
                                eval_dict[field] = eval_dict[field].to_pydatetime()
                        
                        evaluation = ArticleEvaluation.model_validate(eval_dict)
                        evaluations.append(evaluation)
                    except Exception as e:
                        logger.warning(f"Failed to parse evaluation: {e}")
                
                logger.info(f"Retrieved {len(evaluations)} evaluations for {target_date}")
                return evaluations
                
        except Exception as e:
            logger.exception(f"Failed to retrieve evaluations: {e}")
            return []