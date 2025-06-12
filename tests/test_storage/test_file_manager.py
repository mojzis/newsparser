import tempfile
from datetime import date, datetime
from pathlib import Path

from src.models.common import FileType
from src.storage.file_manager import FileManager


class TestFileManagerPaths:
    def test_get_posts_path(self):
        """Test posts file path generation."""
        test_date = date(2024, 1, 15)
        path = FileManager.get_posts_path(test_date)
        assert path == "data/2024/01/15/posts.parquet"

    def test_get_posts_path_with_datetime(self):
        """Test posts path with datetime input."""
        test_datetime = datetime(2024, 1, 15, 10, 30, 0)
        path = FileManager.get_posts_path(test_datetime)
        assert path == "data/2024/01/15/posts.parquet"

    def test_get_evaluations_path(self):
        """Test evaluations file path generation."""
        test_date = date(2024, 3, 5)
        path = FileManager.get_evaluations_path(test_date)
        assert path == "data/2024/03/05/evaluations.parquet"

    def test_get_evaluations_path_with_datetime(self):
        """Test evaluations path with datetime input."""
        test_datetime = datetime(2024, 12, 31, 23, 59, 59)
        path = FileManager.get_evaluations_path(test_datetime)
        assert path == "data/2024/12/31/evaluations.parquet"

    def test_get_report_path(self):
        """Test HTML report path generation."""
        test_date = date(2024, 6, 20)
        path = FileManager.get_report_path(test_date)
        assert path == "reports/2024/06/20/report.html"

    def test_get_report_path_with_datetime(self):
        """Test report path with datetime input."""
        test_datetime = datetime(2024, 6, 20, 15, 45, 30)
        path = FileManager.get_report_path(test_datetime)
        assert path == "reports/2024/06/20/report.html"

    def test_get_metadata_path(self):
        """Test metadata file path generation."""
        test_date = date(2024, 9, 10)
        path = FileManager.get_metadata_path(test_date)
        assert path == "data/2024/09/10/metadata.json"

    def test_get_metadata_path_with_datetime(self):
        """Test metadata path with datetime input."""
        test_datetime = datetime(2024, 9, 10, 8, 0, 0)
        path = FileManager.get_metadata_path(test_datetime)
        assert path == "data/2024/09/10/metadata.json"


class TestFileManagerValidation:
    def test_validate_path_valid_data_paths(self):
        """Test validation of valid data paths."""
        valid_paths = [
            "data/2024/01/15/posts.parquet",
            "data/2024/12/31/evaluations.parquet",
            "data/2024/06/20/metadata.json",
        ]

        for path in valid_paths:
            assert FileManager.validate_path(path) is True

    def test_validate_path_valid_report_paths(self):
        """Test validation of valid report paths."""
        valid_paths = [
            "reports/2024/01/15/report.html",
            "reports/2024/12/31/summary.html",
        ]

        for path in valid_paths:
            assert FileManager.validate_path(path) is True

    def test_validate_path_directory_traversal(self):
        """Test rejection of directory traversal attempts."""
        invalid_paths = [
            "../data/posts.parquet",
            "data/../reports/report.html",
            "data/2024/../../../etc/passwd",
            "data/2024/01/15/../../posts.parquet",
        ]

        for path in invalid_paths:
            assert FileManager.validate_path(path) is False

    def test_validate_path_absolute_paths(self):
        """Test rejection of absolute paths."""
        invalid_paths = [
            "/data/posts.parquet",
            "/home/user/data/posts.parquet",
            "/etc/passwd",
        ]

        for path in invalid_paths:
            assert FileManager.validate_path(path) is False

    def test_validate_path_invalid_base(self):
        """Test rejection of paths with invalid base directories."""
        invalid_paths = [
            "invalid/2024/01/15/posts.parquet",
            "tmp/posts.parquet",
            "etc/config.json",
            "home/user/file.txt",
        ]

        for path in invalid_paths:
            assert FileManager.validate_path(path) is False

    def test_validate_path_edge_cases(self):
        """Test edge cases for path validation."""
        edge_cases = [
            "",  # Empty string
            "data",  # Just base directory
            "data/",  # Base with trailing slash
        ]

        # These should be valid as they start with valid base
        for path in edge_cases[1:]:
            assert FileManager.validate_path(path) is True

        # Empty string should be invalid
        assert FileManager.validate_path(edge_cases[0]) is False


