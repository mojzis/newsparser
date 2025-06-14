"""HTML report generator."""

from datetime import date
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models.report import ArchiveLink, HomepageData, ReportArticle, ReportDay
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates HTML reports from collected data."""
    
    def __init__(self, template_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            template_dir: Directory containing Jinja2 templates
            output_dir: Directory for generated reports
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        if output_dir is None:
            output_dir = Path("output")
            
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def generate_daily_report(self, report_day: ReportDay) -> Path:
        """
        Generate HTML report for a single day.
        
        Args:
            report_day: Report data for the day
            
        Returns:
            Path to generated report file
        """
        # Create output directory
        report_dir = self.output_dir / "reports" / report_day.date.strftime("%Y-%m-%d")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Render template
        template = self.env.get_template("daily.html")
        html_content = template.render(
            date_formatted=report_day.date_formatted,
            articles=report_day.articles
        )
        
        # Write to file
        report_path = report_dir / "report.html"
        report_path.write_text(html_content)
        
        logger.info(f"Generated daily report: {report_path}")
        return report_path
    
    def generate_homepage(self, homepage_data: HomepageData) -> Path:
        """
        Generate homepage with latest articles and archive.
        
        Args:
            homepage_data: Homepage data including today's articles and archive
            
        Returns:
            Path to generated homepage
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Render template
        template = self.env.get_template("homepage.html")
        html_content = template.render(
            today=homepage_data.today,
            today_articles=homepage_data.today_articles,
            archive_dates=homepage_data.archive_dates
        )
        
        # Write to file
        homepage_path = self.output_dir / "index.html"
        homepage_path.write_text(html_content)
        
        logger.info(f"Generated homepage: {homepage_path}")
        return homepage_path
    
    def preview_template(self, template_name: str, context: dict) -> str:
        """
        Preview a template with given context.
        
        Args:
            template_name: Name of template to preview
            context: Context data for rendering
            
        Returns:
            Rendered HTML as string
        """
        template = self.env.get_template(f"{template_name}.html")
        return template.render(**context)