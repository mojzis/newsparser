import re
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import Any

from src.utils.language_detection import LanguageType, detect_language_from_text


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
    tags: list[str] = Field(
        default_factory=list, description="Hashtags extracted from post content"
    )
    language: LanguageType = Field(
        default=LanguageType.LATIN, description="Detected language type based on character analysis"
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

    @model_validator(mode="before")
    @classmethod
    def detect_language_if_not_provided(cls, data: Any) -> Any:
        """Detect language from content if language field is not provided."""
        if isinstance(data, dict):
            # Only detect language if not explicitly provided
            if "language" not in data and "content" in data:
                content = data["content"]
                if content:
                    detected_language = detect_language_from_text(content)
                    data["language"] = detected_language
        return data
    
    @model_validator(mode="after")
    def extract_tags_from_content(self) -> "BlueskyPost":
        """Extract hashtags from content if not explicitly provided."""
        # Extract hashtags if not already populated
        if not self.tags and self.content:
            # Find hashtags (# followed by word characters)
            hashtag_pattern = r'#(\w+)'
            hashtags = re.findall(hashtag_pattern, self.content, re.IGNORECASE)
            
            # Remove duplicates and convert to lowercase for consistency
            unique_tags = list(dict.fromkeys(tag.lower() for tag in hashtags))
            
            # Update tags field
            self.tags = unique_tags
        
        return self

    @staticmethod
    def extract_hashtags_from_text(text: str) -> list[str]:
        """Utility method to extract hashtags from any text."""
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
        return list(dict.fromkeys(tag.lower() for tag in hashtags))

    def detect_language(self) -> LanguageType:
        """Manually detect language from post content."""
        return detect_language_from_text(self.content)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(), 
            HttpUrl: str,
            LanguageType: str
        }
