"""URL registry utilities for managing URL tracking."""

from datetime import datetime
from typing import Optional

import pandas as pd
from pydantic import HttpUrl

from src.models.url_registry import URLEntry


def normalize_url(url: str | HttpUrl) -> str:
    """Normalize URL for consistent comparison."""
    url_str = str(url)
    # Remove trailing slash if it's just the domain
    if url_str.endswith('/') and url_str.count('/') == 3:  # e.g., https://example.com/
        url_str = url_str[:-1]
    return url_str


class URLRegistry:
    """Manages URL registry operations using pandas DataFrame."""
    
    def __init__(self, df: Optional[pd.DataFrame] = None):
        """Initialize registry with optional existing DataFrame."""
        if df is None:
            self.df = pd.DataFrame(columns=[
                'url', 'first_seen', 'published_date', 
                'first_post_id', 'first_post_author', 
                'times_seen', 'last_updated',
                'evaluated', 'evaluated_at', 'is_mcp_related', 'relevance_score'
            ])
        else:
            self.df = df
            # Add new columns if missing (for backward compatibility)
            for col in ['evaluated', 'evaluated_at', 'is_mcp_related', 'relevance_score']:
                if col not in self.df.columns:
                    if col == 'evaluated':
                        self.df[col] = False
                    else:
                        self.df[col] = None
        
        # Ensure URL column is string type for indexing
        if not self.df.empty:
            self.df['url'] = self.df['url'].astype(str)
    
    def add_url(self, url: str | HttpUrl, post_id: str, author: str) -> bool:
        """Add URL to registry or increment times_seen. Returns True if new URL."""
        url_str = normalize_url(url)
        now = datetime.now()
        
        # Check if URL exists
        if not self.df.empty and (self.df['url'] == url_str).any():
            # Update existing entry
            idx = self.df[self.df['url'] == url_str].index[0]
            self.df.at[idx, 'times_seen'] += 1
            self.df.at[idx, 'last_updated'] = now
            return False
        else:
            # Add new entry - use original URL for storage
            new_entry = URLEntry(
                url=url,
                first_seen=now,
                first_post_id=post_id,
                first_post_author=author,
                last_updated=now
            )
            
            # Convert to dict and normalize URL
            entry_dict = new_entry.model_dump()
            entry_dict['url'] = url_str  # Store normalized URL
            
            new_row = pd.DataFrame([entry_dict])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            # Ensure URL column remains string type
            self.df['url'] = self.df['url'].astype(str)
            return True
    
    def contains_url(self, url: str | HttpUrl) -> bool:
        """Check if URL exists in registry."""
        url_str = normalize_url(url)
        if self.df.empty:
            return False
        return bool((self.df['url'] == url_str).any())
    
    def is_evaluated(self, url: str | HttpUrl) -> bool:
        """Check if URL has been evaluated."""
        url_str = normalize_url(url)
        if self.df.empty:
            return False
        
        mask = self.df['url'] == url_str
        if mask.any():
            return bool(self.df.loc[mask, 'evaluated'].iloc[0])
        return False
    
    def mark_evaluated(
        self, 
        url: str | HttpUrl, 
        is_mcp_related: bool,
        relevance_score: float
    ) -> None:
        """Mark URL as evaluated with results."""
        url_str = normalize_url(url)
        now = datetime.now()
        
        if not self.df.empty and (self.df['url'] == url_str).any():
            idx = self.df[self.df['url'] == url_str].index[0]
            self.df.at[idx, 'evaluated'] = True
            self.df.at[idx, 'evaluated_at'] = now
            self.df.at[idx, 'is_mcp_related'] = is_mcp_related
            self.df.at[idx, 'relevance_score'] = relevance_score
            self.df.at[idx, 'last_updated'] = now
    
    def get_stats(self) -> dict:
        """Get registry statistics."""
        if self.df.empty:
            return {
                'total_urls': 0,
                'total_occurrences': 0,
                'unique_domains': 0,
                'evaluated_urls': 0,
                'mcp_related_urls': 0,
                'avg_relevance_score': 0.0
            }
        
        # Extract domains
        domains = self.df['url'].apply(lambda x: x.split('/')[2] if '://' in x else '')
        
        # Calculate evaluation stats
        evaluated = self.df['evaluated'].sum()
        mcp_related = self.df[self.df['is_mcp_related'] == True].shape[0]
        avg_relevance = self.df[self.df['evaluated'] == True]['relevance_score'].mean()
        
        return {
            'total_urls': len(self.df),
            'total_occurrences': self.df['times_seen'].sum(),
            'unique_domains': domains.nunique(),
            'evaluated_urls': int(evaluated),
            'mcp_related_urls': int(mcp_related),
            'avg_relevance_score': float(avg_relevance) if not pd.isna(avg_relevance) else 0.0
        }
    
    def to_parquet(self, path: str) -> None:
        """Save registry to Parquet file."""
        self.df.to_parquet(path, index=False)
    
    @classmethod
    def from_parquet(cls, path: str) -> 'URLRegistry':
        """Load registry from Parquet file."""
        df = pd.read_parquet(path)
        return cls(df)