import asyncio
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.bluesky.collector import BlueskyDataCollector
from src.config.searches import load_search_config
from src.config.settings import get_settings
from src.content.extractor import ContentExtractor
from src.content.fetcher import ArticleFetcher
from src.content.models import ContentError

console = Console()


@click.group()
def cli():
    """Bluesky MCP Monitor CLI"""
    pass


@cli.command()
@click.option("--max-posts", default=500, help="Maximum posts to collect")
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--search", default="mcp_tag", help="Search definition to use")
@click.option("--config", "config_path", help="Path to search configuration YAML file")
def collect(max_posts: int, target_date: Optional[str], search: str, config_path: Optional[str]):
    """Collect posts from Bluesky using configurable search definitions."""
    
    # Parse target date
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            console.print(f"❌ Invalid date format: {target_date}. Use YYYY-MM-DD", style="red")
            sys.exit(1)
    else:
        parsed_date = date.today()
    
    console.print(f"🔍 Collecting posts for {parsed_date} using search '{search}'...")
    
    try:
        settings = get_settings()
        
        if not settings.has_bluesky_credentials:
            console.print("❌ Bluesky credentials not configured", style="red")
            console.print("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables")
            sys.exit(1)
        
        # Load search configuration
        search_config = load_search_config(config_path)
        
        # Get specific search definition
        search_definition = search_config.get_search(search)
        if not search_definition:
            console.print(f"❌ Search definition '{search}' not found", style="red")
            available_searches = list(search_config.searches.keys())
            console.print(f"Available searches: {', '.join(available_searches)}")
            sys.exit(1)
        
        if not search_definition.enabled:
            console.print(f"❌ Search definition '{search}' is disabled", style="red")
            sys.exit(1)
        
        collector = BlueskyDataCollector(settings)
        
        # Run async collection with search definition
        posts_count, success = asyncio.run(
            collector.collect_and_store_by_definition(
                search_definition=search_definition,
                target_date=parsed_date, 
                max_posts=max_posts
            )
        )
        
        if success:
            console.print(
                f"✅ Successfully collected and stored {posts_count} posts", 
                style="green"
            )
        else:
            console.print(
                f"⚠️  Collected {posts_count} posts but storage failed", 
                style="yellow"
            )
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Collection failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
def status(target_date: Optional[str]):
    """Check if data exists for a specific date."""
    
    # Parse target date
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            console.print(f"❌ Invalid date format: {target_date}. Use YYYY-MM-DD", style="red")
            sys.exit(1)
    else:
        parsed_date = date.today()
    
    try:
        settings = get_settings()
        collector = BlueskyDataCollector(settings)
        
        exists = collector.check_stored_data(parsed_date)
        
        if exists:
            console.print(f"✅ Data exists for {parsed_date}", style="green")
            
            # Try to get post count
            posts = asyncio.run(collector.get_stored_posts(parsed_date))
            console.print(f"📊 Found {len(posts)} stored posts")
        else:
            console.print(f"❌ No data found for {parsed_date}", style="red")
            
    except Exception as e:
        console.print(f"❌ Status check failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--limit", default=10, help="Number of posts to display")
def list_posts(target_date: Optional[str], limit: int):
    """List stored posts for a specific date."""
    
    # Parse target date
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            console.print(f"❌ Invalid date format: {target_date}. Use YYYY-MM-DD", style="red")
            sys.exit(1)
    else:
        parsed_date = date.today()
    
    try:
        settings = get_settings()
        collector = BlueskyDataCollector(settings)
        
        posts = asyncio.run(collector.get_stored_posts(parsed_date))
        
        if not posts:
            console.print(f"❌ No posts found for {parsed_date}", style="red")
            return
        
        # Create table
        table = Table(title=f"Posts for {parsed_date}")
        table.add_column("Author", style="cyan", no_wrap=True)
        table.add_column("Content", style="white", max_width=50)
        table.add_column("Engagement", style="green", justify="center")
        table.add_column("Links", style="blue")
        
        for post in posts[:limit]:
            engagement = f"{post.engagement_metrics.likes}❤️ {post.engagement_metrics.reposts}🔄 {post.engagement_metrics.replies}💬"
            links = ", ".join(str(link) for link in post.links[:2])  # Show first 2 links
            if len(post.links) > 2:
                links += f" (+{len(post.links) - 2} more)"
            
            table.add_row(
                post.author,
                post.content[:100] + "..." if len(post.content) > 100 else post.content,
                engagement,
                links or "None"
            )
        
        console.print(table)
        
        if len(posts) > limit:
            console.print(f"\n... and {len(posts) - limit} more posts")
            
    except Exception as e:
        console.print(f"❌ Failed to list posts: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--config", "config_path", help="Path to search configuration YAML file")
