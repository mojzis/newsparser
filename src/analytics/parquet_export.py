"""Utilities for exporting stage data to Parquet files."""

import logging
from datetime import date
from pathlib import Path
from typing import Type, TypeVar, Optional

from src.models.analytics import AnalyticsBase

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=AnalyticsBase)


async def export_stage_to_parquet(
    stage_name: str, 
    model_class: Type[T], 
    target_date: date,
    export_enabled: bool = True,
    days_back: int = 7,
    upload_to_r2: bool = True,
    settings: Optional['Settings'] = None
) -> None:
    """
    Export stage data to Parquet file containing the last N days of history.
    
    Args:
        stage_name: Name of the stage (collect, fetch, evaluate)
        model_class: Pydantic model class for the stage data
        target_date: Date when the export is run (used for output filename)
        export_enabled: Whether to actually perform the export
        days_back: Number of days of history to include (default: 7)
        upload_to_r2: Whether to upload the file to R2 storage (default: True)
        settings: Settings object for R2 credentials (optional, will load if not provided)
    """
    if not export_enabled:
        logger.debug(f"Parquet export disabled for {stage_name} stage")
        return
    
    try:
        # Load data from the last N days using the model's method
        logger.info(f"Loading {days_back} days of {stage_name} data for export")
        df = model_class.df_from_stage_dir(stage_name, days_back=days_back)
        
        if df.empty:
            logger.warning(f"No data found for {stage_name} stage in the last {days_back} days")
            return
        
        # Create output path based on run date
        output_dir = Path("parquet") / stage_name / "by-run-date"
        output_file = output_dir / f"{target_date.strftime('%Y-%m-%d')}_last_{days_back}_days.parquet"
        
        # Export to Parquet locally
        model_class.to_parquet(df, output_file)
        logger.info(f"Successfully exported {len(df)} records from last {days_back} days to {output_file}")
        
        # Upload to R2 if enabled
        if upload_to_r2:
            await upload_parquet_to_r2(output_file, stage_name, target_date, days_back, settings)
        
    except Exception as e:
        logger.error(f"Failed to export {stage_name} stage to Parquet: {e}")


async def upload_parquet_to_r2(
    local_file_path: Path,
    stage_name: str,
    target_date: date,
    days_back: int,
    settings: Optional['Settings'] = None
) -> None:
    """
    Upload a parquet file to R2 storage.
    
    Args:
        local_file_path: Path to the local parquet file
        stage_name: Name of the stage (collect, fetch, evaluate)
        target_date: Date when the export was run
        days_back: Number of days of history in the file
        settings: Settings object for R2 credentials (optional, will load if not provided)
    """
    try:
        # Import here to avoid circular imports
        from src.config.settings import get_settings
        from src.storage.r2_client import R2Client
        
        # Load settings if not provided
        if settings is None:
            settings = get_settings()
        
        # Check if R2 is configured
        if not settings.has_r2_credentials:
            logger.debug(f"R2 credentials not configured, skipping upload of {local_file_path}")
            return
        
        # Create R2 client
        r2_client = R2Client(settings)
        
        # Create R2 key with same structure as local path
        # parquet/{stage_name}/by-run-date/{date}_last_{days_back}_days.parquet
        r2_key = f"parquet/{stage_name}/by-run-date/{target_date.strftime('%Y-%m-%d')}_last_{days_back}_days.parquet"
        
        # Upload file
        success = r2_client.upload_file(
            file_path=local_file_path,
            key=r2_key,
            content_type="application/octet-stream"
        )
        
        if success:
            logger.info(f"Successfully uploaded {local_file_path} to R2 as {r2_key}")
        else:
            logger.error(f"Failed to upload {local_file_path} to R2")
            
    except Exception as e:
        logger.error(f"Error uploading parquet file to R2: {e}")
        # Don't raise the exception as we don't want to fail the entire export process
        # if R2 upload fails


def get_model_class_for_stage(stage_name: str) -> Type[AnalyticsBase]:
    """
    Get the appropriate model class for a stage.
    
    Args:
        stage_name: Name of the stage
        
    Returns:
        Model class for the stage
    """
    if stage_name == "collect":
        from src.models.post import BlueskyPost
        return BlueskyPost
    elif stage_name == "fetch":
        from src.models.fetch import FetchResult
        return FetchResult
    elif stage_name == "evaluate":
        from src.models.evaluation import ArticleEvaluation
        return ArticleEvaluation
    else:
        raise ValueError(f"Unknown stage: {stage_name}")