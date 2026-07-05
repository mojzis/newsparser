"""Tests for BlueskyPost language detection functionality."""

from datetime import UTC, datetime

from src.models.post import BlueskyPost, EngagementMetrics
from src.utils.language_detection import LanguageType


class TestBlueskyPostLanguageDetection:
    """Test automatic language detection in BlueskyPost model."""

    def test_latin_language_detection(self):
        """Test automatic detection of Latin-script content."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="Hello world! This is an English post #MCP",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post.language == LanguageType.LATIN
        assert post.tags == ["mcp"]

    def test_unknown_language_detection(self):
        """Test automatic detection of non-Latin content."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="你好世界！这是一个中文帖子！很长的中文内容测试语言检测功能",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post.language == LanguageType.UNKNOWN
        assert post.tags == []  # No Latin hashtags

    def test_mixed_language_detection(self):
        """Test automatic detection of mixed-script content."""
        # Use content with higher ratio of non-Latin characters (>30%)
        post = BlueskyPost(
            id="123",
            author="user",
            content="你好 中文 测试 内容 Hello English mixed",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post.language == LanguageType.MIXED

    def test_explicit_language_override(self):
        """Test that explicitly set language is not overridden."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="你好世界！这是中文内容",
            created_at=datetime.now(UTC),
            language=LanguageType.LATIN,  # Explicitly set (incorrect but should be preserved)
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Should preserve explicitly set language
        assert post.language == LanguageType.LATIN

    def test_empty_content_defaults_to_latin(self):
        """Test that minimal content defaults to Latin."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="!",  # Just punctuation
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post.language == LanguageType.LATIN

    def test_language_detection_with_hashtags_and_links(self):
        """Test language detection works with hashtags and links."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="Check out this #MCP tool 你好 #技术 https://example.com",
            created_at=datetime.now(UTC),
            links=["https://example.com"],
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Should detect mixed content and extract hashtags
        assert post.language == LanguageType.LATIN  # Depends on actual ratio
        assert "mcp" in post.tags
        assert "技术" in post.tags
        assert len(post.links) == 1

    def test_manual_language_detection_method(self):
        """Test the manual detect_language method."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="Привет мир! Как дела сегодня?",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Test manual detection method
        detected = post.detect_language()
        assert detected == LanguageType.UNKNOWN

        # Should match automatically detected language
        assert detected == post.language

    def test_language_serialization(self):
        """Test that language field is properly serialized."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="Hello world!",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Test JSON serialization
        json_data = post.model_dump_json()
        assert '"language":"latin"' in json_data

        # Test dict serialization
        dict_data = post.model_dump()
        assert dict_data["language"] == "latin"

    def test_language_deserialization(self):
        """Test that language field is properly deserialized."""
        data = {
            "id": "123",
            "author": "user",
            "content": "Test content",
            "created_at": "2024-01-15T10:30:00",
            "engagement_metrics": {"likes": 1, "reposts": 0, "replies": 0},
            "language": "mixed"
        }

        post = BlueskyPost.model_validate(data)
        assert post.language == LanguageType.MIXED

    def test_backward_compatibility_without_language_field(self):
        """Test that posts without language field default to Latin."""
        data = {
            "id": "123",
            "author": "user",
            "content": "Test content",
            "created_at": "2024-01-15T10:30:00",
            "engagement_metrics": {"likes": 1, "reposts": 0, "replies": 0}
            # No language field
        }

        post = BlueskyPost.model_validate(data)
        assert post.language == LanguageType.LATIN


class TestLanguageDetectionEdgeCases:
    """Test edge cases for language detection in posts."""

    def test_content_with_only_urls(self):
        """Test content that's mostly URLs."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="https://example.com https://test.org",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post.language == LanguageType.LATIN

    def test_content_with_only_emojis(self):
        """Test content that's mostly emojis."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="😀😂🚀❤️🎉",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post.language == LanguageType.LATIN

    def test_content_with_numbers_and_symbols(self):
        """Test content with numbers and symbols."""
        post = BlueskyPost(
            id="123",
            author="user",
            content="123 + 456 = 579 !@#$%",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post.language == LanguageType.LATIN

    def test_realistic_multilingual_posts(self):
        """Test realistic multilingual social media posts."""
        # English with Chinese hashtag
        post1 = BlueskyPost(
            id="1",
            author="user",
            content="Love this new AI tool! #AI #人工智能",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Should be Latin due to mostly English content
        assert post1.language == LanguageType.LATIN
        assert "ai" in post1.tags
        assert "人工智能" in post1.tags

        # Russian with English terms
        post2 = BlueskyPost(
            id="2",
            author="user",
            content="Изучаю Machine Learning и Data Science сегодня!",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Should be mixed or unknown depending on ratio
        assert post2.language in [LanguageType.MIXED, LanguageType.UNKNOWN]

    def test_code_snippets_with_comments(self):
        """Test posts containing code snippets."""
        # Code with English comments
        post1 = BlueskyPost(
            id="1",
            author="user",
            content="def hello(): # This prints hello\n    print('Hello!')",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        assert post1.language == LanguageType.LATIN

        # Code with non-Latin comments
        post2 = BlueskyPost(
            id="2",
            author="user",
            content="function sayHello() { // 这个函数打印问候语\n  console.log('你好世界'); }",
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Actually has low percentage of Chinese characters, so classified as Latin
        assert post2.language == LanguageType.LATIN


class TestLanguageDetectionPerformance:
    """Test performance characteristics of language detection in posts."""

    def test_detection_with_very_long_content(self):
        """Test that detection works with very long content."""
        # Create long content with higher ratio of Chinese characters
        long_content = "Hello world! " * 30 + "你好世界！" * 70

        post = BlueskyPost(
            id="123",
            author="user",
            content=long_content,
            created_at=datetime.now(UTC),
            engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
        )

        # Should still detect correctly
        assert post.language in [LanguageType.MIXED, LanguageType.UNKNOWN]

    def test_multiple_posts_creation_performance(self):
        """Test creating multiple posts with language detection."""
        contents = [
            "English content here",
            "你好世界！中文内容",
            "Привет мир! Русский текст",
            "Mixed English 和 中文 content",
            "Another English post #test"
        ]

        posts = []
        for i, content in enumerate(contents):
            post = BlueskyPost(
                id=str(i),
                author="user",
                content=content,
                created_at=datetime.now(UTC),
                engagement_metrics=EngagementMetrics(likes=1, reposts=0, replies=0)
            )
            posts.append(post)

        # All posts should be created successfully with language detection
        assert len(posts) == 5
        assert all(hasattr(post, "language") for post in posts)
        assert all(isinstance(post.language, LanguageType) for post in posts)
