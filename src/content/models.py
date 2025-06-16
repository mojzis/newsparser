"""Data models for content processing."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ExtractedContent(BaseModel):
    """Content extracted from an article."""
    
    url: HttpUrl
    title: str | None = None
    content_markdown: str = Field(..., description="Article content in Markdown format")
    word_count: int = Field(ge=0, description="Number of words in content")
    language: str | None = Field(default=None, description="Detected language")
    content_type: str | None = Field(default=None, description="Detected content type (video, article, blog post, etc.)")
    domain: str = Field(..., description="Domain of the URL")
    author: str | None = Field(default=None, description="Article author if available")
    medium: str | None = Field(default=None, description="Publication/source name")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"json_encoders": {datetime: lambda v: v.isoformat(), HttpUrl: str}}


class ArticleContent(BaseModel):
    """Raw article content from HTTP fetch."""
    
    url: HttpUrl
    html: str
    status_code: int
    headers: dict[str, Any] = Field(default_factory=dict)
    fetch_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"json_encoders": {datetime: lambda v: v.isoformat(), HttpUrl: str}}


class ContentError(BaseModel):
    """Error information for failed content processing."""
    
    url: HttpUrl
    error_type: str = Field(..., description="Type of error (fetch, extraction, etc.)")
    error_message: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"json_encoders": {datetime: lambda v: v.isoformat(), HttpUrl: str}}