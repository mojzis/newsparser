"""Tests for post filtering utilities."""

from datetime import datetime
import pytest

from src.models.post import BlueskyPost, EngagementMetrics
from src.utils.language_detection import LanguageType
from src.utils.filtering import (
    filter_posts_by_language,
    get_language_statistics,
    PostLanguageFilter,
    FilterResult,
    create_default_language_filter,
    filter_latin_posts_only,
    filter_exclude_unknown_language,
    validate_language_filter_criteria
)


def create_test_post(content: str, language: LanguageType = LanguageType.LATIN, 
                    has_links: bool = False, has_tags: bool = False) -> BlueskyPost:
    """Helper to create test posts."""
    return BlueskyPost(
        id=f"test_{hash(content)}",
        author="test_user",
        content=content,
        created_at=datetime.now(),
        links=["https://example.com"] if has_links else [],
        tags=["test"] if has_tags else [],
        language=language,
        engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
    )


class TestLanguageFiltering:
    """Test basic language filtering functions."""
    
    def test_filter_empty_list(self):
        """Test filtering empty list."""
        result = filter_posts_by_language([])
        assert result == []
        
        result = filter_posts_by_language([], include_languages=[LanguageType.LATIN])
        assert result == []
        
        result = filter_posts_by_language([], exclude_languages=[LanguageType.UNKNOWN])
        assert result == []
    
    def test_filter_with_no_criteria(self):
        """Test filtering with no criteria returns all posts."""
        posts = [
            create_test_post("English post", LanguageType.LATIN),
            create_test_post("Mixed post", LanguageType.MIXED),
            create_test_post("Unknown post", LanguageType.UNKNOWN)
        ]
        
        result = filter_posts_by_language(posts)
        assert len(result) == 3
        assert result == posts
    
    def test_include_languages_filtering(self):
        """Test filtering with include_languages."""
        posts = [
            create_test_post("English post", LanguageType.LATIN),
            create_test_post("Mixed post", LanguageType.MIXED),
            create_test_post("Unknown post", LanguageType.UNKNOWN),
            create_test_post("Another English", LanguageType.LATIN)
        ]
        
        # Include only Latin
        result = filter_posts_by_language(posts, include_languages=[LanguageType.LATIN])
        assert len(result) == 2
        assert all(post.language == LanguageType.LATIN for post in result)
        
        # Include Latin and Mixed
        result = filter_posts_by_language(posts, include_languages=[LanguageType.LATIN, LanguageType.MIXED])
        assert len(result) == 3
        assert all(post.language in [LanguageType.LATIN, LanguageType.MIXED] for post in result)
        
        # Include only Unknown
        result = filter_posts_by_language(posts, include_languages=[LanguageType.UNKNOWN])
        assert len(result) == 1
        assert result[0].language == LanguageType.UNKNOWN
    
    def test_exclude_languages_filtering(self):
        """Test filtering with exclude_languages."""
        posts = [
            create_test_post("English post", LanguageType.LATIN),
            create_test_post("Mixed post", LanguageType.MIXED),
            create_test_post("Unknown post", LanguageType.UNKNOWN),
            create_test_post("Another English", LanguageType.LATIN)
        ]
        
        # Exclude Unknown
        result = filter_posts_by_language(posts, exclude_languages=[LanguageType.UNKNOWN])
        assert len(result) == 3
        assert all(post.language != LanguageType.UNKNOWN for post in result)
        
        # Exclude Mixed and Unknown
        result = filter_posts_by_language(posts, exclude_languages=[LanguageType.MIXED, LanguageType.UNKNOWN])
        assert len(result) == 2
        assert all(post.language == LanguageType.LATIN for post in result)
        
        # Exclude all types
        result = filter_posts_by_language(posts, exclude_languages=[LanguageType.LATIN, LanguageType.MIXED, LanguageType.UNKNOWN])
        assert len(result) == 0
    
    def test_conflicting_criteria_error(self):
        """Test that specifying both include and exclude raises error."""
        posts = [create_test_post("Test", LanguageType.LATIN)]
        
        with pytest.raises(ValueError, match="Cannot specify both include_languages and exclude_languages"):
            filter_posts_by_language(
                posts, 
                include_languages=[LanguageType.LATIN],
                exclude_languages=[LanguageType.UNKNOWN]
            )


