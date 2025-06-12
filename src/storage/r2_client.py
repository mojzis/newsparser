from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.config.settings import Settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class R2Client:
    """Cloudflare R2 storage client using S3-compatible API."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize R2 client with settings.

        Args:
            settings: Application settings containing R2 credentials
        """
        self.bucket_name = settings.r2_bucket_name
        self.settings = settings

        # Configure boto3 client with retries
        config = Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=config,
        )

        logger.info(f"R2Client initialized for bucket: {self.bucket_name}")

    def upload_file(
        self, file_path: str | Path, key: str, content_type: str | None = None
    ) -> bool:
        """
        Upload a file to R2.

        Args:
            file_path: Local file path to upload
            key: Object key in R2 (path within bucket)
            content_type: Optional MIME type

        Returns:
            True if successful, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                key,
                ExtraArgs=extra_args if extra_args else None,
            )
            logger.info(f"Successfully uploaded {file_path} to {key}")
            return True

        except (ClientError, BotoCoreError) as e:
            logger.exception(f"Failed to upload {file_path} to {key}: {e}")
            return False

    def upload_bytes(
        self, data: bytes, key: str, content_type: str | None = None
    ) -> bool:
        """
        Upload bytes data to R2.

        Args:
            data: Bytes data to upload
            key: Object key in R2
            content_type: Optional MIME type

        Returns:
            True if successful, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=key, Body=data, **extra_args
            )
            logger.info(f"Successfully uploaded bytes to {key}")
            return True

        except (ClientError, BotoCoreError) as e:
            logger.exception(f"Failed to upload bytes to {key}: {e}")
            return False

    def download_file(self, key: str, file_path: str | Path) -> bool:
        """
        Download a file from R2.

        Args:
            key: Object key in R2
            file_path: Local file path to save to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            self.s3_client.download_file(self.bucket_name, key, str(file_path))
            logger.info(f"Successfully downloaded {key} to {file_path}")
            return True

        except (ClientError, BotoCoreError) as e:
            logger.exception(f"Failed to download {key} to {file_path}: {e}")
            return False

    def download_bytes(self, key: str) -> bytes | None:
        """
        Download object as bytes from R2.

        Args:
            key: Object key in R2

        Returns:
            Bytes data if successful, None otherwise
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = response["Body"].read()
            logger.info(f"Successfully downloaded bytes from {key}")
            return data

        except (ClientError, BotoCoreError) as e:
            logger.exception(f"Failed to download bytes from {key}: {e}")
            return None

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in R2.

        Args:
            key: Object key to check

        Returns:
            True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.exception(f"Error checking if {key} exists: {e}")
            return False

    def list_files(self, prefix: str | None = None, max_keys: int = 1000) -> list[str]:
        """
        List files in R2 with optional prefix filter.

        Args:
            prefix: Optional prefix to filter results
            max_keys: Maximum number of keys to return

        Returns:
            List of object keys
        """
        try:
            params = {"Bucket": self.bucket_name, "MaxKeys": max_keys}
            if prefix:
                params["Prefix"] = prefix

            response = self.s3_client.list_objects_v2(**params)

            if "Contents" not in response:
                return []

            keys = [obj["Key"] for obj in response["Contents"]]
            logger.info(f"Listed {len(keys)} files with prefix '{prefix}'")
            return keys

        except (ClientError, BotoCoreError) as e:
            logger.exception(f"Failed to list files with prefix '{prefix}': {e}")
            return []

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from R2.

        Args:
            key: Object key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted {key}")
            return True

        except (ClientError, BotoCoreError) as e:
            logger.exception(f"Failed to delete {key}: {e}")
            return False
