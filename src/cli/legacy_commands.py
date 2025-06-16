"""Legacy CLI utilities - use 'nsp' for main stage-based commands."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from src.config.searches import load_search_config

console = Console()


@click.group()
def legacy_cli():
    """Legacy utilities for Bluesky MCP Monitor - use 'nsp' for main commands"""
    pass


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
                return
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


@legacy_cli.command()
def notebook():
    """Launch marimo notebook for data exploration."""
    console.print("🚀 Launching marimo notebook...")
    console.print("This will open the data exploration notebook in your browser.")
    
    notebook_path = Path("notebooks/data_exploration.py")
    
    if not notebook_path.exists():
        console.print(f"❌ Notebook not found: {notebook_path}", style="red")
        console.print("Run this command from the project root directory")
        return
    
    import subprocess
    
    try:
        subprocess.run(["marimo", "edit", str(notebook_path)], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Failed to launch notebook: {e}", style="red")
    except FileNotFoundError:
        console.print("❌ marimo not found. Install with: poetry install", style="red")


if __name__ == "__main__":
    legacy_cli()