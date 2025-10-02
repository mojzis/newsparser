"""New streamlined CLI commands focused on stage-based architecture."""

import click
from rich.console import Console

from src.cli.stage_commands import stages
from src.cli.config_commands import config
from src.config.config_manager import get_config_manager

console = Console()


@click.group()
def cli():
    """Bluesky MCP Monitor - Stage-based Processing"""
    # Validate configuration on startup
    try:
        config_manager = get_config_manager()
        if not config_manager.validate_config():
            console.print("[red]Configuration validation failed. Please check your config files.[/red]")
            raise click.Abort()
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise click.Abort()


# Add the stage-based commands as the primary interface
cli.add_command(stages)

# Add configuration management commands
cli.add_command(config)

# Add convenient top-level aliases for the most common operations
@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--max-posts", default=100, help="Maximum posts to collect")
@click.option("--search", default="mcp_tag", help="Search definition to use")
@click.option("--config", "config_path", help="Path to search configuration YAML file")
@click.option("--expand-urls/--no-expand-urls", default=True, help="Expand shortened URLs to final destinations")
@click.option("--threads/--no-threads", default=False, help="Collect entire threads instead of just individual posts")
@click.option("--max-thread-depth", default=6, help="Maximum depth to traverse in thread replies (default: 6)")
@click.option("--max-parent-height", default=80, help="Maximum height to traverse up parent chain (default: 80)")
@click.option("--export-parquet/--no-export-parquet", default=True, help="Export data to Parquet files for analytics (default: True)")
@click.option("--expand-references/--no-expand-references", default=True, help="Expand Bluesky post references into new posts (default: True)")
@click.option("--max-reference-depth", default=2, help="Maximum depth for reference expansion (default: 2)")
def collect(target_date, max_posts, search, config_path, expand_urls, threads, max_thread_depth, max_parent_height, export_parquet, expand_references, max_reference_depth):
    """Collect posts using stage-based architecture."""
    from src.cli.stage_commands import collect as stage_collect
    ctx = click.Context(stage_collect)
    ctx.invoke(stage_collect, target_date=target_date, max_posts=max_posts, search=search, config_path=config_path, 
               expand_urls=expand_urls, threads=threads, max_thread_depth=max_thread_depth, max_parent_height=max_parent_height, export_parquet=export_parquet, expand_references=expand_references, max_reference_depth=max_reference_depth)


@cli.command()
@click.option("--days-back", default=7, help="Number of days to look back for unfetched URLs (default: 7)")
@click.option("--export-parquet/--no-export-parquet", default=True, help="Export data to Parquet files for analytics (default: True)")
def fetch(days_back, export_parquet):
    """Fetch content from URLs found in posts from the last N days."""
    from src.cli.stage_commands import fetch as stage_fetch
    ctx = click.Context(stage_fetch)
    ctx.invoke(stage_fetch, days_back=days_back, export_parquet=export_parquet)


@cli.command()
@click.option("--days-back", default=7, help="Number of days to look back for unevaluated content (default: 7)")
@click.option("--regenerate/--no-regenerate", default=False, help="Re-evaluate existing evaluations (default: False)")
@click.option("--export-parquet/--no-export-parquet", default=True, help="Export data to Parquet files for analytics (default: True)")
def evaluate(days_back, regenerate, export_parquet):
    """Evaluate content from fetched URLs in the last N days."""
    from src.cli.stage_commands import evaluate as stage_evaluate
    ctx = click.Context(stage_evaluate)
    ctx.invoke(stage_evaluate, days_back=days_back, regenerate=regenerate, export_parquet=export_parquet)


@cli.command()
@click.option("--days-back", default=7, help="Number of days to look back for evaluated content (default: 7)")
@click.option("--regenerate/--no-regenerate", default=True, help="Regenerate existing reports (default: True)")
@click.option("--output-date", help="Date to use for report filename (YYYY-MM-DD), defaults to today")
@click.option("--bulk/--single", default=False, help="Generate reports for all days with content in range (default: auto-detect)")
@click.option("--debug/--no-debug", default=False, help="Show debug information including evaluation filenames")
@click.option("--sitemap/--no-sitemap", default=True, help="Generate sitemap.xml (default: True)")
@click.option("--rss/--no-rss", default=True, help="Generate rss.xml (default: True)")
def report(days_back, regenerate, output_date, bulk, debug, sitemap, rss):
    """Generate report from evaluated content in the last N days."""
    from src.cli.stage_commands import report as stage_report
    ctx = click.Context(stage_report)
    ctx.invoke(stage_report, days_back=days_back, regenerate=regenerate, output_date=output_date, bulk=bulk, debug=debug, sitemap=sitemap, rss=rss)


