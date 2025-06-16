# Analytics Infrastructure Implementation Plan

## Overview
Implemented a generic framework for converting markdown frontmatter to Pydantic models, then to Pandas DataFrames, and finally to Parquet files for streamlined analytics.

## Implementation Status: ✅ COMPLETE

### ✅ 1. Base Analytics Model (`src/models/analytics.py`)
Created `AnalyticsBase` class extending Pydantic's BaseModel with:
- `from_frontmatter(cls, frontmatter: dict)` - Load model from YAML frontmatter
- `to_pandas_dict()` - Convert to DataFrame-friendly format with flattened structures
- `df_from_stage_dir(cls, stage_name: str, days_back: int)` - Load data from stage directories
- `df_from_files(cls, file_paths: List[Path])` - Load from specific markdown files
- `to_parquet(cls, df: pd.DataFrame, output_path: Path)` - Export to Parquet with optimal settings

### ✅ 2. Updated Existing Models
- Made `BlueskyPost` and `ArticleEvaluation` inherit from `AnalyticsBase`
- Created new `FetchResult` model for fetch stage data
- Automatic type conversion for Pandas compatibility (HttpUrl → str, Enum → value, etc.)
- Flattened nested structures (e.g., `engagement.likes` → `engagement_likes`)

### ✅ 3. Parquet Export Module (`src/analytics/parquet_export.py`)
- Generic export function `export_stage_to_parquet()` for any stage
- Automatic model class selection based on stage name
- Error handling for malformed data

### ✅ 4. Stage Integration
Added `export_parquet: bool = True` parameter to all stage classes:
- `CollectStage` - exports after successful collection
- `FetchStage` - exports after fetching new URLs
- `EvaluateStage` - exports after new evaluations

Automatic export triggers at end of each stage's run method.

### ✅ 5. CLI Integration
Added `--export-parquet/--no-export-parquet` flag (default: True) to:
- `nsp collect`
- `nsp fetch`
- `nsp evaluate`
- `nsp run-all`
- `nsp stages collect`
- `nsp stages fetch`
- `nsp stages evaluate`
- `nsp stages run-all`

## Directory Structure
```
parquet/
├── collect/
│   ├── 2024-12-06.parquet
│   ├── 2024-12-07.parquet
│   └── ...
├── fetch/
│   ├── 2024-12-06.parquet
│   └── ...
└── evaluate/
    ├── 2024-12-06.parquet
    └── ...
```

## Type Mapping Strategy
Schema automatically derived from Pydantic models:
- `str` → `string[pyarrow]`
- `int` → `Int64` (nullable)
- `float` → `Float64` (nullable)
- `datetime` → `datetime64[ns, UTC]`
- `HttpUrl` → `string[pyarrow]`
- `list[str]` → `list<string>` (Parquet native list)
- `Enum` → `category`
- Nested Pydantic models → flattened with underscore separator

## Usage Examples

### Load Data for Analysis
```python
from src.models.post import BlueskyPost
from src.models.evaluation import ArticleEvaluation
from src.models.fetch import FetchResult

# Load last 7 days of collected posts
posts_df = BlueskyPost.df_from_stage_dir("collect", days_back=7)

# Load last 30 days of evaluations
evals_df = ArticleEvaluation.df_from_stage_dir("evaluate", days_back=30)

# Load fetch results
fetch_df = FetchResult.df_from_stage_dir("fetch", days_back=7)

# Or load directly from parquet
import pandas as pd
posts_df = pd.read_parquet("parquet/collect/2024-12-06.parquet")
```

### CLI Usage
```bash
# Collect with parquet export (default)
poetry run nsp collect --search mcp_tag --max-posts 50

# Collect without parquet export
poetry run nsp collect --search mcp_tag --max-posts 50 --no-export-parquet

# Run all stages with parquet export
poetry run nsp run-all --search mcp_tag --max-posts 50

# Run all stages without parquet export
poetry run nsp run-all --search mcp_tag --max-posts 50 --no-export-parquet
```

## Benefits Achieved
- ✅ Zero friction - happens automatically by default
- ✅ Schema derived from Pydantic models (single source of truth)
- ✅ Easy data exploration with standardized methods
- ✅ Efficient storage and querying with Parquet
- ✅ No separate analytics commands to remember
- ✅ Type-safe data loading with proper error handling
- ✅ Consistent analytics across all stages
- ✅ Support for schema evolution

## Technical Details

### Data Flattening
Nested structures are automatically flattened:
```python
# Original
{
  "engagement": {
    "likes": 10,
    "reposts": 5,
    "replies": 2
  }
}

# Flattened for Pandas
{
  "engagement_likes": 10,
  "engagement_reposts": 5,
  "engagement_replies": 2
}
```

### Automatic Type Optimization
- String columns with low cardinality (< 50% unique, < 100 total) become categories
- Datetime columns are timezone-aware (UTC)
- Nullable integer/float types preserve missing values
- Lists are stored as Parquet native list types

### Error Handling
- Malformed frontmatter files are logged but don't break the export
- Invalid date formats are handled gracefully
- Empty DataFrames are handled correctly

## Future Enhancements
- Partitioned Parquet files by date for better query performance
- Schema evolution tracking
- Data quality validation
- Integration with data visualization tools