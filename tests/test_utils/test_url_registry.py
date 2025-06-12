"""Tests for URL registry utilities."""

from datetime import datetime
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.utils.url_registry import URLRegistry


class TestURLRegistry:
    """Test URLRegistry operations."""
    
    def test_empty_registry_creation(self):
        """Test creating an empty registry."""
        registry = URLRegistry()
        assert registry.df.empty
        assert len(registry.df.columns) == 11  # Now includes evaluation fields
        assert 'url' in registry.df.columns
        assert 'first_seen' in registry.df.columns
        assert 'evaluated' in registry.df.columns
        assert 'is_mcp_related' in registry.df.columns
    
    def test_add_new_url(self):
        """Test adding a new URL to registry."""
        registry = URLRegistry()
        
        # Add new URL
        is_new = registry.add_url(
            "https://example.com/article",
            "post123",
            "@user.bsky.social"
        )
        
        assert is_new is True
        assert len(registry.df) == 1
        assert registry.df.iloc[0]['url'] == "https://example.com/article"
        assert registry.df.iloc[0]['first_post_id'] == "post123"
        assert registry.df.iloc[0]['first_post_author'] == "@user.bsky.social"
        assert registry.df.iloc[0]['times_seen'] == 1
    
    def test_add_existing_url(self):
        """Test adding an existing URL increments times_seen."""
        registry = URLRegistry()
        
        # Add URL first time
        registry.add_url("https://example.com", "post1", "@user1")
        
        # Add same URL again
        is_new = registry.add_url("https://example.com", "post2", "@user2")
        
        assert is_new is False
        assert len(registry.df) == 1
        assert registry.df.iloc[0]['times_seen'] == 2
        # Original post info should be preserved
        assert registry.df.iloc[0]['first_post_id'] == "post1"
        assert registry.df.iloc[0]['first_post_author'] == "@user1"
    
    def test_contains_url(self):
        """Test checking if URL exists in registry."""
        registry = URLRegistry()
        
        assert registry.contains_url("https://example.com") is False
        
        registry.add_url("https://example.com", "post1", "@user1")
        
        assert registry.contains_url("https://example.com") is True
        assert registry.contains_url("https://other.com") is False
    
    def test_get_stats_empty(self):
        """Test statistics for empty registry."""
        registry = URLRegistry()
        stats = registry.get_stats()
        
        assert stats['total_urls'] == 0
        assert stats['total_occurrences'] == 0
        assert stats['unique_domains'] == 0
    
    def test_get_stats_with_data(self):
        """Test statistics with data."""
        registry = URLRegistry()
        
        # Add URLs from different domains
        registry.add_url("https://example.com/1", "p1", "@u1")
        registry.add_url("https://example.com/2", "p2", "@u2")
        registry.add_url("https://other.com/1", "p3", "@u3")
        
        # Add duplicate
        registry.add_url("https://example.com/1", "p4", "@u4")
        
        # Mark some as evaluated
        registry.mark_evaluated("https://example.com/1", True, 0.9)
        registry.mark_evaluated("https://example.com/2", False, 0.2)
        
        stats = registry.get_stats()
        
        assert stats['total_urls'] == 3
        assert stats['total_occurrences'] == 4  # 3 unique + 1 duplicate
        assert stats['unique_domains'] == 2  # example.com and other.com
        assert stats['evaluated_urls'] == 2
        assert stats['mcp_related_urls'] == 1
        assert 0.5 <= stats['avg_relevance_score'] <= 0.6  # (0.9 + 0.2) / 2
    
    def test_parquet_save_load(self):
        """Test saving and loading from Parquet."""
        registry = URLRegistry()
        
        # Add some URLs
        registry.add_url("https://example.com/1", "p1", "@u1")
        registry.add_url("https://example.com/2", "p2", "@u2")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            registry.to_parquet(tmp.name)
            
            # Load from file
            loaded_registry = URLRegistry.from_parquet(tmp.name)
            
            # Verify data
            assert len(loaded_registry.df) == 2
            assert loaded_registry.contains_url("https://example.com/1")
            assert loaded_registry.contains_url("https://example.com/2")
            
            # Clean up
            Path(tmp.name).unlink()
    
    def test_url_type_handling(self):
        """Test handling of different URL types."""
        from pydantic import HttpUrl
        
        registry = URLRegistry()
        
        # Test with string URL
        registry.add_url("https://example.com/string", "p1", "@u1")
        
        # Test with HttpUrl object
        http_url = HttpUrl("https://example.com/httpurl")
        registry.add_url(http_url, "p2", "@u2")
        
        assert len(registry.df) == 2
        assert registry.contains_url("https://example.com/string")
        assert registry.contains_url(http_url)
    
    def test_evaluation_tracking(self):
        """Test URL evaluation tracking."""
        registry = URLRegistry()
        
        # Add URL
        registry.add_url("https://example.com/article", "p1", "@u1")
        
        # Check initial state
        assert registry.is_evaluated("https://example.com/article") is False
        
        # Mark as evaluated
        registry.mark_evaluated("https://example.com/article", True, 0.85)
        
        # Check evaluated state
        assert registry.is_evaluated("https://example.com/article") is True
        
        # Check data was updated
        row = registry.df[registry.df['url'] == 'https://example.com/article'].iloc[0]
        assert row['evaluated'] is True
        assert row['is_mcp_related'] is True
        assert row['relevance_score'] == 0.85
        assert row['evaluated_at'] is not None
    
    def test_evaluation_tracking_unknown_url(self):
        """Test evaluation tracking for unknown URL."""
        registry = URLRegistry()
        
        # Check non-existent URL
        assert registry.is_evaluated("https://unknown.com") is False
        
        # Try to mark non-existent URL as evaluated (should not crash)
        registry.mark_evaluated("https://unknown.com", True, 0.5)
        
        # Still not in registry
        assert registry.contains_url("https://unknown.com") is False