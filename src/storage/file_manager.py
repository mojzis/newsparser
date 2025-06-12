from datetime import date, datetime
from pathlib import Path

from src.models.common import FileType, date_to_path


class FileManager:
    """Manages file paths and naming conventions for storage."""

    DATA_BASE_PATH = "data"
    REPORTS_BASE_PATH = "reports"

    @staticmethod
    def get_posts_path(date_obj: date | datetime) -> str:
        """
        Get the path for posts data file.

        Args:
            date_obj: Date for the posts

        Returns:
            Path string like "data/2024/01/15/posts.parquet"
        """
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()

        date_path = date_to_path(date_obj)
        return f"{FileManager.DATA_BASE_PATH}/{date_path}/posts.parquet"

    @staticmethod
    def get_evaluations_path(date_obj: date | datetime) -> str:
        """
        Get the path for article evaluations data file.

        Args:
            date_obj: Date for the evaluations

        Returns:
            Path string like "data/2024/01/15/evaluations.parquet"
        """
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()

        date_path = date_to_path(date_obj)
        return f"{FileManager.DATA_BASE_PATH}/{date_path}/evaluations.parquet"

    @staticmethod
    def get_report_path(date_obj: date | datetime) -> str:
        """
        Get the path for HTML report file.

        Args:
            date_obj: Date for the report

        Returns:
            Path string like "reports/2024/01/15/report.html"
        """
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()

        date_path = date_to_path(date_obj)
        return f"{FileManager.REPORTS_BASE_PATH}/{date_path}/report.html"

    @staticmethod
    def get_metadata_path(date_obj: date | datetime) -> str:
        """
        Get the path for daily metadata file.

        Args:
            date_obj: Date for the metadata

        Returns:
            Path string like "data/2024/01/15/metadata.json"
        """
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()

        date_path = date_to_path(date_obj)
        return f"{FileManager.DATA_BASE_PATH}/{date_path}/metadata.json"

    @staticmethod
    def list_dates_with_data(
        base_path: str = DATA_BASE_PATH, file_type: FileType = FileType.PARQUET
    ) -> list[date]:
        """
        List all dates that have data files.

        Args:
            base_path: Base path to search ("data" or "reports")
            file_type: Type of file to look for

        Returns:
            List of dates with data files
        """
        # This would typically use the R2 client to list files
        # For now, returns empty list as placeholder
        return []

    @staticmethod
    def validate_path(path: str) -> bool:
        """
        Validate that a path follows expected conventions.

        Args:
            path: Path to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check for directory traversal attempts
            if ".." in path or path.startswith("/"):
                return False

            # Check if path starts with valid base
            valid_bases = [FileManager.DATA_BASE_PATH, FileManager.REPORTS_BASE_PATH]
            if not any(path.startswith(base) for base in valid_bases):
                return False

            # Additional validation could be added here
            return True

        except Exception:
            return False

    @staticmethod
    def ensure_local_directory(file_path: str | Path) -> Path:
        """
        Ensure the parent directory exists for a local file path.

        Args:
            file_path: File path to check

        Returns:
            Path object for the file
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
