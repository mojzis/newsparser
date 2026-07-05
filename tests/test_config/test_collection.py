from pathlib import Path

import pytest

from src.config.collection import load_collection
from src.config.config_manager import ConfigManager


class TestLoadCollection:
    def test_mcp_matches_base_app_config(self):
        """The mcp collection must reproduce today's base app config exactly."""
        app_config = ConfigManager(config_path="config", branch="base").load_app_config()
        collection = load_collection("mcp")

        assert collection.topic.name == app_config.topic.name
        assert collection.topic.description == app_config.topic.description
        assert (
            collection.topic.min_relevance_score
            == app_config.topic.min_relevance_score
        )

    def test_mcp_paths(self):
        collection = load_collection("mcp")

        assert collection.stages_base == Path("stages/mcp")
        assert collection.output_base == Path("output/mcp")

    def test_duckdb_resolves_own_topic_and_ui(self):
        collection = load_collection("duckdb")

        assert collection.topic.name == "DuckDB"
        assert "duckdb" in collection.topic.description.lower()
        assert collection.ui.site_title == "DuckDB News"
        assert collection.default_search == "duckdb_mentions"

    @pytest.mark.parametrize("name", ["mcp", "duckdb"])
    def test_default_search_enabled(self, name):
        collection = load_collection(name)
        search = collection.searches.get_search(collection.default_search)

        assert search is not None
        assert search.enabled is True

    def test_unknown_collection_raises(self):
        with pytest.raises(FileNotFoundError):
            load_collection("does-not-exist")
