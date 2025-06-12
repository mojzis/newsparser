from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.models.common import FileType, date_to_path, path_to_date


class TestDateToPath:
    def test_date_to_path_formatting(self):
        """Test date to path conversion with proper formatting."""
        test_date = date(2024, 1, 15)
        result = date_to_path(test_date)
        assert result == "2024/01/15"

    def test_date_to_path_padding(self):
        """Test that single digit months and days are padded."""
        test_date = date(2024, 3, 5)
        result = date_to_path(test_date)
        assert result == "2024/03/05"

    def test_date_to_path_year_2000(self):
        """Test dates from year 2000."""
        test_date = date(2000, 12, 31)
        result = date_to_path(test_date)
        assert result == "2000/12/31"

    @given(st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)))
    def test_date_to_path_property_based(self, test_date):
        """Property-based test for date to path conversion."""
        result = date_to_path(test_date)
        parts = result.split("/")

        assert len(parts) == 3
        assert parts[0] == f"{test_date.year:04d}"
        assert parts[1] == f"{test_date.month:02d}"
        assert parts[2] == f"{test_date.day:02d}"


class TestPathToDate:
    def test_path_to_date_valid(self):
        """Test converting valid path to date."""
        path = "2024/01/15"
        result = path_to_date(path)
        assert result == date(2024, 1, 15)

    def test_path_to_date_padded(self):
        """Test converting path with padded values."""
        path = "2024/03/05"
        result = path_to_date(path)
        assert result == date(2024, 3, 5)

    def test_path_to_date_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        invalid_paths = [
            "2024-01-15",  # Wrong separator
            "2024/1/15",  # Not padded
            "24/01/15",  # Short year
            "2024/13/01",  # Invalid month
            "2024/01/32",  # Invalid day
            "2024/01",  # Missing day
            "2024",  # Missing month and day
            "abc/01/15",  # Non-numeric year
            "2024/ab/15",  # Non-numeric month
            "2024/01/ab",  # Non-numeric day
            "",  # Empty string
        ]

        for path in invalid_paths:
            with pytest.raises(ValueError) as exc_info:
                path_to_date(path)
            assert "Invalid date path format" in str(exc_info.value)

    def test_path_to_date_roundtrip(self):
        """Test roundtrip conversion date -> path -> date."""
        original_date = date(2024, 6, 20)
        path = date_to_path(original_date)
        result_date = path_to_date(path)
        assert result_date == original_date

    @given(st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)))
    def test_path_to_date_roundtrip_property_based(self, test_date):
        """Property-based test for roundtrip conversion."""
        path = date_to_path(test_date)
        result = path_to_date(path)
        assert result == test_date


class TestFileType:
    def test_file_type_enum_values(self):
        """Test that FileType enum has expected values."""
        assert hasattr(FileType, "PARQUET")
        assert hasattr(FileType, "HTML")
        assert hasattr(FileType, "JSON")

    def test_file_type_enum_usage(self):
        """Test using FileType enum."""
        parquet_type = FileType.PARQUET
        html_type = FileType.HTML
        json_type = FileType.JSON

        assert parquet_type.name == "PARQUET"
        assert html_type.name == "HTML"
        assert json_type.name == "JSON"

    def test_file_type_comparison(self):
        """Test FileType enum comparison."""
        assert FileType.PARQUET == FileType.PARQUET
        assert FileType.PARQUET != FileType.HTML
        assert FileType.HTML != FileType.JSON