class TestFileManagerLocalDirectory:
    def test_ensure_local_directory_creates_parent(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nested" / "deep" / "file.txt"

            result = FileManager.ensure_local_directory(file_path)

            assert result == file_path
            assert file_path.parent.exists()
            assert file_path.parent.is_dir()

    def test_ensure_local_directory_existing_parent(self):
        """Test with existing parent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir) / "existing"
            existing_dir.mkdir()

            file_path = existing_dir / "file.txt"
            result = FileManager.ensure_local_directory(file_path)

            assert result == file_path
            assert file_path.parent.exists()

    def test_ensure_local_directory_string_path(self):
        """Test with string path input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path_str = str(Path(temp_dir) / "new_dir" / "file.txt")

            result = FileManager.ensure_local_directory(file_path_str)

            assert isinstance(result, Path)
            assert result.parent.exists()
            assert str(result) == file_path_str


class TestFileManagerConstants:
    def test_base_path_constants(self):
        """Test base path constants."""
        assert FileManager.DATA_BASE_PATH == "data"
        assert FileManager.REPORTS_BASE_PATH == "reports"


class TestFileManagerListDates:
    def test_list_dates_with_data_placeholder(self):
        """Test list_dates_with_data returns empty list (placeholder)."""
        # This is a placeholder test for the unimplemented method
        result = FileManager.list_dates_with_data()
        assert result == []

        result_with_params = FileManager.list_dates_with_data(
            base_path="reports", file_type=FileType.HTML
        )
        assert result_with_params == []


class TestFileManagerIntegration:
    def test_path_generation_consistency(self):
        """Test that all path generation methods are consistent."""
        test_date = date(2024, 7, 4)

        posts_path = FileManager.get_posts_path(test_date)
        evaluations_path = FileManager.get_evaluations_path(test_date)
        metadata_path = FileManager.get_metadata_path(test_date)
        report_path = FileManager.get_report_path(test_date)

        # All data paths should have same date part
        expected_date_part = "2024/07/04"
        assert expected_date_part in posts_path
        assert expected_date_part in evaluations_path
        assert expected_date_part in metadata_path
        assert expected_date_part in report_path

        # Validate all generated paths
        assert FileManager.validate_path(posts_path) is True
        assert FileManager.validate_path(evaluations_path) is True
        assert FileManager.validate_path(metadata_path) is True
        assert FileManager.validate_path(report_path) is True

    def test_datetime_date_equivalence(self):
        """Test that datetime and date inputs produce same paths."""
        test_date = date(2024, 8, 15)
        test_datetime = datetime(2024, 8, 15, 14, 30, 45)

        # Posts paths should be identical
        posts_from_date = FileManager.get_posts_path(test_date)
        posts_from_datetime = FileManager.get_posts_path(test_datetime)
        assert posts_from_date == posts_from_datetime

        # Evaluations paths should be identical
        eval_from_date = FileManager.get_evaluations_path(test_date)
        eval_from_datetime = FileManager.get_evaluations_path(test_datetime)
        assert eval_from_date == eval_from_datetime

        # Report paths should be identical
        report_from_date = FileManager.get_report_path(test_date)
        report_from_datetime = FileManager.get_report_path(test_datetime)
        assert report_from_date == report_from_datetime

        # Metadata paths should be identical
        meta_from_date = FileManager.get_metadata_path(test_date)
        meta_from_datetime = FileManager.get_metadata_path(test_datetime)
        assert meta_from_date == meta_from_datetime