def list_searches(config_path: Optional[str]):
    """List available search definitions."""
    try:
        search_config = load_search_config(config_path)
        
        table = Table(title="Available Search Definitions")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Description", style="blue", max_width=40)
        table.add_column("Enabled", style="green", justify="center")
        table.add_column("Sort", style="yellow", justify="center")
        table.add_column("Include Terms", style="magenta", max_width=30)
        table.add_column("Exclude Terms", style="red", max_width=30)
        
        for key, search_def in search_config.searches.items():
            include_terms = ", ".join(search_def.include_terms[:2])
            if len(search_def.include_terms) > 2:
                include_terms += f" (+{len(search_def.include_terms) - 2} more)"
            
            exclude_terms = ", ".join(search_def.exclude_terms[:2]) if search_def.exclude_terms else "None"
            if len(search_def.exclude_terms) > 2:
                exclude_terms += f" (+{len(search_def.exclude_terms) - 2} more)"
            
            enabled_icon = "✅" if search_def.enabled else "❌"
            
            table.add_row(
                key,
                search_def.name,
                search_def.description,
                enabled_icon,
                search_def.sort,
                include_terms,
                exclude_terms
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Failed to load search configuration: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--config", "config_path", help="Path to search configuration YAML file")
def validate_config(config_path: Optional[str]):
    """Validate search configuration file."""
    try:
        search_config = load_search_config(config_path)
        
        console.print("✅ Configuration is valid", style="green")
        console.print(f"📊 Found {len(search_config.searches)} search definitions")
        
        enabled_count = len(search_config.get_enabled_searches())
        console.print(f"🔄 {enabled_count} definitions are enabled")
        
        # Test query building for each definition
        from src.bluesky.query_builder import LuceneQueryBuilder
        
        for key, search_def in search_config.searches.items():
            if search_def.enabled:
                try:
                    query = LuceneQueryBuilder.build_and_validate(search_def)
                    console.print(f"✅ '{key}': Query builds successfully", style="green")
                    console.print(f"   Query: {query}", style="dim")
                except Exception as e:
                    console.print(f"❌ '{key}': Query build failed: {e}", style="red")
        
    except Exception as e:
        console.print(f"❌ Configuration validation failed: {e}", style="red")
        sys.exit(1)


@cli.command()
def notebook():
    """Launch marimo notebook for data exploration."""
    console.print("🚀 Launching marimo notebook...")
    console.print("This will open the data exploration notebook in your browser.")
    
    notebook_path = Path("notebooks/data_exploration.py")
    
    if not notebook_path.exists():
        console.print(f"❌ Notebook not found: {notebook_path}", style="red")
        console.print("Run this command from the project root directory")
        sys.exit(1)
    
    import subprocess
    
    try:
        subprocess.run(["marimo", "edit", str(notebook_path)], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Failed to launch notebook: {e}", style="red")
        sys.exit(1)
    except FileNotFoundError:
        console.print("❌ marimo not found. Install with: poetry install", style="red")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--show-content", is_flag=True, help="Show extracted markdown content")
@click.option("--show-html", is_flag=True, help="Show raw HTML content")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed extraction debugging info")
def process_article(url: str, show_content: bool, show_html: bool, verbose: bool):
    """Process a single article URL to test content extraction."""
    async def _process_article():
        console.print(f"[blue]Processing article: {url}[/blue]\n")
        
        async with ArticleFetcher() as fetcher:
            # Fetch the article
            console.print("[yellow]Fetching article...[/yellow]")
            fetch_result = await fetcher.fetch_article(url)
            
            if isinstance(fetch_result, ContentError):
                console.print(Panel(
                    f"[red]Fetch Error ({fetch_result.error_type}):[/red]\n{fetch_result.error_message}",
                    title="❌ Article Fetch Failed",
                    border_style="red"
                ))
                return
            
            console.print("[green]✓ Article fetched successfully[/green]")
            
            # Show fetch info
            fetch_info = Table(title="📥 Fetch Information")
            fetch_info.add_column("Property", style="cyan")
            fetch_info.add_column("Value", style="white")
            
            fetch_info.add_row("Status Code", str(fetch_result.status_code))
            fetch_info.add_row("Content Length", f"{len(fetch_result.html):,} characters")
            fetch_info.add_row("Content Type", fetch_result.headers.get("content-type", "unknown"))
            fetch_info.add_row("Fetch Time", fetch_result.fetch_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            
            console.print(fetch_info)
            console.print()
            
            # Extract content
            console.print("[yellow]Extracting content...[/yellow]")
            extractor = ContentExtractor()
            
            if verbose:
                console.print("[dim]Running in verbose mode - check logs for detailed extraction info[/dim]")
                
            extract_result = extractor.extract_content(fetch_result, debug=verbose)
            
            if isinstance(extract_result, ContentError):
                error_panel_content = f"[red]Extraction Error ({extract_result.error_type}):[/red]\n{extract_result.error_message}"
                
                if verbose:
                    # Add debugging suggestions
                    error_panel_content += "\n\n[yellow]Debugging suggestions:[/yellow]"
                    error_panel_content += "\n• Check the HTML structure with --show-html"
                    error_panel_content += "\n• The website might use heavy JavaScript for content"
                    error_panel_content += "\n• Content might be behind authentication"
                    error_panel_content += "\n• Try a different article URL"
                
                console.print(Panel(
                    error_panel_content,
                    title="❌ Content Extraction Failed",
                    border_style="red"
                ))
                
                if verbose and show_html:
                    # Show HTML structure analysis
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(fetch_result.html, "html.parser")
                    
                    structure_info = Table(title="🔍 HTML Structure Analysis")
                    structure_info.add_column("Element", style="cyan")
                    structure_info.add_column("Count", style="white")
                    
                    elements = ["title", "h1", "h2", "h3", "p", "div", "article", "main", "section"]
                    for element in elements:
                        count = len(soup.find_all(element))
                        structure_info.add_row(element, str(count))
                    
                    console.print("\n")
                    console.print(structure_info)
                    
                    # Check for common content indicators
                    content_indicators = [
                        ("Content class", soup.find_all(attrs={"class": re.compile(r"content", re.I)})),
                        ("Article class", soup.find_all(attrs={"class": re.compile(r"article", re.I)})),
                        ("Post class", soup.find_all(attrs={"class": re.compile(r"post", re.I)})),
                        ("Main content", soup.find_all(attrs={"class": re.compile(r"main", re.I)})),
                    ]
                    
                    indicators_table = Table(title="📝 Content Indicators")
                    indicators_table.add_column("Indicator", style="cyan")
                    indicators_table.add_column("Found", style="white")
                    
                    for name, elements in content_indicators:
                        found = f"{len(elements)} elements" if elements else "None"
                        indicators_table.add_row(name, found)
                    
                    console.print("\n")
                    console.print(indicators_table)
                
                return
            
            console.print("[green]✓ Content extracted successfully[/green]")
            
            # Show extraction info
            extract_info = Table(title="📄 Extracted Content Information")
            extract_info.add_column("Property", style="cyan")
            extract_info.add_column("Value", style="white")
            
            extract_info.add_row("Title", extract_result.title or "[dim]Not found[/dim]")
            extract_info.add_row("Author", extract_result.author or "[dim]Not found[/dim]")
            extract_info.add_row("Medium", extract_result.medium or "[dim]Not found[/dim]")
            extract_info.add_row("Domain", extract_result.domain)
            extract_info.add_row("Language", extract_result.language or "[dim]Not detected[/dim]")
            extract_info.add_row("Word Count", f"{extract_result.word_count:,}")
            extract_info.add_row("Content Length", f"{len(extract_result.content_markdown):,} characters")
            extract_info.add_row("Extraction Time", extract_result.extraction_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            
            console.print(extract_info)
            console.print()
            
            # Show HTML if requested
            if show_html:
                html_preview = fetch_result.html[:500] + "..." if len(fetch_result.html) > 500 else fetch_result.html
                console.print(Panel(
                    html_preview,
                    title="🔍 Raw HTML (first 500 chars)",
                    border_style="dim"
                ))
                console.print()
            
            # Show markdown content if requested
            if show_content:
                content_preview = extract_result.content_markdown[:1000] + "..." if len(extract_result.content_markdown) > 1000 else extract_result.content_markdown
                console.print(Panel(
                    content_preview,
                    title="📝 Extracted Markdown (first 1000 chars)",
                    border_style="green"
                ))
            else:
                console.print("[dim]Use --show-content to see extracted markdown[/dim]")
                console.print("[dim]Use --show-html to see raw HTML[/dim]")
    
    try:
        asyncio.run(_process_article())
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


if __name__ == "__main__":
    cli()