"""Anthropic API client for article evaluation."""

import json
from typing import Optional

from anthropic import Anthropic
from pydantic import HttpUrl

from src.config.settings import Settings
from src.content.models import ExtractedContent
from src.models.evaluation import ArticleEvaluation
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Content limits
MAX_WORDS = 5000  # Maximum words to send to API
MAX_CHARS = 30000  # Maximum characters to send to API


class AnthropicEvaluator:
    """Evaluates articles using Anthropic API."""
    
    def __init__(self, settings: Settings):
        """Initialize evaluator with API settings."""
        self.settings = settings
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        
    def evaluate_article(
        self, 
        content: ExtractedContent, 
        url: str | HttpUrl
    ) -> ArticleEvaluation:
        """
        Evaluate article content for MCP relevance.
        
        Args:
            content: Extracted article content
            url: Article URL
            
        Returns:
            ArticleEvaluation with results
        """
        try:
            # Truncate content if needed
            article_text = content.content_markdown
            truncated = False
            
            word_count = len(article_text.split())
            if word_count > MAX_WORDS or len(article_text) > MAX_CHARS:
                # Truncate to word limit
                words = article_text.split()[:MAX_WORDS]
                article_text = ' '.join(words)
                if len(article_text) > MAX_CHARS:
                    article_text = article_text[:MAX_CHARS]
                truncated = True
                logger.info(f"Truncated content from {word_count} to {len(article_text.split())} words")
            
            # Create prompt with hints from content extraction
            prompt = self._create_evaluation_prompt(
                article_text, 
                content.title,
                detected_language=content.language,
                detected_content_type=content.content_type
            )
            
            # Call Anthropic API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Using Haiku for cost efficiency
                max_tokens=500,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            result = self._parse_response(response.content[0].text)
            
            # Create evaluation
            return ArticleEvaluation(
                url=str(url),
                is_mcp_related=result["is_mcp_related"],
                relevance_score=result["relevance_score"],
                summary=result["summary"],
                perex=result["perex"],
                key_topics=result["key_topics"],
                content_type=result["content_type"],
                language=result["language"],
                title=content.title,
                author=content.author,
                medium=content.medium,
                domain=content.domain,
                evaluated_at=content.extraction_timestamp,
                word_count=word_count,
                truncated=truncated
            )
            
        except Exception as e:
            logger.exception(f"Failed to evaluate article: {e}")
            
            # Return evaluation with error
            return ArticleEvaluation(
                url=str(url),
                is_mcp_related=False,
                relevance_score=0.0,
                summary="Evaluation failed",
                perex="Evaluation failed",
                key_topics=[],
                content_type="article",
                language="en",
                domain=content.domain,
                evaluated_at=content.extraction_timestamp,
                word_count=len(content.content_markdown.split()),
                error=str(e)
            )
    
    def _create_evaluation_prompt(
        self, 
        content: str, 
        title: Optional[str],
        detected_language: Optional[str] = None,
        detected_content_type: Optional[str] = None
    ) -> str:
        """Create evaluation prompt for Anthropic."""
        title_part = f"\nTitle: {title}" if title else ""
        
        # Add hints if available
        hints = []
        if detected_language:
            hints.append(f"Detected language: {detected_language}")
        if detected_content_type:
            hints.append(f"Detected content type: {detected_content_type}")
        
        hints_part = "\n" + "\n".join(hints) if hints else ""
        
        return f"""Analyze this article for relevance to Model Context Protocol (MCP).

MCP is a protocol for AI tool integration that allows language models to access external tools and data sources.

Article:{title_part}{hints_part}
Content:
{content}

Evaluate and respond with JSON containing:
1. is_mcp_related (boolean): Is this article about MCP, AI tool integration, or related topics?
2. relevance_score (0.0-1.0): How relevant is this to MCP? 0=unrelated, 1=directly about MCP
3. summary (string, max 200 chars): Write as the author would - direct, engaging content without meta-language like "This article" or "The piece describes"
4. perex (string, max 150 chars): Witty, engaging summary for display - slightly funny but informative, avoid exclamation marks
5. key_topics (array of strings): Extract 2-5 specific technical topics, tools, services, or implementation details. Focus on concrete technologies, not abstract concepts. Examples of GOOD topics: "Claude API", "OpenAI GPT-4", "TypeScript SDK", "PostgreSQL integration", "Slack bot", "GitHub Actions", "Visual Studio Code extension", "WebSocket transport", "JSON-RPC protocol", "Docker containers", "AWS Lambda", "React components". Examples of BAD topics to avoid: "AI", "MCP", "integration", "development", "tools", "technology"
6. content_type (string): One of: "video", "newsletter", "article", "blog post", "product update", "invite" (hint provided above if detected)
7. language (string): ISO 639-1 language code (e.g., "en" for English, "es" for Spanish, "fr" for French, "ja" for Japanese) (hint provided above if detected)

Respond only with valid JSON, no other text."""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse JSON response from Anthropic."""
        try:
            # Extract JSON from response
            response_text = response_text.strip()
            
            # Try to parse as JSON
            data = json.loads(response_text)
            
            # Validate required fields
            return {
                "is_mcp_related": bool(data.get("is_mcp_related", False)),
                "relevance_score": float(data.get("relevance_score", 0.0)),
                "summary": str(data.get("summary", ""))[:500],
                "perex": str(data.get("perex", ""))[:200],
                "key_topics": list(data.get("key_topics", [])),
                "content_type": str(data.get("content_type", "article")),
                "language": str(data.get("language", "en"))
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            # Return default values
            return {
                "is_mcp_related": False,
                "relevance_score": 0.0,
                "summary": "Failed to parse response",
                "perex": "Failed to parse response",
                "key_topics": [],
                "content_type": "article",
                "language": "en"
            }