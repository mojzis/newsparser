"""Stage-based CLI commands for the refactored architecture."""

import asyncio
import contextlib
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import click
import markdown
from rich.console import Console
from rich.table import Table

from src.config.collection import CollectionConfig, load_collection
from src.config.settings import get_settings
from src.stages.collect import CollectStage
from src.stages.evaluate import EvaluateStage
from src.stages.fetch import FetchStage
from src.stages.report import ReportStage

console = Console()


def parse_date(date_str: str | None) -> date:
    """Parse date string or return today if None."""
    if date_str:
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            console.print(
                f"❌ Invalid date format: {date_str}. Use YYYY-MM-DD", style="red"
            )
            sys.exit(1)
    return datetime.now(UTC).date()


def load_collection_or_exit(collection_name: str) -> CollectionConfig:
    """Load a collection, exiting with a friendly error if it's not found."""
    try:
        return load_collection(collection_name)
    except FileNotFoundError as e:
        console.print(f"❌ {e}", style="red")
        sys.exit(1)


@click.group()
def stages() -> None:
    """Stage-based processing commands"""


@stages.command()
@click.option(
    "--date",
    "target_date",
    help="Date for logging only (YYYY-MM-DD). Posts organized by publication date.",
)
@click.option("--max-posts", default=400, help="Maximum posts to collect")
@click.option(
    "--search",
    default=None,
    help="Search definition to use (defaults to the collection's default_search)",
)
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
@click.option(
    "--expand-urls/--no-expand-urls",
    default=True,
    help="Expand shortened URLs to final destinations",
)
@click.option(
    "--threads/--no-threads",
    default=True,
    help="Collect entire threads instead of just individual posts",
)
@click.option(
    "--max-thread-depth",
    default=6,
    help="Maximum depth to traverse in thread replies (default: 6)",
)
@click.option(
    "--max-parent-height",
    default=80,
    help="Maximum height to traverse up parent chain (default: 80)",
)
@click.option(
    "--export-parquet/--no-export-parquet",
    default=True,
    help="Export data to Parquet files for analytics (default: True)",
)
@click.option(
    "--expand-references/--no-expand-references",
    default=True,
    help="Expand Bluesky post references into new posts (default: True)",
)
@click.option(
    "--max-reference-depth",
    default=2,
    help="Maximum depth for reference expansion (default: 2)",
)
def collect(
    target_date: str | None,
    max_posts: int,
    search: str | None,
    collection_name: str,
    expand_urls: bool,
    threads: bool,
    max_thread_depth: int,
    max_parent_height: int,
    export_parquet: bool,
    expand_references: bool,
    max_reference_depth: int,
) -> None:
    """Collect posts from Bluesky. Posts are organized by their publication date."""

    parsed_date = parse_date(target_date)

    try:
        collection = load_collection(collection_name)
        search_key = search or collection.default_search

        mode_text = "threads" if threads else "posts"
        console.print(f"🔍 Collecting {mode_text} using search '{search_key}'...")

        if threads:
            console.print(
                f"   Thread collection enabled: depth={max_thread_depth}, parent_height={max_parent_height}"
            )

        settings = get_settings()

        if not settings.has_bluesky_credentials:
            console.print("❌ Bluesky credentials not configured", style="red")
            console.print(
                "Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables"
            )
            sys.exit(1)

        search_definition = collection.searches.get_search(search_key)

        if not search_definition:
            console.print(f"❌ Search definition '{search_key}' not found", style="red")
            available_searches = list(collection.searches.searches.keys())
            console.print(f"Available searches: {', '.join(available_searches)}")
            sys.exit(1)

        if not search_definition.enabled:
            console.print(
                f"❌ Search definition '{search_key}' is disabled", style="red"
            )
            sys.exit(1)

        # Create and run collect stage
        collect_stage = CollectStage(
            settings=settings,
            search_definition=search_definition,
            max_posts=max_posts,
            expand_urls=expand_urls,
            collect_threads=threads,
            max_thread_depth=max_thread_depth,
            max_parent_height=max_parent_height,
            export_parquet=export_parquet,
            expand_references=expand_references,
            max_reference_depth=max_reference_depth,
            base_path=collection.stages_base,
        )

        result = asyncio.run(collect_stage.run_collection(parsed_date))

        console.print("✅ Collection completed:", style="green")
        console.print(f"  • New posts: {result.get('new_posts', 0)}")
        console.print(f"  • Updated posts: {result.get('updated_posts', 0)}")
        console.print(f"  • Failed: {result['failed']}")
        console.print(f"  • Total: {result['total']}")

        # Show posts by date
        posts_by_date = result.get("posts_by_date", {})
        if posts_by_date:
            console.print("\n📅 Posts by publication date:")
            for date_str, count in sorted(posts_by_date.items()):
                console.print(f"  • {date_str}: {count} posts")

    except Exception as e:
        console.print(f"❌ Collection failed: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option(
    "--days-back",
    default=7,
    help="Number of days to look back for unfetched URLs (default: 7)",
)
@click.option(
    "--export-parquet/--no-export-parquet",
    default=True,
    help="Export data to Parquet files for analytics (default: True)",
)
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
def fetch(days_back: int, export_parquet: bool, collection_name: str) -> None:
    """Fetch full content from URLs found in collected posts from the last N days."""

    console.print(f"🌐 Fetching content from posts in the last {days_back} days...")

    try:
        collection = load_collection(collection_name)
        fetch_stage = FetchStage(
            export_parquet=export_parquet, base_path=collection.stages_base
        )
        result = asyncio.run(fetch_stage.run_fetch(days_back))

        console.print("✅ Fetch completed:", style="green")
        console.print(f"  • Date range: {result['date_range']}")
        console.print(f"  • Processed posts: {result['processed_posts']}")
        console.print(f"  • New URLs fetched: {result['new_urls_fetched']}")
        console.print(f"  • Previously fetched: {result['previously_fetched']}")
        console.print(f"  • Total URLs found: {result['total_urls_found']}")

        # Show URLs by date if any were fetched
        urls_by_date = result.get("urls_by_date", {})
        if urls_by_date:
            console.print("\n📅 URLs fetched by date:")
            for date_str, count in sorted(urls_by_date.items()):
                console.print(f"  • {date_str}: {count} URLs")

    except Exception as e:
        console.print(f"❌ Fetch failed: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option(
    "--days-back",
    default=7,
    help="Number of days to look back for unevaluated content (default: 7)",
)
@click.option(
    "--regenerate/--no-regenerate",
    default=False,
    help="Re-evaluate existing evaluations (default: False)",
)
@click.option(
    "--export-parquet/--no-export-parquet",
    default=True,
    help="Export data to Parquet files for analytics (default: True)",
)
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
def evaluate(
    days_back: int, regenerate: bool, export_parquet: bool, collection_name: str
) -> None:
    """Evaluate content relevance using Anthropic API for fetched content from the last N days."""

    if regenerate:
        console.print(f"🤖 Re-evaluating content from the last {days_back} days...")
    else:
        console.print(f"🤖 Evaluating new content from the last {days_back} days...")

    try:
        collection = load_collection(collection_name)
        settings = get_settings()

        if not settings.anthropic_api_key:
            console.print("❌ Anthropic API key not configured", style="red")
            console.print("Set ANTHROPIC_API_KEY environment variable")
            sys.exit(1)

        evaluate_stage = EvaluateStage(
            settings,
            base_path=collection.stages_base,
            export_parquet=export_parquet,
            collection=collection,
        )
        result = asyncio.run(
            evaluate_stage.run_evaluate(days_back, regenerate=regenerate)
        )

        console.print("✅ Evaluation completed:", style="green")
        console.print(f"  • Date range: {result['date_range']}")
        console.print(f"  • New evaluations: {result['new_evaluations']}")
        console.print(f"  • Previously evaluated: {result['previously_evaluated']}")
        console.print(f"  • Skipped: {result['skipped']}")
        console.print(f"  • Failed: {result['failed']}")
        console.print(f"  • Relevant: {result['relevant']}")
        console.print(f"  • Avg relevance: {result['avg_relevance_score']}")

        # Show evaluations by date if any were processed
        evaluations_by_date = result.get("evaluations_by_date", {})
        if evaluations_by_date:
            console.print("\n📅 Evaluations by date:")
            for date_str, count in sorted(evaluations_by_date.items()):
                console.print(f"  • {date_str}: {count} evaluations")

    except Exception as e:
        console.print(f"❌ Evaluation failed: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option(
    "--days-back",
    default=7,
    help="Number of days to look back for evaluated content (default: 7)",
)
@click.option(
    "--regenerate/--no-regenerate",
    default=True,
    help="Regenerate existing reports (default: True)",
)
@click.option(
    "--output-date",
    help="Date to use for report filename (YYYY-MM-DD), defaults to today",
)
@click.option(
    "--bulk/--single",
    default=False,
    help="Generate reports for all days with content in range (default: auto-detect)",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Show debug information including evaluation filenames",
)
@click.option(
    "--sitemap/--no-sitemap", default=True, help="Generate sitemap.xml (default: True)"
)
@click.option("--rss/--no-rss", default=True, help="Generate rss.xml (default: True)")
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
def report(
    days_back: int,
    regenerate: bool,
    output_date: str | None,
    bulk: bool,
    debug: bool,
    sitemap: bool,
    rss: bool,
    collection_name: str,
) -> None:
    """Generate report from evaluated content in the last N days."""

    parsed_output_date = parse_date(output_date)

    # Auto-enable bulk mode if days_back > 0 and not explicitly set to single
    if days_back > 0 and not bulk:
        bulk = True
        console.print(
            f"📊 Auto-enabling bulk mode to regenerate reports for all {days_back} days with content..."
        )
    elif bulk:
        console.print(
            f"📊 Generating reports for each day with content in the last {days_back} days..."
        )
    else:
        console.print(
            f"📊 Generating single report from content in the last {days_back} days..."
        )

    try:
        collection = load_collection(collection_name)
        report_stage = ReportStage(
            base_path=collection.stages_base, output_base=collection.output_base
        )

        if bulk:
            result = asyncio.run(
                report_stage.run_bulk_report(
                    days_back, regenerate, parsed_output_date, debug, sitemap, rss
                )
            )

            console.print("✅ Bulk report generation completed:", style="green")
            console.print(f"  • Reference date: {result['reference_date']}")
            console.print(f"  • Days scanned: {result['days_scanned']}")
            console.print(f"  • Reports generated: {result['reports_generated']}")
            console.print(f"  • Total articles: {result['total_articles']}")
            console.print(
                f"  • Dates processed: {', '.join(result['dates_processed'])}"
            )
        else:
            result = asyncio.run(
                report_stage.run_report(
                    days_back, regenerate, parsed_output_date, debug, sitemap, rss
                )
            )

            if result.get("status") == "already_exists":
                console.print(
                    f"ℹ️  Report already exists for {parsed_output_date}", style="yellow"
                )
                return

            console.print("✅ Report completed:", style="green")
            console.print(f"  • Days scanned: {result['days_scanned']}")
            console.print(f"  • Articles found: {result['articles_found']}")
            console.print(f"  • Report generated: {result['report_generated']}")
            console.print(
                f"  • Homepage generated: {result.get('homepage_generated', False)}"
            )
            console.print(f"  • Metadata saved: {result['metadata_saved']}")
            console.print(f"  • Output date: {result['date']}")
            console.print(f"  • Avg relevance: {result.get('avg_relevance', 0)}")

            if result["articles_found"] > 0:
                console.print(f"  • Avg relevance: {result['avg_relevance']}")

    except Exception as e:
        console.print(f"❌ Report generation failed: {e}", style="red")
        sys.exit(1)


