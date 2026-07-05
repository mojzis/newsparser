"""Formatting helpers used as Jinja2 filters in report templates."""

# Icon per content type (see ArticleEvaluation.content_type vocabulary).
_CONTENT_TYPE_ICONS = {
    "video": "🎥",
    "newsletter": "📰",
    "article": "📄",
    "blog post": "✍️",
    "product update": "🚀",
    "invite": "✉️",
}
_DEFAULT_CONTENT_ICON = "📄"

# Flag per language. Keyed by ISO code and by LanguageType values.
# Latin/English is treated as the default and produces no flag.
_LANGUAGE_FLAGS = {
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
    "it": "🇮🇹",
    "pt": "🇵🇹",
    "ja": "🇯🇵",
    "zh": "🇨🇳",
    "ko": "🇰🇷",
    "ru": "🇷🇺",
    "ar": "🇸🇦",
    "hi": "🇮🇳",
    "cs": "🇨🇿",
    "nl": "🇳🇱",
    "pl": "🇵🇱",
    "mixed": "🌐",
    "unknown": "🏳️",
}


def get_content_type_icon(content_type: str) -> str:
    """Return an emoji icon for the given content type."""
    if not content_type:
        return _DEFAULT_CONTENT_ICON
    return _CONTENT_TYPE_ICONS.get(content_type.strip().lower(), _DEFAULT_CONTENT_ICON)


def get_content_type_with_tooltip(content_type: str) -> str:
    """Return the content-type icon wrapped in a span with a tooltip."""
    icon = get_content_type_icon(content_type)
    label = (content_type or "article").strip()
    return f'<span title="{label}">{icon}</span>'


def get_language_flag(language: str) -> str:
    """Return a flag emoji for the language, or empty string for English/Latin."""
    if not language:
        return ""
    return _LANGUAGE_FLAGS.get(language.strip().lower(), "")
