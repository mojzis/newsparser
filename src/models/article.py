from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ArticleEvaluation(BaseModel):
    url: HttpUrl = Field(..., description="URL of the evaluated article")
    title: str | None = Field(None, description="Article title")
    content_summary: str = Field(
        ..., max_length=500, description="Brief summary of the article content"
    )
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="MCP relevance score from 0.0 to 1.0"
    )
    key_topics: list[str] = Field(
        ..., min_items=1, description="Key MCP-related topics identified in the article"
    )
    evaluation_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the evaluation was performed"
    )

    @field_validator("content_summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content summary cannot be empty or whitespace only")
        return v

    @field_validator("key_topics")
    @classmethod
    def validate_topics(cls, v: list[str]) -> list[str]:
        cleaned_topics = [topic.strip() for topic in v if topic.strip()]
        if not cleaned_topics:
            raise ValueError("At least one non-empty topic is required")
        return cleaned_topics

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), HttpUrl: str}
