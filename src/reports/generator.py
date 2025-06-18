"""HTML report generator."""

from datetime import date, datetime
from pathlib import Path
from typing import Optional, List
import xml.etree.ElementTree as ET
from xml.dom import minidom

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models.report import ArchiveLink, HomepageData, ReportArticle, ReportDay
from src.reports.formatting import get_content_type_icon, get_content_type_with_tooltip, get_language_flag
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
        
        # Add custom filters
        self.env.filters['content_icon'] = get_content_type_icon
        self.env.filters['content_icon_tooltip'] = get_content_type_with_tooltip
        self.env.filters['language_flag'] = get_language_flag
    
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
            day_sections=homepage_data.day_sections,
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
    
    def generate_sitemap(self, base_url: str = "https://example.com", 
                        report_dates: Optional[List[date]] = None) -> Path:
        """
        Generate sitemap.xml file for all reports.
        
        Args:
            base_url: Base URL for the website
            report_dates: List of dates with reports (if not provided, scans output/reports/)
            
        Returns:
            Path to generated sitemap.xml
        """
        # Create root element
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        
        # Add homepage
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = base_url + "/index.html"
        ET.SubElement(url_elem, "changefreq").text = "daily"
        ET.SubElement(url_elem, "priority").text = "1.0"
        ET.SubElement(url_elem, "lastmod").text = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Scan for report dates if not provided
        if report_dates is None:
            report_dates = []
            reports_dir = self.output_dir / "reports"
            if reports_dir.exists():
                for date_dir in sorted(reports_dir.iterdir(), reverse=True):
                    if date_dir.is_dir() and (date_dir / "report.html").exists():
                        try:
                            report_date = date.fromisoformat(date_dir.name)
                            report_dates.append(report_date)
                        except ValueError:
                            continue
        
        # Add report pages
        for report_date in sorted(report_dates, reverse=True):
            url_elem = ET.SubElement(urlset, "url")
            ET.SubElement(url_elem, "loc").text = f"{base_url}/reports/{report_date.strftime('%Y-%m-%d')}/report.html"
            ET.SubElement(url_elem, "lastmod").text = report_date.strftime("%Y-%m-%d")
            ET.SubElement(url_elem, "changefreq").text = "yearly"
            ET.SubElement(url_elem, "priority").text = "0.8"
        
        # Pretty print the XML
        xml_str = minidom.parseString(ET.tostring(urlset)).toprettyxml(indent="  ")
        
        # Write to file
        sitemap_path = self.output_dir / "sitemap.xml"
        sitemap_path.write_text(xml_str)
        
        logger.info(f"Generated sitemap with {len(report_dates) + 1} URLs: {sitemap_path}")
        return sitemap_path
    
    def generate_rss(self, articles: List[ReportArticle], 
                     feed_title: str = "MCP Monitor Daily Report",
                     feed_description: str = "Daily monitoring of Model Context Protocol mentions",
                     feed_link: str = "https://example.com",
                     max_items: int = 50) -> Path:
        """
        Generate RSS feed for recent articles.
        
        Args:
            articles: List of articles to include in feed
            feed_title: Title of the RSS feed
            feed_description: Description of the RSS feed
            feed_link: Link to the website
            max_items: Maximum number of items in feed
            
        Returns:
            Path to generated rss.xml
        """
        # Create RSS root element
        rss = ET.Element("rss", version="2.0", 
                        attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
        channel = ET.SubElement(rss, "channel")
        
        # Add channel metadata
        ET.SubElement(channel, "title").text = feed_title
        ET.SubElement(channel, "link").text = feed_link
        ET.SubElement(channel, "description").text = feed_description
        ET.SubElement(channel, "language").text = "en-us"
        ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        # Add atom:link for feed autodiscovery
        atom_link = ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
        atom_link.set("href", f"{feed_link}/rss.xml")
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")
        
        # Sort articles by date and limit
        sorted_articles = sorted(articles, key=lambda x: x.created_at, reverse=True)[:max_items]
        
        # Add items
        for article in sorted_articles:
            item = ET.SubElement(channel, "item")
            
            ET.SubElement(item, "title").text = article.title
            ET.SubElement(item, "link").text = str(article.url)
            ET.SubElement(item, "description").text = article.perex
            ET.SubElement(item, "pubDate").text = article.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")
            ET.SubElement(item, "guid", isPermaLink="false").text = f"{feed_link}#{article.post_id}"
            
            # Add category for content type
            if article.content_type:
                ET.SubElement(item, "category").text = article.content_type
        
        # Pretty print the XML
        xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
        
        # Write to file
        rss_path = self.output_dir / "rss.xml"
        rss_path.write_text(xml_str)
        
        logger.info(f"Generated RSS feed with {len(sorted_articles)} items: {rss_path}")
        return rss_path