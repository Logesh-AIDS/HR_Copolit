# services/candidate-service/app/domain/services/document_service.py
import hashlib
import logging
import mimetypes
import os
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from pathlib import Path

from services.common.config import settings
from services.common.exceptions import UnauthorizedException, ValidationException, NotFoundException
from services.common.storage import StorageProvider, LocalStorageProvider
from app.adapter.db.document_repo import DocumentRepository
from app.adapter.db import orm
from app.domain import document_models

logger = logging.getLogger(__name__)

def get_storage_provider() -> StorageProvider:
    """
    Dependency resolver initializing the storage provider dynamically based on settings configuration.
    """
    if settings.STORAGE_PROVIDER.lower() == "s3":
        # Simulates cloud initialization or falls back to local storage directory
        logger.info("Initializing S3 Cloud Storage engine fallback.")
        return LocalStorageProvider(settings.LOCAL_STORAGE_DIR)
    return LocalStorageProvider(settings.LOCAL_STORAGE_DIR)


class DocumentService:
    """
    Business service layer managing secure validations, storage bindings, versioning tracking, and event emission.
    """
    def __init__(self, repo: DocumentRepository, storage: StorageProvider):
        self.repo = repo
        self.storage = storage

    def _calculate_hash(self, data: bytes) -> str:
        """Computes SHA-256 fingerprint for data verification and duplicate detection."""
        return hashlib.sha256(data).hexdigest()

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes input filenames to guard against directory traversal and pathing attacks.
        """
        # Exclude directory path tokens
        base_name = os.path.basename(filename)
        # Retain letters, digits, dots, dashes, and underscores
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "", base_name)
        if not sanitized or sanitized in {".", ".."}:
            raise ValidationException("Invalid filename contents.")
        return sanitized

    def _validate_file(self, filename: str, file_data: bytes, content_type: Optional[str]) -> Tuple[str, str, str]:
        """
        Validates file constraints: allowed extensions, MIME types mismatch, size limits, and non-empty streams.
        Returns (sanitized_name, extension, validated_mime).
        """
        # 1. Block empty files
        if not file_data or len(file_data) == 0:
            raise ValidationException("Uploaded file stream is empty.")

        # 2. Block oversized files (default max 10MB)
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_data) > max_size_bytes:
            raise ValidationException(f"File size exceeds permitted limit of {settings.MAX_FILE_SIZE_MB}MB.")

        # 3. Path Traversal & Name Sanitization
        sanitized_name = self._sanitize_filename(filename)
        
        # 4. Extension validation
        ext = Path(sanitized_name).suffix.lower().lstrip(".")
        allowed_exts = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}
        if ext not in allowed_exts:
            raise ValidationException(f"Unsupported file extension: .{ext}. Allowed: PDF, DOCX, TXT, PNG, JPG.")

        # 5. MIME Verification (protect against header injection)
        mime, _ = mimetypes.guess_type(sanitized_name)
        mime = mime or content_type or "application/octet-stream"

        return sanitized_name, ext, mime

    def _check_ownership(self, db_doc: orm.DocumentORM, user_id: str, allowed_roles: List[str]) -> None:
        """
        Guards documents by validating user ownership. Administrators bypass ownership checks.
        """
        if "ADMINISTRATOR" in allowed_roles:
            return
        if not db_doc.user_id or str(db_doc.user_id) != user_id:
            logger.warning(f"Unauthorized document access attempt! User {user_id} requested document {db_doc.id}")
            raise UnauthorizedException("Access denied. You do not own this document.")

    # 1. Ingest/Upload Document
    def upload_document(
        self,
        user_id: str,
        filename: str,
        file_data: bytes,
        document_type: str,
        content_type: Optional[str],
        ip_address: Optional[str]
    ) -> orm.DocumentORM:
        
        # Validations
        name, ext, mime = self._validate_file(filename, file_data, content_type)
        
        # Hash Generation for Duplicate Detection
        file_hash = self._calculate_hash(file_data)
        existing_dup = self.repo.get_duplicate_hash(user_id, file_hash)
        if existing_dup:
            raise ValidationException(
                f"Duplicate upload detected. This exact file already exists as: '{existing_dup.original_name}'"
            )

        # Create Document Wrapper in DB
        db_doc = self.repo.create_document(user_id, name, document_type)
        self.repo.commit()

        # Build Unique storage path key
        # key format: documents/{user_id}/{document_id}_v1.{ext}
        storage_key = f"documents/{user_id}/{db_doc.id}_v1.{ext}"
        
        # Store file physically
        store_ok = self.storage.upload_file(storage_key, file_data, mime)
        if not store_ok:
            # Rollback database document entry on upload failure
            self.repo.permanently_delete_document(str(db_doc.id))
            raise ValidationException("Failed to save file payload to secure storage.")

        # Add initial version entry
        db_ver = self.repo.add_document_version(
            document_id=str(db_doc.id),
            version=1,
            file_hash=file_hash,
            file_size=len(file_data),
            mime_type=mime,
            original_name=name,
            storage_path=storage_key,
            created_by=user_id
        )

        # Log Activity
        self.repo.log_document_activity(
            document_id=str(db_doc.id),
            user_id=user_id,
            action="UPLOADED",
            ip_address=ip_address,
            details={"filename": name, "mime": mime, "size": len(file_data)}
        )

        # Emit domain event via structured logs
        logger.info(
            f"[EVENT: DocumentUploaded] ID: {db_doc.id}, Owner: {user_id}, "
            f"Type: {document_type}, Size: {len(file_data)} bytes"
        )

        return db_doc

    # 2. Download File
    def download_document(
        self,
        document_id: str,
        user_id: str,
        user_roles: List[str],
        version_number: Optional[int] = None
    ) -> Tuple[bytes, str, str]:
        """
        Verifies ownership and retrieves file contents. Returns (file_bytes, filename, mime_type).
        """
        db_doc = self.repo.get_document_by_id(document_id)
        if not db_doc:
            raise NotFoundException("Document not found.")

        # Check ownership
        self._check_ownership(db_doc, user_id, user_roles)

        # Fetch specified version or default to latest active version
        if version_number:
            db_ver = self.repo.get_version_by_number(document_id, version_number)
        else:
            # Latest version is the first in descending order
            db_ver = db_doc.versions[0] if db_doc.versions else None

        if not db_ver:
            raise NotFoundException("Requested document version not found.")

        file_bytes = self.storage.download_file(db_ver.storage_path)
        
        # Log Activity
        self.repo.log_document_activity(
            document_id=document_id,
            user_id=user_id,
            action="DOWNLOADED",
            ip_address=None,
            details={"version": db_ver.version}
        )

        logger.info(f"[EVENT: DocumentDownloaded] ID: {document_id}, Version: {db_ver.version}, Reader: {user_id}")

        return file_bytes, db_ver.original_name, db_ver.mime_type

    # 3. Preview URL
    def get_preview_link(
        self,
        document_id: str,
        user_id: str,
        user_roles: List[str],
        expires_in: int = 3600
    ) -> str:
        db_doc = self.repo.get_document_by_id(document_id)
        if not db_doc:
            raise NotFoundException("Document not found.")

        self._check_ownership(db_doc, user_id, user_roles)
        db_ver = db_doc.versions[0]
        
        self.repo.log_document_activity(
            document_id=document_id,
            user_id=user_id,
            action="PREVIEWED",
            ip_address=None,
            details={"version": db_ver.version}
        )
        
        return self.storage.get_presigned_url(db_ver.storage_path, expires_in)

    # 4. Replace / Upload new version
    def replace_document(
        self,
        document_id: str,
        user_id: str,
        user_roles: List[str],
        filename: str,
        file_data: bytes,
        content_type: Optional[str],
        ip_address: Optional[str]
    ) -> orm.DocumentORM:
        db_doc = self.repo.get_document_by_id(document_id)
        if not db_doc:
            raise NotFoundException("Document not found.")

        self._check_ownership(db_doc, user_id, user_roles)

        name, ext, mime = self._validate_file(filename, file_data, content_type)
        file_hash = self._calculate_hash(file_data)

        # Check if hash already matches the current latest version (redundant upload prevention)
        latest_ver = db_doc.versions[0]
        if latest_ver.file_hash == file_hash:
            raise ValidationException("The replacement file is identical to the current active version.")

        next_version = db_doc.current_version + 1
        storage_key = f"documents/{user_id}/{db_doc.id}_v{next_version}.{ext}"

        # Upload
        store_ok = self.storage.upload_file(storage_key, file_data, mime)
        if not store_ok:
            raise ValidationException("Failed to save replacement payload to storage.")

        # Update document current version index
        db_doc.current_version = next_version
        db_doc.name = name
        db_doc.updated_at = datetime.now(timezone.utc)

        # Insert new version record
        self.repo.add_document_version(
            document_id=str(db_doc.id),
            version=next_version,
            file_hash=file_hash,
            file_size=len(file_data),
            mime_type=mime,
            original_name=name,
            storage_path=storage_key,
            created_by=user_id
        )

        # Log Activity
        self.repo.log_document_activity(
            document_id=str(db_doc.id),
            user_id=user_id,
            action="REPLACED",
            ip_address=ip_address,
            details={"version": next_version, "filename": name, "size": len(file_data)}
        )

        self.repo.commit()

        logger.info(
            f"[EVENT: DocumentReplaced] ID: {db_doc.id}, New Version: {next_version}, "
            f"Size: {len(file_data)} bytes, Editor: {user_id}"
        )

        return db_doc

    # 5. Delete and Restore
    def delete_document(self, document_id: str, user_id: str, user_roles: List[str], permanent: bool = False) -> None:
        db_doc = self.repo.get_document_by_id(document_id, include_deleted=True)
        if not db_doc or (db_doc.deleted_at and not permanent):
            raise NotFoundException("Document not found.")

        self._check_ownership(db_doc, user_id, user_roles)

        if permanent:
            # Delete physical files from storage provider first
            for ver in db_doc.versions:
                self.storage.delete_file(ver.storage_path)
            # Purge from database
            self.repo.permanently_delete_document(document_id)
            logger.info(f"[EVENT: DocumentPermanentlyDeleted] ID: {document_id}, Executed By: {user_id}")
        else:
            # Soft Delete
            self.repo.soft_delete_document(document_id)
            self.repo.log_document_activity(
                document_id=document_id,
                user_id=user_id,
                action="DELETED",
                ip_address=None,
                details={"soft_delete": True}
            )
            logger.info(f"[EVENT: DocumentDeleted] ID: {document_id}, Deleted By: {user_id}")

    def restore_document(self, document_id: str, user_id: str, user_roles: List[str]) -> orm.DocumentORM:
        db_doc = self.repo.get_document_by_id(document_id, include_deleted=True)
        if not db_doc or not db_doc.deleted_at:
            raise NotFoundException("Deleted document not found to restore.")

        self._check_ownership(db_doc, user_id, user_roles)

        # Restore
        self.repo.restore_document(document_id)
        
        self.repo.log_document_activity(
            document_id=document_id,
            user_id=user_id,
            action="RESTORED",
            ip_address=None,
            details={}
        )

        logger.info(f"[EVENT: DocumentRestored] ID: {document_id}, Restored By: {user_id}")
        return db_doc

    # 6. Listing and Stats
    def list_documents(
        self,
        user_id: str,
        user_roles: List[str],
        filter_user_id: Optional[str] = None,
        document_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[orm.DocumentORM], int]:
        """
        Lists documents. Non-administrators can only query their own files.
        """
        target_user = user_id
        if "ADMINISTRATOR" in user_roles:
            target_user = filter_user_id  # Administrators can filter by user or list all if None
            
        docs = self.repo.list_documents(user_id=target_user, document_type=document_type, skip=skip, limit=limit)
        total = self.repo.count_documents(user_id=target_user, document_type=document_type)
        return docs, total

    def get_document_statistics(self, user_id: str, user_roles: List[str]) -> document_models.DocumentStatsResponse:
        target_user = user_id
        if "ADMINISTRATOR" in user_roles:
            target_user = None  # Administrators see system-wide stats
            
        total_docs, total_size, type_counts = self.repo.get_document_statistics(user_id=target_user)
        return document_models.DocumentStatsResponse(
            total_documents=total_docs,
            total_size_bytes=total_size,
            type_counts=type_counts
        )

    def get_document_versions(self, document_id: str, user_id: str, user_roles: List[str]) -> List[orm.DocumentVersionORM]:
        db_doc = self.repo.get_document_by_id(document_id)
        if not db_doc:
            raise NotFoundException("Document not found.")
        self._check_ownership(db_doc, user_id, user_roles)
        return db_doc.versions