class TestLanguageStatistics:
    """Test language statistics functions."""
    
    def test_empty_posts_statistics(self):
        """Test statistics for empty post list."""
        stats = get_language_statistics([])
        assert stats == {}
    
    def test_single_language_statistics(self):
        """Test statistics for posts with single language."""
        posts = [
            create_test_post("Post 1", LanguageType.LATIN),
            create_test_post("Post 2", LanguageType.LATIN),
            create_test_post("Post 3", LanguageType.LATIN)
        ]
        
        stats = get_language_statistics(posts)
        assert stats == {"latin": 3}
    
    def test_mixed_language_statistics(self):
        """Test statistics for posts with multiple languages."""
        posts = [
            create_test_post("English 1", LanguageType.LATIN),
            create_test_post("English 2", LanguageType.LATIN),
            create_test_post("Mixed", LanguageType.MIXED),
            create_test_post("Unknown 1", LanguageType.UNKNOWN),
            create_test_post("Unknown 2", LanguageType.UNKNOWN),
            create_test_post("Unknown 3", LanguageType.UNKNOWN)
        ]
        
        stats = get_language_statistics(posts)
        expected = {"latin": 2, "mixed": 1, "unknown": 3}
        assert stats == expected


class TestPostLanguageFilter:
    """Test the PostLanguageFilter class."""
    
    def test_filter_initialization(self):
        """Test filter initialization with various parameters."""
        # Default filter
        filter1 = PostLanguageFilter()
        assert filter1.include_languages is None
        assert filter1.exclude_languages is None
        assert filter1.min_content_length is None
        assert filter1.max_content_length is None
        assert filter1.require_links is None
        assert filter1.require_tags is None
        
        # Filter with language criteria
        filter2 = PostLanguageFilter(include_languages=[LanguageType.LATIN])
        assert filter2.include_languages == [LanguageType.LATIN]
        
        # Filter with content length criteria
        filter3 = PostLanguageFilter(min_content_length=10, max_content_length=100)
        assert filter3.min_content_length == 10
        assert filter3.max_content_length == 100
        
        # Filter with link/tag requirements
        filter4 = PostLanguageFilter(require_links=True, require_tags=False)
        assert filter4.require_links is True
        assert filter4.require_tags is False
    
    def test_filter_initialization_error(self):
        """Test that conflicting language criteria raise error."""
        with pytest.raises(ValueError, match="Cannot specify both include_languages and exclude_languages"):
            PostLanguageFilter(
                include_languages=[LanguageType.LATIN],
                exclude_languages=[LanguageType.UNKNOWN]
            )
    
    def test_language_only_filtering(self):
        """Test filtering with only language criteria."""
        posts = [
            create_test_post("English", LanguageType.LATIN),
            create_test_post("Mixed", LanguageType.MIXED),
            create_test_post("Unknown", LanguageType.UNKNOWN)
        ]
        
        # Include filter
        filter_include = PostLanguageFilter(include_languages=[LanguageType.LATIN])
        result = filter_include.filter(posts)
        assert len(result) == 1
        assert result[0].language == LanguageType.LATIN
        
        # Exclude filter
        filter_exclude = PostLanguageFilter(exclude_languages=[LanguageType.UNKNOWN])
        result = filter_exclude.filter(posts)
        assert len(result) == 2
        assert all(post.language != LanguageType.UNKNOWN for post in result)
    
    def test_content_length_filtering(self):
        """Test filtering by content length."""
        posts = [
            create_test_post("Short", LanguageType.LATIN),  # 5 chars
            create_test_post("Medium length content", LanguageType.LATIN),  # 20 chars
            create_test_post("This is a very long piece of content for testing", LanguageType.LATIN)  # 49 chars
        ]
        
        # Minimum length filter
        filter_min = PostLanguageFilter(min_content_length=10)
        result = filter_min.filter(posts)
        assert len(result) == 2
        assert all(len(post.content) >= 10 for post in result)
        
        # Maximum length filter
        filter_max = PostLanguageFilter(max_content_length=25)
        result = filter_max.filter(posts)
        assert len(result) == 2
        assert all(len(post.content) <= 25 for post in result)
        
        # Range filter
        filter_range = PostLanguageFilter(min_content_length=10, max_content_length=25)
        result = filter_range.filter(posts)
        assert len(result) == 1
        assert 10 <= len(result[0].content) <= 25
    
    def test_links_requirement_filtering(self):
        """Test filtering by link requirements."""
        posts = [
            create_test_post("No links", has_links=False),
            create_test_post("Has links", has_links=True),
            create_test_post("Also no links", has_links=False)
        ]
        
        # Require links
        filter_require = PostLanguageFilter(require_links=True)
        result = filter_require.filter(posts)
        assert len(result) == 1
        assert len(result[0].links) > 0
        
        # Require no links
        filter_no_links = PostLanguageFilter(require_links=False)
        result = filter_no_links.filter(posts)
        assert len(result) == 2
        assert all(len(post.links) == 0 for post in result)
    
    def test_tags_requirement_filtering(self):
        """Test filtering by tag requirements."""
        posts = [
            create_test_post("No tags", has_tags=False),
            create_test_post("Has tags", has_tags=True),
            create_test_post("Also no tags", has_tags=False)
        ]
        
        # Require tags
        filter_require = PostLanguageFilter(require_tags=True)
        result = filter_require.filter(posts)
        assert len(result) == 1
        assert len(result[0].tags) > 0
        
        # Require no tags
        filter_no_tags = PostLanguageFilter(require_tags=False)
        result = filter_no_tags.filter(posts)
        assert len(result) == 2
        assert all(len(post.tags) == 0 for post in result)
    
    def test_combined_filtering_criteria(self):
        """Test filtering with multiple criteria combined."""
        posts = [
            create_test_post("Short", LanguageType.LATIN, has_links=False, has_tags=False),
            create_test_post("Medium length with links", LanguageType.LATIN, has_links=True, has_tags=False),
            create_test_post("Long content with tags and links", LanguageType.LATIN, has_links=True, has_tags=True),
            create_test_post("Mixed language medium", LanguageType.MIXED, has_links=False, has_tags=True),
            create_test_post("Unknown long content", LanguageType.UNKNOWN, has_links=True, has_tags=True)
        ]
        
        # Complex filter: Latin language, min 10 chars, requires links
        complex_filter = PostLanguageFilter(
            include_languages=[LanguageType.LATIN],
            min_content_length=10,
            require_links=True
        )
        result = complex_filter.filter(posts)
        assert len(result) == 2
        for post in result:
            assert post.language == LanguageType.LATIN
            assert len(post.content) >= 10
            assert len(post.links) > 0
    
    def test_filter_and_report(self):
        """Test the filter_and_report method."""
        posts = [
            create_test_post("English 1", LanguageType.LATIN),
            create_test_post("English 2", LanguageType.LATIN),
            create_test_post("Mixed", LanguageType.MIXED),
            create_test_post("Unknown", LanguageType.UNKNOWN)
        ]
        
        filter_obj = PostLanguageFilter(exclude_languages=[LanguageType.UNKNOWN])
        result = filter_obj.filter_and_report(posts)
        
        assert isinstance(result, FilterResult)
        assert result.original_count == 4
        assert result.filtered_count == 3
        assert result.removed_count == 1
        assert result.removal_percentage == 25.0
        assert result.retention_percentage == 75.0
        
        assert "latin" in result.language_stats
        assert "mixed" in result.language_stats
        assert "unknown" in result.language_stats
        assert result.language_stats["latin"] == 2
        assert result.language_stats["mixed"] == 1
        assert result.language_stats["unknown"] == 1
        
        assert result.filter_criteria["exclude_languages"] == ["unknown"]
        assert result.filter_criteria["include_languages"] is None


