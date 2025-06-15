"""Stage-based CLI commands for the refactored architecture."""

import asyncio
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config.searches import load_search_config
from src.config.settings import get_settings
from src.stages.collect import CollectStage
from src.stages.fetch import FetchStage
from src.stages.evaluate import EvaluateStage
from src.stages.report import ReportStage
from src.stages.markdown import MarkdownFile

console = Console()


def parse_date(date_str: Optional[str]) -> date:
    """Parse date string or return today if None."""
    if date_str:
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            console.print(f"❌ Invalid date format: {date_str}. Use YYYY-MM-DD", style="red")
            sys.exit(1)
    return date.today()


@click.group()
def stages():
    """Stage-based processing commands"""
    pass


@stages.command()
@click.option("--date", "target_date", help="Date for logging only (YYYY-MM-DD). Posts organized by publication date.")
@click.option("--max-posts", default=200, help="Maximum posts to collect")
@click.option("--search", default="mcp_tag", help="Search definition to use")
@click.option("--config", "config_path", help="Path to search configuration YAML file")
@click.option("--expand-urls/--no-expand-urls", default=True, help="Expand shortened URLs to final destinations")
def collect(target_date: Optional[str], max_posts: int, search: str, config_path: Optional[str], expand_urls: bool):
    """Collect posts from Bluesky. Posts are organized by their publication date."""
    
    parsed_date = parse_date(target_date)
    console.print(f"🔍 Collecting posts using search '{search}'...")
    
    try:
        settings = get_settings()
        
        if not settings.has_bluesky_credentials:
            console.print("❌ Bluesky credentials not configured", style="red")
            console.print("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables")
            sys.exit(1)
        
        # Load search configuration
        search_config = load_search_config(config_path)
        search_definition = search_config.get_search(search)
        
        if not search_definition:
            console.print(f"❌ Search definition '{search}' not found", style="red")
            available_searches = list(search_config.searches.keys())
            console.print(f"Available searches: {', '.join(available_searches)}")
            sys.exit(1)
        
        if not search_definition.enabled:
            console.print(f"❌ Search definition '{search}' is disabled", style="red")
            sys.exit(1)
        
        # Create and run collect stage
        collect_stage = CollectStage(
            settings=settings,
            search_definition=search_definition,
            max_posts=max_posts,
            expand_urls=expand_urls
        )
        
        result = asyncio.run(collect_stage.run_collection(parsed_date))
        
        console.print(f"✅ Collection completed:", style="green")
        console.print(f"  • New posts: {result.get('new_posts', 0)}")
        console.print(f"  • Updated posts: {result.get('updated_posts', 0)}")
        console.print(f"  • Failed: {result['failed']}")
        console.print(f"  • Total: {result['total']}")
        
        # Show posts by date
        posts_by_date = result.get('posts_by_date', {})
        if posts_by_date:
            console.print("\n📅 Posts by publication date:")
            for date_str, count in sorted(posts_by_date.items()):
                console.print(f"  • {date_str}: {count} posts")
        
    except Exception as e:
        console.print(f"❌ Collection failed: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option("--days-back", default=7, help="Number of days to look back for unfetched URLs (default: 7)")
def fetch(days_back: int):
    """Fetch full content from URLs found in collected posts from the last N days."""
    
    console.print(f"🌐 Fetching content from posts in the last {days_back} days...")
    
    try:
        fetch_stage = FetchStage()
        result = asyncio.run(fetch_stage.run_fetch(days_back))
        
        console.print(f"✅ Fetch completed:", style="green")
        console.print(f"  • Date range: {result['date_range']}")
        console.print(f"  • Processed posts: {result['processed_posts']}")
        console.print(f"  • New URLs fetched: {result['new_urls_fetched']}")
        console.print(f"  • Previously fetched: {result['previously_fetched']}")
        console.print(f"  • Total URLs found: {result['total_urls_found']}")
        
        # Show URLs by date if any were fetched
        urls_by_date = result.get('urls_by_date', {})
        if urls_by_date:
            console.print("\n📅 URLs fetched by date:")
            for date_str, count in sorted(urls_by_date.items()):
                console.print(f"  • {date_str}: {count} URLs")
        
    except Exception as e:
        console.print(f"❌ Fetch failed: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option("--days-back", default=7, help="Number of days to look back for unevaluated content (default: 7)")
def evaluate(days_back: int):
    """Evaluate content relevance using Anthropic API for fetched content from the last N days."""
    
    console.print(f"🤖 Evaluating content from the last {days_back} days...")
    
    try:
        settings = get_settings()
        
        if not settings.anthropic_api_key:
            console.print("❌ Anthropic API key not configured", style="red")
            console.print("Set ANTHROPIC_API_KEY environment variable")
            sys.exit(1)
        
        evaluate_stage = EvaluateStage(settings)
        result = asyncio.run(evaluate_stage.run_evaluate(days_back))
        
        console.print(f"✅ Evaluation completed:", style="green")
        console.print(f"  • Date range: {result['date_range']}")
        console.print(f"  • New evaluations: {result['new_evaluations']}")
        console.print(f"  • Previously evaluated: {result['previously_evaluated']}")
        console.print(f"  • Skipped: {result['skipped']}")
        console.print(f"  • Failed: {result['failed']}")
        console.print(f"  • MCP related: {result['mcp_related']}")
        console.print(f"  • Avg relevance: {result['avg_relevance_score']}")
        
        # Show evaluations by date if any were processed
        evaluations_by_date = result.get('evaluations_by_date', {})
        if evaluations_by_date:
            console.print("\n📅 Evaluations by date:")
            for date_str, count in sorted(evaluations_by_date.items()):
                console.print(f"  • {date_str}: {count} evaluations")
        
    except Exception as e:
        console.print(f"❌ Evaluation failed: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option("--days-back", default=7, help="Number of days to look back for evaluated content (default: 7)")
@click.option("--regenerate/--no-regenerate", default=True, help="Regenerate existing reports (default: True)")
@click.option("--output-date", help="Date to use for report filename (YYYY-MM-DD), defaults to today")
def report(days_back: int, regenerate: bool, output_date: Optional[str]):
    """Generate report from evaluated content in the last N days."""
    
    parsed_output_date = parse_date(output_date)
    console.print(f"📊 Generating report from content in the last {days_back} days...")
    
    try:
        report_stage = ReportStage()
        result = asyncio.run(report_stage.run_report(days_back, regenerate, parsed_output_date))
        
        if result.get("status") == "already_exists":
            console.print(f"ℹ️  Report already exists for {parsed_output_date}", style="yellow")
            return
        
        console.print(f"✅ Report completed:", style="green")
        console.print(f"  • Days scanned: {result['days_scanned']}")
        console.print(f"  • Articles found: {result['articles_found']}")
        console.print(f"  • Report generated: {result['report_generated']}")
        console.print(f"  • Homepage generated: {result.get('homepage_generated', False)}")
        console.print(f"  • Metadata saved: {result['metadata_saved']}")
        console.print(f"  • Output date: {result['date']}")
        console.print(f"  • Avg relevance: {result.get('avg_relevance', 0)}")
        
        if result['articles_found'] > 0:
            console.print(f"  • Avg relevance: {result['avg_relevance']}")
        
    except Exception as e:
        console.print(f"❌ Report generation failed: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option("--date", "target_date", help="Date for logging only (YYYY-MM-DD). Posts organized by publication date.")
@click.option("--max-posts", default=200, help="Maximum posts to collect")
@click.option("--search", default="mcp_tag", help="Search definition to use")
@click.option("--config", "config_path", help="Path to search configuration YAML file")
@click.option("--expand-urls/--no-expand-urls", default=True, help="Expand shortened URLs to final destinations")
@click.option("--days-back", default=7, help="Days to look back for unfetched URLs (default: 7)")
@click.option("--regenerate/--no-regenerate", default=True, help="Regenerate existing reports (default: True)")
def run_all(target_date: Optional[str], max_posts: int, search: str, config_path: Optional[str], expand_urls: bool, days_back: int, regenerate: bool):
    """Run all stages in sequence. Posts organized by publication date."""
    
    parsed_date = parse_date(target_date)
    console.print(f"🚀 Running all stages...")
    
    # Stage 1: Collect
    console.print("\n[bold blue]Stage 1: Collect[/bold blue]")
    ctx = click.Context(collect)
    ctx.invoke(collect, target_date=target_date, max_posts=max_posts, search=search, config_path=config_path, expand_urls=expand_urls)
    
    # Stage 2: Fetch
    console.print("\n[bold blue]Stage 2: Fetch[/bold blue]")
    ctx = click.Context(fetch)
    ctx.invoke(fetch, days_back=days_back)
    
    # Stage 3: Evaluate
    console.print("\n[bold blue]Stage 3: Evaluate[/bold blue]")
    ctx = click.Context(evaluate)
    ctx.invoke(evaluate, days_back=days_back)
    
    # Stage 4: Report
    console.print("\n[bold blue]Stage 4: Report[/bold blue]")
    ctx = click.Context(report)
    ctx.invoke(report, days_back=days_back, regenerate=regenerate, output_date=target_date)
    
    console.print(f"\n✅ All stages completed for {parsed_date}!", style="green")


@stages.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
def status(target_date: Optional[str]):
    """Show status of all stages for a date."""
    
    parsed_date = parse_date(target_date)
    
    # Check each stage directory
    stages_base = Path("stages")
    stage_names = ["collect", "fetch", "evaluate", "report"]
    
    table = Table(title=f"Stage Status for {parsed_date}")
    table.add_column("Stage", style="cyan")
    table.add_column("Files", justify="right")
    table.add_column("Status", style="green")
    
    for stage_name in stage_names:
        stage_dir = stages_base / stage_name / parsed_date.strftime("%Y-%m-%d")
        
        if stage_dir.exists():
            files = list(stage_dir.glob("*.md")) + list(stage_dir.glob("*.html"))
            count = len(files)
            status_text = "✅ Complete" if count > 0 else "📂 Empty"
        else:
            count = 0
            status_text = "❌ Missing"
        
        table.add_row(stage_name.title(), str(count), status_text)
    
    console.print(table)


@stages.command()
@click.argument("stage_name", type=click.Choice(["collect", "fetch", "evaluate", "report"]))
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--limit", default=10, help="Maximum number of files to list")
def list_files(stage_name: str, target_date: Optional[str], limit: int):
    """List files in a specific stage."""
    
    parsed_date = parse_date(target_date)
    stage_dir = Path("stages") / stage_name / parsed_date.strftime("%Y-%m-%d")
    
    if not stage_dir.exists():
        console.print(f"❌ Stage directory does not exist: {stage_dir}", style="red")
        return
    
    files = list(stage_dir.glob("*.md")) + list(stage_dir.glob("*.html"))
    
    if not files:
        console.print(f"📂 No files found in {stage_name} stage for {parsed_date}")
        return
    
    table = Table(title=f"{stage_name.title()} Stage Files for {parsed_date}")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Modified", style="dim")
    
    for file_path in sorted(files)[:limit]:
        stat = file_path.stat()
        size = f"{stat.st_size:,} bytes"
        modified = file_path.stat().st_mtime
        
        table.add_row(file_path.name, size, f"{modified:.0f}")
    
    if len(files) > limit:
        console.print(f"\n... and {len(files) - limit} more files")
    
    console.print(table)


@stages.command()
@click.argument("stage_name", type=click.Choice(["collect", "fetch", "evaluate", "report"]))
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def clean(stage_name: str, target_date: Optional[str], confirm: bool):
    """Clean (remove) all files from a specific stage."""
    
    parsed_date = parse_date(target_date)
    stage_dir = Path("stages") / stage_name / parsed_date.strftime("%Y-%m-%d")
    
    if not stage_dir.exists():
        console.print(f"❌ Stage directory does not exist: {stage_dir}", style="red")
        return
    
    files = list(stage_dir.glob("*"))
    
    if not files:
        console.print(f"📂 No files to clean in {stage_name} stage for {parsed_date}")
        return
    
    if not confirm:
        console.print(f"⚠️  This will delete {len(files)} files from {stage_name} stage for {parsed_date}")
        if not click.confirm("Do you want to continue?"):
            console.print("❌ Cancelled")
            return
    
    for file_path in files:
        file_path.unlink()
    
    # Remove directory if empty
    try:
        stage_dir.rmdir()
    except OSError:
        pass  # Directory not empty
    
    console.print(f"✅ Cleaned {len(files)} files from {stage_name} stage", style="green")


if __name__ == "__main__":
    stages()