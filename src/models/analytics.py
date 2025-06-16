"""Base model for analytics-enabled Pydantic models."""

import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar, get_args, get_origin
from datetime import date, datetime, timedelta
from enum import Enum

from pydantic import BaseModel, HttpUrl
from pydantic.fields import FieldInfo

from src.stages.markdown import MarkdownFile

T = TypeVar('T', bound='AnalyticsBase')


class AnalyticsBase(BaseModel):
    """Base class for Pydantic models that can be converted to DataFrames."""
    
    @classmethod
    def from_frontmatter(cls: Type[T], frontmatter: Dict[str, Any]) -> T:
        """Create model instance from markdown frontmatter."""
        return cls.model_validate(frontmatter)
    
    def to_pandas_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary suitable for pandas DataFrame.
        Flattens nested structures and converts types.
        """
        result = {}
        
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            
            if value is None:
                result[field_name] = None
                continue
            
            # Handle nested Pydantic models
            if isinstance(value, BaseModel):
                # Flatten nested model with prefix
                nested_dict = value.model_dump()
                for nested_key, nested_value in nested_dict.items():
                    result[f"{field_name}_{nested_key}"] = self._convert_value(nested_value)
            else:
                result[field_name] = self._convert_value(value)
        
        return result
    
    def _convert_value(self, value: Any) -> Any:
        """Convert values to pandas-friendly types."""
        if isinstance(value, HttpUrl):
            return str(value)
        elif isinstance(value, Enum):
            return value.value
        elif isinstance(value, datetime):
            return pd.to_datetime(value, utc=True)
        elif isinstance(value, date):
            return pd.to_datetime(value)
        elif isinstance(value, list):
            # Keep lists as lists for Parquet's native list support
            return [self._convert_value(v) for v in value]
        elif isinstance(value, dict):
            # Convert dict to string for simple storage
            return str(value)
        else:
            return value
    
    @classmethod
    def df_from_stage_dir(cls: Type[T], stage_name: str, days_back: int = 1) -> pd.DataFrame:
        """
        Load data from stage directories for the last N days.
        
        Args:
            stage_name: Name of the stage (collect, fetch, evaluate)
            days_back: Number of days to look back (default: 1)
        
        Returns:
            DataFrame with all records from the specified days
        """
        base_path = Path("stages") / stage_name
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back - 1)
        
        all_files = []
        current_date = start_date
        
        while current_date <= end_date:
            date_dir = base_path / current_date.strftime("%Y-%m-%d")
            if date_dir.exists():
                # Collect all markdown files
                files = list(date_dir.glob("*.md"))
                all_files.extend(files)
            current_date += timedelta(days=1)
        
        if not all_files:
            # Return empty DataFrame with expected columns
            return pd.DataFrame()
        
        return cls.df_from_files(all_files)
    
    @classmethod
    def df_from_files(cls: Type[T], file_paths: List[Path]) -> pd.DataFrame:
        """
        Load data from specific markdown files.
        
        Args:
            file_paths: List of paths to markdown files
        
        Returns:
            DataFrame with all records
        """
        records = []
        
        for file_path in file_paths:
            try:
                md_file = MarkdownFile.load(file_path)
                model = cls.from_frontmatter(md_file.frontmatter)
                record = model.to_pandas_dict()
                # Add file metadata
                record['_file_path'] = str(file_path)
                record['_file_name'] = file_path.name
                records.append(record)
            except Exception as e:
                # Log error but continue processing other files
                print(f"Error processing {file_path}: {e}")
                continue
        
        if not records:
            return pd.DataFrame()
        
        # Create DataFrame and optimize dtypes
        df = pd.DataFrame(records)
        df = cls._optimize_dtypes(df)
        
        return df
    
    @classmethod
    def _optimize_dtypes(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame dtypes based on Pydantic model."""
        if df.empty:
            return df
        
        # Convert string columns to category if they have low cardinality
        for col in df.select_dtypes(include=['object']).columns:
            if col.startswith('_'):  # Skip metadata columns
                continue
            num_unique = df[col].nunique()
            num_total = len(df[col])
            if num_unique / num_total < 0.5 and num_unique < 100:
                df[col] = df[col].astype('category')
        
        # Ensure datetime columns are timezone-aware
        for col in df.select_dtypes(include=['datetime64']).columns:
            if df[col].dt.tz is None:
                df[col] = df[col].dt.tz_localize('UTC')
        
        return df
    
    @classmethod
    def to_parquet(cls, df: pd.DataFrame, output_path: Path) -> None:
        """
        Save DataFrame to Parquet file.
        
        Args:
            df: DataFrame to save
            output_path: Path for output Parquet file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with compression and good defaults
        df.to_parquet(
            output_path,
            engine='pyarrow',
            compression='snappy',
            index=False,
            use_deprecated_int96_timestamps=False,
            coerce_timestamps='us'  # Microsecond precision for timestamps
        )
    
    @classmethod
    def get_pandas_dtypes(cls) -> Dict[str, str]:
        """
        Get recommended pandas dtypes for model fields.
        Returns mapping of field names to pandas dtype strings.
        """
        dtypes = {}
        
        for field_name, field_info in cls.model_fields.items():
            field_type = field_info.annotation
            
            # Handle Optional types
            if get_origin(field_type) is type(None):
                continue
            
            # Extract inner type from Optional
            if hasattr(field_type, '__args__'):
                args = get_args(field_type)
                if len(args) > 0 and args[0] is not type(None):
                    field_type = args[0]
            
            # Map types to pandas dtypes
            if field_type is str:
                dtypes[field_name] = 'string'
            elif field_type is int:
                dtypes[field_name] = 'Int64'  # Nullable integer
            elif field_type is float:
                dtypes[field_name] = 'Float64'  # Nullable float
            elif field_type is bool:
                dtypes[field_name] = 'boolean'  # Nullable boolean
            elif field_type is datetime:
                dtypes[field_name] = 'datetime64[ns, UTC]'
            elif field_type is date:
                dtypes[field_name] = 'datetime64[ns]'
            elif hasattr(field_type, '__bases__') and issubclass(field_type, Enum):
                dtypes[field_name] = 'category'
        
        return dtypes