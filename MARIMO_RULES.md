# MARIMO_RULES.md

Guidelines for writing marimo notebooks in this project.

## Key Rules

1. **Unique cell variables**: Every variable must have a unique name across all cells
   - Don't reuse variable names like `df` 
   - Use descriptive names like `evaluated_content`, `mcp_articles`, etc.
   - dont repeat import statements

2. **No conditional output**: Don't wrap output in conditional checks
   - Bad: `if not df.empty: mo.ui.table(df)`
   - Good: `mo.ui.table(df)`

3. **No export features**: Don't build export functionality
   - Marimo notebooks are for analysis and exploration
   - There is an export feature built in

4. **One mo call per cell**: Only one marimo display call per cell
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