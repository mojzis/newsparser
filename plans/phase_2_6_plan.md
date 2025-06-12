# Phase 2.6: Configurable Search Queries - Implementation Plan

## Overview

Phase 2.6 enhances the Bluesky search functionality by implementing configurable search definitions with include/exclude terms, leveraging Lucene query syntax, and adding sorting options. This addresses the issue of false positives (e.g., #mcp used for other purposes) and provides flexibility for multiple search scenarios.

## Goals

1. Replace hardcoded "mcp" search with configurable YAML-based search definitions
2. Implement Lucene query syntax support for complex search patterns
3. Add include/exclude term functionality
4. Implement sorting options (starting with "latest")
5. Support multiple search definitions for different use cases
6. Maintain backward compatibility with existing CLI commands

## Technical Requirements

### Search Configuration Schema
```yaml
# Example: searches.yaml
searches:
  mcp_mentions:
    name: "MCP Protocol Mentions"
    description: "Posts about Model Context Protocol"
    include_terms:
      - "mcp"
      - "model context protocol"
      - "anthropic mcp"
    exclude_terms:
      - "#mcp AND (medical OR healthcare OR clinic)"
      - "minecraft"
    sort: "latest"
    enabled: true
    
  mcp_tools:
    name: "MCP Tools and Implementations"
    description: "Posts about MCP tools and implementations"
    include_terms:
      - "mcp tool"
      - "mcp server"
      - "mcp client"
    exclude_terms:
      - "minecraft"
    sort: "latest"
    enabled: true
```

### Lucene Query Building
- Convert YAML search definitions to Lucene query syntax
- Support boolean operators (AND, OR, NOT)
- Handle hashtag exclusions properly
- Validate query syntax before execution

### API Integration
- Update BlueskyClient to accept Lucene queries
- Implement sort parameter support
- Maintain pagination with new query structure
- Add query validation and error handling

## Implementation Tasks

### 1. Search Configuration Management
- [ ] Create `SearchConfig` Pydantic model for YAML schema validation
- [ ] Implement YAML file loading with pydantic-settings integration
- [ ] Add configuration validation and error reporting
- [ ] Create default searches.yaml with MCP-focused definitions

### 2. Lucene Query Builder
- [ ] Implement `LuceneQueryBuilder` class
- [ ] Add methods for combining include/exclude terms
- [ ] Handle special characters and escaping
- [ ] Support hashtag-specific exclusions
- [ ] Add query validation before API calls

### 3. BlueskyClient Enhancement
- [ ] Update search methods to accept Lucene queries
- [ ] Add sort parameter support ("latest", "top")
- [ ] Modify existing search_posts method signature
- [ ] Update search_mcp_mentions to use configurable queries
- [ ] Add search definition selection capability

### 4. CLI Command Updates
- [ ] Add search definition selection to collect command
- [ ] Update status and list-posts commands for multiple searches
- [ ] Add search configuration validation command
- [ ] Provide search definition listing capability

### 5. Data Collection Updates
- [ ] Update BlueskyDataCollector to handle multiple search definitions
- [ ] Modify storage structure to include search metadata
- [ ] Add search definition tracking in stored data
- [ ] Update retrieval methods for search-specific data

### 6. Configuration Integration
- [ ] Add searches.yaml to project structure
- [ ] Update Settings class to include search configuration
- [ ] Add environment variable for custom search config path
- [ ] Create example configuration file

### 7. Testing
- [ ] Create unit tests for LuceneQueryBuilder
- [ ] Add tests for SearchConfig validation
- [ ] Mock Bluesky API responses for new query formats
- [ ] Test CLI commands with multiple search definitions
- [ ] Add integration tests for end-to-end search workflow

### 8. Documentation
- [ ] Document search configuration format
- [ ] Add examples of complex Lucene queries
- [ ] Update CLI help text and examples
- [ ] Create troubleshooting guide for search configuration

## File Structure Changes

```
src/
├── config/
│   ├── searches.py          # SearchConfig models
│   └── searches.yaml        # Default search definitions
├── bluesky/
│   ├── query_builder.py     # LuceneQueryBuilder
│   └── client.py            # Updated with query support
└── cli/
    └── commands.py          # Updated CLI commands

tests/
├── test_config/
│   └── test_searches.py     # Search config tests
├── test_bluesky/
│   └── test_query_builder.py # Query builder tests
└── fixtures/
    └── test_searches.yaml   # Test configurations
```

## API Changes

### BlueskyClient Updates
```python
# Current
async def search_mcp_mentions(self, limit: int = 25, cursor: str | None = None)

# New
async def search_posts_by_definition(
    self, 
    search_definition: SearchDefinition,
    limit: int = 25, 
    cursor: str | None = None,
    sort: str = "latest"
) -> tuple[list[BlueskyPost], str | None]

async def search_all_definitions(
    self, 
    limit_per_search: int = 25
) -> dict[str, list[BlueskyPost]]
```

### CLI Command Updates
```bash
# New options
poetry run newsparser collect --search mcp_mentions
poetry run newsparser collect --search all
poetry run newsparser list-searches
poetry run newsparser validate-config
```

## Search Definition Examples

### Basic MCP Search
```yaml
mcp_mentions:
  name: "MCP Protocol Mentions"
  include_terms:
    - "mcp"
    - "model context protocol"
  exclude_terms:
    - "minecraft"
    - "#mcp AND medical"
  sort: "latest"
```

### Advanced Search with Boolean Logic
```yaml
mcp_implementations:
  name: "MCP Implementations"
  include_terms:
    - "(mcp AND (server OR client OR tool))"
    - "anthropic mcp"
  exclude_terms:
    - "minecraft"
    - "(medical OR healthcare) AND #mcp"
  sort: "latest"
```

## Backward Compatibility

- Existing CLI commands continue to work with default MCP search
- Current data storage format remains unchanged
- API methods maintain existing signatures with new optional parameters
- Phase 2.5 notebook continues to function with enhanced data

## Success Criteria

1. YAML configuration loads and validates correctly
2. Lucene queries generate expected API calls
3. Search exclusions effectively filter false positives
4. Multiple search definitions can run simultaneously
5. CLI commands support new search selection
6. Existing functionality remains unaffected
7. Search results show improved relevance

## Risk Mitigation

### Query Complexity
- Validate Lucene syntax before API calls
- Provide clear error messages for invalid queries
- Test complex boolean expressions thoroughly

### API Rate Limits
- Maintain existing rate limiting for multiple searches
- Consider staggered execution for multiple definitions
- Monitor API usage with enhanced queries

### Configuration Errors
- Comprehensive YAML validation
- Default fallback configurations
- Clear error reporting for configuration issues

## Future Enhancements

- Web interface for search configuration management
- Machine learning-based relevance scoring
- Search result analytics and optimization
- Dynamic search term suggestions
- A/B testing for search effectiveness

## Dependencies

No new external dependencies required. Uses existing:
- pydantic for configuration validation
- PyYAML (if not already included)
- Existing atproto and typer infrastructure

This plan provides a comprehensive approach to configurable search while maintaining system stability and backward compatibility.