@stages.command()
def render_stats() -> None:
    """Generate statistics pages from marimo notebooks."""
    import re
    import subprocess

    # Notebooks to render
    notebooks = [
        {
            "file": Path("notebooks/content_stats.py"),
            "output": "content_stats.html",
            "title": "Content Stats",
            "active_menu": "stats",
        },
        {
            "file": Path("notebooks/stats.py"),
            "output": "project_stats.html",
            "title": "Project Stats",
            "active_menu": "stats",
        },
    ]

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for notebook_config in notebooks:
        notebook_file = Path(notebook_config["file"])
        output_filename = notebook_config["output"]

        # Check if notebook exists
        if not notebook_file.exists():
            console.print(f"❌ Notebook file not found: {notebook_file}", style="red")
            continue

        try:
            # Export marimo notebook to HTML
            output_file = output_dir / output_filename

            # Run marimo export command
            result = subprocess.run(  # noqa: S603  fixed trusted command from venv PATH
                [  # noqa: S607  partial executable path "marimo" resolved from PATH
                    "marimo",
                    "export",
                    "html",
                    str(notebook_file),
                    "--output",
                    str(output_file),
                    "--no-include-code",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                console.print(
                    f"❌ Failed to export {notebook_file}: {result.stderr}", style="red"
                )
                continue

            # Post-process the HTML to add navigation
            with open(output_file, encoding="utf-8") as f:
                html_content = f.read()

            # Navigation HTML with active menu highlighting
            nav_html = f"""
    <nav class="navbar" style="background-color: #2c3e50; padding: 1rem 0; margin-bottom: 20px;">
        <div class="nav-container" style="max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center;">
            <div class="nav-brand">
                <a href="/index.html" style="color: white; font-size: 1.2rem; font-weight: 600; text-decoration: none; letter-spacing: -0.3px;">Bluesky MCP Monitor</a>
            </div>
            <ul class="nav-menu" style="display: flex; list-style: none; margin: 0; padding: 0; gap: 2rem;">
                <li class="nav-item" style="margin: 0;">
                    <a href="/index.html" class="nav-link" style="color: #bdc3c7; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; transition: background-color 0.3s ease; font-size: 15px;">Home</a>
                </li>
                <li class="nav-item" style="margin: 0;">
                    <a href="/query/duckdb.html" class="nav-link" style="color: #bdc3c7; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; transition: background-color 0.3s ease; font-size: 15px;">Query</a>
                </li>
                <li class="nav-item" style="margin: 0;">
                    <a href="/content_stats.html" class="nav-link" style="{"background-color: #3498db; color: white;" if notebook_config["active_menu"] == "stats" else "color: #bdc3c7;"} text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; transition: background-color 0.3s ease; font-size: 15px;">Stats</a>
                </li>
                <li class="nav-item" style="margin: 0;">
                    <a href="/about.html" class="nav-link" style="color: #bdc3c7; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; transition: background-color 0.3s ease; font-size: 15px;">About</a>
                </li>
            </ul>
        </div>
    </nav>"""

            # Insert navigation after the <body> tag
            html_content = re.sub(r"(<body[^>]*>)", r"\1" + nav_html, html_content)

            # Write the modified HTML back
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            file_size = output_file.stat().st_size
            console.print(f"✅ Generated {notebook_config['title']} at {output_file}")
            console.print(f"📊 File size: {file_size:,} bytes")

        except subprocess.TimeoutExpired:
            console.print(f"❌ {notebook_file} export timed out", style="red")
            continue
        except Exception as e:
            console.print(f"❌ Failed to generate {notebook_file}: {e}", style="red")
            continue

    console.print("🌐 Access content stats at: output/content_stats.html")
    console.print("🌐 Access project stats at: output/project_stats.html")


@stages.command()
def render_about() -> None:
    """Render about page from markdown file."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    # Source markdown file
    source_file = Path("lyrics/about.md")

    # Check if source exists
    if not source_file.exists():
        console.print(f"❌ Source file not found: {source_file}", style="red")
        sys.exit(1)

    try:
        # Read markdown content
        with open(source_file, encoding="utf-8") as f:
            markdown_content = f.read()

        # Process Mermaid blocks before markdown conversion
        import re

        def replace_mermaid(match):
            mermaid_code = match.group(1)
            return f'<div class="mermaid">\n{mermaid_code}\n</div>'

        # Replace ```mermaid blocks with <div class="mermaid">
        markdown_content = re.sub(
            r"```mermaid\n(.*?)\n```",
            replace_mermaid,
            markdown_content,
            flags=re.DOTALL,
        )

        # Convert markdown to HTML
        html_content = markdown.markdown(markdown_content)

        # Set up Jinja2 environment
        env = Environment(
            loader=FileSystemLoader("src/templates"), autoescape=select_autoescape()
        )

        # Load the about template
        template = env.get_template("about.html")

        # Render with content
        template_str = template.render(active_menu="about")
        final_html = template_str.replace("{content}", html_content)

        # Create output directory and write file
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "about.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)

        file_size = output_file.stat().st_size
        console.print(f"✅ Rendered about page to {output_file}")
        console.print(f"📊 File size: {file_size:,} bytes")

    except Exception as e:
        console.print(f"❌ Failed to render about page: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option(
    "--date",
    "target_date",
    help="Date for logging only (YYYY-MM-DD). Posts organized by publication date.",
)
@click.option("--max-posts", default=500, help="Maximum posts to collect")
@click.option(
    "--search",
    default=None,
    help="Search definition to use (defaults to the collection's default_search)",
)
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
@click.option(
    "--expand-urls/--no-expand-urls",
    default=True,
    help="Expand shortened URLs to final destinations",
)
@click.option(
    "--threads/--no-threads",
    default=True,
    help="Collect entire threads instead of just individual posts",
)
@click.option(
    "--max-thread-depth",
    default=6,
    help="Maximum depth to traverse in thread replies (default: 6)",
)
@click.option(
    "--max-parent-height",
    default=80,
    help="Maximum height to traverse up parent chain (default: 80)",
)
@click.option(
    "--days-back", default=7, help="Days to look back for unfetched URLs (default: 7)"
)
@click.option(
    "--regenerate-reports/--no-regenerate-reports",
    default=True,
    help="Regenerate existing reports (default: True)",
)
@click.option(
    "--regenerate-evaluations/--no-regenerate-evaluations",
    default=False,
    help="Re-evaluate existing evaluations (default: False)",
)
@click.option(
    "--export-parquet/--no-export-parquet",
    default=True,
    help="Export data to Parquet files for analytics (default: True)",
)
@click.option(
    "--expand-references/--no-expand-references",
    default=True,
    help="Expand Bluesky post references into new posts (default: True)",
)
@click.option(
    "--max-reference-depth",
    default=2,
    help="Maximum depth for reference expansion (default: 2)",
)
@click.option(
    "--sitemap/--no-sitemap", default=True, help="Generate sitemap.xml (default: True)"
)
@click.option("--rss/--no-rss", default=True, help="Generate rss.xml (default: True)")
@click.option(
    "--publish/--no-publish",
    default=True,
    help="Publish DuckDB query interface (default: True)",
)
def run_all(
    target_date: str | None,
    max_posts: int,
    search: str | None,
    collection_name: str,
    expand_urls: bool,
    threads: bool,
    max_thread_depth: int,
    max_parent_height: int,
    days_back: int,
    regenerate_reports: bool,
    regenerate_evaluations: bool,
    export_parquet: bool,
    expand_references: bool,
    max_reference_depth: int,
    sitemap: bool,
    rss: bool,
    publish: bool,
) -> None:
    """Run all stages in sequence. Posts organized by publication date."""

    # Store reference to publish command before parameter shadows it
    publish_cmd = globals()["publish"]

    parsed_date = parse_date(target_date)
    console.print("🚀 Running all stages...")

    # Stage 1: Collect
    console.print("\n[bold blue]Stage 1: Collect[/bold blue]")
    ctx = click.Context(collect)
    ctx.invoke(
        collect,
        target_date=target_date,
        max_posts=max_posts,
        search=search,
        collection_name=collection_name,
        expand_urls=expand_urls,
        threads=threads,
        max_thread_depth=max_thread_depth,
        max_parent_height=max_parent_height,
        export_parquet=export_parquet,
        expand_references=expand_references,
        max_reference_depth=max_reference_depth,
    )

    # Stage 2: Fetch
    console.print("\n[bold blue]Stage 2: Fetch[/bold blue]")
    ctx = click.Context(fetch)
    ctx.invoke(
        fetch,
        days_back=days_back,
        export_parquet=export_parquet,
        collection_name=collection_name,
    )

    # Stage 3: Evaluate
    console.print("\n[bold blue]Stage 3: Evaluate[/bold blue]")
    ctx = click.Context(evaluate)
    ctx.invoke(
        evaluate,
        days_back=days_back,
        regenerate=regenerate_evaluations,
        export_parquet=export_parquet,
        collection_name=collection_name,
    )

    # Stage 4: Report
    console.print("\n[bold blue]Stage 4: Report[/bold blue]")
    ctx = click.Context(report)
    ctx.invoke(
        report,
        days_back=days_back,
        regenerate=regenerate_reports,
        output_date=target_date,
        sitemap=sitemap,
        rss=rss,
        collection_name=collection_name,
    )

    # Stage 5: Render Stats
    console.print("\n[bold blue]Stage 5: Render Stats[/bold blue]")
    assert render_stats.callback is not None
    render_stats.callback()

    # Stage 6: Render About
    console.print("\n[bold blue]Stage 6: Render About[/bold blue]")
    assert render_about.callback is not None
    render_about.callback()

    # Stage 7: Publish (optional)
    if publish:
        console.print("\n[bold blue]Stage 7: Publish[/bold blue]")
        # Call publish function directly since it's in the same module
        publish_cmd.callback()

    console.print(f"\n✅ All stages completed for {parsed_date}!", style="green")


@stages.command()
@click.option(
    "--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today"
)
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
def status(target_date: str | None, collection_name: str) -> None:
    """Show status of all stages for a date."""

    parsed_date = parse_date(target_date)
    collection = load_collection_or_exit(collection_name)

    # Check each stage directory
    stages_base = collection.stages_base
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
@click.argument(
    "stage_name", type=click.Choice(["collect", "fetch", "evaluate", "report"])
)
@click.option(
    "--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today"
)
@click.option("--limit", default=10, help="Maximum number of files to list")
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
def list_files(
    stage_name: str, target_date: str | None, limit: int, collection_name: str
) -> None:
    """List files in a specific stage."""

    parsed_date = parse_date(target_date)
    collection = load_collection_or_exit(collection_name)
    stage_dir = collection.stages_base / stage_name / parsed_date.strftime("%Y-%m-%d")

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
@click.argument(
    "stage_name", type=click.Choice(["collect", "fetch", "evaluate", "report"])
)
@click.option(
    "--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today"
)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--collection", "collection_name", default="mcp", help="Collection to operate on"
)
def clean(
    stage_name: str, target_date: str | None, confirm: bool, collection_name: str
) -> None:
    """Clean (remove) all files from a specific stage."""

    parsed_date = parse_date(target_date)
    collection = load_collection_or_exit(collection_name)
    stage_dir = collection.stages_base / stage_name / parsed_date.strftime("%Y-%m-%d")

    if not stage_dir.exists():
        console.print(f"❌ Stage directory does not exist: {stage_dir}", style="red")
        return

    files = list(stage_dir.glob("*"))

    if not files:
        console.print(f"📂 No files to clean in {stage_name} stage for {parsed_date}")
        return

    if not confirm:
        console.print(
            f"⚠️  This will delete {len(files)} files from {stage_name} stage for {parsed_date}"
        )
        if not click.confirm("Do you want to continue?"):
            console.print("❌ Cancelled")
            return

    for file_path in files:
        file_path.unlink()

    # Remove directory if empty
    with contextlib.suppress(OSError):  # Directory not empty
        stage_dir.rmdir()

    console.print(
        f"✅ Cleaned {len(files)} files from {stage_name} stage", style="green"
    )


@stages.command()
def publish() -> None:
    """Publish DuckDB query interface and metadata to output directory."""
    import shutil

    # Source file path for query interface
    source_file = Path("src/html/duckdb-query-tool-r2.html")

    # Check if source exists
    if not source_file.exists():
        console.print(f"❌ Source file not found: {source_file}", style="red")
        sys.exit(1)

    # Create output directory structure
    output_dir = Path("output")
    query_dir = output_dir / "query"
    metadata_dir = output_dir / "metadata"

    query_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Publish query interface
    target_file = query_dir / "duckdb.html"

    try:
        # Copy the query interface
        shutil.copy2(source_file, target_file)

        file_size = target_file.stat().st_size
        console.print(f"✅ Published query interface to {target_file}")
        console.print(f"📊 File size: {file_size:,} bytes")

        # Copy metadata directory
        source_metadata_dir = Path("metadata")
        if source_metadata_dir.exists():
            # Copy all files from metadata directory
            for item in source_metadata_dir.iterdir():
                if item.is_file():
                    target_metadata_file = metadata_dir / item.name
                    shutil.copy2(item, target_metadata_file)
                    console.print(f"✅ Published metadata file: {target_metadata_file}")

            console.print(f"📁 Metadata published to: {metadata_dir}")
        else:
            console.print(
                f"⚠️  Metadata directory not found: {source_metadata_dir}",
                style="yellow",
            )

        # Copy metadata browser HTML to query directory
        metadata_browser_source = Path("src/html/metadata-example.html")
        if metadata_browser_source.exists():
            metadata_browser_target = query_dir / "metadata.html"
            shutil.copy2(metadata_browser_source, metadata_browser_target)
            console.print(f"✅ Published metadata browser: {metadata_browser_target}")
        else:
            console.print(
                f"⚠️  Metadata browser not found: {metadata_browser_source}",
                style="yellow",
            )

        console.print("🌐 Access query interface at: output/query/duckdb.html")
        console.print("📄 Metadata available at: output/metadata/")
        console.print("📊 Metadata browser at: output/query/metadata.html")

    except Exception as e:
        console.print(f"❌ Failed to publish: {e}", style="red")
        sys.exit(1)


@stages.command()
@click.option("--port", default=8000, help="Port to serve on (default: 8000)")
@click.option(
    "--host", default="localhost", help="Host to bind to (default: localhost)"
)
def present(port: int, host: str) -> None:
    """Start HTTP server to view generated HTML reports."""
    import subprocess
    import time
    import webbrowser
    from pathlib import Path

    output_dir = Path("output")
    if not output_dir.exists():
        console.print(
            "❌ Output directory does not exist. Generate reports first.", style="red"
        )
        sys.exit(1)

    console.print(f"🌐 Starting HTTP server on http://{host}:{port}")
    console.print(f"📁 Serving files from: {output_dir.absolute()}")
    console.print("💡 Press Ctrl+C to stop the server")

    try:
        # Change to output directory and start Python HTTP server
        import os

        os.chdir(output_dir)

        # Open browser after a short delay
        def open_browser():
            time.sleep(1)
            webbrowser.open(f"http://{host}:{port}")

        import threading

        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Start the server
        subprocess.run(  # noqa: S603  fixed command, sys.executable + local args
            [
                sys.executable,
                "-m",
                "http.server",
                str(port),
                "--bind",
                host,
            ]
        )

    except KeyboardInterrupt:
        console.print("\n👋 Server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Server failed: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    stages()
