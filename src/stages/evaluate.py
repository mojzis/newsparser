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
        """Process a single fetched content file for evaluation."""
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
            
            # Add evaluation to frontmatter
            evaluation_data = {
                "is_mcp_related": evaluation.is_mcp_related,
                "relevance_score": evaluation.relevance_score,
                "summary": evaluation.summary,
                "perex": evaluation.perex,
                "key_topics": evaluation.key_topics,
                "evaluated_at": evaluation.evaluated_at.isoformat() + 'Z',
                "evaluator": "claude-3-haiku-20240307"  # Model used for evaluation
            }
            
            # Update frontmatter with evaluation
            md_file.update_frontmatter({
                "evaluation": evaluation_data,
                "stage": "evaluated"
            })
            
            # Save to output path
            output_path = self.get_output_path(input_path, target_date)
            md_file.save(output_path)
            
            logger.info(f"Evaluated and saved: {output_path.name} (relevance: {evaluation.relevance_score})")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to evaluate {input_path}: {e}")
            return None
    
    async def run_evaluate(self, target_date: Optional[date] = None) -> dict:
        """
        Run the evaluate stage for the specified date.
        
        Returns:
            Summary of evaluation results
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Running evaluate stage for {target_date}")
        
        # Ensure output directory exists
        self.ensure_stage_dir(target_date)
        
        # Process all fetched content
        processed = 0
        skipped = 0
        failed = 0
        mcp_related = 0
        total_relevance_score = 0.0
        
        for input_path in self.get_inputs(target_date):
            try:
                if not self.should_process_item(input_path, target_date):
                    skipped += 1
                    continue
                
                result = await self.process_item(input_path, target_date)
                if result:
                    processed += 1
                    
                    # Load the result to get evaluation metrics
                    result_md = MarkdownFile.load(result)
                    evaluation = result_md.get_frontmatter_value("evaluation", {})
                    
                    if evaluation.get("is_mcp_related", False):
                        mcp_related += 1
                    
                    total_relevance_score += evaluation.get("relevance_score", 0.0)
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                logger.error(f"Failed to process {input_path}: {e}")
        
        avg_relevance = total_relevance_score / processed if processed > 0 else 0.0
        
        result = {
            "stage": self.stage_name,
            "date": target_date,
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "total": processed + skipped + failed,
            "mcp_related": mcp_related,
            "avg_relevance_score": round(avg_relevance, 3)
        }
        
        logger.info(f"Evaluate stage completed: {result}")
        return result