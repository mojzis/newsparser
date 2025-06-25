# Notebooks

This directory contains marimo notebooks for analytics and data exploration.

## Files

- **`stats.py`** - Project statistics dashboard showing data pipeline metrics

## Usage

### Running Notebooks Directly

```bash
# Run the stats notebook interactively
poetry run marimo run notebooks/stats.py

# Edit the stats notebook
poetry run marimo edit notebooks/stats.py
```

### Generating HTML Pages

```bash
# Generate stats HTML page (includes navigation)
poetry run nsp stages render-stats

# Output: output/stats.html
```

## Development Guidelines

When creating new marimo notebooks:
- Use unique variable names across cells to avoid conflicts
- Follow the existing naming patterns (`variable_name_suffix`)
- Ensure notebooks work in both interactive and export modes
- Add comprehensive markdown documentation for each section
- Use relative imports when accessing project modules

## Export Integration

The `render-stats` command automatically:
1. Exports the notebook to HTML using marimo
2. Adds project navigation header
3. Saves to `output/stats.html`
4. Includes as part of the `run-all` pipeline