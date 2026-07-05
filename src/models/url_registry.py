"""URL registry models for tracking unique URLs across collections."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class URLEntry(BaseModel):
    """Single URL entry in the registry."""

    url: HttpUrl = Field(..., description="The URL")
    first_seen: datetime = Field(..., description="When URL was first seen")
    published_date: datetime | None = Field(
        None, description="Article publish date if known"
    )
    first_post_id: str = Field(..., description="ID of first post containing this URL")
    first_post_author: str = Field(..., description="Author of first post")
    times_seen: int = Field(default=1, ge=1, description="Number of times URL was seen")
    last_updated: datetime = Field(..., description="Last time this entry was updated")

    # Evaluation tracking
    evaluated: bool = Field(default=False, description="Whether URL has been evaluated")
    evaluated_at: datetime | None = Field(None, description="When URL was evaluated")
    is_mcp_related: bool | None = Field(
        None, description="Whether article is MCP-related"
    )
    relevance_score: float | None = Field(
        None, ge=0.0, le=1.0, description="MCP relevance score"
    )
