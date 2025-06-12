from pathlib import Path
from typing import Any, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from src.utils.logging import get_logger

logger = get_logger(__name__)


class SearchDefinition(BaseModel):
    """Configuration for a single search definition."""
    
    name: str = Field(..., description="Human-readable name for the search")
    description: str = Field(..., description="Description of what this search targets")
    include_terms: list[str] = Field(..., description="Terms that must be present")
    exclude_terms: list[str] = Field(default_factory=list, description="Terms to exclude")
    sort: str = Field(default="latest", description="Sort order: latest, top")
    enabled: bool = Field(default=True, description="Whether this search is active")
    
    @model_validator(mode="after")
    def validate_sort_option(self) -> "SearchDefinition":
        """Validate sort option is supported."""
        valid_sorts = ["latest", "top"]
        if self.sort not in valid_sorts:
            raise ValueError(f"Sort must be one of {valid_sorts}, got: {self.sort}")
        return self
    
    @field_validator('exclude_terms', mode='before')
    @classmethod
    def validate_exclude_terms(cls, v):
        """Clean up exclude terms before validation."""
        if v is None:
            return []
        if isinstance(v, list):
            # Filter out None, empty strings, and whitespace-only strings
            return [term for term in v if term is not None and isinstance(term, str) and term.strip()]
        return v
    
    @model_validator(mode="after") 
    def validate_terms(self) -> "SearchDefinition":
        """Validate that include terms are provided."""
        if not self.include_terms:
            raise ValueError("At least one include term must be provided")
        return self


class SearchConfig(BaseModel):
    """Configuration for all search definitions."""
    
    searches: dict[str, SearchDefinition] = Field(..., description="Search definitions by key")
    
    @model_validator(mode="after")
    def validate_searches(self) -> "SearchConfig":
        """Validate that at least one search is enabled."""
        enabled_searches = [s for s in self.searches.values() if s.enabled]
        if not enabled_searches:
            raise ValueError("At least one search definition must be enabled")
        return self
    
    def get_enabled_searches(self) -> dict[str, SearchDefinition]:
        """Get only enabled search definitions."""
        return {key: search for key, search in self.searches.items() if search.enabled}
    
    def get_search(self, key: str) -> SearchDefinition | None:
        """Get a specific search definition by key."""
        return self.searches.get(key)
    
    @classmethod
    def load_from_file(cls, file_path: str | Path) -> "SearchConfig":
        """Load search configuration from YAML file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Search configuration file not found: {file_path}")
        
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                raise ValueError("Search configuration must be a YAML object")
            
            logger.info(f"Loaded search configuration from {file_path}")
            return cls.model_validate(data)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in search configuration: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load search configuration: {e}") from e
    
    @classmethod
    def get_default_config(cls) -> "SearchConfig":
        """Get default search configuration."""
        default_searches = {
            "mcp_mentions": SearchDefinition(
                name="MCP Protocol Mentions",
                description="Posts about Model Context Protocol",
                include_terms=[
                    "mcp",
                    "model context protocol",
                    "anthropic mcp"
                ],
                exclude_terms=[
                    "minecraft",
                    "#mcp AND (medical OR healthcare OR clinic)"
                ],
                sort="latest",
                enabled=True
            ),
            "mcp_tools": SearchDefinition(
                name="MCP Tools and Implementations", 
                description="Posts about MCP tools and implementations",
                include_terms=[
                    "mcp tool",
                    "mcp server", 
                    "mcp client",
                    "mcp implementation"
                ],
                exclude_terms=[
                    "minecraft"
                ],
                sort="latest",
                enabled=True
            )
        }
        
        return cls(searches=default_searches)


def load_search_config(config_path: str | Path | None = None) -> SearchConfig:
    """
    Load search configuration from file or return default.
    
    Args:
        config_path: Path to YAML configuration file. If None, uses default config.
        
    Returns:
        SearchConfig instance
    """
    if config_path is None:
        logger.info("Using default search configuration")
        return SearchConfig.get_default_config()
    
    try:
        return SearchConfig.load_from_file(config_path)
    except Exception as e:
        logger.warning(f"Failed to load search config from {config_path}: {e}")
        logger.info("Falling back to default search configuration")
        return SearchConfig.get_default_config()