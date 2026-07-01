# services/common/storage.py
import logging
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
