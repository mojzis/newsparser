from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class EngagementMetrics(BaseModel):
    likes: int = Field(ge=0, description="Number of likes on the post")
    reposts: int = Field(ge=0, description="Number of reposts/reblogs")
    replies: int = Field(ge=0, description="Number of replies to the post")


class BlueskyPost(BaseModel):
    id: str = Field(..., description="Unique identifier for the post")
    author: str = Field(..., description="Author handle/username")
    content: str = Field(..., min_length=1, description="Post content text")
    created_at: datetime = Field(..., description="When the post was created")
    links: list[HttpUrl] = Field(
        default_factory=list, description="Article links found in the post"
    )
    engagement_metrics: EngagementMetrics = Field(
        ..., description="Engagement statistics"
    )

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Post content cannot be empty or whitespace only")
        return v

    @field_validator("links")
    @classmethod
    def validate_links(cls, v: list[HttpUrl]) -> list[HttpUrl]:
        return [link for link in v if link is not None]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), HttpUrl: str}
