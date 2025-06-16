"""Evaluate stage - evaluates content relevance using Anthropic API."""

from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional
import logging

from src.config.settings import Settings
from src.evaluation.anthropic_client import AnthropicEvaluator
from src.content.models import ExtractedContent
from src.stages.base import ProcessingStage
from src.stages.markdown import MarkdownFile

logger = logging.getLogger(__name__)


class EvaluateStage(ProcessingStage):
    """Evaluates content relevance using Anthropic API."""
    
    def __init__(self, settings: Settings, base_path: Path = Path("stages")):
        super().__init__("evaluate", "fetch", base_path)
        self.settings = settings
        self.evaluator = AnthropicEvaluator(settings)
    
    def should_process_item(self, input_path: Path, target_date: date) -> bool:
        """Check if item should be processed - only successful fetches."""
        try:
            md_file = MarkdownFile.load(input_path)
            fetch_status = md_file.get_frontmatter_value("fetch_status")
            
            # Only process successfully fetched content
            if fetch_status != "success":
                return False
            
            # Check if already evaluated
            output_path = self.get_output_path(input_path, target_date)
            return not output_path.exists()
            
        except Exception as e:
            logger.error(f"Error checking if {input_path} should be processed: {e}")
            return False
    
    def markdown_to_extracted_content(self, md_file: MarkdownFile) -> ExtractedContent:
        """Convert markdown file to ExtractedContent for evaluation."""
        frontmatter = md_file.frontmatter
        
        # Extract content (remove the "# Title" header)
        content_lines = md_file.content.split('\n')
        if content_lines and content_lines[0].startswith('# '):
            content_markdown = '\n'.join(content_lines[1:]).strip()
        else:
            content_markdown = md_file.content.strip()
        
        # Create ExtractedContent object
        return ExtractedContent(
            url=frontmatter["url"],
            title=frontmatter.get("title", "Untitled"),
            author=frontmatter.get("author"),
            content_markdown=content_markdown,
            word_count=frontmatter.get("word_count", 0),
            domain=frontmatter.get("domain", ""),
            published_date=datetime.fromisoformat(frontmatter["published_date"].rstrip('Z')) if frontmatter.get("published_date") else None,
            extract_timestamp=datetime.utcnow()
        )
    
    async def process_item(self, input_path: Path, target_date: date) -> Optional[Path]:
        """Process a single fetched content file for evaluation.
        
        NOTE: This method is kept for backward compatibility but is not used
        in the new multi-day scanning approach.
        """
        try:
            # Load the fetched content
            md_file = MarkdownFile.load(input_path)
            
            # Check if fetch was successful
            if md_file.get_frontmatter_value("fetch_status") != "success":
                logger.debug(f"Skipping {input_path.name} - fetch was not successful")
                return None
            
            # Convert to ExtractedContent
            extracted_content = self.markdown_to_extracted_content(md_file)
            
            # Evaluate using Anthropic API
            logger.info(f"Evaluating content: {extracted_content.url}")
            evaluation = self.evaluator.evaluate_article(extracted_content, extracted_content.url)
            
            # Create minimal evaluation file with only essential data
            evaluation_data = {
                "is_mcp_related": evaluation.is_mcp_related,
                "relevance_score": evaluation.relevance_score,
                "summary": evaluation.summary,
                "perex": evaluation.perex,
                "key_topics": evaluation.key_topics,
                "content_type": evaluation.content_type,
                "language": evaluation.language,
                "evaluated_at": evaluation.evaluated_at.isoformat() + 'Z',
                "evaluator": "claude-3-haiku-20240307"  # Model used for evaluation
            }
            
            # Get essential reference data from original file
            url = md_file.get_frontmatter_value("url")
            found_in_posts = md_file.get_frontmatter_value("found_in_posts", [])
            
            # Create minimal evaluation-only file
            evaluation_frontmatter = {
                "url": url,
                "found_in_posts": found_in_posts,
                "evaluation": evaluation_data,
                "stage": "evaluated"
            }
            
            # Create minimal content (just reference to fetch stage)
            evaluation_content = f"""# Evaluation Results

This content was evaluated for MCP relevance.

**Relevance Score:** {evaluation.relevance_score}  
**MCP Related:** {'Yes' if evaluation.is_mcp_related else 'No'}  
**Content Type:** {evaluation.content_type}  
**Language:** {evaluation.language}

*Full content available in fetch stage.*
"""
            
            # Create new evaluation file
            from src.utils.markdown_file import MarkdownFile
            eval_md = MarkdownFile(evaluation_frontmatter, evaluation_content)
            
            # Save to output path
            output_path = self.get_output_path(input_path, target_date)
            eval_md.save(output_path)
            
            logger.info(f"Evaluated and saved: {output_path.name} (relevance: {evaluation.relevance_score})")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to evaluate {input_path}: {e}")
            return None
    
    async def run_evaluate(self, days_back: int = 7, regenerate: bool = False) -> dict:
        """
        Run the evaluate stage, scanning fetched content from the last N days for unevaluated items.
        
        Args:
            days_back: Number of days to look back for unevaluated content (default: 7)
            regenerate: Whether to re-evaluate existing evaluations (default: False)
        
        Returns:
            Summary of evaluation results
        """
        from datetime import timedelta
        
        logger.info(f"Running evaluate stage, scanning fetched content from last {days_back} days")
        
        # Track all content we've already evaluated across all dates (unless regenerating)
        evaluated_urls = set()
        
        if not regenerate:
            # Only track existing evaluations if not regenerating
            evaluate_base = self.base_path / self.stage_name
            if evaluate_base.exists():
                for date_dir in evaluate_base.iterdir():
                    if date_dir.is_dir():
                        for md_file_path in date_dir.glob("*.md"):
                            try:
                                md = MarkdownFile.load(md_file_path)
                                url = md.get_frontmatter_value("url")
                                if url:
                                    evaluated_urls.add(url)
                            except Exception as e:
                                logger.debug(f"Error reading {md_file_path}: {e}")
            
            logger.info(f"Found {len(evaluated_urls)} already evaluated URLs")
        else:
            logger.info("Regenerate mode: will re-evaluate all content")
        
        # Now scan fetched content from the last N days
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        processed = 0
        skipped = 0
        failed = 0
        new_evaluations = 0
        mcp_related = 0
        total_relevance_score = 0.0
        evaluations_by_date = {}
        
        # Scan each day in the range
        current_date = start_date
        while current_date <= end_date:
            # Check if fetch stage has data for this date
            fetch_dir = self.base_path / self.input_stage_name / current_date.strftime("%Y-%m-%d")
            
            if fetch_dir.exists():
                logger.info(f"Scanning fetched content from {current_date}")
                
                for input_path in fetch_dir.glob("*.md"):
                    try:
                        # Load fetched content
                        md_file = MarkdownFile.load(input_path)
                        url = md_file.get_frontmatter_value("url")
                        fetch_status = md_file.get_frontmatter_value("fetch_status")
                        
                        # Only process successfully fetched content
                        if fetch_status != "success":
                            skipped += 1
                            continue
                        
                        # Skip if already evaluated
                        if url in evaluated_urls:
                            logger.debug(f"Content already evaluated: {url}")
                            skipped += 1
                            continue
                        
                        try:
                            # Convert to ExtractedContent
                            extracted_content = self.markdown_to_extracted_content(md_file)
                            
                            # Evaluate using Anthropic API
                            logger.info(f"Evaluating content: {extracted_content.url}")
                            evaluation = self.evaluator.evaluate_article(extracted_content, extracted_content.url)
                            
                            # Add evaluation to frontmatter
                            evaluation_data = {
                                "is_mcp_related": evaluation.is_mcp_related,
                                "relevance_score": evaluation.relevance_score,
                                "summary": evaluation.summary,
                                "perex": evaluation.perex,
                                "key_topics": evaluation.key_topics,
                                "content_type": evaluation.content_type,
                                "language": evaluation.language,
                                "evaluated_at": evaluation.evaluated_at.isoformat() + 'Z',
                                "evaluator": "claude-3-haiku-20240307"  # Model used for evaluation
                            }
                            
                            # Update frontmatter with evaluation
                            md_file.update_frontmatter({
                                "evaluation": evaluation_data,
                                "stage": "evaluated"
                            })
                            
                            # Ensure output directory exists for this date
                            self.ensure_stage_dir(current_date)
                            
                            # Save to output path in the same date directory
                            output_path = self.base_path / self.stage_name / current_date.strftime("%Y-%m-%d") / input_path.name
                            md_file.save(output_path)
                            
                            evaluated_urls.add(url)
                            new_evaluations += 1
                            processed += 1
                            
                            # Track MCP-related content
                            if evaluation.is_mcp_related:
                                mcp_related += 1
                            
                            total_relevance_score += evaluation.relevance_score
                            
                            # Track evaluations by date
                            date_str = str(current_date)
                            if date_str not in evaluations_by_date:
                                evaluations_by_date[date_str] = 0
                            evaluations_by_date[date_str] += 1
                            
                            logger.info(f"Evaluated and saved: {output_path.name} (relevance: {evaluation.relevance_score})")
                            
                        except Exception as e:
                            failed += 1
                            logger.error(f"Failed to evaluate {url}: {e}")
                        
                    except Exception as e:
                        failed += 1
                        logger.error(f"Failed to process {input_path}: {e}")
            
            current_date += timedelta(days=1)
        
        avg_relevance = total_relevance_score / new_evaluations if new_evaluations > 0 else 0.0
        
        result = {
            "stage": self.stage_name,
            "days_scanned": days_back,
            "date_range": f"{start_date} to {end_date}",
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "total": processed + skipped + failed,
            "new_evaluations": new_evaluations,
            "previously_evaluated": len(evaluated_urls) - new_evaluations,
            "mcp_related": mcp_related,
            "avg_relevance_score": round(avg_relevance, 3),
            "evaluations_by_date": evaluations_by_date
        }
        
        logger.info(f"Evaluate stage completed: {result}")
        return result