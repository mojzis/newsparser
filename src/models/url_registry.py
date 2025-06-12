"""URL registry models for tracking unique URLs across collections."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class URLEntry(BaseModel):
    """Single URL entry in the registry."""
    
    url: HttpUrl = Field(..., description="The URL")
    first_seen: datetime = Field(..., description="When URL was first seen")
    published_date: Optional[datetime] = Field(None, description="Article publish date if known")
    first_post_id: str = Field(..., description="ID of first post containing this URL")
    first_post_author: str = Field(..., description="Author of first post")
    times_seen: int = Field(default=1, ge=1, description="Number of times URL was seen")
    last_updated: datetime = Field(..., description="Last time this entry was updated")
    
    # Evaluation tracking
    evaluated: bool = Field(default=False, description="Whether URL has been evaluated")
    evaluated_at: Optional[datetime] = Field(None, description="When URL was evaluated")
    is_mcp_related: Optional[bool] = Field(None, description="Whether article is MCP-related")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="MCP relevance score")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            HttpUrl: str
        }
    }