"""Report data models for HTML generation."""

from datetime import date as date_type, datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ReportArticle(BaseModel):
    """Article data prepared for HTML report rendering."""
    
    # Article info
    url: HttpUrl = Field(..., description="Article URL")
    title: str = Field(..., description="Article title")
    perex: str = Field(..., description="Witty summary for display")
    
    # Bluesky post info
    post_id: str = Field(..., description="Post ID")
    bluesky_url: HttpUrl = Field(..., description="Link to original Bluesky post")
    author: str = Field(..., description="Bluesky author handle")
    timestamp: str = Field(..., description="Formatted timestamp")
    created_at: datetime = Field(..., description="Raw creation datetime")
    
    # Metadata
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    domain: str = Field(..., description="Article domain")
    content_type: str = Field(..., description="Type of content")
    language: str = Field(..., description="Language code")
    
    # Debug info (optional)
    debug_filename: Optional[str] = Field(None, description="Source evaluation filename for debugging")
    
    @classmethod
    def from_post_and_evaluation(
        cls,
        post_id: str,
        author: str,
        created_at: datetime,
        evaluation: dict,
        debug_filename: Optional[str] = None
    ) -> "ReportArticle":
        """Create ReportArticle from post data and evaluation."""
        # Extract post ID from AT protocol URI if necessary
        if post_id.startswith("at://"):
            # Extract the last part after the final slash
            actual_post_id = post_id.split("/")[-1]
        else:
            actual_post_id = post_id
        
        # Format Bluesky URL
        bluesky_url = f"https://bsky.app/profile/{author}/post/{actual_post_id}"
        
        # Format timestamp (e.g., "3:45 PM")
        timestamp = created_at.strftime("%-I:%M %p")
        
        # Use perex if available, otherwise fall back to summary
        perex = evaluation.get("perex") or evaluation.get("summary", "")
        
        return cls(
            url=evaluation["url"],
            title=evaluation.get("title", "Untitled"),
            perex=perex,
            post_id=actual_post_id,
            bluesky_url=bluesky_url,
            author=author,
            timestamp=timestamp,
            created_at=created_at,
            relevance_score=evaluation["relevance_score"],
            domain=evaluation["domain"],
            content_type=evaluation.get("content_type", "article"),
            language=evaluation.get("language", "en"),
            debug_filename=debug_filename
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
        path = report_date.strftime("reports/%Y-%m-%d/report.html")
        
        return cls(
            date=report_date,
            formatted=formatted,
            path=path,
            article_count=article_count
        )


class DaySection(BaseModel):
    """A section of articles for a specific day."""
    
    date: date_type = Field(..., description="The date")
    formatted_date: str = Field(..., description="Human-readable date")
    articles: list[ReportArticle] = Field(..., description="Articles for this day")
    
    @classmethod
    def create(cls, report_date: date_type, articles: list[ReportArticle]) -> "DaySection":
        """Create a day section."""
        # Format as "Today (June 16, 2025)" or "Yesterday (June 15, 2025)" or just "June 14, 2025"
        today = date_type.today()
        if report_date == today:
            formatted_date = f"Today ({report_date.strftime('%B %-d, %Y')})"
        elif report_date == today - timedelta(days=1):
            formatted_date = f"Yesterday ({report_date.strftime('%B %-d, %Y')})"
        else:
            formatted_date = report_date.strftime("%B %-d, %Y")
        
        return cls(
            date=report_date,
            formatted_date=formatted_date,
            articles=articles
        )


class HomepageData(BaseModel):
    """Data for rendering the homepage."""
    
    today: str = Field(..., description="Today's date formatted")
    today_articles: list[ReportArticle] = Field(..., description="Today's articles")  # Keep for backward compatibility
    day_sections: list[DaySection] = Field(..., description="Day-by-day article sections")
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
            day_sections=[],  # Will be populated by enhanced logic
            archive_dates=archive_dates
        )
    
    @classmethod
    def create_enhanced(
        cls,
        day_sections: list[DaySection],
        archive_dates: list[ArchiveLink]
    ) -> "HomepageData":
        """Create enhanced homepage data with day sections."""
        from datetime import timedelta
        
        today = date_type.today().strftime("%B %-d, %Y")
        
        # Extract today's articles for backward compatibility
        today_articles = []
        for section in day_sections:
            if section.date == date_type.today():
                today_articles = section.articles
                break
        
        return cls(
            today=today,
            today_articles=today_articles,
            day_sections=day_sections,
            archive_dates=archive_dates
        )