@cli.command()
def publish():
    """Publish DuckDB query interface to output directory."""
    from src.cli.stage_commands import publish as stage_publish
    ctx = click.Context(stage_publish)
    ctx.invoke(stage_publish)


@cli.command()
@click.option("--date", "target_date", help="Date for logging only (YYYY-MM-DD). Posts organized by publication date.")
@click.option("--max-posts", default=100, help="Maximum posts to collect")
@click.option("--search", default="mcp_tag", help="Search definition to use")
@click.option("--config", "config_path", help="Path to search configuration YAML file")
@click.option("--expand-urls/--no-expand-urls", default=True, help="Expand shortened URLs to final destinations")
@click.option("--threads/--no-threads", default=False, help="Collect entire threads instead of just individual posts")
@click.option("--max-thread-depth", default=6, help="Maximum depth to traverse in thread replies (default: 6)")
@click.option("--max-parent-height", default=80, help="Maximum height to traverse up parent chain (default: 80)")
@click.option("--days-back", default=7, help="Days to look back for unfetched URLs and unevaluated content (default: 7)")
@click.option("--regenerate-reports/--no-regenerate-reports", default=True, help="Regenerate existing reports (default: True)")
@click.option("--regenerate-evaluations/--no-regenerate-evaluations", default=False, help="Re-evaluate existing evaluations (default: False)")
@click.option("--export-parquet/--no-export-parquet", default=True, help="Export data to Parquet files for analytics (default: True)")
@click.option("--expand-references/--no-expand-references", default=True, help="Expand Bluesky post references into new posts (default: True)")
@click.option("--max-reference-depth", default=2, help="Maximum depth for reference expansion (default: 2)")
@click.option("--sitemap/--no-sitemap", default=True, help="Generate sitemap.xml (default: True)")
@click.option("--rss/--no-rss", default=True, help="Generate rss.xml (default: True)")
@click.option("--publish/--no-publish", default=True, help="Publish DuckDB query interface (default: True)")
def run_all(target_date, max_posts, search, config_path, expand_urls, threads, max_thread_depth, max_parent_height, days_back, regenerate_reports, regenerate_evaluations, export_parquet, expand_references, max_reference_depth, sitemap, rss, publish):
    """Run all stages in sequence. Posts are organized by their publication date."""
    from src.cli.stage_commands import run_all as stage_run_all
    ctx = click.Context(stage_run_all)
    ctx.invoke(stage_run_all, target_date=target_date, max_posts=max_posts, search=search, config_path=config_path, expand_urls=expand_urls, threads=threads, max_thread_depth=max_thread_depth, max_parent_height=max_parent_height, days_back=days_back, regenerate_reports=regenerate_reports, regenerate_evaluations=regenerate_evaluations, export_parquet=export_parquet, expand_references=expand_references, max_reference_depth=max_reference_depth, sitemap=sitemap, rss=rss, publish=publish)


@cli.command()
@click.option("--date", "target_date", help="Date to check status for (YYYY-MM-DD), defaults to today")
def status(target_date):
    """Show status of all stages for a date."""
    from src.cli.stage_commands import status as stage_status
    ctx = click.Context(stage_status)
    ctx.invoke(stage_status, target_date=target_date)


@cli.command()
@click.option("--port", default=8000, help="Port to serve on (default: 8000)")
@click.option("--host", default="localhost", help="Host to bind to (default: localhost)")
def present(port, host):
    """Start HTTP server to view generated HTML reports."""
    from src.cli.stage_commands import present as stage_present
    ctx = click.Context(stage_present)
    ctx.invoke(stage_present, port=port, host=host)


if __name__ == "__main__":
    cli()