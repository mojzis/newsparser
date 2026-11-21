from src.config.collection import load_collection
from src.config.config_manager import get_config_manager
from src.config.settings import Settings
from src.evaluation.anthropic_client import AnthropicEvaluator


def _settings() -> Settings:
    return Settings(
        r2_access_key_id="test_key",
        r2_secret_access_key="test_secret",
        r2_bucket_name="test-bucket",
        r2_endpoint_url="https://test.r2.cloudflarestorage.com",
        anthropic_api_key="test-anthropic-key",
    )


class TestAnthropicEvaluatorCollectionWiring:
    def test_no_collection_falls_back_to_global_defaults(self):
        evaluator = AnthropicEvaluator(_settings())

        config_manager = get_config_manager()
        assert evaluator.topic == config_manager.get_topic_config()
        assert evaluator.model_config == config_manager.get_model_config()
        assert evaluator.prompt_config == config_manager.get_prompt_config()

    def test_mcp_collection_resolves_same_defaults(self):
        """The mcp collection must reproduce today's default evaluator config."""
        collection = load_collection("mcp")
        evaluator = AnthropicEvaluator(_settings(), collection=collection)

        config_manager = get_config_manager()
        assert evaluator.topic == collection.topic
        assert evaluator.topic == config_manager.get_topic_config()
        assert evaluator.model_config == config_manager.get_model_config(
            collection.evaluation.model_config_name
        )
        assert evaluator.prompt_config == config_manager.get_prompt_config(
            collection.evaluation.prompt_config
        )

    def test_duckdb_collection_resolves_its_own_topic(self):
        collection = load_collection("duckdb")
        evaluator = AnthropicEvaluator(_settings(), collection=collection)

        assert evaluator.topic.name == "DuckDB"
        assert evaluator.topic == collection.topic


def _content():
    from datetime import datetime

    from src.content.models import ExtractedContent

    return ExtractedContent(
        url="https://example.com/a",
        title="An MCP server",
        content_markdown="Building an MCP server.",
        word_count=4,
        language="en",
        content_type="tutorial",
        domain="example.com",
        extraction_timestamp=datetime(2026, 11, 21),
    )


def _response(blocks, stop_reason="end_turn"):
    from unittest.mock import MagicMock

    return MagicMock(content=blocks, stop_reason=stop_reason)


class TestAnthropicEvaluatorResponseParsing:
    def test_parses_text_after_thinking_block(self, mocker):
        from anthropic.types import TextBlock, ThinkingBlock

        evaluator = AnthropicEvaluator(_settings())
        payload = (
            '{"is_relevant": true, "relevance_score": 0.9, "summary": "A tutorial on MCP.", '
            '"perex": "Build an MCP server.", "key_topics": ["mcp"], "content_type": "tutorial", '
            '"language": "en"}'
        )
        create = mocker.patch.object(
            evaluator.client.messages,
            "create",
            return_value=_response(
                [
                    ThinkingBlock(type="thinking", thinking="", signature="x"),
                    TextBlock(type="text", text=payload),
                ]
            ),
        )

        result = evaluator.evaluate_article(_content(), "https://example.com/a")

        assert result.error is None
        assert result.is_relevant is True
        assert result.relevance_score == 0.9
        kwargs = create.call_args.kwargs
        assert kwargs["thinking"] == evaluator.model_config.config["thinking"]
        assert "temperature" not in kwargs

    def test_no_text_block_records_error_with_model(self, mocker):
        from anthropic.types import ThinkingBlock

        evaluator = AnthropicEvaluator(_settings())
        mocker.patch.object(
            evaluator.client.messages,
            "create",
            return_value=_response(
                [ThinkingBlock(type="thinking", thinking="", signature="x")],
                stop_reason="refusal",
            ),
        )

        result = evaluator.evaluate_article(_content(), "https://example.com/a")

        assert "stop_reason=refusal" in result.error
        assert result.model_id == evaluator.model_config.model_id
