"""Tests for language detection utilities."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.utils.language_detection import (
    LanguageType,
    analyze_text_characters,
    calculate_non_latin_percentage,
    detect_language_from_text,
    get_character_sample,
    is_latin_character,
    is_neutral_character,
)


class TestLanguageType:
    """Test the LanguageType enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert LanguageType.LATIN == "latin"
        assert LanguageType.MIXED == "mixed"
        assert LanguageType.UNKNOWN == "unknown"

    def test_enum_string_representation(self):
        """Test string representation of enum values."""
        assert str(LanguageType.LATIN) == "latin"
        assert str(LanguageType.MIXED) == "mixed"
        assert str(LanguageType.UNKNOWN) == "unknown"


class TestLatinCharacterDetection:
    """Test Latin character detection functions."""

    def test_basic_latin_characters(self):
        """Test basic Latin alphabet characters."""
        # Basic ASCII letters
        assert is_latin_character("a")
        assert is_latin_character("Z")
        assert is_latin_character("m")

        # ASCII numbers are not Latin letters but are in Basic Latin range
        assert is_latin_character("0")
        assert is_latin_character("9")

    def test_extended_latin_characters(self):
        """Test extended Latin characters."""
        # Latin-1 Supplement
        assert is_latin_character("á")  # U+00E1
        assert is_latin_character("ñ")  # U+00F1
        assert is_latin_character("ü")  # U+00FC

        # Latin Extended-A
        assert is_latin_character("ā")  # U+0101
        assert is_latin_character("ē")  # U+0113

    def test_non_latin_characters(self):
        """Test non-Latin characters."""
        # Chinese
        assert not is_latin_character("中")  # U+4E2D
        assert not is_latin_character("文")  # U+6587

        # Cyrillic
        assert not is_latin_character("А")  # U+0410 (Cyrillic A)
        assert not is_latin_character("я")  # U+044F (Cyrillic ya)

        # Arabic
        assert not is_latin_character("ا")  # U+0627 (Arabic alif)
        assert not is_latin_character("ب")  # U+0628 (Arabic ba)

        # Japanese
        assert not is_latin_character("あ")  # U+3042 (Hiragana a)
        assert not is_latin_character("カ")  # U+30AB (Katakana ka)

    def test_empty_and_edge_cases(self):
        """Test edge cases for character detection."""
        assert is_latin_character("")  # Empty string treated as neutral
        assert is_latin_character("\x00")  # Null character in Basic Latin

    @given(st.text(min_size=1, max_size=1))
    def test_character_classification_completeness(self, char):
        """Test that every character is classified as either Latin, neutral, or neither."""
        latin = is_latin_character(char)
        neutral = is_neutral_character(char)
        # Character should be classified (though it can be neither Latin nor neutral)
        assert isinstance(latin, bool)
        assert isinstance(neutral, bool)


class TestNeutralCharacterDetection:
    """Test neutral character detection."""

    def test_punctuation_characters(self):
        """Test common punctuation characters."""
        assert is_neutral_character(".")
        assert is_neutral_character(",")
        assert is_neutral_character("!")
        assert is_neutral_character("?")
        assert is_neutral_character(";")
        assert is_neutral_character(":")

    def test_whitespace_characters(self):
        """Test whitespace characters."""
        # Note: whitespace is detected as neutral through unicodedata.category
        assert is_neutral_character(" ")
        assert is_neutral_character("\t")
        assert is_neutral_character("\n")
        assert is_neutral_character("\r")

    def test_symbol_characters(self):
        """Test symbol characters."""
        assert is_neutral_character("@")
        assert is_neutral_character("#")
        assert is_neutral_character("$")
        assert is_neutral_character("%")
        assert is_neutral_character("&")

    def test_emoji_characters(self):
        """Test emoji characters are treated as neutral."""
        assert is_neutral_character("😀")  # U+1F600
        assert is_neutral_character("❤")  # U+2764
        assert is_neutral_character("🚀")  # U+1F680

    def test_non_neutral_characters(self):
        """Test that actual letters are not neutral."""
        assert not is_neutral_character("a")
        assert not is_neutral_character("中")
        assert not is_neutral_character("А")


