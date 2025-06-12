"""
Language detection utilities for Bluesky posts.

This module provides character-based language detection using Unicode ranges
to identify posts containing significant amounts of non-Latin characters.
"""

import unicodedata
from enum import Enum
from typing import Tuple


class LanguageType(str, Enum):
    """Enumeration of detected language types based on character analysis."""
    
    LATIN = "latin"      # <30% non-Latin characters
    MIXED = "mixed"      # 30-70% non-Latin characters  
    UNKNOWN = "unknown"  # >70% non-Latin characters
    
    def __str__(self) -> str:
        return self.value


# Latin Unicode ranges for character classification
LATIN_RANGES = [
    # Basic Latin
    (0x0000, 0x007F),
    # Latin-1 Supplement  
    (0x0080, 0x00FF),
    # Latin Extended-A
    (0x0100, 0x017F),
    # Latin Extended-B
    (0x0180, 0x024F),
    # Latin Extended Additional
    (0x1E00, 0x1EFF),
    # Latin Extended-C
    (0x2C60, 0x2C7F),
    # Latin Extended-D
    (0xA720, 0xA7FF),
]

# Common punctuation and symbol ranges to treat as neutral
NEUTRAL_RANGES = [
    # General Punctuation
    (0x2000, 0x206F),
    # Currency Symbols
    (0x20A0, 0x20CF),
    # Mathematical Operators
    (0x2200, 0x22FF),
    # Miscellaneous Symbols
    (0x2600, 0x26FF),
    # Dingbats
    (0x2700, 0x27BF),
    # Emoticons
    (0x1F600, 0x1F64F),
    # Miscellaneous Symbols and Pictographs
    (0x1F300, 0x1F5FF),
    # Transport and Map Symbols
    (0x1F680, 0x1F6FF),
]


def is_latin_character(char: str) -> bool:
    """
    Check if a character belongs to Latin Unicode ranges.
    
    Args:
        char: Single character to check
        
    Returns:
        True if character is Latin, False otherwise
    """
    if not char:
        return True  # Empty character treated as neutral
    
    code_point = ord(char)
    
    # Check Latin ranges
    for start, end in LATIN_RANGES:
        if start <= code_point <= end:
            return True
    
    return False


def is_neutral_character(char: str) -> bool:
    """
    Check if a character is neutral (punctuation, symbols, etc.).
    
    Args:
        char: Single character to check
        
    Returns:
        True if character is neutral, False otherwise
    """
    if not char:
        return True
    
    code_point = ord(char)
    
    # Check neutral ranges (punctuation, symbols, etc.)
    for start, end in NEUTRAL_RANGES:
        if start <= code_point <= end:
            return True
    
    # Also treat ASCII punctuation and whitespace as neutral
    category = unicodedata.category(char)
    if category.startswith('P') or category.startswith('Z') or category.startswith('S'):
        return True
    
    return False


def calculate_non_latin_percentage(text: str) -> float:
    """
    Calculate the percentage of non-Latin characters in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Percentage of non-Latin characters (0.0 to 1.0)
    """
    if not text or not text.strip():
        return 0.0
    
    total_chars = 0
    non_latin_chars = 0
    
    for char in text:
        # Skip whitespace and control characters for meaningful analysis
        if char.isspace() or unicodedata.category(char) in ('Cc', 'Cf'):
            continue
        
        total_chars += 1
        
        # Count characters that are neither Latin nor neutral as non-Latin
        if not is_latin_character(char) and not is_neutral_character(char):
            non_latin_chars += 1
    
    if total_chars == 0:
        return 0.0
    
    return non_latin_chars / total_chars


def detect_language_from_text(
    text: str, 
    threshold: float = 0.3, 
    mixed_threshold: float = 0.7
) -> LanguageType:
    """
    Detect language type based on character analysis.
    
    Args:
        text: Text content to analyze
        threshold: Threshold for considering text as mixed (default 30%)
        mixed_threshold: Threshold for considering text as unknown (default 70%)
        
    Returns:
        LanguageType enum value (latin, mixed, or unknown)
    """
    if not text or not text.strip():
        return LanguageType.LATIN
    
    non_latin_percentage = calculate_non_latin_percentage(text)
    
    if non_latin_percentage < threshold:
        return LanguageType.LATIN
    elif non_latin_percentage < mixed_threshold:
        return LanguageType.MIXED
    else:
        return LanguageType.UNKNOWN


def analyze_text_characters(text: str) -> dict:
    """
    Analyze character composition of text for debugging purposes.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with character analysis details
    """
    if not text:
        return {
            "total_chars": 0,
            "latin_chars": 0,
            "non_latin_chars": 0,
            "neutral_chars": 0,
            "whitespace_chars": 0,
            "meaningful_chars": 0,
            "non_latin_percentage": 0.0,
            "language_type": LanguageType.LATIN
        }
    
    total_chars = len(text)
    latin_chars = 0
    non_latin_chars = 0
    neutral_chars = 0
    whitespace_chars = 0
    
    for char in text:
        if char.isspace() or unicodedata.category(char) in ('Cc', 'Cf'):
            whitespace_chars += 1
        elif is_latin_character(char):
            latin_chars += 1
        elif is_neutral_character(char):
            neutral_chars += 1
        else:
            non_latin_chars += 1
    
    meaningful_chars = total_chars - whitespace_chars
    non_latin_percentage = (
        non_latin_chars / meaningful_chars if meaningful_chars > 0 else 0.0
    )
    
    return {
        "total_chars": total_chars,
        "latin_chars": latin_chars,
        "non_latin_chars": non_latin_chars,
        "neutral_chars": neutral_chars,
        "whitespace_chars": whitespace_chars,
        "meaningful_chars": meaningful_chars,
        "non_latin_percentage": non_latin_percentage,
        "language_type": detect_language_from_text(text)
    }


def get_character_sample(text: str, char_type: str = "non_latin", limit: int = 10) -> list[str]:
    """
    Extract sample characters of a specific type for debugging.
    
    Args:
        text: Text to sample from
        char_type: Type of characters to sample ("latin", "non_latin", "neutral")
        limit: Maximum number of characters to return
        
    Returns:
        List of sample characters
    """
    if not text:
        return []
    
    samples = []
    
    for char in text:
        if len(samples) >= limit:
            break
        
        if char.isspace() or unicodedata.category(char) in ('Cc', 'Cf'):
            continue
        
        if char_type == "latin" and is_latin_character(char):
            samples.append(char)
        elif char_type == "non_latin" and not is_latin_character(char) and not is_neutral_character(char):
            samples.append(char)
        elif char_type == "neutral" and is_neutral_character(char):
            samples.append(char)
    
    return list(set(samples))  # Remove duplicates while preserving order