import tempfile
from pathlib import Path

import boto3
import pytest
from moto import mock_s3

from src.config.settings import Settings
from src.storage.r2_client import R2Client


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        r2_access_key_id="test_key",
        r2_secret_access_key="test_secret",
        r2_bucket_name="test-bucket",
        r2_endpoint_url="https://test.r2.cloudflarestorage.com",
    )


@pytest.fixture
def mock_r2_client(mock_settings):
    """Create R2Client with mock settings."""
    with mock_s3():
        # Create the bucket in the mock S3
        s3 = boto3.client(
            "s3",
            endpoint_url=mock_settings.r2_endpoint_url,
            aws_access_key_id=mock_settings.r2_access_key_id,
            aws_secret_access_key=mock_settings.r2_secret_access_key,
        )
        s3.create_bucket(Bucket=mock_settings.r2_bucket_name)

        client = R2Client(mock_settings)
        yield client


class TestR2ClientInit:
    def test_init_with_settings(self, mock_settings):
        """Test R2Client initialization."""
        with mock_s3():
            client = R2Client(mock_settings)
            assert client.bucket_name == "test-bucket"
            assert client.settings == mock_settings
            assert client.s3_client is not None


class TestR2ClientUploadFile:
    def test_upload_file_success(self, mock_r2_client):
        """Test successful file upload."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = mock_r2_client.upload_file(temp_path, "test/file.txt")
            assert result is True

            # Verify file exists
            assert mock_r2_client.file_exists("test/file.txt") is True

        finally:
            Path(temp_path).unlink()

    def test_upload_file_with_content_type(self, mock_r2_client):
        """Test file upload with content type."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = mock_r2_client.upload_file(
                temp_path, "test/file.txt", content_type="text/plain"
            )
            assert result is True

        finally:
            Path(temp_path).unlink()

    def test_upload_nonexistent_file(self, mock_r2_client):
        """Test uploading non-existent file."""
        result = mock_r2_client.upload_file("/nonexistent/file.txt", "test/file.txt")
        assert result is False


class TestR2ClientUploadBytes:
    def test_upload_bytes_success(self, mock_r2_client):
        """Test successful bytes upload."""
        test_data = b"test byte content"
        result = mock_r2_client.upload_bytes(test_data, "test/data.bin")
        assert result is True

        # Verify file exists
        assert mock_r2_client.file_exists("test/data.bin") is True

    def test_upload_bytes_with_content_type(self, mock_r2_client):
        """Test bytes upload with content type."""
        test_data = b"test data"
        result = mock_r2_client.upload_bytes(
            test_data, "test/data.bin", content_type="application/octet-stream"
        )
        assert result is True


