import marimo

__generated_with = "0.13.15"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import sys
    from pathlib import Path
    
    sys.path.append(str(Path(__file__).parent.parent / "src"))
    
    return mo, pd, sys, Path


@app.cell
def _(mo):
    mo.md("# Notebook Title")
    return


@app.cell
def _(mo):
    # Example: Conditional display - CORRECT PATTERN
    
    # 1. Do computation inside control blocks
    try:
        result = "computation successful"
        status = "✅ Success"
    except Exception as e:
        result = "computation failed"
        status = f"❌ Error: {e}"
    
    # 2. Display OUTSIDE control blocks, BEFORE return
    mo.md(f"Status: {status}")
    return result,


@app.cell
def _(mo):
    # Example: Conditional UI - CORRECT PATTERN
    
    # 1. Prepare UI element based on condition
    if True:  # your condition here
        display_element = mo.md("Show this content")
    else:
        display_element = mo.md("Show alternative content")
    
    # 2. Display OUTSIDE if/else, BEFORE return
    display_element
    return


if __name__ == "__main__":
    app.run()