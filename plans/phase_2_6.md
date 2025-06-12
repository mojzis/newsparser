# Phase 2.6: Configurable Search Queries - Implementation Documentation

## Overview

Phase 2.6 enhanced the Bluesky search functionality by implementing configurable search definitions with include/exclude terms, leveraging Lucene query syntax, and adding sorting options. This addresses the issue of false positives (e.g., #mcp used for other purposes) and provides flexibility for multiple search scenarios.

## Implementation Steps

### 1. Search Configuration Management

**Created SearchConfig Pydantic Models (`src/config/searches.py`):**
- `SearchDefinition`: Model for individual search configurations
- `SearchConfig`: Container for multiple search definitions
- YAML file loading with validation and error handling
- Default configuration fallback mechanism

**Key Features:**
```python
class SearchDefinition(BaseModel):
    name: str
    description: str
    include_terms: list[str]
    exclude_terms: list[str] = []
    sort: str = "latest"
    enabled: bool = True
```

**Configuration File (`src/config/searches.yaml`):**
- Default MCP-focused search definitions
- Include/exclude term examples
- Hashtag exclusion patterns
- Boolean logic examples

### 2. Lucene Query Builder

**Implemented LuceneQueryBuilder (`src/bluesky/query_builder.py`):**
- Converts search definitions to Lucene query syntax
- Handles special character escaping
- Supports complex boolean expressions
- Query validation and error checking

**Core Functionality:**
- Include term combination with OR logic
- Exclude term negation with NOT logic
- Special character escaping for safety
- Complex query detection and handling
- Query validation before API calls

### 3. BlueskyClient Enhancement

**Updated BlueskyClient (`src/bluesky/client.py`):**
- Added `search_by_definition()` method for configurable searches
- Enhanced `search_posts()` with sort parameter support
- New `get_posts_by_definition()` for paginated collection
- Maintained backward compatibility with existing methods

**API Changes:**
```python
async def search_by_definition(
    self, search_definition: SearchDefinition, limit: int = 25, cursor: str | None = None
) -> tuple[list[BlueskyPost], str | None]

async def search_posts(
    self, query: str, limit: int = 25, cursor: str | None = None, sort: str = "latest"
) -> tuple[list[BlueskyPost], str | None]
```

### 4. CLI Command Updates

**Enhanced CLI Commands (`src/cli/commands.py`):**

#### Updated `collect` command:
- Added `--search` option for search definition selection
- Added `--config` option for custom YAML configuration
- Enhanced error handling and validation
- Rich console feedback with search context

#### New `list-searches` command:
- Displays available search definitions in formatted table
- Shows enabled/disabled status, terms, and configuration
- Supports custom configuration files

#### New `validate-config` command:
- Validates YAML configuration syntax and structure
- Tests query building for all definitions
- Provides detailed error reporting
- Confirms search definition validity

**Updated CLI Usage:**
```bash
# Use specific search definition
poetry run newsparser collect --search mcp_tools

# Use custom configuration
poetry run newsparser collect --config custom_searches.yaml

# List available searches
poetry run newsparser list-searches

# Validate configuration
poetry run newsparser validate-config --config searches.yaml
```

### 5. Data Collection Updates

**Enhanced BlueskyDataCollector (`src/bluesky/collector.py`):**
- Added `collect_posts_by_definition()` method
- Added `collect_and_store_by_definition()` method
- Maintained backward compatibility with existing methods
- Enhanced logging with search definition context

**New Methods:**
```python
async def collect_posts_by_definition(
    self, search_definition: SearchDefinition, target_date: date | None = None, max_posts: int = 100
) -> list[BlueskyPost]

async def collect_and_store_by_definition(
    self, search_definition: SearchDefinition, target_date: date | None = None, max_posts: int = 100
) -> tuple[int, bool]
```

### 6. Comprehensive Testing

**Created Test Suites:**

#### SearchConfig Tests (`tests/test_config/test_searches.py`):
- SearchDefinition validation testing
- YAML file loading and error handling
- Default configuration testing
- Search filtering and retrieval testing

#### LuceneQueryBuilder Tests (`tests/test_bluesky/test_query_builder.py`):
- Query building with various term types
- Special character escaping validation
- Complex query detection and handling
- Query validation testing
- Real-world example testing

**Test Coverage:**
- Unit tests for all new functionality
- Edge case handling (empty terms, special characters)
- Error condition testing
- Integration testing with existing components

## Technical Implementation Details

### Query Building Logic

**Include Terms Processing:**
1. Detect complex vs. simple queries
2. Escape special characters in simple terms
3. Quote terms containing spaces
4. Combine multiple terms with OR logic
5. Wrap complex expressions in parentheses

**Exclude Terms Processing:**
1. Apply same processing as include terms
2. Prefix each term with NOT operator
3. Combine multiple exclusions with AND logic
4. Maintain operator precedence with parentheses

### Search Definition Examples

**Basic MCP Search:**
```yaml
mcp_mentions:
  name: "MCP Protocol Mentions"
  include_terms:
    - "mcp"
    - "model context protocol"
  exclude_terms:
    - "minecraft"
    - "#mcp AND (medical OR healthcare)"
  sort: "latest"
```

**Generated Query:**
```
(mcp OR "model context protocol") AND (NOT minecraft AND NOT (#mcp AND (medical OR healthcare)))
```

**Advanced Boolean Search:**
```yaml
mcp_tools:
  name: "MCP Tools"
  include_terms:
    - "(mcp AND (tool OR server OR client))"
    - "anthropic mcp"
  exclude_terms:
    - "minecraft"
```

**Generated Query:**
```
(((mcp AND (tool OR server OR client))) OR "anthropic mcp") AND (NOT minecraft)
```

### Error Handling Strategy

**Configuration Loading:**
- YAML syntax validation
- Pydantic model validation
- Graceful fallback to default configuration
- Detailed error reporting

**Query Building:**
- Special character escaping
- Query syntax validation
- Operator precedence handling
- Clear error messages for invalid patterns

**API Integration:**
- Query validation before API calls
- Comprehensive error logging
- Graceful degradation on failures
- Rate limiting preservation

## Integration Points

### Backward Compatibility
- All existing CLI commands continue to work
- Previous API methods remain functional
- Default behavior unchanged for existing workflows
- Gradual migration path available

### Configuration Management
- Environment-based configuration loading
- Custom configuration file support
- Default configuration embedded in code
- Runtime validation and error reporting

### Search Flexibility
- Multiple search definitions support
- Enable/disable individual searches
- Custom boolean logic expressions
- Hashtag and keyword exclusion patterns

## Usage Examples

### CLI Operations
```bash
# List available search definitions
poetry run newsparser list-searches

# Validate configuration file
poetry run newsparser validate-config

# Collect using specific search
poetry run newsparser collect --search mcp_tools --max-posts 50

# Use custom configuration
poetry run newsparser collect --config custom.yaml --search advanced_mcp
```

### Configuration Examples
```yaml
searches:
  precise_mcp:
    name: "Precise MCP Search"
    description: "High-precision MCP posts"
    include_terms:
      - "(mcp AND (anthropic OR claude OR protocol))"
      - "model context protocol"
    exclude_terms:
      - "minecraft"
      - "(medical OR healthcare) AND #mcp"
      - "minecraft OR mc"
    sort: "latest"
    enabled: true
```

## Benefits Achieved

### Search Quality Improvements
- Reduced false positives from unrelated #mcp usage
- Better targeting of relevant MCP content
- Flexible exclusion patterns for noise reduction
- Support for complex boolean search logic

### Operational Flexibility
- Multiple search scenarios without code changes
- Easy configuration updates via YAML files
- Runtime search definition switching
- Custom search patterns for different use cases

### Developer Experience
- Rich CLI feedback and error reporting
- Comprehensive validation and testing
- Clear documentation and examples
- Graceful error handling and fallbacks

## Phase 2.6 Completion Status

✅ **Core Implementation:**
- YAML-based search configuration system
- Lucene query builder with validation
- Enhanced BlueskyClient with configurable searches
- Updated CLI commands with new options

✅ **Quality Assurance:**
- Comprehensive test coverage for new functionality
- Error handling and edge case validation
- Backward compatibility maintenance
- Real-world usage examples

✅ **Documentation:**
- Implementation documentation
- Configuration examples
- CLI usage guides
- Integration patterns

## Dependencies Added

```toml
# Production dependency
pyyaml = "^6.0.0"
```

## Configuration Files

```
src/config/searches.yaml    # Default search definitions
```

## Known Limitations

### Query Complexity
- Limited to Bluesky's Lucene syntax support
- No advanced semantic search capabilities
- Manual tuning required for optimal results

### Configuration Management
- No web interface for configuration editing
- Manual YAML file management required
- No runtime configuration hot-reloading

### Future Enhancements
- Web-based configuration management
- Machine learning-based relevance tuning
- Search analytics and optimization
- Dynamic search suggestion system

## Lessons Learned

1. **Query Complexity**: Lucene syntax provides powerful filtering but requires careful validation
2. **Configuration Design**: YAML provides good balance of readability and functionality
3. **Backward Compatibility**: Maintaining existing APIs while adding new features requires careful planning
4. **Error Handling**: Comprehensive validation prevents runtime errors and improves user experience
5. **Testing Strategy**: Complex query building logic benefits from extensive unit testing

## Next Steps

Phase 2.6 provides a robust foundation for flexible search configuration. The next phase (Phase 3) will focus on content processing using the Anthropic API, leveraging the improved search capabilities to process higher-quality, more relevant posts.