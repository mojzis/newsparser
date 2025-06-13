"""Legacy CLI commands - kept for backward compatibility but moved to 'onsp' command."""

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
def legacy_cli():
    """Legacy Bluesky MCP Monitor CLI - use 'nsp' for new stage-based commands"""
    pass


@legacy_cli.command()
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


@legacy_cli.command()
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


@legacy_cli.command()
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


@legacy_cli.command()
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


@legacy_cli.command()
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


@legacy_cli.command()
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


@legacy_cli.command()
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


# Add more legacy commands here...


if __name__ == "__main__":
    legacy_cli()