class TestFilterResult:
    """Test the FilterResult dataclass."""
    
    def test_filter_result_properties(self):
        """Test FilterResult property calculations."""
        # Test normal case
        result = FilterResult(
            filtered_posts=[],
            original_count=100,
            filtered_count=75,
            removed_count=25,
            language_stats={"latin": 75, "unknown": 25},
            filter_criteria={}
        )
        
        assert result.removal_percentage == 25.0
        assert result.retention_percentage == 75.0
        
        # Test edge case with no posts
        empty_result = FilterResult(
            filtered_posts=[],
            original_count=0,
            filtered_count=0,
            removed_count=0,
            language_stats={},
            filter_criteria={}
        )
        
        assert empty_result.removal_percentage == 0.0
        assert empty_result.retention_percentage == 100.0
        
        # Test case with all posts removed
        all_removed = FilterResult(
            filtered_posts=[],
            original_count=50,
            filtered_count=0,
            removed_count=50,
            language_stats={"unknown": 50},
            filter_criteria={}
        )
        
        assert all_removed.removal_percentage == 100.0
        assert all_removed.retention_percentage == 0.0


class TestConvenienceFunctions:
    """Test convenience filtering functions."""
    
    def test_create_default_language_filter(self):
        """Test default filter creation."""
        # Default excludes unknown
        default_filter = create_default_language_filter()
        assert default_filter.exclude_languages == [LanguageType.UNKNOWN]
        assert default_filter.include_languages is None
        
        # Option to include unknown
        inclusive_filter = create_default_language_filter(exclude_unknown=False)
        assert inclusive_filter.exclude_languages is None
        assert inclusive_filter.include_languages is None
    
    def test_filter_latin_posts_only(self):
        """Test Latin-only filtering convenience function."""
        posts = [
            create_test_post("English", LanguageType.LATIN),
            create_test_post("Mixed", LanguageType.MIXED),
            create_test_post("Unknown", LanguageType.UNKNOWN)
        ]
        
        result = filter_latin_posts_only(posts)
        assert len(result) == 1
        assert result[0].language == LanguageType.LATIN
    
    def test_filter_exclude_unknown_language(self):
        """Test unknown exclusion convenience function."""
        posts = [
            create_test_post("English", LanguageType.LATIN),
            create_test_post("Mixed", LanguageType.MIXED),
            create_test_post("Unknown", LanguageType.UNKNOWN)
        ]
        
        result = filter_exclude_unknown_language(posts)
        assert len(result) == 2
        assert all(post.language != LanguageType.UNKNOWN for post in result)


