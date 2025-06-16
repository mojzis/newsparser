"""Utilities for exporting stage data to Parquet files."""

import logging
from datetime import date
from pathlib import Path
from typing import Type, TypeVar

from src.models.analytics import AnalyticsBase

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=AnalyticsBase)


async def export_stage_to_parquet(
    stage_name: str, 
    model_class: Type[T], 
    target_date: date,
    export_enabled: bool = True
) -> None:
    """
    Export stage data to Parquet file.
    
    Args:
        stage_name: Name of the stage (collect, fetch, evaluate)
        model_class: Pydantic model class for the stage data
        target_date: Date to export data for
        export_enabled: Whether to actually perform the export
    """
    if not export_enabled:
        logger.debug(f"Parquet export disabled for {stage_name} stage")
        return
    
    try:
        # Check if stage directory exists and has data
        stage_dir = Path("stages") / stage_name / target_date.strftime("%Y-%m-%d")
        if not stage_dir.exists():
            logger.debug(f"No data found for {stage_name} stage on {target_date}")
            return
        
        # Count markdown files
        md_files = list(stage_dir.glob("*.md"))
        if not md_files:
            logger.debug(f"No markdown files found in {stage_dir}")
            return
        
        logger.info(f"Exporting {len(md_files)} {stage_name} records to Parquet for {target_date}")
        
        # Load data directly from the target date's files
        df = model_class.df_from_files(md_files)
        
        if df.empty:
            logger.warning(f"No valid data found for {stage_name} stage on {target_date}")
            return
        
        # Create output path
        output_dir = Path("parquet") / stage_name
        output_file = output_dir / f"{target_date.strftime('%Y-%m-%d')}.parquet"
        
        # Export to Parquet
        model_class.to_parquet(df, output_file)
        
        logger.info(f"Successfully exported {len(df)} records to {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to export {stage_name} stage to Parquet: {e}")


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