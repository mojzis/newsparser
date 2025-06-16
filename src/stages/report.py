"""Report stage - generates daily reports from evaluated content."""

from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional, List
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models.report import ReportArticle, ReportDay, HomepageData, ArchiveLink, DaySection
from src.reports.generator import ReportGenerator
from src.reports.formatting import get_content_type_icon, get_content_type_with_tooltip, get_language_flag
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
        
        # Add custom filters (for potential template previews)
        self.env.filters['content_icon'] = get_content_type_icon
        self.env.filters['content_icon_tooltip'] = get_content_type_with_tooltip
        self.env.filters['language_flag'] = get_language_flag
    
    def get_inputs(self, target_date: date) -> Iterator[Path]:
        """Get all evaluated files for the date."""
        return super().get_inputs(target_date)
    
    def collect_mcp_articles_multi_day(self, days_back: int, reference_date: date, min_relevance: float = 0.3, debug: bool = False) -> List[ReportArticle]:
        """
        Collect MCP-related articles from evaluated content across multiple days.
        This method is used as fallback when no content exists for the specific date.
        
        Args:
            days_back: Number of days to look back
            reference_date: Reference date for the scan
            min_relevance: Minimum relevance score to include
            
        Returns:
            List of ReportArticle objects
        """
        from datetime import timedelta
        
        articles = []
        processed_urls = set()  # Deduplicate by URL
        articles_by_date = {}
        
        # Scan each day in the range
        end_date = reference_date
        start_date = end_date - timedelta(days=days_back)
        
        current_date = start_date
        while current_date <= end_date:
            # Check if evaluate stage has data for this date
            evaluate_dir = self.base_path / self.input_stage_name / current_date.strftime("%Y-%m-%d")
            
            if evaluate_dir.exists():
                logger.info(f"Scanning evaluated content from {current_date}")
                date_articles = 0
                
                for input_path in evaluate_dir.glob("*.md"):
                    try:
                        md_file = MarkdownFile.load(input_path)
                        evaluation = md_file.get_frontmatter_value("evaluation", {})
                        
                        # Only include MCP-related articles above threshold
                        if not evaluation.get("is_mcp_related", False):
                            continue
                        
                        relevance_score = evaluation.get("relevance_score", 0.0)
                        if relevance_score < min_relevance:
                            continue
                        
                        # Extract post information
                        url = md_file.get_frontmatter_value("url")
                        
                        # Deduplicate by URL
                        if url in processed_urls:
                            logger.debug(f"Skipping duplicate URL: {url}")
                            continue
                        processed_urls.add(url)
                        
                        found_in_posts = md_file.get_frontmatter_value("found_in_posts", [])
                        
                        # Get original post data to extract correct author and timestamp
                        author = "unknown"
                        created_at = datetime.utcnow()  # fallback
                        post_id = None
                        
                        if found_in_posts:
                            post_id = found_in_posts[0]
                            
                            # Look up the original post to get author and timestamp
                            try:
                                # Extract post ID from AT protocol URI
                                if post_id.startswith("at://did:"):
                                    actual_post_id = post_id.split("/")[-1]
                                else:
                                    actual_post_id = post_id
                                
                                # Find the original post file in collect stage - search across all dates
                                post_found = False
                                for search_days_back in range(days_back + 7):  # Search a bit further back
                                    search_date = reference_date - timedelta(days=search_days_back)
                                    collect_dir = Path("stages/collect") / search_date.strftime("%Y-%m-%d")
                                    post_file = collect_dir / f"post_{actual_post_id}.md"
                                    
                                    if post_file.exists():
                                        post_md = MarkdownFile.load(post_file)
                                        author = post_md.get_frontmatter_value("author", "unknown")
                                        created_at_str = post_md.get_frontmatter_value("created_at")
                                        if created_at_str:
                                            # Handle both ISO format with and without timezone
                                            if created_at_str.endswith('+00:00'):
                                                created_at = datetime.fromisoformat(created_at_str.replace('+00:00', 'Z').rstrip('Z'))
                                            else:
                                                created_at = datetime.fromisoformat(created_at_str.rstrip('Z'))
                                        post_found = True
                                        break
                                
                                if not post_found:
                                    logger.warning(f"Could not find original post for {post_id}")
                                    
                            except Exception as e:
                                logger.warning(f"Failed to load original post data for {post_id}: {e}")
                                # Fallback to domain-based author
                                author = md_file.get_frontmatter_value("domain", "unknown")
                        
                        if not post_id:
                            post_id = f"synthetic_{url}"
                            author = md_file.get_frontmatter_value("domain", "unknown")
                        
                        # Prepare evaluation dict in expected format
                        eval_dict = {
                            "url": url,
                            "title": md_file.get_frontmatter_value("title", "Untitled"),
                            "perex": evaluation.get("perex", evaluation.get("summary", "")),
                            "relevance_score": relevance_score,
                            "domain": md_file.get_frontmatter_value("domain", ""),
                            "content_type": evaluation.get("content_type", "article"),
                            "language": evaluation.get("language", "en")
                        }
                        
                        # IMPORTANT: Only include articles posted on the specific current_date
                        if created_at.date() == current_date:
                            debug_filename = input_path.name if debug else None
                            article = ReportArticle.from_post_and_evaluation(
                                post_id=post_id,
                                author=author,
                                created_at=created_at,
                                evaluation=eval_dict,
                                debug_filename=debug_filename
                            )
                            articles.append(article)
                            date_articles += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to process {input_path} for report: {e}")
                
                if date_articles > 0:
                    articles_by_date[str(current_date)] = date_articles
            
            current_date += timedelta(days=1)
        
        # Sort by relevance score (highest first)
        articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Collected {len(articles)} unique MCP-related articles from {days_back} days (date-filtered)")
        if articles_by_date:
            for date_str, count in sorted(articles_by_date.items()):
                logger.info(f"  - {date_str}: {count} articles")
        
        return articles
    
    def collect_mcp_articles(self, target_date: date, min_relevance: float = 0.3, debug: bool = False) -> List[ReportArticle]:
        """
        Collect MCP-related articles from evaluated content for a single date.
        Only includes articles that were originally posted on the target date.
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
                
                # Extract post information from original post data
                url = md_file.get_frontmatter_value("url")
                found_in_posts = md_file.get_frontmatter_value("found_in_posts", [])
                
                # Get original post data to extract correct author and timestamp
                author = "unknown"
                created_at = datetime.utcnow()  # fallback
                post_id = None
                
                if found_in_posts:
                    post_id = found_in_posts[0]
                    
                    # Look up the original post to get author and timestamp
                    try:
                        # Extract post ID from AT protocol URI
                        if post_id.startswith("at://did:"):
                            actual_post_id = post_id.split("/")[-1]
                        else:
                            actual_post_id = post_id
                        
                        # Search for the original post - first try target date, then expand search
                        post_found = False
                        from datetime import timedelta
                        
                        for search_days_back in range(10):  # Search up to 10 days back
                            search_date = target_date - timedelta(days=search_days_back)
                            collect_dir = Path("stages/collect") / search_date.strftime("%Y-%m-%d")
                            post_file = collect_dir / f"post_{actual_post_id}.md"
                            
                            if post_file.exists():
                                post_md = MarkdownFile.load(post_file)
                                author = post_md.get_frontmatter_value("author", "unknown")
                                created_at_str = post_md.get_frontmatter_value("created_at")
                                if created_at_str:
                                    # Handle both ISO format with and without timezone
                                    if created_at_str.endswith('+00:00'):
                                        created_at = datetime.fromisoformat(created_at_str.replace('+00:00', 'Z').rstrip('Z'))
                                    else:
                                        created_at = datetime.fromisoformat(created_at_str.rstrip('Z'))
                                post_found = True
                                break
                        
                        if not post_found:
                            logger.warning(f"Could not find original post for {post_id}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to load original post data for {post_id}: {e}")
                        # Fallback to domain-based author
                        author = md_file.get_frontmatter_value("domain", "unknown")
                
                if not post_id:
                    post_id = f"synthetic_{url}"
                    author = md_file.get_frontmatter_value("domain", "unknown")
                
                # IMPORTANT: Only include articles that were posted on the target date
                if created_at.date() != target_date:
                    logger.debug(f"Skipping article from {created_at.date()} - not from target date {target_date}")
                    continue
                
                # Prepare evaluation dict in expected format
                eval_dict = {
                    "url": url,
                    "title": md_file.get_frontmatter_value("title", "Untitled"),
                    "perex": evaluation.get("perex", evaluation.get("summary", "")),
                    "relevance_score": relevance_score,
                    "domain": md_file.get_frontmatter_value("domain", ""),
                    "content_type": evaluation.get("content_type", "article"),
                    "language": evaluation.get("language", "en")
                }
                
                debug_filename = input_path.name if debug else None
                article = ReportArticle.from_post_and_evaluation(
                    post_id=post_id,
                    author=author,
                    created_at=created_at,
                    evaluation=eval_dict,
                    debug_filename=debug_filename
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Failed to process {input_path} for report: {e}")
        
        # Sort by relevance score (highest first)
        articles.sort(key=lambda x: x.relevance_score, reverse=True)
        logger.info(f"Collected {len(articles)} articles specifically from {target_date}")
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
        # Reports go to output/reports/ directory with simple date format
        reports_dir = Path("output") / "reports" / target_date.strftime("%Y-%m-%d")
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / "report.html"
    
    def get_metadata_output_path(self, target_date: date) -> Path:
        """Get output path for the report metadata."""
        stage_dir = self.ensure_stage_dir(target_date)
        return stage_dir / "report_meta.md"
    
    async def run_report(self, days_back: int = 7, regenerate: bool = True, output_date: Optional[date] = None, debug: bool = False) -> dict:
        """
        Run the report stage, scanning evaluated content from the last N days.
        
        Args:
            days_back: Number of days to look back for evaluated content (default: 7)
            regenerate: Whether to regenerate existing reports (default True)
            output_date: Date to use for the report filename (defaults to today)
        
        Returns:
            Summary of report generation results
        """
        from datetime import timedelta
        
        if output_date is None:
            output_date = date.today()
        
        logger.info(f"Running report stage, scanning evaluated content from last {days_back} days")
        
        # Ensure output directory exists
        self.ensure_stage_dir(output_date)
        
        # Check if report already exists and whether to regenerate
        if not regenerate and not self.should_process_item(Path(), output_date):
            logger.info(f"Report already exists for {output_date} and regenerate=False")
            return {
                "stage": self.stage_name,
                "date": output_date,
                "status": "already_exists"
            }
        
        # First try to collect articles from the specific output date
        articles = self.collect_mcp_articles(output_date, debug=debug)
        
        # If no articles found for the output date, fall back to recent content
        if not articles:
            logger.info(f"No articles found for {output_date}, scanning last {days_back} days for fallback")
            articles = self.collect_mcp_articles_multi_day(days_back, output_date, debug=debug)
            
            # Since we already filtered by date in collect_mcp_articles_multi_day,
            # no additional filtering needed here
            logger.info(f"Using {len(articles)} articles from multi-day fallback")
        
        if not articles:
            logger.warning(f"No MCP-related articles found in the last {days_back} days")
            
            # Create empty report metadata
            metadata = {
                "date": output_date.isoformat(),
                "days_scanned": days_back,
                "mcp_related_articles": 0,
                "report_generated_at": datetime.utcnow().isoformat() + 'Z',
                "stage": "reported",
                "articles": []
            }
            
            metadata_md = MarkdownFile(metadata, f"# Daily Report Summary\n\nNo MCP-related articles found in the last {days_back} days.")
            metadata_path = self.get_metadata_output_path(output_date)
            metadata_md.save(metadata_path)
            
            return {
                "stage": self.stage_name,
                "date": output_date,
                "days_scanned": days_back,
                "articles_found": 0,
                "report_generated": False,
                "metadata_saved": True
            }
        
        # Create ReportDay
        report_day = ReportDay.create(output_date, articles)
        
        # Generate HTML report using ReportGenerator for consistency
        generator = ReportGenerator()
        html_content = None
        homepage_content = None
        
        try:
            # Generate daily report
            daily_path = generator.generate_daily_report(report_day)
            html_content = True
            logger.info(f"Generated HTML report: {daily_path}")
            
            # Generate enhanced homepage with minimum 10 articles
            day_sections = self.collect_homepage_articles(min_articles=10, debug=debug)
            
            # Get archive dates by checking for recent evaluations (beyond the day sections)
            archive_links = []
            days_covered = {section.date for section in day_sections}
            
            for check_days_back in range(1, 15):  # Check last 15 days for archive
                check_date = date.fromordinal(output_date.toordinal() - check_days_back)
                
                # Skip dates already included in day sections
                if check_date in days_covered:
                    continue
                
                # Check if there are evaluated articles for this date
                evaluated_articles = self.collect_mcp_articles(check_date, debug=False)  # No debug for archive check
                if evaluated_articles:
                    archive_links.append(ArchiveLink.create(
                        report_date=check_date,
                        article_count=len(evaluated_articles)
                    ))
            
            # Create enhanced homepage data
            homepage_data = HomepageData.create_enhanced(
                day_sections=day_sections,
                archive_dates=archive_links
            )
            
            # Generate homepage
            homepage_path = generator.generate_homepage(homepage_data)
            homepage_content = True
            logger.info(f"Generated homepage: {homepage_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate HTML reports: {e}")
            html_content = None
            homepage_content = None
        
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
            "date": output_date.isoformat(),
            "days_scanned": days_back,
            "mcp_related_articles": len(articles),
            "report_generated_at": datetime.utcnow().isoformat() + 'Z',
            "stage": "reported",
            "articles": article_summaries
        }
        
        metadata_content = f"# Daily Report Summary\n\nGenerated report for {report_day.date_formatted} with {len(articles)} MCP-related articles from the last {days_back} days."
        metadata_md = MarkdownFile(metadata, metadata_content)
        metadata_path = self.get_metadata_output_path(output_date)
        metadata_md.save(metadata_path)
        
        result = {
            "stage": self.stage_name,
            "date": output_date,
            "days_scanned": days_back,
            "articles_found": len(articles),
            "report_generated": html_content is not None,
            "homepage_generated": homepage_content is not None,
            "metadata_saved": True,
            "avg_relevance": round(sum(a.relevance_score for a in articles) / len(articles), 3) if articles else 0
        }
        
        logger.info(f"Report stage completed: {result}")
        return result
    
    async def run_bulk_report(self, days_back: int = 7, regenerate: bool = True, output_date: Optional[date] = None, debug: bool = False) -> dict:
        """
        Generate reports for each day that has evaluated content in the last N days.
        
        Args:
            days_back: Number of days to look back for evaluated content (default: 7)
            regenerate: Whether to regenerate existing reports (default True)
            output_date: Reference date to work backwards from (defaults to today)
        
        Returns:
            Summary of bulk report generation results
        """
        from datetime import timedelta
        
        if output_date is None:
            output_date = date.today()
        
        logger.info(f"Running bulk report generation, scanning last {days_back} days from {output_date}")
        
        reports_generated = 0
        total_articles = 0
        dates_processed = []
        
        # Scan each day in the range
        for days_ago in range(days_back + 1):  # Include the output_date itself
            check_date = output_date - timedelta(days=days_ago)
            
            # Check if there are evaluated articles for this date
            articles = self.collect_mcp_articles(check_date, debug=debug)
            
            if articles:
                logger.info(f"Found {len(articles)} articles for {check_date}, generating report...")
                
                # Check if we should regenerate
                if not regenerate and not self.should_process_item(Path(), check_date):
                    logger.info(f"Report already exists for {check_date} and regenerate=False, skipping")
                    continue
                
                try:
                    # Generate report for this specific date
                    result = await self.run_report(0, regenerate, check_date, debug)  # days_back=0 to avoid recursion
                    
                    if result.get("report_generated"):
                        reports_generated += 1
                        total_articles += result.get("articles_found", 0)
                        dates_processed.append(check_date.isoformat())
                        logger.info(f"✅ Generated report for {check_date} with {result.get('articles_found', 0)} articles")
                    else:
                        logger.warning(f"⚠️  Failed to generate report for {check_date}")
                        
                except Exception as e:
                    logger.error(f"❌ Error generating report for {check_date}: {e}")
            else:
                logger.debug(f"No articles found for {check_date}, skipping")
        
        # Generate updated homepage with all the reports
        if reports_generated > 0:
            try:
                # Generate enhanced homepage with minimum 10 articles
                day_sections = self.collect_homepage_articles(min_articles=10, debug=debug)
                
                # Get archive dates by checking for recent evaluations (beyond the day sections)
                archive_links = []
                days_covered = {section.date for section in day_sections}
                
                for check_days_back in range(1, 15):  # Check last 15 days for archive
                    check_date = output_date - timedelta(days=check_days_back)
                    
                    # Skip dates already included in day sections
                    if check_date in days_covered:
                        continue
                    
                    # Check if there are evaluated articles for this date
                    evaluated_articles = self.collect_mcp_articles(check_date, debug=False)
                    if evaluated_articles:
                        archive_links.append(ArchiveLink.create(
                            report_date=check_date,
                            article_count=len(evaluated_articles)
                        ))
                
                # Create enhanced homepage data
                homepage_data = HomepageData.create_enhanced(
                    day_sections=day_sections,
                    archive_dates=archive_links
                )
                
                # Generate homepage
                generator = ReportGenerator()
                homepage_path = generator.generate_homepage(homepage_data)
                logger.info(f"✅ Updated homepage with {reports_generated} regenerated reports: {homepage_path}")
            except Exception as e:
                logger.error(f"❌ Failed to update homepage: {e}")
        
        result = {
            "stage": self.stage_name,
            "bulk_operation": True,
            "reference_date": output_date,
            "days_scanned": days_back,
            "reports_generated": reports_generated,
            "total_articles": total_articles,
            "dates_processed": dates_processed
        }
        
        logger.info(f"Bulk report generation completed: {result}")
        return result
    
    def collect_homepage_articles(self, min_articles: int = 10, max_days_back: int = 14, debug: bool = False) -> list[DaySection]:
        """
        Collect articles for homepage, ensuring at least min_articles are included.
        Groups articles by day and continues collecting from previous days until minimum is met.
        
        Args:
            min_articles: Minimum number of articles to collect
            max_days_back: Maximum number of days to look back
            debug: Whether to include debug information
            
        Returns:
            List of DaySection objects, ordered from newest to oldest
        """
        from datetime import timedelta
        
        day_sections = []
        total_articles = 0
        today = date.today()
        
        logger.info(f"Collecting homepage articles with minimum {min_articles} articles")
        
        # Collect articles day by day until we have enough
        for days_ago in range(max_days_back + 1):
            if total_articles >= min_articles:
                break
                
            check_date = today - timedelta(days=days_ago)
            articles = self.collect_mcp_articles(check_date, debug=debug)
            
            if articles:
                day_section = DaySection.create(check_date, articles)
                day_sections.append(day_section)
                total_articles += len(articles)
                logger.info(f"Added {len(articles)} articles from {check_date} (total: {total_articles})")
        
        logger.info(f"Collected {total_articles} articles across {len(day_sections)} days for homepage")
        return day_sections