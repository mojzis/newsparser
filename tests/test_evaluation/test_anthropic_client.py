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
