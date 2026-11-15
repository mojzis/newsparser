from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner
from pydantic import HttpUrl

from src.cli.new_commands import cli
from src.config.settings import Settings
from src.models.post import BlueskyPost, EngagementMetrics
from src.term_tester import (
    BlueskyLoginError,
    post_url,
    render_html,
    run_terms,
    searches_yaml,
    summarize,
)

NOW = datetime(2026, 11, 15, tzinfo=UTC)


def _post(i, days_ago=0, content="hello #ax #mcp", links=(), likes=0, source="bluesky"):
    return BlueskyPost(
        id=f"at://did:plc:x/app.bsky.feed.post/r{i}"
        if source == "bluesky"
        else f"hn_{i}",
        author="someone.bsky.social",
        content=content,
        created_at=NOW - timedelta(days=days_ago),
        links=[HttpUrl(u) for u in links],
        engagement_metrics=EngagementMetrics(likes=likes, reposts=0, replies=0),
        source=source,
    )


def test_summarize_counts_volume_domains_and_hashtags():
    posts = [
        _post(1, days_ago=0, links=["https://www.example.com/a"], likes=5),
        _post(2, days_ago=2, links=["https://example.com/b", "https://other.org"]),
        _post(3, days_ago=4, content="no tags here", likes=9),
        _post(4, days_ago=40, links=["https://bsky.app/profile/x"]),
    ]

    result = summarize("#mcp", "bluesky", posts, max_posts=4, now=NOW)

    assert result.count == 4
    assert result.hit_cap
    assert result.posts_per_day == 0.1  # 4 posts over the 40 days they span
    assert result.last_30_days == 3
    assert result.top_domains == [("example.com", 2), ("other.org", 1)]  # no bsky.app
    assert result.top_hashtags == [("ax", 3)]  # the searched tag itself is left out
    assert [p.id for p in result.samples] == [
        p.id for p in (posts[2], posts[0], posts[1], posts[3])
    ]


def test_summarize_rate_of_uncapped_result_runs_to_now():
    posts = [_post(1, days_ago=10), _post(2, days_ago=20)]
    result = summarize("x", "bluesky", posts, max_posts=100, now=NOW)
    assert result.posts_per_day == 0.1  # 2 posts in the last 20 days


def test_summarize_rate_of_busy_capped_result():
    posts = [_post(i, days_ago=0) for i in range(10)]
    result = summarize("x", "bluesky", posts, max_posts=10, now=NOW)
    assert result.posts_per_day == 240.0  # 10 posts within the one-hour floor


def test_summarize_empty():
    result = summarize("nothing", "hackernews", [], max_posts=100, now=NOW)
    assert result.count == 0
    assert result.posts_per_day is None
    assert result.oldest is None
    assert result.top_domains == []
    assert result.samples == []
    assert not result.hit_cap


def test_post_url_per_source():
    assert post_url(_post(7)) == "https://bsky.app/profile/someone.bsky.social/post/r7"
    assert (
        post_url(_post(7, source="hackernews"))
        == "https://news.ycombinator.com/item?id=7"
    )


def test_searches_yaml_is_valid_collection_snippet():
    snippet = yaml.safe_load(searches_yaml(['"agent experience"', "llms.txt"]))
    searches = snippet["searches"]["searches"]
    assert searches["agent_experience"]["include_terms"] == ['"agent experience"']
    assert searches["llms_txt"]["include_terms"] == ["llms.txt"]


def test_searches_yaml_keeps_odd_and_colliding_terms():
    terms = ["#mcp", "mcp", "MCP", "foo\\bar"]
    snippet = yaml.safe_load(searches_yaml(terms))
    searches = snippet["searches"]["searches"]
    assert list(searches) == ["mcp", "mcp_2", "mcp_3", "foo_bar"]
    assert [s["include_terms"][0] for s in searches.values()] == terms


def test_render_html_escapes_content():
    result = summarize(
        "x", "bluesky", [_post(1, content="<script>bad</script>")], 10, NOW
    )
    html = render_html([result], ["x"])
    assert "&lt;script&gt;" in html
    assert "<script>bad" not in html


@pytest.mark.asyncio
async def test_run_terms_hackernews_only_skips_bluesky_login():
    with (
        patch("src.term_tester.BlueskyClient.authenticate", new=AsyncMock()) as auth,
        patch(
            "src.sources.hackernews.HackerNewsSource.search",
            new=AsyncMock(return_value=[_post(1, source="hackernews")]),
        ),
    ):
        results = await run_terms(
            ["a", "b"], ["hackernews"], 50, MagicMock(spec=Settings)
        )

    auth.assert_not_called()
    assert [(r.term, r.source, r.count) for r in results] == [
        ("a", "hackernews", 1),
        ("b", "hackernews", 1),
    ]


@pytest.mark.asyncio
async def test_run_terms_fails_loudly_without_bluesky_login():
    with (
        patch(
            "src.term_tester.BlueskyClient.authenticate",
            new=AsyncMock(return_value=False),
        ),
        pytest.raises(BlueskyLoginError, match="Bluesky login failed"),
    ):
        await run_terms(["a"], ["bluesky"], 50, MagicMock(spec=Settings))


@pytest.mark.asyncio
async def test_run_terms_bluesky_searches_and_closes_client():
    with (
        patch(
            "src.term_tester.BlueskyClient.authenticate",
            new=AsyncMock(return_value=True),
        ),
        patch("src.term_tester.BlueskyClient.close", new=AsyncMock()) as close,
        patch(
            "src.sources.bluesky.BlueskySource.search",
            new=AsyncMock(return_value=[_post(1), _post(2)]),
        ),
    ):
        results = await run_terms(["a"], ["bluesky"], 50, MagicMock(spec=Settings))

    close.assert_awaited_once()
    assert [(r.term, r.source, r.count) for r in results] == [("a", "bluesky", 2)]


def test_try_terms_cli_writes_page(tmp_path):
    result = summarize(
        "llms.txt", "hackernews", [_post(1, source="hackernews")], 5, NOW
    )
    out = tmp_path / "page.html"
    with (
        patch("src.cli.new_commands.get_config_manager"),
        patch("src.cli.new_commands.run_terms", new=AsyncMock(return_value=[result])),
        patch("src.config.settings.get_settings"),
    ):
        cli_result = CliRunner().invoke(
            cli,
            [
                "try-terms",
                "llms.txt",
                "--source",
                "hackernews",
                "--out",
                str(out),
                "--no-open",
            ],
        )

    assert cli_result.exit_code == 0, cli_result.output
    assert "llms.txt on hackernews: 1 posts" in cli_result.output
    assert "llms.txt" in out.read_text()


def test_try_terms_cli_reports_login_failure(tmp_path):
    with (
        patch("src.cli.new_commands.get_config_manager"),
        patch(
            "src.cli.new_commands.run_terms",
            new=AsyncMock(side_effect=BlueskyLoginError("Bluesky login failed.")),
        ),
        patch("src.config.settings.get_settings"),
    ):
        cli_result = CliRunner().invoke(
            cli, ["try-terms", "x", "--out", str(tmp_path / "p.html"), "--no-open"]
        )

    assert cli_result.exit_code != 0
    assert "Bluesky login failed" in cli_result.output