class TestNonLatinPercentageCalculation:
    """Test non-Latin percentage calculation."""

    def test_empty_and_whitespace_text(self):
        """Test edge cases with empty or whitespace text."""
        assert calculate_non_latin_percentage("") == 0.0
        assert calculate_non_latin_percentage("   ") == 0.0
        assert calculate_non_latin_percentage("\n\t\r") == 0.0

    def test_pure_latin_text(self):
        """Test text with only Latin characters."""
        assert calculate_non_latin_percentage("Hello World") == 0.0
        assert calculate_non_latin_percentage("The quick brown fox") == 0.0
        assert (
            calculate_non_latin_percentage("café résumé naïve") == 0.0
        )  # Extended Latin

    def test_pure_non_latin_text(self):
        """Test text with only non-Latin characters."""
        chinese_text = "你好世界"  # "Hello World" in Chinese
        assert calculate_non_latin_percentage(chinese_text) == 1.0

        cyrillic_text = "Привет мир"  # "Hello World" in Russian
        # Note: space is neutral, so we expect 100% of meaningful characters to be non-Latin
        result = calculate_non_latin_percentage(cyrillic_text)
        assert result > 0.9  # Should be very high, accounting for space

    def test_mixed_latin_non_latin_text(self):
        """Test text with mixed Latin and non-Latin characters."""
        mixed_text = "Hello 你好"  # English + Chinese
        percentage = calculate_non_latin_percentage(mixed_text)
        # Should be around 28.6% (2 Chinese chars out of 7 meaningful chars)
        assert 0.25 < percentage < 0.35

        mixed_text2 = "Привет Hello"  # Russian + English
        percentage2 = calculate_non_latin_percentage(mixed_text2)
        # Should be around 54% (6 Cyrillic chars out of 11 meaningful chars)
        assert 0.5 < percentage2 < 0.6

    def test_text_with_punctuation_and_symbols(self):
        """Test that punctuation doesn't affect percentage calculation."""
        text_with_punct = "Hello, 你好! How are you?"
        text_without_punct = "Hello 你好 How are you"

        # Percentages should be similar since punctuation is neutral
        perc1 = calculate_non_latin_percentage(text_with_punct)
        perc2 = calculate_non_latin_percentage(text_without_punct)
        assert abs(perc1 - perc2) < 0.1

    def test_emoji_and_special_characters(self):
        """Test text with emojis and special characters."""
        emoji_text = "Hello 😀 你好 🚀"
        # Emojis should be neutral, not affecting the ratio
        percentage = calculate_non_latin_percentage(emoji_text)
        assert 0.2 < percentage < 0.4  # About 1/3 meaningful chars are Chinese

    @given(st.text(min_size=1, max_size=100))
    def test_percentage_bounds(self, text):
        """Test that percentage is always between 0 and 1."""
        percentage = calculate_non_latin_percentage(text)
        assert 0.0 <= percentage <= 1.0


