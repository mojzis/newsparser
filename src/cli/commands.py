import asyncio
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import click
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.bluesky.collector import BlueskyDataCollector
from src.config.searches import load_search_config
from src.config.settings import get_settings
from src.content.extractor import ContentExtractor
from src.content.fetcher import ArticleFetcher
from src.content.models import ContentError
from src.evaluation.processor import EvaluationProcessor
from src.storage.r2_client import R2Client
from src.utils.language_detection import LanguageType
from src.utils.filtering import filter_posts_by_language, get_language_statistics

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
@click.option("--track-urls", is_flag=True, help="Track URLs in registry")
def collect(max_posts: int, target_date: Optional[str], search: str, config_path: Optional[str], track_urls: bool):
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
                max_posts=max_posts,
                track_urls=track_urls
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
@click.option("--show-language-stats", is_flag=True, help="Show language distribution statistics")
def status(target_date: Optional[str], show_language_stats: bool):
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
            
            # Try to get post count and language stats
            posts = asyncio.run(collector.get_stored_posts(parsed_date))
            console.print(f"📊 Found {len(posts)} stored posts")
            
            if show_language_stats and posts:
                console.print(f"\n📈 Language Distribution:")
                stats = get_language_statistics(posts)
                for lang, count in sorted(stats.items()):
                    percentage = (count / len(posts)) * 100
                    console.print(f"  {lang.upper()}: {count:,} posts ({percentage:.1f}%)")
        else:
            console.print(f"❌ No data found for {parsed_date}", style="red")
            
    except Exception as e:
        console.print(f"❌ Status check failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--limit", default=10, help="Number of posts to display")
