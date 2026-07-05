"""Fetch stage models."""

from datetime import datetime
from typing import Literal

from pydantic import Field, HttpUrl

from src.models.analytics import AnalyticsBase

FetchStatus = Literal["success", "error"]


class FetchResult(AnalyticsBase):
    """Result of fetching and extracting content from a URL."""

    url: HttpUrl = Field(..., description="The URL that was fetched")
    fetched_at: datetime = Field(..., description="When the fetch was performed")
    fetch_status: FetchStatus = Field(..., description="Status of the fetch operation")
    stage: str = Field(default="fetched", description="Processing stage")

    # Success fields
    word_count: int | None = Field(None, ge=0, description="Number of words in extracted content")
    title: str | None = Field(None, description="Article title")
    author: str | None = Field(None, description="Article author")
    domain: str = Field(..., description="Domain of the URL")
    medium: str | None = Field(None, description="Publication medium")
    language: str | None = Field(None, description="Detected language")
    extraction_timestamp: datetime | None = Field(None, description="When content was extracted")

    # Error fields
    error_type: str | None = Field(None, description="Type of error if fetch failed")
    error_message: str | None = Field(None, description="Error message if fetch failed")

    # Metadata
    found_in_posts: list[str] = Field(default_factory=list, description="Post IDs where this URL was found")

    def to_pandas_dict(self) -> dict:
        """Convert to pandas-friendly dictionary."""
        result = super().to_pandas_dict()

        # Convert found_in_posts list to comma-separated string for easier analysis
        if result.get("found_in_posts"):
            result["found_in_posts_str"] = ",".join(result["found_in_posts"])
            result["found_in_posts_count"] = len(result["found_in_posts"])
        else:
            result["found_in_posts_str"] = None
            result["found_in_posts_count"] = 0

        return result