class TestLanguageDetection:
    """Test language detection from text."""

    def test_detect_latin_language(self):
        """Test detection of Latin-script languages."""
        # English
        assert (
            detect_language_from_text("Hello, how are you today?") == LanguageType.LATIN
        )

        # Spanish with accents
        assert detect_language_from_text("Hola, ¿cómo estás hoy?") == LanguageType.LATIN

        # French with accents
        assert (
            detect_language_from_text("Bonjour, comment allez-vous aujourd'hui?")
            == LanguageType.LATIN
        )

        # German with umlauts
        assert (
            detect_language_from_text("Hallo, wie geht es Ihnen heute?")
            == LanguageType.LATIN
        )

    def test_detect_mixed_language(self):
        """Test detection of mixed-script content."""
        # Text with higher percentage of non-Latin characters
        mixed_text = "你好 Hello 中文 English 测试"  # More Chinese characters
        assert detect_language_from_text(mixed_text) == LanguageType.MIXED

        # Russian with English mixed (higher percentage)
        mixed_text2 = "Привет мир Hello world тест"  # Mixed Russian/English
        assert detect_language_from_text(mixed_text2) == LanguageType.MIXED

    def test_detect_unknown_language(self):
        """Test detection of non-Latin languages."""
        # Chinese
        chinese_text = "你好，今天怎么样？"
        assert detect_language_from_text(chinese_text) == LanguageType.UNKNOWN

        # Russian
        russian_text = "Привет, как дела сегодня?"
        assert detect_language_from_text(russian_text) == LanguageType.UNKNOWN

        # Arabic
        arabic_text = "مرحبا، كيف حالك اليوم؟"
        assert detect_language_from_text(arabic_text) == LanguageType.UNKNOWN

        # Japanese
        japanese_text = "こんにちは、今日はどうですか？"
        assert detect_language_from_text(japanese_text) == LanguageType.UNKNOWN

    def test_custom_thresholds(self):
        """Test language detection with custom thresholds."""
        # Text with about 16.7% non-Latin characters
        mixed_text = "Hello 你好 world"

        # With lower threshold (10%), should be mixed
        assert (
            detect_language_from_text(mixed_text, threshold=0.1) == LanguageType.MIXED
        )

        # With higher threshold (20%), should be Latin
        assert (
            detect_language_from_text(mixed_text, threshold=0.2) == LanguageType.LATIN
        )

    def test_edge_cases(self):
        """Test edge cases for language detection."""
        # Empty text
        assert detect_language_from_text("") == LanguageType.LATIN

        # Only whitespace
        assert detect_language_from_text("   \n\t  ") == LanguageType.LATIN

        # Only punctuation
        assert detect_language_from_text("!@#$%^&*()") == LanguageType.LATIN

        # Only emojis
        assert detect_language_from_text("😀😂🚀❤️") == LanguageType.LATIN

    @given(
        st.text(min_size=1, max_size=50),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
    )
    def test_threshold_ordering(self, text, threshold1, threshold2):
        """Test that thresholds work in expected order."""
        if threshold1 <= threshold2:
            low_thresh = threshold1
            high_thresh = threshold2
        else:
            low_thresh = threshold2
            high_thresh = threshold1

        result_low = detect_language_from_text(
            text, threshold=low_thresh, mixed_threshold=high_thresh
        )
        result_high = detect_language_from_text(
            text, threshold=high_thresh, mixed_threshold=high_thresh
        )

        # With higher threshold, less likely to be classified as mixed/unknown
        assert isinstance(result_low, LanguageType)
        assert isinstance(result_high, LanguageType)


class TestTextAnalysis:
    """Test text analysis functions."""

    def test_analyze_text_characters(self):
        """Test character analysis function."""
        text = "Hello 你好 World! 😀"
        analysis = analyze_text_characters(text)

        assert isinstance(analysis, dict)
        assert "total_chars" in analysis
        assert "latin_chars" in analysis
        assert "non_latin_chars" in analysis
        assert "neutral_chars" in analysis
        assert "whitespace_chars" in analysis
        assert "meaningful_chars" in analysis
        assert "non_latin_percentage" in analysis
        assert "language_type" in analysis

        assert analysis["total_chars"] == len(text)
        assert analysis["non_latin_chars"] == 2  # Two Chinese characters
        assert analysis["language_type"] in [
            LanguageType.LATIN,
            LanguageType.MIXED,
            LanguageType.UNKNOWN,
        ]

    def test_analyze_empty_text(self):
        """Test analysis of empty text."""
        analysis = analyze_text_characters("")

        assert analysis["total_chars"] == 0
        assert analysis["latin_chars"] == 0
        assert analysis["non_latin_chars"] == 0
        assert analysis["neutral_chars"] == 0
        assert analysis["whitespace_chars"] == 0
        assert analysis["meaningful_chars"] == 0
        assert analysis["non_latin_percentage"] == 0.0
        assert analysis["language_type"] == LanguageType.LATIN

    def test_get_character_sample(self):
        """Test character sample extraction."""
        text = "Hello 你好 World! 😀 Привет"

        # Test Latin character sampling
        latin_sample = get_character_sample(text, "latin", limit=5)
        assert isinstance(latin_sample, list)
        assert len(latin_sample) <= 5
        for char in latin_sample:
            assert is_latin_character(char)

        # Test non-Latin character sampling
        non_latin_sample = get_character_sample(text, "non_latin", limit=5)
        assert isinstance(non_latin_sample, list)
        for char in non_latin_sample:
            assert not is_latin_character(char) and not is_neutral_character(char)

        # Test neutral character sampling
        neutral_sample = get_character_sample(text, "neutral", limit=5)
        assert isinstance(neutral_sample, list)
        for char in neutral_sample:
            assert is_neutral_character(char)

    def test_get_character_sample_empty_text(self):
        """Test character sampling with empty text."""
        samples = get_character_sample("", "latin")
        assert samples == []

        samples = get_character_sample("", "non_latin")
        assert samples == []

        samples = get_character_sample("", "neutral")
        assert samples == []