@click.option("--include-languages", help="Include only these languages (comma-separated: latin,mixed,unknown)")
@click.option("--exclude-languages", help="Exclude these languages (comma-separated: latin,mixed,unknown)")
@click.option("--show-language-stats", is_flag=True, help="Show language distribution statistics")
def list_posts(target_date: Optional[str], limit: int, include_languages: Optional[str], 
               exclude_languages: Optional[str], show_language_stats: bool):
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
    
    # Parse language filtering options
    include_langs = None
    exclude_langs = None
    
    if include_languages and exclude_languages:
        console.print("❌ Cannot specify both --include-languages and --exclude-languages", style="red")
        sys.exit(1)
    
    if include_languages:
        try:
            include_langs = [LanguageType(lang.strip()) for lang in include_languages.split(',')]
        except ValueError as e:
            console.print(f"❌ Invalid language in include list: {e}", style="red")
            sys.exit(1)
    
    if exclude_languages:
        try:
            exclude_langs = [LanguageType(lang.strip()) for lang in exclude_languages.split(',')]
        except ValueError as e:
            console.print(f"❌ Invalid language in exclude list: {e}", style="red")
            sys.exit(1)
    
    try:
        settings = get_settings()
        collector = BlueskyDataCollector(settings)
        
        posts = asyncio.run(collector.get_stored_posts(parsed_date))
        
        if not posts:
            console.print(f"❌ No posts found for {parsed_date}", style="red")
            return
        
        # Show original language statistics if requested
        if show_language_stats:
            original_stats = get_language_statistics(posts)
            console.print(f"\n📊 Language Statistics for {parsed_date}")
            console.print(f"Total posts: {len(posts)}")
            for lang, count in sorted(original_stats.items()):
                percentage = (count / len(posts)) * 100
                console.print(f"  {lang.upper()}: {count:,} ({percentage:.1f}%)")
            console.print()
        
        # Apply language filtering
        if include_langs or exclude_langs:
            original_count = len(posts)
            posts = filter_posts_by_language(posts, include_langs, exclude_langs)
            filtered_count = len(posts)
            
            if show_language_stats:
                console.print(f"🔍 After language filtering: {filtered_count}/{original_count} posts")
                if filtered_count != original_count:
                    filtered_stats = get_language_statistics(posts)
                    for lang, count in sorted(filtered_stats.items()):
                        percentage = (count / filtered_count) * 100 if filtered_count > 0 else 0
                        console.print(f"  {lang.upper()}: {count:,} ({percentage:.1f}%)")
                console.print()
        
        if not posts:
            console.print(f"❌ No posts match the filtering criteria", style="red")
            return
        
        # Create table
        table_title = f"Posts for {parsed_date}"
        if include_langs or exclude_langs:
            filter_desc = f"languages: {','.join([l.value for l in (include_langs or exclude_langs)])}"
            action = "including" if include_langs else "excluding"
            table_title += f" ({action} {filter_desc})"
        
        table = Table(title=table_title)
        table.add_column("Author", style="cyan", no_wrap=True)
        table.add_column("Content", style="white", max_width=50)
        table.add_column("Language", style="yellow", justify="center")
        table.add_column("Engagement", style="green", justify="center")
        table.add_column("Links", style="blue")
        
        for post in posts[:limit]:
            engagement = f"{post.engagement_metrics.likes}❤️ {post.engagement_metrics.reposts}🔄 {post.engagement_metrics.replies}💬"
            links = ", ".join(str(link) for link in post.links[:2])  # Show first 2 links
            if len(post.links) > 2:
                links += f" (+{len(post.links) - 2} more)"
            
            # Format language with appropriate styling
            lang_display = post.language.value.upper()
            if post.language == LanguageType.UNKNOWN:
                lang_display = f"[red]{lang_display}[/red]"
            elif post.language == LanguageType.MIXED:
                lang_display = f"[orange3]{lang_display}[/orange3]"
            else:
                lang_display = f"[green]{lang_display}[/green]"
            
            table.add_row(
                post.author,
                post.content[:100] + "..." if len(post.content) > 100 else post.content,
                lang_display,
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
        from src.bluesky.query_builders import QueryBuilderFactory
        
        for key, search_def in search_config.searches.items():
            if search_def.enabled:
                try:
                    builder = QueryBuilderFactory.create(search_def.query_syntax)
                    query = builder.build_query(search_def)
                    is_valid, error_msg = builder.validate_query(query)
                    
                    if is_valid:
                        console.print(f"✅ '{key}': Query builds successfully ({search_def.query_syntax} syntax)", style="green")
                        console.print(f"   Query: {query}", style="dim")
                    else:
                        console.print(f"❌ '{key}': Query validation failed: {error_msg}", style="red")
                except Exception as e:
                    console.print(f"❌ '{key}': Query build failed: {e}", style="red")
        
    except Exception as e:
        console.print(f"❌ Configuration validation failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--config", "config_path", help="Path to search configuration YAML file")
@click.option("--query", help="Search definition key to compare")
def compare_syntaxes(config_path: Optional[str], query: Optional[str]):
    """Compare native and Lucene query syntaxes side by side."""
    try:
        from src.bluesky.query_builders import QueryBuilderFactory
        
        search_config = load_search_config(config_path)
        
        # Select which searches to compare
        if query:
            if query not in search_config.searches:
                console.print(f"❌ Search '{query}' not found", style="red")
                sys.exit(1)
            searches = {query: search_config.searches[query]}
        else:
            searches = search_config.get_enabled_searches()
        
        # Build comparison table
        table = Table(title="Query Syntax Comparison")
        table.add_column("Search", style="cyan", no_wrap=True)
        table.add_column("Native Query", style="green")
        table.add_column("Lucene Query", style="blue")
        table.add_column("Include Terms", style="magenta")
        table.add_column("Exclude Terms", style="red")
        
        for key, search_def in searches.items():
            try:
                # Build native query
                native_builder = QueryBuilderFactory.create("native")
                native_query = native_builder.build_query(search_def)
                
                # Build Lucene query
                lucene_builder = QueryBuilderFactory.create("lucene")
                lucene_query = lucene_builder.build_query(search_def)
                
                # Format terms
                include_str = ", ".join(search_def.include_terms[:3])
                if len(search_def.include_terms) > 3:
                    include_str += f" (+{len(search_def.include_terms) - 3})"
                
                exclude_str = ", ".join(search_def.exclude_terms[:3]) if search_def.exclude_terms else "None"
                if len(search_def.exclude_terms) > 3:
                    exclude_str += f" (+{len(search_def.exclude_terms) - 3})"
                
                table.add_row(
                    key,
                    native_query[:40] + "..." if len(native_query) > 40 else native_query,
                    lucene_query[:40] + "..." if len(lucene_query) > 40 else lucene_query,
                    include_str,
                    exclude_str
                )
                
            except Exception as e:
                table.add_row(key, f"Error: {e}", "Error", "", "")
        
        console.print(table)
        
        # Show note about complex expressions
        console.print("\n[yellow]Note: Complex boolean expressions in exclude terms are skipped in native syntax[/yellow]")
        
    except Exception as e:
        console.print(f"❌ Comparison failed: {e}", style="red")
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


@cli.command()
@click.argument("text")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed character analysis")
def detect_language(text: str, verbose: bool):
    """Test language detection on provided text."""
    from src.utils.language_detection import detect_language_from_text, analyze_text_characters
    
    console.print(f"[blue]Testing language detection on:[/blue]")
    console.print(f'"{text}"')
    console.print()
    
    # Detect language
    detected = detect_language_from_text(text)
    console.print(f"[green]Detected language:[/green] {detected.value.upper()}")
    
    if verbose:
        console.print("\n[yellow]Detailed Analysis:[/yellow]")
        analysis = analyze_text_characters(text)
        
        analysis_table = Table(title="Character Analysis")
        analysis_table.add_column("Metric", style="cyan")
        analysis_table.add_column("Value", style="white")
        
        analysis_table.add_row("Total Characters", str(analysis['total_chars']))
        analysis_table.add_row("Latin Characters", str(analysis['latin_chars']))
        analysis_table.add_row("Non-Latin Characters", str(analysis['non_latin_chars']))
        analysis_table.add_row("Neutral Characters", str(analysis['neutral_chars']))
        analysis_table.add_row("Whitespace Characters", str(analysis['whitespace_chars']))
        analysis_table.add_row("Meaningful Characters", str(analysis['meaningful_chars']))
        analysis_table.add_row("Non-Latin Percentage", f"{analysis['non_latin_percentage']:.1%}")
        
        console.print(analysis_table)
        
        # Show character samples
        from src.utils.language_detection import get_character_sample
        
        console.print("\n[yellow]Character Samples:[/yellow]")
        
        latin_chars = get_character_sample(text, "latin", limit=10)
        if latin_chars:
            console.print(f"Latin: {' '.join(latin_chars)}")
        
        non_latin_chars = get_character_sample(text, "non_latin", limit=10)
        if non_latin_chars:
            console.print(f"Non-Latin: {' '.join(non_latin_chars)}")
        
        neutral_chars = get_character_sample(text, "neutral", limit=10)
        if neutral_chars:
            console.print(f"Neutral: {' '.join(neutral_chars)}")


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--show-samples", is_flag=True, help="Show sample posts for each language type")
def language_report(target_date: Optional[str], show_samples: bool):
    """Generate a comprehensive language detection report for stored posts."""
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
        
        console.print(f"🔍 Language Detection Report for {parsed_date}")
        console.print(f"Total posts analyzed: {len(posts)}")
        console.print()
        
        # Get language statistics
        stats = get_language_statistics(posts)
        
        # Create detailed statistics table
        stats_table = Table(title="Language Distribution")
        stats_table.add_column("Language", style="cyan")
        stats_table.add_column("Count", style="white", justify="right")
        stats_table.add_column("Percentage", style="green", justify="right")
        
        for lang in ["latin", "mixed", "unknown"]:
            count = stats.get(lang, 0)
            percentage = (count / len(posts)) * 100 if posts else 0
            
            # Color code the language names
            if lang == "latin":
                lang_display = f"[green]{lang.upper()}[/green]"
            elif lang == "mixed":
                lang_display = f"[orange3]{lang.upper()}[/orange3]"
            else:
                lang_display = f"[red]{lang.upper()}[/red]"
            
            stats_table.add_row(
                lang_display,
                f"{count:,}",
                f"{percentage:.1f}%"
            )
        
        console.print(stats_table)
        
        if show_samples:
            console.print("\n[yellow]Sample Posts by Language:[/yellow]")
            
            for lang_type in [LanguageType.LATIN, LanguageType.MIXED, LanguageType.UNKNOWN]:
                lang_posts = [p for p in posts if p.language == lang_type]
                if lang_posts:
                    console.print(f"\n[bold]{lang_type.value.upper()} Posts:[/bold]")
                    for i, post in enumerate(lang_posts[:3]):  # Show first 3 samples
                        sample_content = post.content[:80] + "..." if len(post.content) > 80 else post.content
                        console.print(f"  {i+1}. {sample_content}")
                        console.print(f"     Author: {post.author}")
                        if post.tags:
                            console.print(f"     Tags: {', '.join(post.tags[:3])}")
                        console.print()
        
        # Summary insights
        console.print("\n[bold]Summary Insights:[/bold]")
        
        latin_pct = (stats.get("latin", 0) / len(posts)) * 100 if posts else 0
        mixed_pct = (stats.get("mixed", 0) / len(posts)) * 100 if posts else 0
        unknown_pct = (stats.get("unknown", 0) / len(posts)) * 100 if posts else 0
        
        if latin_pct > 80:
            console.print("• Content is predominantly Latin-script based")
        if mixed_pct > 20:
            console.print("• Significant multilingual content detected")
        if unknown_pct > 10:
            console.print("• Consider filtering non-Latin content for processing")
        
        console.print(f"• Language detection coverage: 100% ({len(posts)} posts analyzed)")
        
    except Exception as e:
        console.print(f"❌ Language report failed: {e}", style="red")
        sys.exit(1)


@cli.command()
def url_stats():
    """Show URL registry statistics."""
    try:
        settings = get_settings()
        r2_client = R2Client(settings)
        
        # Download registry
        registry = r2_client.download_url_registry()
        
        if registry is None:
            console.print("No URL registry found. Run collect with --track-urls to create one.", style="yellow")
            return
        
        stats = registry.get_stats()
        
        # Show statistics
        console.print(Panel(
            f"[green]Total URLs:[/green] {stats['total_urls']:,}\n"
            f"[blue]Total Occurrences:[/blue] {stats['total_occurrences']:,}\n"
            f"[cyan]Unique Domains:[/cyan] {stats['unique_domains']:,}\n"
            f"[yellow]Evaluated URLs:[/yellow] {stats['evaluated_urls']:,}\n"
            f"[magenta]MCP-Related:[/magenta] {stats['mcp_related_urls']:,}\n"
            f"[orange3]Avg Relevance:[/orange3] {stats['avg_relevance_score']:.2f}",
            title="📊 URL Registry Statistics",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"❌ Failed to get URL statistics: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--limit", default=20, help="Number of URLs to display")
@click.option("--domain", help="Filter by domain")
def url_list(limit: int, domain: Optional[str]):
    """List URLs in the registry."""
    try:
        settings = get_settings()
        r2_client = R2Client(settings)
        
        # Download registry
        registry = r2_client.download_url_registry()
        
        if registry is None:
            console.print("No URL registry found. Run collect with --track-urls to create one.", style="yellow")
            return
        
        if registry.df.empty:
            console.print("URL registry is empty.", style="yellow")
            return
        
        # Filter by domain if specified
        df = registry.df
        if domain:
            df = df[df['url'].str.contains(domain, case=False)]
            if df.empty:
                console.print(f"No URLs found for domain: {domain}", style="yellow")
                return
        
        # Sort by times_seen descending
        df = df.sort_values('times_seen', ascending=False)
        
        # Create table
        table = Table(title="URL Registry")
        table.add_column("URL", style="cyan", no_wrap=False, max_width=60)
        table.add_column("Times Seen", style="green", justify="right")
        table.add_column("First Seen", style="yellow")
        table.add_column("First Author", style="blue", max_width=20)
        
        for _, row in df.head(limit).iterrows():
            table.add_row(
                str(row['url']),
                str(row['times_seen']),
                row['first_seen'].strftime("%Y-%m-%d %H:%M") if pd.notna(row['first_seen']) else "Unknown",
                row['first_post_author'][:20] + "..." if len(row['first_post_author']) > 20 else row['first_post_author']
            )
        
        console.print(table)
        
        if len(df) > limit:
            console.print(f"\n... and {len(df) - limit} more URLs", style="dim")
        
    except Exception as e:
        console.print(f"❌ Failed to list URLs: {e}", style="red")
        sys.exit(1)


@cli.command()
def url_sync():
    """Download or upload URL registry manually."""
    try:
        settings = get_settings()
        r2_client = R2Client(settings)
        
        # Check if registry exists
        registry = r2_client.download_url_registry()
        
        if registry is None:
            console.print("No URL registry found in R2.", style="yellow")
            
            # Ask if user wants to create one
            if click.confirm("Create a new empty registry?"):
                from src.utils.url_registry import URLRegistry
                new_registry = URLRegistry()
                
                if r2_client.upload_url_registry(new_registry):
                    console.print("✅ Created and uploaded new URL registry", style="green")
                else:
                    console.print("❌ Failed to upload new registry", style="red")
                    sys.exit(1)
        else:
            console.print(f"✅ Downloaded URL registry with {len(registry.df)} entries", style="green")
            
            # Show stats
            stats = registry.get_stats()
            console.print(f"   Total URLs: {stats['total_urls']:,}")
            console.print(f"   Total occurrences: {stats['total_occurrences']:,}")
            console.print(f"   Unique domains: {stats['unique_domains']:,}")
            
    except Exception as e:
        console.print(f"❌ URL sync failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--force", is_flag=True, help="Force re-evaluation of already processed URLs")
@click.option("--include-languages", help="Include only these languages (comma-separated: latin,mixed,unknown)")
@click.option("--show-stats", is_flag=True, help="Show evaluation statistics")
def evaluate(target_date: Optional[str], force: bool, include_languages: Optional[str], show_stats: bool):
    """Evaluate articles from collected posts using Anthropic API."""
    
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
        
        if not settings.has_anthropic_credentials:
            console.print("❌ Anthropic API key not configured", style="red")
            console.print("Set ANTHROPIC_API_KEY environment variable")
            sys.exit(1)
        
        # Parse language filtering
        include_langs = None
        if include_languages:
            try:
                include_langs = [LanguageType(lang.strip()) for lang in include_languages.split(',')]
            except ValueError as e:
                console.print(f"❌ Invalid language: {e}", style="red")
                sys.exit(1)
        
        console.print(f"🔍 Evaluating articles from posts on {parsed_date}...")
        
        # Get posts for the date
        collector = BlueskyDataCollector(settings)
        posts = asyncio.run(collector.get_stored_posts(parsed_date))
        
        if not posts:
            console.print(f"❌ No posts found for {parsed_date}", style="red")
            sys.exit(1)
        
        console.print(f"📊 Found {len(posts)} posts")
        
        # Filter by language if requested
        if include_langs:
            posts = filter_posts_by_language(posts, include_languages=include_langs)
            console.print(f"   After language filter: {len(posts)} posts")
        
        # Count URLs
        total_urls = sum(len(post.links) for post in posts)
        if total_urls == 0:
            console.print("❌ No URLs found in posts", style="red")
            sys.exit(1)
        
        console.print(f"   Found {total_urls} URLs to process")
        
        # Process evaluations
        processor = EvaluationProcessor(settings)
        
        new_evals, total_registry = asyncio.run(
            processor.evaluate_posts(posts, parsed_date, force=force)
        )
        
        console.print(f"\n✅ Evaluation complete!")
        console.print(f"   New evaluations: {new_evals}")
        console.print(f"   Total URLs in registry: {total_registry}")
        
        if show_stats:
            # Download registry to show stats
            r2_client = R2Client(settings)
            registry = r2_client.download_url_registry()
            
            if registry:
                stats = registry.get_stats()
                
                stats_panel = Panel(
                    f"[green]Total URLs:[/green] {stats['total_urls']:,}\n"
                    f"[blue]Evaluated URLs:[/blue] {stats['evaluated_urls']:,}\n"
                    f"[cyan]MCP-Related:[/cyan] {stats['mcp_related_urls']:,}\n"
                    f"[yellow]Avg Relevance:[/yellow] {stats['avg_relevance_score']:.2f}",
                    title="📊 URL Registry Statistics",
                    border_style="green"
                )
                console.print(stats_panel)
        
    except Exception as e:
        console.print(f"❌ Evaluation failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--date", "target_date", help="Target date (YYYY-MM-DD), defaults to today")
@click.option("--limit", default=20, help="Number of evaluations to display")
@click.option("--mcp-only", is_flag=True, help="Show only MCP-related articles")
@click.option("--min-score", type=float, help="Minimum relevance score to display")
def list_evaluations(target_date: Optional[str], limit: int, mcp_only: bool, min_score: Optional[float]):
    """List article evaluations for a specific date."""
    
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
        processor = EvaluationProcessor(settings)
        
        evaluations = processor.get_stored_evaluations(parsed_date)
        
        if not evaluations:
            console.print(f"❌ No evaluations found for {parsed_date}", style="red")
            return
        
        # Filter evaluations
        if mcp_only:
            evaluations = [e for e in evaluations if e.is_mcp_related]
        
        if min_score is not None:
            evaluations = [e for e in evaluations if e.relevance_score >= min_score]
        
        if not evaluations:
            console.print("No evaluations match the filter criteria", style="yellow")
            return
        
        # Sort by relevance score
        evaluations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Create table
        table = Table(title=f"Article Evaluations for {parsed_date}")
        table.add_column("URL", style="cyan", no_wrap=False, max_width=50)
        table.add_column("Title", style="white", max_width=40)
        table.add_column("MCP", style="green", justify="center")
        table.add_column("Score", style="yellow", justify="right")
        table.add_column("Summary", style="blue", max_width=50)
        
        for eval in evaluations[:limit]:
            # Format URL
            url_display = str(eval.url)
            if len(url_display) > 50:
                url_display = url_display[:47] + "..."
            
            # Format title
            title = eval.title or "No title"
            if len(title) > 40:
                title = title[:37] + "..."
            
            # Format MCP status
            mcp_status = "✅" if eval.is_mcp_related else "❌"
            
            # Format summary
            summary = eval.summary
            if len(summary) > 50:
                summary = summary[:47] + "..."
            
            table.add_row(
                url_display,
                title,
                mcp_status,
                f"{eval.relevance_score:.2f}",
                summary
            )
        
        console.print(table)
        
        if len(evaluations) > limit:
            console.print(f"\n... and {len(evaluations) - limit} more evaluations")
        
    except Exception as e:
        console.print(f"❌ Failed to list evaluations: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    cli()