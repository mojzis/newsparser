# Phase 2.7: Native Bluesky Search Syntax

## Overview
Phase 2.7 introduces a native Bluesky search syntax query builder as an alternative to the Lucene-based approach. This is based on observed behavior where Bluesky's web interface successfully processes queries like `#mcp -#marvel` for hashtag-based filtering.

## Background
- The Lucene query syntax implemented in Phase 2.6 may not be fully compatible with Bluesky's search API
- Testing shows that Bluesky's native syntax uses simple hashtag inclusion/exclusion (e.g., `#mcp -#marvel`)
- Need to provide both options and make native syntax the default

## Objectives
- Implement a native Bluesky query builder using observed syntax patterns
- Support hashtag-based include/exclude with `-` prefix for exclusions
- Make query builder selectable per search definition
- Set native syntax as the default approach
- Maintain backward compatibility with Lucene syntax

## Implementation Design

### 1. Native Query Syntax Rules
```
Include hashtag: #tag
Exclude hashtag: -#tag
Multiple terms: #mcp -#marvel -#minipainting
Regular keywords: mcp tools (no special syntax)
Mixed: mcp #tools -#minecraft
```

### 2. Query Builder Architecture
```python
class QueryBuilder(ABC):
    @abstractmethod
    def build_query(self, search_definition: SearchDefinition) -> str:
        pass

class NativeQueryBuilder(QueryBuilder):
    """Bluesky native search syntax"""
    
class LuceneQueryBuilder(QueryBuilder):
    """Lucene-based syntax (existing)"""
```

### 3. Enhanced SearchDefinition
```yaml
searches:
  mcp_tag:
    name: "MCP Hashtag"
    query_syntax: "native"  # or "lucene"
    include_terms:
      - "#mcp"
    exclude_terms:
      - "#marvel"
      - "#minipainting"
```

## Implementation Tasks

### Task 1: Create Query Builder Infrastructure
- [ ] Create abstract QueryBuilder base class
- [ ] Move existing Lucene logic to LuceneQueryBuilder
- [ ] Add query builder factory pattern
- [ ] Update imports and references

### Task 2: Implement Native Query Builder
- [ ] Create NativeQueryBuilder class
- [ ] Implement hashtag detection and formatting
- [ ] Handle exclude terms with `-` prefix
- [ ] Support mixed keyword and hashtag queries
- [ ] Add query validation

### Task 3: Update Search Configuration
- [ ] Add `query_syntax` field to SearchDefinition (default: "native")
- [ ] Update YAML schema and examples
- [ ] Add validation for syntax selection
- [ ] Update default search configurations

### Task 4: Integration and Testing
- [ ] Update BlueskyClient to use query builder factory
- [ ] Add tests for both query builders
- [ ] Test with real Bluesky searches
- [ ] Document syntax differences

### Task 5: CLI and Documentation
- [ ] Update CLI to show query syntax in use
- [ ] Add syntax examples to help text
- [ ] Update CLAUDE.md with new options
- [ ] Add migration notes for existing configs

## Technical Details

### Native Query Builder Logic
```python
def build_query(self, search_definition: SearchDefinition) -> str:
    parts = []
    
    # Add include terms as-is
    for term in search_definition.include_terms:
        parts.append(term)
    
    # Add exclude terms with - prefix
    for term in search_definition.exclude_terms:
        if term.startswith("#"):
            parts.append(f"-{term}")
        else:
            # For non-hashtag excludes, might need different handling
            parts.append(f'-"{term}"')
    
    return " ".join(parts)
```

### Example Outputs
- Include: `["#mcp", "tools"]` → `#mcp tools`
- Exclude: `["#marvel", "minecraft"]` → `-#marvel -"minecraft"`
- Mixed: `["#mcp", "protocol"]` + exclude `["#marvel"]` → `#mcp protocol -#marvel`

## Migration Path
1. Existing searches continue to work with Lucene syntax
2. New searches default to native syntax
3. Users can explicitly set `query_syntax` to override
4. Provide conversion utility if needed

## Success Criteria
- Native syntax queries return expected results from Bluesky
- Both query builders coexist without conflicts
- Search results improve for hashtag-based searches
- Clear documentation on syntax differences
- Smooth migration for existing users

## Risk Mitigation
- Maintain both builders for compatibility
- Default to native but allow easy switching
- Comprehensive testing with real Bluesky data
- Clear error messages for syntax issues
- Document limitations of each approach

## Next Steps
After Phase 2.7, we'll have robust search capabilities with two syntax options, setting the stage for Phase 3's content processing pipeline.