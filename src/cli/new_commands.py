"""New streamlined CLI commands focused on stage-based architecture."""

import click
from rich.console import Console

from src.cli.stage_commands import stages

console = Console()


@click.group()
def cli():
    """Bluesky MCP Monitor - Stage-based Processing"""
    pass


# Add the stage-based commands as the primary interface
cli.add_command(stages)

# Add convenient top-level aliases for the most common operations
@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--max-posts", default=100, help="Maximum posts to collect")
@click.option("--search", default="mcp_tag", help="Search definition to use")
@click.option("--config", "config_path", help="Path to search configuration YAML file")
@click.option("--expand-urls/--no-expand-urls", default=True, help="Expand shortened URLs to final destinations")
def collect(target_date, max_posts, search, config_path, expand_urls):
    """Collect posts using stage-based architecture."""
    from src.cli.stage_commands import collect as stage_collect
    ctx = click.Context(stage_collect)
    ctx.invoke(stage_collect, target_date=target_date, max_posts=max_posts, search=search, config_path=config_path, expand_urls=expand_urls)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
def fetch(target_date):
    """Fetch content using stage-based architecture."""
    from src.cli.stage_commands import fetch as stage_fetch
    ctx = click.Context(stage_fetch)
    ctx.invoke(stage_fetch, target_date=target_date)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
def evaluate(target_date):
    """Evaluate content using stage-based architecture."""
    from src.cli.stage_commands import evaluate as stage_evaluate
    ctx = click.Context(stage_evaluate)
    ctx.invoke(stage_evaluate, target_date=target_date)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--regenerate/--no-regenerate", default=True, help="Regenerate existing reports (default: True)")
def report(target_date, regenerate):
    """Generate report using stage-based architecture."""
    from src.cli.stage_commands import report as stage_report
    ctx = click.Context(stage_report)
    ctx.invoke(stage_report, target_date=target_date, regenerate=regenerate)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--max-posts", default=100, help="Maximum posts to collect")
@click.option("--search", default="mcp_tag", help="Search definition to use")
@click.option("--config", "config_path", help="Path to search configuration YAML file")
@click.option("--expand-urls/--no-expand-urls", default=True, help="Expand shortened URLs to final destinations")
@click.option("--regenerate/--no-regenerate", default=True, help="Regenerate existing reports (default: True)")
def run_all(target_date, max_posts, search, config_path, expand_urls, regenerate):
    """Run all stages in sequence for the specified date."""
    from src.cli.stage_commands import run_all as stage_run_all
    ctx = click.Context(stage_run_all)
    ctx.invoke(stage_run_all, target_date=target_date, max_posts=max_posts, search=search, config_path=config_path, expand_urls=expand_urls, regenerate=regenerate)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
def status(target_date):
    """Show status of all stages for a date."""
    from src.cli.stage_commands import status as stage_status
    ctx = click.Context(stage_status)
    ctx.invoke(stage_status, target_date=target_date)


if __name__ == "__main__":
    cli()