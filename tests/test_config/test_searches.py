from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import yaml

from src.config.searches import SearchConfig, SearchDefinition, load_search_config


class TestSearchDefinition:
    def test_valid_search_definition(self):
        """Test creating a valid search definition."""
        search_def = SearchDefinition(
            name="Test Search",
            description="A test search definition",
            include_terms=["test", "example"],
            exclude_terms=["spam"],
            sort="latest",
            enabled=True
        )
        
        assert search_def.name == "Test Search"
        assert search_def.description == "A test search definition"
        assert search_def.include_terms == ["test", "example"]
        assert search_def.exclude_terms == ["spam"]
        assert search_def.sort == "latest"
        assert search_def.enabled is True
    
    def test_default_values(self):
        """Test search definition with default values."""
        search_def = SearchDefinition(
            name="Test Search",
            description="A test search definition",
            include_terms=["test"]
        )
        
        assert search_def.exclude_terms == []
        assert search_def.sort == "latest"
        assert search_def.enabled is True
    
    def test_empty_exclude_terms(self):
        """Test search definition with explicitly empty exclude terms."""
        search_def = SearchDefinition(
            name="Test Search",
            description="A test search definition",
            include_terms=["test"],
            exclude_terms=[]
        )
        
        assert search_def.exclude_terms == []
    
    def test_none_exclude_terms(self):
        """Test search definition with None exclude terms (from YAML)."""
        search_def = SearchDefinition(
            name="Test Search",
            description="A test search definition",
            include_terms=["test"],
            exclude_terms=None
        )
        
        assert search_def.exclude_terms == []
    
    def test_exclude_terms_with_empty_strings(self):
        """Test that empty strings are filtered from exclude terms."""
        search_def = SearchDefinition(
            name="Test Search",
            description="A test search definition",
            include_terms=["test"],
            exclude_terms=["valid", "", "  ", "also_valid", None]
        )
        
        assert search_def.exclude_terms == ["valid", "also_valid"]
    
    def test_invalid_sort_option(self):
        """Test validation of sort option."""
        with pytest.raises(ValueError, match="Sort must be one of"):
            SearchDefinition(
                name="Test Search",
                description="A test search definition",
                include_terms=["test"],
                sort="invalid"
            )
    
    def test_empty_include_terms(self):
        """Test validation of empty include terms."""
        with pytest.raises(ValueError, match="At least one include term must be provided"):
            SearchDefinition(
                name="Test Search",
                description="A test search definition",
                include_terms=[]
            )


class TestSearchConfig:
    def test_valid_config(self):
        """Test creating a valid search configuration."""
        search_def = SearchDefinition(
            name="Test Search",
            description="A test search definition",
            include_terms=["test"]
        )
        
        config = SearchConfig(searches={"test": search_def})
        
        assert "test" in config.searches
        assert config.searches["test"] == search_def
    
    def test_get_enabled_searches(self):
        """Test getting only enabled searches."""
        enabled_search = SearchDefinition(
            name="Enabled Search",
            description="An enabled search",
            include_terms=["test"],
            enabled=True
        )
        
        disabled_search = SearchDefinition(
            name="Disabled Search",
            description="A disabled search",
            include_terms=["test"],
            enabled=False
        )
        
        config = SearchConfig(searches={
            "enabled": enabled_search,
            "disabled": disabled_search
        })
        
        enabled_searches = config.get_enabled_searches()
        assert len(enabled_searches) == 1
        assert "enabled" in enabled_searches
        assert "disabled" not in enabled_searches
    
    def test_get_search(self):
        """Test getting a specific search definition."""
        search_def = SearchDefinition(
            name="Test Search",
            description="A test search definition",
            include_terms=["test"]
        )
        
        config = SearchConfig(searches={"test": search_def})
        
        retrieved = config.get_search("test")
        assert retrieved == search_def
        
        not_found = config.get_search("nonexistent")
        assert not_found is None
    
    def test_no_enabled_searches(self):
        """Test validation when no searches are enabled."""
        disabled_search = SearchDefinition(
            name="Disabled Search",
            description="A disabled search",
            include_terms=["test"],
            enabled=False
        )
        
        with pytest.raises(ValueError, match="At least one search definition must be enabled"):
            SearchConfig(searches={"disabled": disabled_search})
    
    def test_load_from_file_success(self):
        """Test loading configuration from YAML file."""
        test_config = {
            "searches": {
                "test_search": {
                    "name": "Test Search",
                    "description": "A test search",
                    "include_terms": ["test", "example"],
                    "exclude_terms": ["spam"],
                    "sort": "latest",
                    "enabled": True
                }
            }
        }
        
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name
        
        try:
            config = SearchConfig.load_from_file(temp_path)
            
            assert len(config.searches) == 1
            assert "test_search" in config.searches
            
            search_def = config.searches["test_search"]
            assert search_def.name == "Test Search"
            assert search_def.include_terms == ["test", "example"]
            assert search_def.exclude_terms == ["spam"]
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            SearchConfig.load_from_file("nonexistent.yaml")
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                SearchConfig.load_from_file(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_invalid_structure(self):
        """Test loading YAML with invalid structure."""
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump("invalid_structure", f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Search configuration must be a YAML object"):
                SearchConfig.load_from_file(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        config = SearchConfig.get_default_config()
        
        assert len(config.searches) >= 2  # Should have at least mcp_mentions and mcp_tools
        assert "mcp_mentions" in config.searches
        assert "mcp_tools" in config.searches
        
        # Check that default searches are properly configured
        mcp_mentions = config.searches["mcp_mentions"]
        assert mcp_mentions.enabled is True
        assert "mcp" in mcp_mentions.include_terms
        assert "minecraft" in mcp_mentions.exclude_terms


class TestLoadSearchConfig:
    def test_load_with_none_path(self):
        """Test loading with None path returns default config."""
        config = load_search_config(None)
        
        assert isinstance(config, SearchConfig)
        assert len(config.searches) >= 2
        assert "mcp_mentions" in config.searches
    
    def test_load_with_valid_file(self):
        """Test loading with valid file."""
        test_config = {
            "searches": {
                "custom_search": {
                    "name": "Custom Search",
                    "description": "A custom search",
                    "include_terms": ["custom"],
                    "enabled": True
                }
            }
        }
        
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name
        
        try:
            config = load_search_config(temp_path)
            
            assert len(config.searches) == 1
            assert "custom_search" in config.searches
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_with_invalid_file_falls_back(self):
        """Test that invalid file falls back to default config."""
        config = load_search_config("nonexistent.yaml")
        
        # Should fall back to default config
        assert isinstance(config, SearchConfig)
        assert len(config.searches) >= 2
        assert "mcp_mentions" in config.searches