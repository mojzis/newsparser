"""Report data models for HTML generation."""

from datetime import date as date_type, datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ReportArticle(BaseModel):
    """Article data prepared for HTML report rendering."""
    
    # Article info
    url: HttpUrl = Field(..., description="Article URL")
    title: str = Field(..., description="Article title")
    perex: str = Field(..., description="Witty summary for display")
    
    # Bluesky post info
    bluesky_url: HttpUrl = Field(..., description="Link to original Bluesky post")
    author: str = Field(..., description="Bluesky author handle")
    timestamp: str = Field(..., description="Formatted timestamp")
    
    # Metadata
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    domain: str = Field(..., description="Article domain")
    
    @classmethod
    def from_post_and_evaluation(
        cls,
        post_id: str,
        author: str,
        created_at: datetime,
        evaluation: dict
    ) -> "ReportArticle":
        """Create ReportArticle from post data and evaluation."""
        # Format Bluesky URL
        bluesky_url = f"https://bsky.app/profile/{author}/post/{post_id}"
        
        # Format timestamp (e.g., "3:45 PM")
        timestamp = created_at.strftime("%-I:%M %p")
        
        # Use perex if available, otherwise fall back to summary
        perex = evaluation.get("perex") or evaluation.get("summary", "")
        
        return cls(
            url=evaluation["url"],
            title=evaluation.get("title", "Untitled"),
            perex=perex,
            bluesky_url=bluesky_url,
            author=author,
            timestamp=timestamp,
            relevance_score=evaluation["relevance_score"],
            domain=evaluation["domain"]
        )


class ReportDay(BaseModel):
    """Daily report data for HTML generation."""
    
    date: date_type = Field(..., description="Report date")
    date_formatted: str = Field(..., description="Human-readable date")
    articles: list[ReportArticle] = Field(..., description="Articles for this day")
    article_count: int = Field(..., description="Total article count")
    
    @classmethod
    def create(cls, report_date: date_type, articles: list[ReportArticle]) -> "ReportDay":
        """Create ReportDay with formatted date."""
        # Format date as "December 6, 2025"
        date_formatted = report_date.strftime("%B %-d, %Y")
        
        return cls(
            date=report_date,
            date_formatted=date_formatted,
            articles=articles,
            article_count=len(articles)
        )


class ArchiveLink(BaseModel):
    """Link to a previous day's report."""
    
    date: date_type = Field(..., description="Report date")
    formatted: str = Field(..., description="Display text for link")
    path: str = Field(..., description="Relative path to report")
    article_count: int = Field(..., description="Number of articles")
    
    @classmethod
    def create(cls, report_date: date_type, article_count: int) -> "ArchiveLink":
        """Create archive link with formatted date and path."""
        # Format as "December 6" (no year for current year)
        if report_date.year == date_type.today().year:
            formatted = report_date.strftime("%B %-d")
        else:
            formatted = report_date.strftime("%B %-d, %Y")
        
        # Create path
        path = report_date.strftime("reports/%Y/%m/%d/report.html")
        
        return cls(
            date=report_date,
            formatted=formatted,
            path=path,
            article_count=article_count
        )


class HomepageData(BaseModel):
    """Data for rendering the homepage."""
    
    today: str = Field(..., description="Today's date formatted")
    today_articles: list[ReportArticle] = Field(..., description="Today's articles")
    archive_dates: list[ArchiveLink] = Field(..., description="Links to previous reports")
    
    @classmethod
    def create(
        cls,
        today_articles: list[ReportArticle],
        archive_dates: list[ArchiveLink]
    ) -> "HomepageData":
        """Create homepage data."""
        today = date_type.today().strftime("%B %-d, %Y")
        
        return cls(
            today=today,
            today_articles=today_articles,
            archive_dates=archive_dates
        )