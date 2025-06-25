# MARIMO_RULES.md

Guidelines for writing marimo notebooks in this project.

## CRITICAL RULES - MUST FOLLOW

1. **Display calls MUST be the last expression**: The output of a marimo cell is determined by the LAST expression in the cell
   - Bad: `if condition: mo.md("text")` (conditional is last expression, not mo.md)
   - Bad: `mo.md("text"); some_variable = 5` (assignment is last expression)
   - Good: `mo.md("text")` (mo.md is last expression)
   - Good: Separate computation and display into different cells

2. **No conditional output**: NEVER wrap mo.md(), mo.ui.table(), etc. in conditionals
   - Bad: `if not df.empty: mo.md("content")`
   - Good: `mo.md(f"Content: {len(df)} rows")` (assume data exists)

3. **Assume data exists**: Don't check for empty dataframes - let it fail with exception if data missing
   - Bad: `if not df.empty: analysis = df.describe()`
   - Good: `analysis = df.describe()` (if df is empty, we have bigger problems)

4. **Unique cell variables**: Every variable must have a unique name across all cells
   - Don't reuse variable names like `df` 
   - Use descriptive names like `evaluated_content`, `mcp_articles`, etc.
   - Don't repeat import statements

5. **One display call per cell**: Only one marimo display call per cell
   - Bad: Two `mo.md()` calls in one cell
   - Good: Combine into single call or split into separate cells


## Example Patterns

### Loading data
```python
@app.cell
def _(Path, pd, yaml):
    def load_evaluated_content(days_back: int = 7) -> pd.DataFrame:
        # implementation
        return df
    
    return (load_evaluated_content,)
```

### Displaying tables
```python
@app.cell
def _(evaluated_content, mo):
    mo.ui.table(
        evaluated_content,
        selection=None,
        pagination=True,
        page_size=30
    )
    return
```

### Filtering data
```python
@app.cell
def _(evaluated_content):
    mcp_articles = evaluated_content[evaluated_content['is_mcp_related']].copy()
    return (mcp_articles,)
```