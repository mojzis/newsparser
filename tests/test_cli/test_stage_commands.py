"""Tests that CLI stage commands route through the selected collection's paths."""

from pathlib import Path

from click.testing import CliRunner

from src.cli.stage_commands import collect, status


def _chdir_with_config(tmp_path: Path, monkeypatch) -> None:
    """Run from an isolated tmp_path, but keep the real config/ directory visible
    so load_collection("mcp"/"duckdb") can still find the real collection YAMLs.
    """
    repo_config = Path.cwd() / "config"
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").symlink_to(repo_config)


class TestStatusCollectionRouting:
    def test_status_scans_the_named_collection_stages_dir(self, tmp_path, monkeypatch):
        _chdir_with_config(tmp_path, monkeypatch)

        marker_dir = tmp_path / "stages" / "duckdb" / "collect" / "2026-01-05"
        marker_dir.mkdir(parents=True)
        (marker_dir / "post_1.md").write_text("---\n---\n\ncontent")

        runner = CliRunner()
        result = runner.invoke(
            status, ["--collection", "duckdb", "--date", "2026-01-05"]
        )

        assert result.exit_code == 0, result.output
        assert "Complete" in result.output

    def test_status_does_not_see_other_collections_data(self, tmp_path, monkeypatch):
        _chdir_with_config(tmp_path, monkeypatch)

        marker_dir = tmp_path / "stages" / "duckdb" / "collect" / "2026-01-05"
        marker_dir.mkdir(parents=True)
        (marker_dir / "post_1.md").write_text("---\n---\n\ncontent")

        runner = CliRunner()
        result = runner.invoke(status, ["--collection", "mcp", "--date", "2026-01-05"])

        assert result.exit_code == 0, result.output
        assert "Missing" in result.output

    def test_unknown_collection_fails_cleanly(self, tmp_path, monkeypatch):
        # load_collection_or_exit turns the FileNotFoundError into a friendly
        # sys.exit(1) rather than an unhandled traceback.
        _chdir_with_config(tmp_path, monkeypatch)

        runner = CliRunner()
        result = runner.invoke(status, ["--collection", "does-not-exist"])

        assert result.exit_code != 0


class TestCollectDefaultSearch:
    def test_missing_search_option_uses_collection_default(
        self, tmp_path, monkeypatch
    ):
        """`--search` should default to the collection's own default_search, not a
        hardcoded value, so `--collection duckdb` works without also passing --search.
        """
        _chdir_with_config(tmp_path, monkeypatch)

        runner = CliRunner()
        result = runner.invoke(collect, ["--collection", "duckdb"])

        # Ordering dependency: this assertion relies on collect() resolving and
        # printing the search key *before* it checks Bluesky credentials (no creds
        # are configured in tests, so the command exits non-zero right after this
        # print). If that ordering in stage_commands.collect() ever changes so the
        # credential check runs first, this assertion will stop being reached and
        # the test will fail without indicating a real regression in search
        # resolution.
        assert "using search 'duckdb_mentions'" in result.output