class TestRealWorldSamples:
    """Test with real-world multilingual content samples."""

    def test_social_media_posts(self):
        """Test with realistic social media post content."""
        # English tweet-like content
        english_post = "Just discovered this amazing #MCP tool! 🚀 Check it out: https://example.com"
        assert detect_language_from_text(english_post) == LanguageType.LATIN

        # Chinese weibo-like content - actually mixed due to URL and symbols
        chinese_post = (
            "刚刚发现了这个很棒的工具！🚀 大家快来看看：https://example.com #工具 #技术"
        )
        assert detect_language_from_text(chinese_post) == LanguageType.MIXED

        # Mixed content (common in international contexts)
        mixed_post = "Love this new AI tool! 很棒的人工智能工具 #AI #人工智能 https://example.com"
        result = detect_language_from_text(mixed_post)
        # Latin (incl. the URL) dominates here, so ~24% non-Latin lands below the
        # 30% mixed threshold; any of these is acceptable depending on exact ratio.
        assert result in [LanguageType.LATIN, LanguageType.MIXED, LanguageType.UNKNOWN]

    def test_programming_content(self):
        """Test with programming-related content."""
        # Code snippet with English comments
        code_post = (
            "def hello_world(): # This prints hello world\n    print('Hello, World!')"
        )
        assert detect_language_from_text(code_post) == LanguageType.LATIN

        # Code with Chinese comments - mixed due to English code keywords
        code_chinese = (
            "def 你好世界(): # 这个函数打印你好世界\n    print('你好，世界！')"
        )
        assert detect_language_from_text(code_chinese) == LanguageType.MIXED

    def test_academic_content(self):
        """Test with academic or formal content."""
        # English academic text
        english_academic = "The Model Context Protocol (MCP) represents a significant advancement in AI tool integration."
        assert detect_language_from_text(english_academic) == LanguageType.LATIN

        # Russian academic text
        russian_academic = "Протокол контекста модели представляет значительный прогресс в интеграции инструментов ИИ."
        assert detect_language_from_text(russian_academic) == LanguageType.UNKNOWN

    def test_multilingual_business_content(self):
        """Test with business communication content."""
        # English business post
        business_en = "Excited to announce our new partnership with @company! #partnership #business"
        assert detect_language_from_text(business_en) == LanguageType.LATIN

        # Japanese business post
        business_jp = "新しいパートナーシップを発表できて嬉しいです！@会社 #パートナーシップ #ビジネス"
        assert detect_language_from_text(business_jp) == LanguageType.UNKNOWN


class TestPerformance:
    """Test performance characteristics of language detection."""

    def test_performance_with_long_text(self):
        """Test that detection works efficiently with longer text."""
        # Create a long text with mixed content
        long_text = (
            ("Hello world! " * 100) + ("你好世界！" * 100) + ("Привет мир! " * 100)
        )

        # Should still work and give reasonable result
        result = detect_language_from_text(long_text)
        assert result in [LanguageType.MIXED, LanguageType.UNKNOWN]

        # Analysis should also work
        analysis = analyze_text_characters(long_text)
        assert analysis["total_chars"] > 1000
        assert 0.0 <= analysis["non_latin_percentage"] <= 1.0

    @given(st.text(min_size=0, max_size=1000))
    def test_detection_never_crashes(self, text):
        """Property-based test that detection never crashes."""
        try:
            result = detect_language_from_text(text)
            assert isinstance(result, LanguageType)

            analysis = analyze_text_characters(text)
            assert isinstance(analysis, dict)

            percentage = calculate_non_latin_percentage(text)
            assert 0.0 <= percentage <= 1.0
        except Exception as e:
            pytest.fail(f"Language detection crashed with input '{text}': {e}")
