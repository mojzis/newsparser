"""Configuration management for externalized YAML configurations."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator


class PathsConfig(BaseModel):
    """Configuration for file paths."""
    stages_base: str = "stages"
    templates: str = "src/templates"
    data_legacy: str = "data"
    reports: str = "reports"


class ProcessingConfig(BaseModel):
    """Configuration for processing parameters."""
    fetch_lookback_days: int = 10
    min_relevance_score: float = 0.3
    max_concurrent_requests: int = 10
    default_model_config: str = "mcp_evaluator_v1"
    default_prompt_config: str = "mcp_evaluation_v1"
    enable_experiments: bool = True


class UIConfig(BaseModel):
    """Configuration for UI settings."""
    site_title: str = "MCP Monitor"
    site_tagline: str = "Daily digest of Model Context Protocol mentions"
    theme: str = "default"


class MetadataConfig(BaseModel):
    """Configuration metadata."""
    name: str
    description: str


class AppConfig(BaseModel):
    """Main application configuration."""
    version: str
    metadata: MetadataConfig
    paths: PathsConfig
    processing: ProcessingConfig
    ui: UIConfig


class ModelConfig(BaseModel):
    """Individual model configuration."""
    name: str
    version: str
    provider: str
    model_id: str
    config: Dict[str, Any]
    content_limits: Dict[str, int]
    cost_per_token: Dict[str, float]


class ModelsConfig(BaseModel):
    """Models configuration container."""
    version: str
    metadata: MetadataConfig
    models: Dict[str, ModelConfig]


class PromptVariable(BaseModel):
    """Prompt template variable definition."""
    name: str
    required: bool


class PromptConfig(BaseModel):
    """Individual prompt configuration."""
    name: str
    version: str
    compatible_models: list[str]
    template: str
    variables: list[PromptVariable]


class PromptsConfig(BaseModel):
    """Prompts configuration container."""
    version: str
    metadata: MetadataConfig
    prompts: Dict[str, PromptConfig]


class ExperimentConfig(BaseModel):
    """Experimental configuration overrides."""
    version: str
    metadata: MetadataConfig
    processing: Optional[ProcessingConfig] = None
    experiment: Optional[Dict[str, Any]] = None


class ConfigManager:
    """Manages loading and merging of configuration files."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None, branch: str = "base"):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration directory (defaults to ./config)
            branch: Configuration branch to use (defaults to "base")
        """
        self.config_path = Path(config_path) if config_path else Path("config")
        self.branch = branch
        self._app_config: Optional[AppConfig] = None
        self._models_config: Optional[ModelsConfig] = None
        self._prompts_config: Optional[PromptsConfig] = None
        self._experiment_config: Optional[ExperimentConfig] = None
        
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file safely."""
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_config_file(self, config_type: str) -> Path:
        """Get path to configuration file based on branch."""
        if self.branch == "base":
            return self.config_path / "base" / f"{config_type}.yaml"
        else:
            # For experimental branches, check if override exists
            exp_file = self.config_path / "experiments" / f"{self.branch}.yaml"
            if exp_file.exists():
                return exp_file
            else:
                # Fall back to base config
                return self.config_path / "base" / f"{config_type}.yaml"
    
    def load_app_config(self) -> AppConfig:
        """Load application configuration."""
        if self._app_config is None:
            # Always start with base configuration
            base_file = self.config_path / "base" / "app.yaml"
            app_data = self._load_yaml(base_file)
            
            # If using experimental branch, merge with base config
            if self.branch != "base":
                exp_file = self.config_path / "experiments" / f"{self.branch}.yaml"
                if exp_file.exists():
                    exp_data = self._load_yaml(exp_file)
                    if "processing" in exp_data:
                        # Merge processing configuration
                        app_data["processing"].update(exp_data["processing"])
            
            self._app_config = AppConfig(**app_data)
        
        return self._app_config
    
    def load_models_config(self) -> ModelsConfig:
        """Load models configuration."""
        if self._models_config is None:
            # Always load from base config for models
            models_file = self.config_path / "base" / "models.yaml"
            models_data = self._load_yaml(models_file)
            self._models_config = ModelsConfig(**models_data)
        
        return self._models_config
    
    def load_prompts_config(self) -> PromptsConfig:
        """Load prompts configuration."""
        if self._prompts_config is None:
            # Always load from base config for prompts
            prompts_file = self.config_path / "base" / "prompts.yaml"
            prompts_data = self._load_yaml(prompts_file)
            self._prompts_config = PromptsConfig(**prompts_data)
        
        return self._prompts_config
    
    def load_experiment_config(self) -> Optional[ExperimentConfig]:
        """Load experiment configuration if using experimental branch."""
        if self.branch == "base":
            return None
        
        if self._experiment_config is None:
            exp_file = self.config_path / "experiments" / f"{self.branch}.yaml"
            if exp_file.exists():
                exp_data = self._load_yaml(exp_file)
                self._experiment_config = ExperimentConfig(**exp_data)
        
        return self._experiment_config
    
    def get_model_config(self, model_id: Optional[str] = None) -> ModelConfig:
        """Get model configuration by ID."""
        models = self.load_models_config()
        app = self.load_app_config()
        
        model_id = model_id or app.processing.default_model_config
        
        if model_id not in models.models:
            raise ValueError(f"Model configuration not found: {model_id}")
        
        return models.models[model_id]
    
    def get_prompt_config(self, prompt_id: Optional[str] = None) -> PromptConfig:
        """Get prompt configuration by ID."""
        prompts = self.load_prompts_config()
        app = self.load_app_config()
        
        prompt_id = prompt_id or app.processing.default_prompt_config
        
        if prompt_id not in prompts.prompts:
            raise ValueError(f"Prompt configuration not found: {prompt_id}")
        
        return prompts.prompts[prompt_id]
    
    def validate_config(self) -> bool:
        """Validate all configuration files."""
        try:
            app = self.load_app_config()
            models = self.load_models_config()
            prompts = self.load_prompts_config()
            
            # Validate that default model exists
            if app.processing.default_model_config not in models.models:
                raise ValueError(f"Default model config not found: {app.processing.default_model_config}")
            
            # Validate that default prompt exists
            if app.processing.default_prompt_config not in prompts.prompts:
                raise ValueError(f"Default prompt config not found: {app.processing.default_prompt_config}")
            
            # Validate prompt-model compatibility
            default_prompt = prompts.prompts[app.processing.default_prompt_config]
            if app.processing.default_model_config not in default_prompt.compatible_models:
                raise ValueError(f"Default model {app.processing.default_model_config} not compatible with default prompt {app.processing.default_prompt_config}")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        # Get configuration from environment variables
        config_path = os.getenv("NSP_CONFIG_PATH", "config")
        branch = os.getenv("NSP_CONFIG_BRANCH", "base")
        _config_manager = ConfigManager(config_path, branch)
    return _config_manager


def reset_config_manager():
    """Reset global configuration manager (for testing)."""
    global _config_manager
    _config_manager = None