class TestValidation:
    """Test validation functions."""
    
    def test_validate_language_filter_criteria_success(self):
        """Test successful validation of filter criteria."""
        # Valid include languages
        assert validate_language_filter_criteria(include_languages=[LanguageType.LATIN])
        
        # Valid exclude languages
        assert validate_language_filter_criteria(exclude_languages=[LanguageType.UNKNOWN])
        
        # No criteria (valid)
        assert validate_language_filter_criteria()
        
        # Multiple valid languages
        assert validate_language_filter_criteria(
            include_languages=[LanguageType.LATIN, LanguageType.MIXED]
        )
    
    def test_validate_language_filter_criteria_errors(self):
        """Test validation errors for invalid criteria."""
        # Both include and exclude specified
        with pytest.raises(ValueError, match="Cannot specify both include_languages and exclude_languages"):
            validate_language_filter_criteria(
                include_languages=[LanguageType.LATIN],
                exclude_languages=[LanguageType.UNKNOWN]
            )
        
        # Invalid language type in include
        with pytest.raises(ValueError, match="Invalid language type"):
            validate_language_filter_criteria(include_languages=["invalid"])
        
        # Invalid language type in exclude
        with pytest.raises(ValueError, match="Invalid language type"):
            validate_language_filter_criteria(exclude_languages=["invalid"])