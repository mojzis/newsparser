"""Article evaluation models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ArticleEvaluation(BaseModel):
    """Evaluation result for an article from Anthropic API."""
    
    url: HttpUrl = Field(..., description="Article URL")
    is_mcp_related: bool = Field(..., description="Whether article is MCP-related")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    summary: str = Field(..., min_length=10, max_length=500, description="Brief summary")
    perex: str = Field(..., min_length=10, max_length=200, description="Witty, engaging summary for display")
    key_topics: list[str] = Field(default_factory=list, description="Key topics discussed")
    
    # Content classification
    content_type: str = Field(..., description="Type of content (video, newsletter, article, blog post, product update, invite)")
    language: str = Field(..., description="Language of the content (e.g., en, es, fr, ja)")
    
    # Article metadata
    title: Optional[str] = Field(None, description="Article title")
    author: Optional[str] = Field(None, description="Article author")
    medium: Optional[str] = Field(None, description="Publication medium")
    domain: str = Field(..., description="Article domain")
    published_date: Optional[datetime] = Field(None, description="Article publish date")
    
    # Processing metadata
    evaluated_at: datetime = Field(..., description="When evaluation was performed")
    word_count: int = Field(..., ge=0, description="Article word count")
    truncated: bool = Field(default=False, description="Whether content was truncated")
    error: Optional[str] = Field(None, description="Error message if evaluation failed")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            HttpUrl: str
        }
    }