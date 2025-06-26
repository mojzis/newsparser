# Marimo Notebook Development Guidelines

This document provides essential guidelines for developing marimo notebooks effectively.

## Core Display Pattern

**CRITICAL RULE**: In marimo, `mo.md()` and other display functions must be the **last statement** before the `return` statement, **OUTSIDE any control blocks**.

### ❌ WRONG Pattern
```python
@app.cell
def _(mo):
    try:
        result = some_computation()
        mo.md("✅ Success!")  # WRONG: Inside try block
    except Exception as e:
        mo.md(f"❌ Error: {e}")  # WRONG: Inside except block
    return
```

### ❌ WRONG Pattern 
```python
@app.cell
def _(mo):
    if condition:
        mo.md("Condition is true")  # WRONG: Inside if block
    else:
        mo.md("Condition is false")  # WRONG: Inside else block
    return
```

### ✅ CORRECT Pattern
```python
@app.cell
def _(mo):
    # Do computation inside control blocks
    try:
        result = some_computation()
        message = "✅ Success!"
    except Exception as e:
        message = f"❌ Error: {e}"
    
    # Display OUTSIDE control blocks, BEFORE return
    mo.md(message)
    return
```

### ✅ CORRECT Pattern for Conditionals
```python
@app.cell
def _(mo):
    # Prepare content based on condition
    if condition:
        content = "Condition is true"
    else:
        content = "Condition is false"
    
    # Display OUTSIDE if/else, BEFORE return
    mo.md(content)
    return
```

## Key Principles

### 1. Control Blocks vs Display
- **Control blocks** include: `try/except`, `if/else`, `for` loops, `while` loops, function definitions, `with` statements
- **Display functions** include: `mo.md()`, `mo.ui.table()`, `mo.as_html()`, etc.
- **Rule**: Display functions must be OUTSIDE control blocks

### 2. Cell Structure
```python
@app.cell
def _(dependencies):
    # 1. Variable preparation
    # 2. Control flow (try/except, if/else, loops)
    # 3. Content preparation
    # 4. Display call (mo.md, mo.ui.table, etc.) - OUTSIDE control blocks
    # 5. Return statement (for variable passing between cells)
    return variables_for_other_cells
```

### 3. Return Statement Purpose
- The `return` statement is for **passing variables between cells**
- It's an **internal marimo mechanism**, not user-visible
- The **last expression before `return`** is what gets displayed

### 4. Dynamic Content Generation
```python
@app.cell
def _(mo, data):
    # Generate dynamic content
    items = []
    for item in data:
        if item.is_valid:
            items.append(f"✅ {item.name}")
        else:
            items.append(f"❌ {item.name}")
    
    # Create final content
    content = f"""
    ## Results
    {chr(10).join(items)}
    """
    
    # Display OUTSIDE the loop, BEFORE return
    mo.md(content)
    return
```

## Common Mistakes to Avoid

### 1. Display Inside Try/Except
```python
# ❌ WRONG
try:
    result = compute()
    mo.md("Success")  # Won't display!
except:
    mo.md("Failed")   # Won't display!

# ✅ CORRECT
try:
    result = compute()
    status = "Success"
except:
    status = "Failed"
mo.md(status)
```

### 2. Display Inside Loops
```python
# ❌ WRONG
for item in items:
    mo.md(f"Processing {item}")  # Only last one might display

# ✅ CORRECT
messages = []
for item in items:
    messages.append(f"Processing {item}")
mo.md("\n".join(messages))
```

### 3. Display Inside Functions
```python
# ❌ WRONG
def process_data():
    mo.md("Processing...")  # Won't display
    return result

# ✅ CORRECT
def process_data():
    return "Processing complete"

status = process_data()
mo.md(status)
```

## Advanced Patterns

### Conditional UI Elements
```python
@app.cell
def _(mo, condition):
    if condition:
        element = mo.ui.slider(0, 100)
    else:
        element = mo.md("Slider not available")
    
    # Display the chosen element
    element
    return
```

### Error Handling with Rich Display
```python
@app.cell
def _(mo, conn):
    try:
        df = conn.execute("SELECT * FROM table").df()
        display_element = mo.ui.table(df)
    except Exception as e:
        display_element = mo.md(f"""
        ## Database Error
        
        **Error**: {str(e)}
        
        Please check your connection and try again.
        """)
    
    # Display the appropriate element
    display_element
    return
```

## 🚨 RED FLAGS - NEVER DO THIS

### ❌ These patterns are ALWAYS WRONG:
```python
if condition:
    mo.md("text")  # WRONG - display inside if

try:
    result = compute()
    mo.ui.table(df)  # WRONG - display inside try
except:
    mo.md("error")  # WRONG - display inside except

for item in items:
    mo.md(f"item: {item}")  # WRONG - display inside loop
```

### ✅ Correct pattern is ALWAYS:
```python
# 1. Prepare content inside control blocks
if condition:
    content = "success message"
else:
    content = "error message"

# 2. Display OUTSIDE control blocks
mo.md(content)
```

## Checklist Before Writing ANY Cell

Before writing a marimo cell, ask yourself:
1. ❓ Am I putting `mo.md()`, `mo.ui.table()`, or ANY display function inside `if`, `try`, `for`, `while`, or `with`?
2. ❓ If YES → STOP! Prepare content inside, display outside
3. ❓ Is my display function the LAST statement before `return`?
4. ❓ If NO → Move it to be the last statement

## Remember
- **Last statement rule**: Display functions must be the last statement before `return`
- **Outside control blocks**: Never put display functions inside `try`, `if`, `for`, `while`, `with`, or function definitions
- **Prepare then display**: Do computation in control blocks, prepare content, then display outside
- **Return for variables**: Use `return` only to pass variables to other cells

Following these patterns ensures your marimo notebooks display content correctly and maintain proper reactive behavior.