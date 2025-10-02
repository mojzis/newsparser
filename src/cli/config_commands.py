"""Configuration management CLI commands."""

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from src.config.config_manager import get_config_manager

console = Console()


@click.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.option("--branch", default="base", help="Configuration branch to validate")
def validate(branch: str):
    """Validate configuration files."""
    import os
    
    # Set branch for validation
    os.environ["NSP_CONFIG_BRANCH"] = branch
    
    try:
        # Reset the global config manager to pick up new environment
        from src.config.config_manager import reset_config_manager
        reset_config_manager()
        config_manager = get_config_manager()
        if config_manager.validate_config():
            console.print(f"✅ Configuration for branch '{branch}' is valid")
        else:
            console.print(f"❌ Configuration for branch '{branch}' is invalid")
            raise click.Abort()
    except Exception as e:
        console.print(f"❌ Configuration error: {e}")
        raise click.Abort()


@config.command()
@click.option("--branch", default="base", help="Configuration branch to show")
def show(branch: str):
    """Show current configuration."""
    import os
    
    # Set branch for display
    os.environ["NSP_CONFIG_BRANCH"] = branch
    
    try:
        # Reset the global config manager to pick up new environment
        from src.config.config_manager import reset_config_manager
        reset_config_manager()
        config_manager = get_config_manager()
        
        # Load all configurations
        app_config = config_manager.load_app_config()
        models_config = config_manager.load_models_config()
        prompts_config = config_manager.load_prompts_config()
        
        # Create tree view
        tree = Tree(f"Configuration: {branch}")
        
        # Application config
        app_tree = tree.add("Application")
        app_tree.add(f"Name: {app_config.metadata.name}")
        app_tree.add(f"Default Model: {app_config.processing.default_model_config}")
        app_tree.add(f"Default Prompt: {app_config.processing.default_prompt_config}")
        app_tree.add(f"Max Concurrent: {app_config.processing.max_concurrent_requests}")
        
        # Models config
        models_tree = tree.add("Models")
        for model_id, model in models_config.models.items():
            model_tree = models_tree.add(f"{model_id}")
            model_tree.add(f"Name: {model.name}")
            model_tree.add(f"Provider: {model.provider}")
            model_tree.add(f"Model ID: {model.model_id}")
            model_tree.add(f"Temperature: {model.config.get('temperature', 'N/A')}")
            model_tree.add(f"Max Tokens: {model.config.get('max_tokens', 'N/A')}")
        
        # Prompts config
        prompts_tree = tree.add("Prompts")
        for prompt_id, prompt in prompts_config.prompts.items():
            prompt_tree = prompts_tree.add(f"{prompt_id}")
            prompt_tree.add(f"Name: {prompt.name}")
            prompt_tree.add(f"Version: {prompt.version}")
            prompt_tree.add(f"Compatible Models: {', '.join(prompt.compatible_models)}")
        
        console.print(tree)
        
    except Exception as e:
        console.print(f"❌ Error loading configuration: {e}")
        raise click.Abort()


@config.command()
@click.argument("branch1")
@click.argument("branch2")
def diff(branch1: str, branch2: str):
    """Compare two configuration branches."""
    console.print(f"Comparing {branch1} vs {branch2}")
    console.print("⚠️  Configuration diff not yet implemented")


@config.command()
def list_branches():
    """List available configuration branches."""
    import os
    from pathlib import Path
    
    config_path = Path("config")
    
    # Base configuration
    console.print("📁 Available configuration branches:")
    console.print("  • base (default)")
    
    # Experimental branches
    experiments_path = config_path / "experiments"
    if experiments_path.exists():
        for exp_file in experiments_path.glob("*.yaml"):
            branch_name = exp_file.stem
            console.print(f"  • {branch_name}")
    
    if not any(experiments_path.glob("*.yaml")) if experiments_path.exists() else True:
        console.print("  (no experimental branches found)")


if __name__ == "__main__":
    config()