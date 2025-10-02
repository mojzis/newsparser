"""Anthropic API client for article evaluation."""

import json
from typing import Optional

from anthropic import Anthropic
from pydantic import HttpUrl

from src.config.settings import Settings
from src.config.config_manager import get_config_manager
from src.content.models import ExtractedContent
from src.models.evaluation import ArticleEvaluation
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnthropicEvaluator:
    """Evaluates articles using Anthropic API."""
    
    def __init__(self, settings: Settings):
        """Initialize evaluator with API settings."""
        self.settings = settings
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.config_manager = get_config_manager()
        
        # Load model and prompt configurations
        self.model_config = self.config_manager.get_model_config()
        self.prompt_config = self.config_manager.get_prompt_config()
        
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
            max_words = self.model_config.content_limits["max_words"]
            max_chars = self.model_config.content_limits["max_chars"]
            
            if word_count > max_words or len(article_text) > max_chars:
                # Truncate to word limit
                words = article_text.split()[:max_words]
                article_text = ' '.join(words)
                if len(article_text) > max_chars:
                    article_text = article_text[:max_chars]
                truncated = True
                logger.info(f"Truncated content from {word_count} to {len(article_text.split())} words")
            
            # Create prompt with hints from content extraction using configuration
            prompt = self._create_evaluation_prompt(
                content=article_text,
                title=content.title,
                detected_language=content.language,
                detected_content_type=content.content_type
            )
            
            # Call Anthropic API using model configuration
            response = self.client.messages.create(
                model=self.model_config.model_id,
                max_tokens=self.model_config.config["max_tokens"],
                temperature=self.model_config.config["temperature"],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            result = self._parse_response(response.content[0].text)
            
            # Create evaluation with configuration metadata
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
                truncated=truncated,
                prompt_version=self.prompt_config.version,
                prompt_name=self.prompt_config.name,
                model_id=self.model_config.model_id,
                model_version=self.model_config.version,
                config_branch=self.config_manager.branch
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
                error=str(e),
                prompt_version="unknown",
                prompt_name="unknown",
                model_id="unknown",
                model_version="unknown",
                config_branch="unknown"
            )
    
    def _create_evaluation_prompt(
        self,
        content: str,
        title: Optional[str] = None,
        detected_language: Optional[str] = None,
        detected_content_type: Optional[str] = None
    ) -> str:
        """Create evaluation prompt for article content using configuration."""
        # Add title if available
        title_part = f"\nTitle: {title}" if title else ""
        
        # Add hints if available
        hints = []
        if detected_language:
            hints.append(f"Detected language: {detected_language}")
        if detected_content_type:
            hints.append(f"Detected content type: {detected_content_type}")
        
        hints_part = "\n" + "\n".join(hints) if hints else ""
        
        # Use prompt template from configuration
        template = self.prompt_config.template
        
        # Format the template with variables
        return template.format(
            title_part=title_part,
            hints_part=hints_part,
            content=content
        )
    
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