"""Base classes for stage-based processing."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional, Any
import logging

logger = logging.getLogger(__name__)


class Stage(ABC):
    """Base class for all processing stages."""
    
    def __init__(self, stage_name: str, base_path: Path = Path("stages")):
        self.stage_name = stage_name
        self.base_path = base_path
        self.stage_path = base_path / stage_name
    
    def get_stage_dir(self, target_date: date) -> Path:
        """Get the directory for a specific date in this stage."""
        date_str = target_date.strftime("%Y-%m-%d")
        return self.stage_path / date_str
    
    def ensure_stage_dir(self, target_date: date) -> Path:
        """Ensure stage directory exists and return path."""
        stage_dir = self.get_stage_dir(target_date)
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir
    
    @abstractmethod
    def get_inputs(self, target_date: date) -> Iterator[Path]:
        """Find input files to process for the given date."""
        pass
    
    @abstractmethod
    def process_item(self, input_path: Path, target_date: date) -> Optional[Path]:
        """
        Process a single item.
        
        Args:
            input_path: Path to input file
            target_date: Date being processed
            
        Returns:
            Path to output file if successful, None if skipped/failed
        """
        pass
    
    def should_process_item(self, input_path: Path, target_date: date) -> bool:
        """
        Check if an item should be processed (not already done).
        Override in subclasses for custom logic.
        """
        return True
    
    def run(self, target_date: Optional[date] = None) -> dict[str, Any]:
        """
        Run the stage for the specified date.
        
        Args:
            target_date: Date to process, defaults to today
            
        Returns:
            Summary of processing results
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Running {self.stage_name} stage for {target_date}")
        
        # Ensure output directory exists
        self.ensure_stage_dir(target_date)
        
        # Process all inputs
        processed = 0
        skipped = 0
        failed = 0
        
        for input_path in self.get_inputs(target_date):
            try:
                if not self.should_process_item(input_path, target_date):
                    skipped += 1
                    continue
                
                output_path = self.process_item(input_path, target_date)
                if output_path:
                    processed += 1
                    logger.debug(f"Processed {input_path.name} -> {output_path.name}")
                else:
                    skipped += 1
                    
            except Exception as e:
                failed += 1
                logger.error(f"Failed to process {input_path}: {e}")
        
        result = {
            "stage": self.stage_name,
            "date": target_date,
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "total": processed + skipped + failed
        }
        
        logger.info(f"Stage {self.stage_name} completed: {result}")
        return result


class InputStage(Stage):
    """Base class for stages that don't depend on previous stages."""
    
    def get_inputs(self, target_date: date) -> Iterator[Path]:
        """Input stages generate their own inputs."""
        # This will be overridden by specific input stages
        return iter([])


class ProcessingStage(Stage):
    """Base class for stages that process outputs from previous stages."""
    
    def __init__(self, stage_name: str, input_stage_name: str, base_path: Path = Path("stages")):
        super().__init__(stage_name, base_path)
        self.input_stage_name = input_stage_name
        self.input_stage_path = base_path / input_stage_name
    
    def get_inputs(self, target_date: date) -> Iterator[Path]:
        """Get all .md files from the input stage for the given date."""
        input_dir = self.input_stage_path / target_date.strftime("%Y-%m-%d")
        
        if not input_dir.exists():
            logger.warning(f"Input directory does not exist: {input_dir}")
            return iter([])
        
        # Find all .md files in the input directory
        return input_dir.glob("*.md")
    
    def get_output_path(self, input_path: Path, target_date: date) -> Path:
        """
        Generate output path for processed item.
        Default: keep same filename in this stage's directory.
        """
        stage_dir = self.ensure_stage_dir(target_date)
        return stage_dir / input_path.name
    
    def should_process_item(self, input_path: Path, target_date: date) -> bool:
        """Check if output file already exists."""
        output_path = self.get_output_path(input_path, target_date)
        return not output_path.exists()