import re
from datetime import datetime
from typing import Any, Optional, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from src.utils.language_detection import LanguageType, detect_language_from_text
from src.models.analytics import AnalyticsBase

ThreadPosition = Literal["root", "reply", "nested_reply"]


class EngagementMetrics(BaseModel):
    likes: int = Field(ge=0, description="Number of likes on the post")
    reposts: int = Field(ge=0, description="Number of reposts/reblogs")
    replies: int = Field(ge=0, description="Number of replies to the post")


class BlueskyPost(AnalyticsBase):
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
    
    # Thread relationship fields
    thread_root_uri: Optional[str] = Field(
        default=None, description="URI of the root post in this thread"
    )
    thread_position: Optional[ThreadPosition] = Field(
        default=None, description="Position of this post within the thread"
    )
    parent_post_uri: Optional[str] = Field(
        default=None, description="URI of the direct parent post (for replies)"
    )
    thread_depth: Optional[int] = Field(
        default=None, ge=0, description="Nesting level within the thread (0=root)"
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
    
    def is_thread_root(self) -> bool:
        """Check if this post is the root of a thread."""
        return self.thread_position == "root"
    
    def is_reply(self) -> bool:
        """Check if this post is a reply to another post."""
        return self.thread_position in ("reply", "nested_reply")
    
    def set_thread_metadata(
        self, 
        root_uri: str, 
        position: ThreadPosition, 
        depth: int,
        parent_uri: Optional[str] = None
    ) -> "BlueskyPost":
        """Set thread relationship metadata for this post."""
        self.thread_root_uri = root_uri
        self.thread_position = position
        self.thread_depth = depth
        self.parent_post_uri = parent_uri
        return self

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(), 
            HttpUrl: str,
            LanguageType: str
        }
