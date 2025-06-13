"""Report stage - generates daily reports from evaluated content."""

from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional, List
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models.report import ReportArticle, ReportDay
from src.stages.base import ProcessingStage
from src.stages.markdown import MarkdownFile

logger = logging.getLogger(__name__)


class ReportStage(ProcessingStage):
    """Generates daily reports from evaluated content."""
    
    def __init__(self, template_dir: Optional[Path] = None, base_path: Path = Path("stages")):
        super().__init__("report", "evaluate", base_path)
        
        # Set up templates
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.template_dir = template_dir
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def get_inputs(self, target_date: date) -> Iterator[Path]:
        """Get all evaluated files for the date."""
        return super().get_inputs(target_date)
    
    def collect_mcp_articles(self, target_date: date, min_relevance: float = 0.3) -> List[ReportArticle]:
        """
        Collect MCP-related articles from evaluated content.
        
        Args:
            target_date: Date to collect articles for
            min_relevance: Minimum relevance score to include
            
        Returns:
            List of ReportArticle objects
        """
        articles = []
        
        for input_path in self.get_inputs(target_date):
            try:
                md_file = MarkdownFile.load(input_path)
                evaluation = md_file.get_frontmatter_value("evaluation", {})
                
                # Only include MCP-related articles above threshold
                if not evaluation.get("is_mcp_related", False):
                    continue
                
                relevance_score = evaluation.get("relevance_score", 0.0)
                if relevance_score < min_relevance:
                    continue
                
                # Extract post information (we need to find the original post)
                # For now, we'll create a synthetic post ID and author
                url = md_file.get_frontmatter_value("url")
                found_in_posts = md_file.get_frontmatter_value("found_in_posts", [])
                
                # Use first post ID if available, otherwise generate one
                if found_in_posts:
                    post_id = found_in_posts[0]
                    # Extract author from post ID if possible
                    if post_id.startswith("at://did:"):
                        # This is an AT protocol URI, author extraction is complex
                        # For now, use domain from URL
                        author = md_file.get_frontmatter_value("domain", "unknown")
                    else:
                        author = "unknown"
                else:
                    post_id = f"synthetic_{url}"
                    author = md_file.get_frontmatter_value("domain", "unknown")
                
                # Create ReportArticle
                created_at = datetime.fromisoformat(
                    md_file.get_frontmatter_value("fetched_at").rstrip('Z')
                )
                
                # Prepare evaluation dict in expected format
                eval_dict = {
                    "url": url,
                    "title": md_file.get_frontmatter_value("title", "Untitled"),
                    "perex": evaluation.get("perex", evaluation.get("summary", "")),
                    "relevance_score": relevance_score,
                    "domain": md_file.get_frontmatter_value("domain", "")
                }
                
                article = ReportArticle.from_post_and_evaluation(
                    post_id=post_id,
                    author=author,
                    created_at=created_at,
                    evaluation=eval_dict
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Failed to process {input_path} for report: {e}")
        
        # Sort by relevance score (highest first)
        articles.sort(key=lambda x: x.relevance_score, reverse=True)
        return articles
    
    def process_item(self, input_path: Path, target_date: date) -> Optional[Path]:
        """
        Process is handled differently for reports - we process all items together.
        This method is not used for ReportStage.
        """
        return None
    
    def should_process_item(self, input_path: Path, target_date: date) -> bool:
        """Check if report should be generated (not if individual items should be processed)."""
        # For reports, we check if the report already exists
        report_path = self.get_report_output_path(target_date)
        return not report_path.exists()
    
    def get_report_output_path(self, target_date: date) -> Path:
        """Get output path for the daily report."""
        stage_dir = self.ensure_stage_dir(target_date)
        return stage_dir / "report.html"
    
    def get_metadata_output_path(self, target_date: date) -> Path:
        """Get output path for the report metadata."""
        stage_dir = self.ensure_stage_dir(target_date)
        return stage_dir / "report_meta.md"
    
    async def run_report(self, target_date: Optional[date] = None) -> dict:
        """
        Run the report stage for the specified date.
        
        Returns:
            Summary of report generation results
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Running report stage for {target_date}")
        
        # Ensure output directory exists
        self.ensure_stage_dir(target_date)
        
        # Check if report already exists
        if not self.should_process_item(Path(), target_date):
            logger.info(f"Report already exists for {target_date}")
            return {
                "stage": self.stage_name,
                "date": target_date,
                "status": "already_exists"
            }
        
        # Collect MCP-related articles
        articles = self.collect_mcp_articles(target_date)
        
        if not articles:
            logger.warning(f"No MCP-related articles found for {target_date}")
            
            # Create empty report metadata
            metadata = {
                "date": target_date.isoformat(),
                "total_evaluated": len(list(self.get_inputs(target_date))),
                "mcp_related_articles": 0,
                "report_generated_at": datetime.utcnow().isoformat() + 'Z',
                "stage": "reported",
                "articles": []
            }
            
            metadata_md = MarkdownFile(metadata, "# Daily Report Summary\n\nNo MCP-related articles found for this date.")
            metadata_path = self.get_metadata_output_path(target_date)
            metadata_md.save(metadata_path)
            
            return {
                "stage": self.stage_name,
                "date": target_date,
                "articles_found": 0,
                "report_generated": False,
                "metadata_saved": True
            }
        
        # Create ReportDay
        report_day = ReportDay.create(target_date, articles)
        
        # Generate HTML report
        try:
            template = self.env.get_template("daily.html")
            html_content = template.render(
                date_formatted=report_day.date_formatted,
                articles=report_day.articles
            )
            
            # Save HTML report
            report_path = self.get_report_output_path(target_date)
            report_path.write_text(html_content)
            
            logger.info(f"Generated HTML report: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            html_content = None
        
        # Create and save metadata
        article_summaries = []
        for article in articles:
            article_summaries.append({
                "url": str(article.url),
                "relevance_score": article.relevance_score,
                "title": article.title,
                "perex": article.perex[:100] + "..." if len(article.perex) > 100 else article.perex
            })
        
        metadata = {
            "date": target_date.isoformat(),
            "total_evaluated": len(list(self.get_inputs(target_date))),
            "mcp_related_articles": len(articles),
            "report_generated_at": datetime.utcnow().isoformat() + 'Z',
            "stage": "reported",
            "articles": article_summaries
        }
        
        metadata_content = f"# Daily Report Summary\n\nGenerated report for {report_day.date_formatted} with {len(articles)} MCP-related articles."
        metadata_md = MarkdownFile(metadata, metadata_content)
        metadata_path = self.get_metadata_output_path(target_date)
        metadata_md.save(metadata_path)
        
        result = {
            "stage": self.stage_name,
            "date": target_date,
            "articles_found": len(articles),
            "report_generated": html_content is not None,
            "metadata_saved": True,
            "avg_relevance": round(sum(a.relevance_score for a in articles) / len(articles), 3) if articles else 0
        }
        
        logger.info(f"Report stage completed: {result}")
        return result