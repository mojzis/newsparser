"""
Post filtering utilities with language support.

This module provides filtering capabilities for BlueskyPost objects
based on language detection and other criteria.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.models.post import BlueskyPost
from src.utils.language_detection import LanguageType


@dataclass
class FilterResult:
    """Result of filtering operation with statistics."""
    
    filtered_posts: List[BlueskyPost]
    original_count: int
    filtered_count: int
    removed_count: int
    language_stats: Dict[str, int]
    filter_criteria: Dict[str, Any]
    
    @property
    def removal_percentage(self) -> float:
        """Percentage of posts removed by filtering."""
        if self.original_count == 0:
            return 0.0
        return (self.removed_count / self.original_count) * 100
    
    @property
    def retention_percentage(self) -> float:
        """Percentage of posts retained after filtering."""
        return 100.0 - self.removal_percentage


def filter_posts_by_language(
    posts: List[BlueskyPost], 
    include_languages: Optional[List[LanguageType]] = None,
    exclude_languages: Optional[List[LanguageType]] = None
) -> List[BlueskyPost]:
    """
    Filter posts based on detected language types.
    
    Args:
        posts: List of BlueskyPost objects to filter
        include_languages: Only include posts with these language types
        exclude_languages: Exclude posts with these language types
        
    Returns:
        Filtered list of BlueskyPost objects
        
    Raises:
        ValueError: If both include and exclude languages are specified
    """
    if not posts:
        return []
    
    if include_languages and exclude_languages:
        raise ValueError("Cannot specify both include_languages and exclude_languages")
    
    if include_languages:
        return [post for post in posts if post.language in include_languages]
    
    if exclude_languages:
        return [post for post in posts if post.language not in exclude_languages]
    
    # No filtering criteria specified, return all posts
    return posts


def get_language_statistics(posts: List[BlueskyPost]) -> Dict[str, int]:
    """
    Get language distribution statistics for a list of posts.
    
    Args:
        posts: List of BlueskyPost objects to analyze
        
    Returns:
        Dictionary mapping language types to counts
    """
    stats = {}
    
    for post in posts:
        language = post.language.value if hasattr(post.language, 'value') else str(post.language)
        stats[language] = stats.get(language, 0) + 1
    
    return stats


class PostLanguageFilter:
    """Advanced filtering with statistics tracking and multiple criteria support."""
    
    def __init__(
        self,
        include_languages: Optional[List[LanguageType]] = None,
        exclude_languages: Optional[List[LanguageType]] = None,
        min_content_length: Optional[int] = None,
        max_content_length: Optional[int] = None,
        require_links: Optional[bool] = None,
        require_tags: Optional[bool] = None
    ):
        """
        Initialize the filter with criteria.
        
        Args:
            include_languages: Only include posts with these language types
            exclude_languages: Exclude posts with these language types
            min_content_length: Minimum content length in characters
            max_content_length: Maximum content length in characters
            require_links: If True, only include posts with links
            require_tags: If True, only include posts with hashtags
            
        Raises:
            ValueError: If both include and exclude languages are specified
        """
        if include_languages and exclude_languages:
            raise ValueError("Cannot specify both include_languages and exclude_languages")
        
        self.include_languages = include_languages
        self.exclude_languages = exclude_languages
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length
        self.require_links = require_links
        self.require_tags = require_tags
    
    def filter(self, posts: List[BlueskyPost]) -> List[BlueskyPost]:
        """
        Apply all filter criteria to posts.
        
        Args:
            posts: List of posts to filter
            
        Returns:
            Filtered list of posts
        """
        if not posts:
            return []
        
        filtered = posts
        
        # Apply language filtering
        if self.include_languages:
            filtered = [post for post in filtered if post.language in self.include_languages]
        elif self.exclude_languages:
            filtered = [post for post in filtered if post.language not in self.exclude_languages]
        
        # Apply content length filtering
        if self.min_content_length is not None:
            filtered = [post for post in filtered if len(post.content) >= self.min_content_length]
        
        if self.max_content_length is not None:
            filtered = [post for post in filtered if len(post.content) <= self.max_content_length]
        
        # Apply link requirement filtering
        if self.require_links is not None:
            if self.require_links:
                filtered = [post for post in filtered if len(post.links) > 0]
            else:
                filtered = [post for post in filtered if len(post.links) == 0]
        
        # Apply tag requirement filtering
        if self.require_tags is not None:
            if self.require_tags:
                filtered = [post for post in filtered if len(post.tags) > 0]
            else:
                filtered = [post for post in filtered if len(post.tags) == 0]
        
        return filtered
    
    def filter_and_report(self, posts: List[BlueskyPost]) -> FilterResult:
        """
        Filter posts and return detailed statistics.
        
        Args:
            posts: List of posts to filter
            
        Returns:
            FilterResult with filtered posts and statistics
        """
        original_count = len(posts)
        original_stats = get_language_statistics(posts)
        
        filtered_posts = self.filter(posts)
        filtered_count = len(filtered_posts)
        removed_count = original_count - filtered_count
        
        filter_criteria = {
            "include_languages": [lang.value for lang in self.include_languages] if self.include_languages else None,
            "exclude_languages": [lang.value for lang in self.exclude_languages] if self.exclude_languages else None,
            "min_content_length": self.min_content_length,
            "max_content_length": self.max_content_length,
            "require_links": self.require_links,
            "require_tags": self.require_tags
        }
        
        return FilterResult(
            filtered_posts=filtered_posts,
            original_count=original_count,
            filtered_count=filtered_count,
            removed_count=removed_count,
            language_stats=original_stats,
            filter_criteria=filter_criteria
        )


def create_default_language_filter(exclude_unknown: bool = True) -> PostLanguageFilter:
    """
    Create a default language filter that excludes unknown languages.
    
    Args:
        exclude_unknown: If True, exclude posts with unknown language
        
    Returns:
        Configured PostLanguageFilter instance
    """
    if exclude_unknown:
        return PostLanguageFilter(exclude_languages=[LanguageType.UNKNOWN])
    else:
        return PostLanguageFilter()


def filter_latin_posts_only(posts: List[BlueskyPost]) -> List[BlueskyPost]:
    """
    Convenience function to filter only Latin-script posts.
    
    Args:
        posts: List of posts to filter
        
    Returns:
        Posts with only Latin language type
    """
    return filter_posts_by_language(posts, include_languages=[LanguageType.LATIN])


def filter_exclude_unknown_language(posts: List[BlueskyPost]) -> List[BlueskyPost]:
    """
    Convenience function to exclude posts with unknown languages.
    
    Args:
        posts: List of posts to filter
        
    Returns:
        Posts excluding unknown language type
    """
    return filter_posts_by_language(posts, exclude_languages=[LanguageType.UNKNOWN])


def print_language_statistics(posts: List[BlueskyPost], title: str = "Language Statistics") -> None:
    """
    Print language statistics for a list of posts.
    
    Args:
        posts: List of posts to analyze
        title: Title for the statistics output
    """
    stats = get_language_statistics(posts)
    total = len(posts)
    
    print(f"\n{title}")
    print("=" * len(title))
    print(f"Total posts: {total}")
    
    if total == 0:
        print("No posts to analyze")
        return
    
    for language, count in sorted(stats.items()):
        percentage = (count / total) * 100
        print(f"{language.upper()}: {count:,} ({percentage:.1f}%)")


def validate_language_filter_criteria(
    include_languages: Optional[List[LanguageType]] = None,
    exclude_languages: Optional[List[LanguageType]] = None
) -> bool:
    """
    Validate language filter criteria.
    
    Args:
        include_languages: Languages to include
        exclude_languages: Languages to exclude
        
    Returns:
        True if criteria are valid
        
    Raises:
        ValueError: If criteria are invalid
    """
    if include_languages and exclude_languages:
        raise ValueError("Cannot specify both include_languages and exclude_languages")
    
    if include_languages:
        for lang in include_languages:
            if not isinstance(lang, LanguageType):
                raise ValueError(f"Invalid language type: {lang}")
    
    if exclude_languages:
        for lang in exclude_languages:
            if not isinstance(lang, LanguageType):
                raise ValueError(f"Invalid language type: {lang}")
    
    return True