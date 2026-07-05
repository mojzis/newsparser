"""Content processing exceptions and error handling."""


class ContentProcessingError(Exception):
    """Base exception for content processing errors."""

    def __init__(self, message: str, url: str | None = None) -> None:
        super().__init__(message)
        self.url = url


class ArticleFetchError(ContentProcessingError):
    """Exception raised when article fetching fails."""


class ContentExtractionError(ContentProcessingError):
    """Exception raised when content extraction fails."""


class ContentValidationError(ContentProcessingError):
    """Exception raised when content validation fails."""


class RateLimitError(ContentProcessingError):
    """Exception raised when rate limits are exceeded."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