class TestR2ClientDownloadFile:
    def test_download_file_success(self, mock_r2_client):
        """Test successful file download."""
        # First upload a file
        test_content = "test download content"
        mock_r2_client.upload_bytes(test_content.encode(), "test/download.txt")

        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = Path(temp_dir) / "downloaded.txt"
            result = mock_r2_client.download_file("test/download.txt", download_path)

            assert result is True
            assert download_path.exists()
            assert download_path.read_text() == test_content

    def test_download_nonexistent_file(self, mock_r2_client):
        """Test downloading non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = Path(temp_dir) / "not_found.txt"
            result = mock_r2_client.download_file("nonexistent.txt", download_path)
            assert result is False
            assert not download_path.exists()


class TestR2ClientDownloadBytes:
    def test_download_bytes_success(self, mock_r2_client):
        """Test successful bytes download."""
        test_data = b"test byte download"
        mock_r2_client.upload_bytes(test_data, "test/bytes.bin")

        downloaded_data = mock_r2_client.download_bytes("test/bytes.bin")
        assert downloaded_data == test_data

    def test_download_bytes_nonexistent(self, mock_r2_client):
        """Test downloading non-existent file as bytes."""
        result = mock_r2_client.download_bytes("nonexistent.bin")
        assert result is None


class TestR2ClientFileExists:
    def test_file_exists_true(self, mock_r2_client):
        """Test file_exists returns True for existing file."""
        mock_r2_client.upload_bytes(b"test", "exists.txt")
        assert mock_r2_client.file_exists("exists.txt") is True

    def test_file_exists_false(self, mock_r2_client):
        """Test file_exists returns False for non-existent file."""
        assert mock_r2_client.file_exists("does_not_exist.txt") is False


class TestR2ClientListFiles:
    def test_list_files_empty(self, mock_r2_client):
        """Test listing files in empty bucket."""
        files = mock_r2_client.list_files()
        assert files == []

    def test_list_files_with_content(self, mock_r2_client):
        """Test listing files with content."""
        # Upload some test files
        mock_r2_client.upload_bytes(b"test1", "file1.txt")
        mock_r2_client.upload_bytes(b"test2", "dir/file2.txt")
        mock_r2_client.upload_bytes(b"test3", "file3.txt")

        files = mock_r2_client.list_files()
        assert len(files) == 3
        assert "file1.txt" in files
        assert "dir/file2.txt" in files
        assert "file3.txt" in files

    def test_list_files_with_prefix(self, mock_r2_client):
        """Test listing files with prefix filter."""
        # Upload test files
        mock_r2_client.upload_bytes(b"test1", "data/2024/file1.parquet")
        mock_r2_client.upload_bytes(b"test2", "data/2024/file2.parquet")
        mock_r2_client.upload_bytes(b"test3", "reports/2024/report.html")

        data_files = mock_r2_client.list_files(prefix="data/")
        assert len(data_files) == 2
        assert all(f.startswith("data/") for f in data_files)

        report_files = mock_r2_client.list_files(prefix="reports/")
        assert len(report_files) == 1
        assert report_files[0].startswith("reports/")

    def test_list_files_max_keys(self, mock_r2_client):
        """Test listing files with max_keys limit."""
        # Upload multiple files
        for i in range(5):
            mock_r2_client.upload_bytes(b"test", f"file{i}.txt")

        files = mock_r2_client.list_files(max_keys=3)
        assert len(files) <= 3


class TestR2ClientDeleteFile:
    def test_delete_file_success(self, mock_r2_client):
        """Test successful file deletion."""
        # Upload a file first
        mock_r2_client.upload_bytes(b"test", "to_delete.txt")
        assert mock_r2_client.file_exists("to_delete.txt") is True

        # Delete the file
        result = mock_r2_client.delete_file("to_delete.txt")
        assert result is True
        assert mock_r2_client.file_exists("to_delete.txt") is False

    def test_delete_nonexistent_file(self, mock_r2_client):
        """Test deleting non-existent file."""
        result = mock_r2_client.delete_file("does_not_exist.txt")
        # moto doesn't raise error for deleting non-existent files
        assert result is True


@pytest.mark.integration
class TestR2ClientIntegration:
    """Integration tests that test multiple operations together."""

    def test_upload_download_roundtrip(self, mock_r2_client):
        """Test complete upload-download cycle."""
        original_content = "This is test content for roundtrip test"
        key = "roundtrip/test.txt"

        # Upload as bytes
        upload_result = mock_r2_client.upload_bytes(
            original_content.encode(), key, content_type="text/plain"
        )
        assert upload_result is True

        # Download as bytes
        downloaded_data = mock_r2_client.download_bytes(key)
        assert downloaded_data == original_content.encode()

        # Verify file exists
        assert mock_r2_client.file_exists(key) is True

        # Clean up
        delete_result = mock_r2_client.delete_file(key)
        assert delete_result is True
        assert mock_r2_client.file_exists(key) is False

    def test_multiple_file_operations(self, mock_r2_client):
        """Test operations with multiple files."""
        files_data = {
            "data/2024/01/posts.parquet": b"parquet data",
            "data/2024/01/evaluations.parquet": b"evaluation data",
            "reports/2024/01/report.html": b"<html>report</html>",
        }

        # Upload all files
        for key, data in files_data.items():
            result = mock_r2_client.upload_bytes(data, key)
            assert result is True

        # List files by prefix
        data_files = mock_r2_client.list_files(prefix="data/")
        assert len(data_files) == 2

        report_files = mock_r2_client.list_files(prefix="reports/")
        assert len(report_files) == 1

        # Verify all files exist
        for key in files_data:
            assert mock_r2_client.file_exists(key) is True

        # Download and verify content
        for key, expected_data in files_data.items():
            downloaded = mock_r2_client.download_bytes(key)
            assert downloaded == expected_data
