"""Tests for ReportStage's collection-aware path routing."""

import asyncio
import tempfile
from datetime import date
from pathlib import Path

import pytest

from src.config.config_manager import UIConfig
from src.stages.markdown import MarkdownFile
from src.stages.report import ReportStage


class TestReportStagePaths:
    @pytest.fixture
    def workdir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def _write_post(
        self,
        base_path: Path,
        target_date: date,
        post_id: str,
        source: str = "bluesky",
    ) -> None:
        collect_dir = base_path / "collect" / target_date.strftime("%Y-%m-%d")
        collect_dir.mkdir(parents=True, exist_ok=True)
        post = MarkdownFile(
            {
                "author": "someone.bsky.social",
                "created_at": f"{target_date.isoformat()}T12:00:00+00:00",
                "source": source,
            },
            "# Post",
        )
        post.save(collect_dir / f"post_{post_id}.md")

    def _write_fetch(self, base_path: Path, target_date: date, url: str) -> None:
        fetch_dir = base_path / "fetch" / target_date.strftime("%Y-%m-%d")
        fetch_dir.mkdir(parents=True, exist_ok=True)
        fetch_md = MarkdownFile(
            {
                "url": url,
                "title": "A Title",
                "domain": "example.com",
                "fetch_status": "success",
            },
            "# A Title\n\nBody",
        )
        fetch_md.save(fetch_dir / "fetched_content.md")

    def _write_evaluation(
        self, base_path: Path, target_date: date, url: str, post_id: str
    ) -> None:
        evaluate_dir = base_path / "evaluate" / target_date.strftime("%Y-%m-%d")
        evaluate_dir.mkdir(parents=True, exist_ok=True)
        eval_md = MarkdownFile(
            {
                "url": url,
                "found_in_posts": [post_id],
                "evaluation": {
                    "is_relevant": True,
                    "relevance_score": 0.9,
                    "summary": "summary",
                    "perex": "perex",
                    "content_type": "article",
                    "language": "en",
                },
                "stage": "evaluated",
            },
            "# Evaluation Results",
        )
        eval_md.save(evaluate_dir / "evaluated_content.md")

    def test_report_output_path_uses_output_base(self, workdir):
        stage = ReportStage(
            base_path=workdir / "stages" / "duckdb",
            output_base=workdir / "output" / "duckdb",
        )
        target_date = date(2026, 1, 5)

        output_path = stage.get_report_output_path(target_date)

        assert output_path == (
            workdir / "output" / "duckdb" / "reports" / "2026-01-05" / "report.html"
        )

    def test_collect_mcp_articles_reads_from_namespaced_base_path(self, workdir):
        base_path = workdir / "stages" / "duckdb"
        target_date = date(2026, 1, 5)
        url = "https://example.com/article"

        self._write_post(base_path, target_date, post_id="post1")
        self._write_fetch(base_path, target_date, url)
        self._write_evaluation(base_path, target_date, url, post_id="post1")

        stage = ReportStage(base_path=base_path, output_base=workdir / "output")

        articles = stage.collect_mcp_articles(target_date)

        assert len(articles) == 1
        assert str(articles[0].url) == url
        assert articles[0].source == "bluesky"

    def test_collect_mcp_articles_reads_hackernews_source(self, workdir):
        base_path = workdir / "stages" / "duckdb"
        target_date = date(2026, 1, 5)
        url = "https://example.com/article"

        self._write_post(base_path, target_date, post_id="hn_12345", source="hackernews")
        self._write_fetch(base_path, target_date, url)
        self._write_evaluation(base_path, target_date, url, post_id="hn_12345")

        stage = ReportStage(base_path=base_path, output_base=workdir / "output")

        articles = stage.collect_mcp_articles(target_date)

        assert len(articles) == 1
        assert articles[0].source == "hackernews"
        assert str(articles[0].bluesky_url) == "https://news.ycombinator.com/item?id=12345"

    def test_collect_mcp_articles_ignores_other_collections_data(self, workdir):
        """Data under a different collection's base_path must not leak in."""
        target_date = date(2026, 1, 5)
        url = "https://example.com/article"

        # Write data under the "mcp" collection's namespaced path only.
        self._write_post(workdir / "stages" / "mcp", target_date, post_id="post1")
        self._write_fetch(workdir / "stages" / "mcp", target_date, url)
        self._write_evaluation(
            workdir / "stages" / "mcp", target_date, url, post_id="post1"
        )

        # Reading through the "duckdb" collection's stage must see nothing.
        stage = ReportStage(
            base_path=workdir / "stages" / "duckdb", output_base=workdir / "output"
        )
        articles = stage.collect_mcp_articles(target_date)

        assert articles == []

    def test_run_report_uses_collection_ui_branding(self, workdir):
        base_path = workdir / "stages" / "duckdb"
        output_base = workdir / "output" / "duckdb"
        target_date = date(2026, 1, 5)
        url = "https://example.com/article"

        self._write_post(base_path, target_date, post_id="post1")
        self._write_fetch(base_path, target_date, url)
        self._write_evaluation(base_path, target_date, url, post_id="post1")

        stage = ReportStage(
            base_path=base_path,
            output_base=output_base,
            ui=UIConfig(
                site_title="DuckDB News",
                site_tagline="Daily digest of DuckDB mentions",
            ),
        )

        asyncio.run(
            stage.run_report(
                days_back=0,
                output_date=target_date,
                generate_sitemap=False,
                generate_rss=False,
            )
        )

        report_path = output_base / "reports" / "2026-01-05" / "report.html"
        content = report_path.read_text()

        assert "DuckDB News" in content
        assert "MCP Monitor" not in content
