# Phase 3 Update: Add Perex Generation

## Overview
This document outlines the changes needed in Phase 3 to generate perexes during article evaluation, avoiding duplicate Anthropic API calls in Phase 5.

## Required Changes

### 1. Update ArticleEvaluation Model

Add perex field to `src/models/evaluation.py`:

```python
class ArticleEvaluation(BaseModel):
    """Evaluation result for an article from Anthropic API."""
    
    # Existing fields...
    
    # Add new field for Phase 5
    perex: Optional[str] = Field(
        None, 
        min_length=50, 
        max_length=150,
        description="Witty, engaging summary for HTML reports"
    )
```

### 2. Update Anthropic Evaluation Prompt

Modify the prompt in `src/processing/evaluator.py` to include perex generation:

```python
EVALUATION_PROMPT = """Analyze this article about Model Context Protocol (MCP).

Article URL: {url}
Title: {title}
Content (first {word_limit} words):
{content}

Provide your analysis in this EXACT CSV format (one line, no headers):
is_mcp_related,relevance_score,"topic1","topic2","topic3","summary","perex"

Requirements:
- is_mcp_related: true/false - Is this primarily about MCP or MCP tools?
- relevance_score: 0.0-1.0 - How relevant to MCP ecosystem
- topic1,topic2,topic3: Key topics (use "none" for empty slots)
- summary: Professional 2-3 sentence summary (max 250 chars)
- perex: Witty, slightly funny 2-3 sentence teaser that makes people want to click (50-100 words). Be engaging but informative, focusing on what's novel or interesting.

IMPORTANT: 
- Enclose ALL text fields in double quotes
- Keep summary professional and factual
- Make perex engaging with subtle humor
- No line breaks within fields

Example output:
true,0.85,"mcp-tools","claude-desktop","automation","Article explores new MCP tools for Claude Desktop enabling automated workflows.","Turns out Claude Desktop can now talk to your other apps through MCP, like a digital diplomat negotiating peace between your scattered productivity tools. The latest tools let you automate workflows that previously required more copy-paste than a kindergarten art project."
"""
```

### 3. Update CSV Parsing

Update `_parse_csv_response` method to handle the new perex field:

```python
def _parse_csv_response(self, csv_response: str) -> dict[str, Any]:
    """Parse CSV response from Claude."""
    reader = csv.reader(io.StringIO(csv_response.strip()))
    row = next(reader)
    
    if len(row) < 7:  # Now expecting 7 fields instead of 6
        raise ValueError(f"Expected 7 fields, got {len(row)}")
    
    return {
        "is_mcp_related": row[0].strip().lower() == "true",
        "relevance_score": float(row[1].strip()),
        "key_topics": [t.strip() for t in row[2:5] if t.strip() != "none"],
        "summary": row[5].strip(),
        "perex": row[6].strip() if len(row) > 6 else None,  # New field
    }
```

### 4. Update Processing Pipeline

Ensure the perex is included when creating ArticleEvaluation:

```python
evaluation = ArticleEvaluation(
    url=url,
    is_mcp_related=eval_result["is_mcp_related"],
    relevance_score=eval_result["relevance_score"],
    summary=eval_result["summary"],
    key_topics=eval_result["key_topics"],
    perex=eval_result.get("perex"),  # Include perex
    # ... other fields
)
```

## Benefits

1. **Cost Efficiency**: Single API call generates both evaluation and perex
2. **Consistency**: Perex is based on the same analysis as the evaluation
3. **Performance**: No additional API calls during report generation
4. **Simplicity**: Report generation just reads stored data

## Migration Strategy

For existing data without perexes:
1. Phase 5 will use the summary field as fallback
2. Optional: Create a migration command to regenerate evaluations with perexes
3. New evaluations will automatically include perexes

## Testing

Update tests to:
1. Include perex in mock API responses
2. Validate perex field in ArticleEvaluation
3. Test CSV parsing with 7 fields
4. Ensure backward compatibility with 6-field responses

## Estimated Impact

- No additional development time for Phase 3 (just prompt update)
- Saves 2-3 hours in Phase 5 (no perex generation needed)
- Reduces API costs by ~50% for report generation
- Faster report generation (no API calls needed)