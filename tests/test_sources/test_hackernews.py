from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.config.searches import SearchDefinition
from src.sources.hackernews import HackerNewsSource


@pytest.fixture
def search_definition():
    return SearchDefinition(
        name="duckdb_mentions",
        description="DuckDB mentions",
        include_terms=["duckdb", "duck db"],
        exclude_terms=["minecraft"],
    )


def _mock_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status = MagicMock()
    return response


class TestHackerNewsSource:
    def test_name(self):
        assert HackerNewsSource().name == "hackernews"

    @pytest.mark.asyncio
    async def test_search_maps_hits_to_posts(self, search_definition):
        hits = {
            "hits": [
                {
                    "objectID": "111",
                    "title": "DuckDB is great",
                    "url": "https://duckdb.org",
                    "author": "pg",
                    "points": 42,
                    "num_comments": 17,
                    "created_at_i": 1699999999,
                }
            ]
        }

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_mock_response(hits))) as mock_get:
            posts = await HackerNewsSource().search(search_definition, max_posts=10)

        assert len(posts) == 1
        post = posts[0]
        assert post.id == "hn_111"
        assert post.author == "pg"
        assert post.content == "DuckDB is great"
        assert str(post.links[0]) == "https://duckdb.org/"
        assert post.created_at == datetime.fromtimestamp(1699999999, tz=UTC)
        assert post.engagement_metrics.likes == 42
        assert post.engagement_metrics.replies == 17
        assert post.engagement_metrics.reposts == 0
        assert post.source == "hackernews"

        called_kwargs = mock_get.call_args.kwargs
        assert called_kwargs["params"]["query"] == "duckdb duck db"
        assert called_kwargs["params"]["tags"] == "story"
        assert called_kwargs["params"]["hitsPerPage"] == 10

    @pytest.mark.asyncio
    async def test_search_skips_empty_title_hits(self, search_definition):
        hits = {
            "hits": [
                {
                    "objectID": "222",
                    "title": "",
                    "url": None,
                    "author": "someone",
                    "points": 1,
                    "num_comments": 0,
                    "created_at_i": 1699999999,
                }
            ]
        }

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_mock_response(hits))):
            posts = await HackerNewsSource().search(search_definition, max_posts=10)

        assert posts == []

    @pytest.mark.asyncio
    async def test_search_handles_missing_url(self, search_definition):
        hits = {
            "hits": [
                {
                    "objectID": "333",
                    "title": "Ask HN: something",
                    "url": None,
                    "author": "asker",
                    "points": 3,
                    "num_comments": 1,
                    "created_at_i": 1699999999,
                }
            ]
        }

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_mock_response(hits))):
            posts = await HackerNewsSource().search(search_definition, max_posts=10)

        assert len(posts) == 1
        assert posts[0].links == []

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_on_request_error(self, search_definition):
        with patch(
            "httpx.AsyncClient.get",
            new=AsyncMock(side_effect=httpx.ConnectError("boom")),
        ):
            posts = await HackerNewsSource().search(search_definition, max_posts=10)

        assert posts == []

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_on_bad_json(self, search_definition):
        response = _mock_response(None)
        response.json.side_effect = ValueError("bad json")

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=response)):
            posts = await HackerNewsSource().search(search_definition, max_posts=10)

        assert posts == []
