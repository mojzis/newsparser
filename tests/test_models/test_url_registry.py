"""Tests for URL registry models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.url_registry import URLEntry


class TestURLEntry:
    """Test URLEntry model."""
    
    def test_url_entry_creation(self):
        """Test creating a URL entry with all fields."""
        now = datetime.now()
        entry = URLEntry(
            url="https://example.com/article",
            first_seen=now,
            published_date=now,
            first_post_id="123",
            first_post_author="@user.bsky.social",
            times_seen=1,
            last_updated=now
        )
        
        assert str(entry.url) == "https://example.com/article"
        assert entry.first_seen == now
        assert entry.published_date == now
        assert entry.first_post_id == "123"
        assert entry.first_post_author == "@user.bsky.social"
        assert entry.times_seen == 1
        assert entry.last_updated == now
    
    def test_url_entry_minimal(self):
        """Test creating URL entry with minimal required fields."""
        now = datetime.now()
        entry = URLEntry(
            url="https://example.com",
            first_seen=now,
            first_post_id="123",
            first_post_author="@user.bsky.social",
            last_updated=now
        )
        
        assert entry.published_date is None
        assert entry.times_seen == 1  # Default value
    
    def test_url_entry_validation(self):
        """Test URL entry validation."""
        now = datetime.now()
        
        # Invalid URL
        with pytest.raises(ValidationError):
            URLEntry(
                url="not-a-url",
                first_seen=now,
                first_post_id="123",
                first_post_author="@user",
                last_updated=now
            )
        
        # Missing required fields
        with pytest.raises(ValidationError):
            URLEntry(url="https://example.com")
        
        # Invalid times_seen
        with pytest.raises(ValidationError):
            URLEntry(
                url="https://example.com",
                first_seen=now,
                first_post_id="123",
                first_post_author="@user",
                times_seen=0,  # Must be >= 1
                last_updated=now
            )
    
    def test_url_entry_serialization(self):
        """Test URL entry serialization."""
        now = datetime.now()
        entry = URLEntry(
            url="https://example.com/article",
            first_seen=now,
            first_post_id="123",
            first_post_author="@user",
            last_updated=now
        )
        
        # Test dict serialization
        data = entry.model_dump()
        assert str(data["url"]) == "https://example.com/article"
        assert data["times_seen"] == 1
        assert data["published_date"] is None
        
        # Test JSON serialization
        json_data = entry.model_dump_json()
        assert '"url":"https://example.com/article"' in json_data
        assert '"times_seen":1' in json_data