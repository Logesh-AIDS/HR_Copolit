import logging
import os
import boto3
from botocore.exceptions import ClientError
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

class StorageProvider(ABC):
    """
    Abstract interface for binary storage interactions (Local or Cloud S3).
    """
    @abstractmethod
    def upload_file(self, file_key: str, file_data: bytes, mime_type: str) -> bool:
        pass

    @abstractmethod
    def download_file(self, file_key: str) -> bytes:
        pass

    @abstractmethod
    def delete_file(self, file_key: str) -> bool:
        pass

    @abstractmethod
    def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        pass


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider for development environments.
    Guards operations from directory traversal attacks.
    """
    def __init__(self, base_dir: Union[str, Path]):
        self.base_dir = Path(base_dir).resolve()
        # Auto-create base storage folder if missing
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorageProvider initialized at path: {self.base_dir}")

    def _safe_path(self, file_key: str) -> Path:
        """
        Guards paths from path traversal attacks by resolving and validating base parent bounds.
        """
        target_path = Path(self.base_dir / file_key).resolve()
        if not str(target_path).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected! Forbidden file key: {file_key}")
        return target_path

    def upload_file(self, file_key: str, file_data: bytes, mime_type: str) -> bool:
        try:
            target_path = self._safe_path(file_key)
            # Create subdirectories if key contains folders
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(file_data)
            logger.info(f"File uploaded successfully to local storage key: {file_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to write file to local disk: {e}")
            return False

    def download_file(self, file_key: str) -> bytes:
        try:
            target_path = self._safe_path(file_key)
            if not target_path.exists():
                raise FileNotFoundError(f"Local storage key not found on disk: {file_key}")
            return target_path.read_bytes()
        except Exception as e:
            logger.error(f"Failed to read file from local disk: {e}")
            raise e

    def delete_file(self, file_key: str) -> bool:
        try:
            target_path = self._safe_path(file_key)
            if target_path.exists():
                target_path.unlink()
                logger.info(f"File deleted successfully from local storage key: {file_key}")
                return True
            logger.warning(f"Attempted to delete non-existent local file key: {file_key}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete local file from disk: {e}")
            return False

    def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        For local storage, returns the direct download path route on candidate-service.
        """
        # Emulates generating local routes
        return f"/api/v1/documents/download?key={file_key}"

class MinioStorageProvider(StorageProvider):
    """
    MinIO / S3 compatible cloud storage provider.
    """
    def __init__(self, endpoint_url: str, access_key: str, secret_key: str, default_bucket: str = "resumes"):
        self.endpoint_url = endpoint_url
        self.default_bucket = default_bucket
        # Force HTTP if localhost/minio without SSL
        if not endpoint_url.startswith("http"):
            self.endpoint_url = f"http://{endpoint_url}"
            
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1"
        )
        logger.info(f"MinioStorageProvider initialized at endpoint: {self.endpoint_url}")

    def upload_file(self, file_key: str, file_data: bytes, mime_type: str = "application/octet-stream") -> bool:
        try:
            self.client.put_object(
                Bucket=self.default_bucket,
                Key=file_key,
                Body=file_data,
                ContentType=mime_type
            )
            logger.info(f"File uploaded successfully to MinIO key: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to write file to MinIO: {e}")
            return False

    def download_file(self, file_key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.default_bucket, Key=file_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to read file from MinIO: {e}")
            raise FileNotFoundError(f"File not found in MinIO: {file_key}") from e

    def delete_file(self, file_key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.default_bucket, Key=file_key)
            logger.info(f"File deleted successfully from MinIO key: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from MinIO: {e}")
            return False

    def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.default_bucket, 'Key': file_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ""

def get_storage_provider() -> StorageProvider:
    from .config import settings
    if settings.ENV == "production" or hasattr(settings, "MINIO_ENDPOINT"):
        return MinioStorageProvider(
            endpoint_url=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY
        )
    return LocalStorageProvider(base_dir="/tmp/hr_copilot_storage")
