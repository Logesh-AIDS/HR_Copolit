# services/candidate-service/app/adapter/db/document_repo.py
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from services.common.database import SQLAlchemyRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class DocumentRepository(SQLAlchemyRepository):
    """
    Handles database operations for documents, versions, and activity logs.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    # 1. Document Queries
    def get_document_by_id(self, document_id: str, include_deleted: bool = False) -> Optional[orm.DocumentORM]:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            return None
        query = self.db.query(orm.DocumentORM).filter(orm.DocumentORM.id == doc_uuid)
        if not include_deleted:
            query = query.filter(orm.DocumentORM.deleted_at == None)
        return query.first()

    def get_document_with_versions(self, document_id: str, include_deleted: bool = False) -> Optional[orm.DocumentORM]:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            return None
        query = self.db.query(orm.DocumentORM).filter(orm.DocumentORM.id == doc_uuid)
        if not include_deleted:
            query = query.filter(orm.DocumentORM.deleted_at == None)
        return query.first()

    def create_document(self, user_id: Optional[str], name: str, document_type: str) -> orm.DocumentORM:
        db_doc = orm.DocumentORM(
            user_id=uuid.UUID(user_id) if user_id else None,
            name=name,
            document_type=document_type.upper(),
            current_version=1,
            is_archived=False
        )
        return self.add(db_doc)

    def add_document_version(
        self,
        document_id: str,
        version: int,
        file_hash: str,
        file_size: int,
        mime_type: str,
        original_name: str,
        storage_path: str,
        created_by: Optional[str]
    ) -> orm.DocumentVersionORM:
        db_ver = orm.DocumentVersionORM(
            document_id=uuid.UUID(document_id),
            version=version,
            file_hash=file_hash,
            file_size=file_size,
            mime_type=mime_type,
            original_name=original_name,
            storage_path=storage_path,
            created_by=uuid.UUID(created_by) if created_by else None
        )
        return self.add(db_ver)

    # 2. Filtering and Pagination
    def list_documents(
        self,
        user_id: Optional[str] = None,
        document_type: Optional[str] = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> List[orm.DocumentORM]:
        query = self.db.query(orm.DocumentORM)
        if not include_deleted:
            query = query.filter(orm.DocumentORM.deleted_at == None)
        if user_id:
            query = query.filter(orm.DocumentORM.user_id == uuid.UUID(user_id))
        if document_type:
            query = query.filter(orm.DocumentORM.document_type == document_type.upper())
            
        return query.order_by(orm.DocumentORM.created_at.desc()).offset(skip).limit(limit).all()

    def count_documents(
        self,
        user_id: Optional[str] = None,
        document_type: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        query = self.db.query(orm.DocumentORM)
        if not include_deleted:
            query = query.filter(orm.DocumentORM.deleted_at == None)
        if user_id:
            query = query.filter(orm.DocumentORM.user_id == uuid.UUID(user_id))
        if document_type:
            query = query.filter(orm.DocumentORM.document_type == document_type.upper())
            
        return query.count()

    # 3. Duplicate Detection and Version Checks
    def get_duplicate_hash(self, user_id: str, file_hash: str) -> Optional[orm.DocumentVersionORM]:
        """
        Detects if a user has already uploaded a file with the exact same hash.
        """
        return self.db.query(orm.DocumentVersionORM).join(
            orm.DocumentORM, orm.DocumentVersionORM.document_id == orm.DocumentORM.id
        ).filter(
            orm.DocumentORM.user_id == uuid.UUID(user_id),
            orm.DocumentORM.deleted_at == None,
            orm.DocumentVersionORM.file_hash == file_hash
        ).first()

    def get_version_by_number(self, document_id: str, version_number: int) -> Optional[orm.DocumentVersionORM]:
        return self.db.query(orm.DocumentVersionORM).filter(
            orm.DocumentVersionORM.document_id == uuid.UUID(document_id),
            orm.DocumentVersionORM.version == version_number
        ).first()

    # 4. Mutations
    def soft_delete_document(self, document_id: str) -> None:
        db_doc = self.get_document_by_id(document_id)
        if db_doc:
            db_doc.deleted_at = datetime.now(timezone.utc)
            self.db.commit()

    def restore_document(self, document_id: str) -> None:
        db_doc = self.get_document_by_id(document_id, include_deleted=True)
        if db_doc:
            db_doc.deleted_at = None
            self.db.commit()

    def permanently_delete_document(self, document_id: str) -> None:
        db_doc = self.get_document_by_id(document_id, include_deleted=True)
        if db_doc:
            self.db.delete(db_doc)
            self.db.commit()

    # 5. Activity Audit Logs
    def log_document_activity(
        self,
        document_id: str,
        user_id: Optional[str],
        action: str,
        ip_address: Optional[str],
        details: dict
    ) -> orm.DocumentActivityLogORM:
        db_log = orm.DocumentActivityLogORM(
            document_id=uuid.UUID(document_id),
            user_id=uuid.UUID(user_id) if user_id else None,
            action=action.upper(),
            ip_address=ip_address,
            details=details
        )
        return self.add(db_log)

    def list_document_activity(self, document_id: str, limit: int = 50) -> List[orm.DocumentActivityLogORM]:
        return self.db.query(orm.DocumentActivityLogORM).filter(
            orm.DocumentActivityLogORM.document_id == uuid.UUID(document_id)
        ).order_by(orm.DocumentActivityLogORM.created_at.desc()).limit(limit).all()

    # 6. Global Stats
    def get_document_statistics(self, user_id: Optional[str] = None) -> Tuple[int, int, dict]:
        """
        Returns (total_documents, total_size_bytes, type_counts) for a user or system-wide.
        """
        # Count documents
        doc_query = self.db.query(orm.DocumentORM).filter(orm.DocumentORM.deleted_at == None)
        if user_id:
            doc_query = doc_query.filter(orm.DocumentORM.user_id == uuid.UUID(user_id))
        total_docs = doc_query.count()

        # Sum sizes of latest versions of active documents
        # For simplicity in this dev stage, sum all active versions
        ver_query = self.db.query(func.sum(orm.DocumentVersionORM.file_size)).join(
            orm.DocumentORM, orm.DocumentVersionORM.document_id == orm.DocumentORM.id
        ).filter(
            orm.DocumentORM.deleted_at == None
        )
        if user_id:
            ver_query = ver_query.filter(orm.DocumentORM.user_id == uuid.UUID(user_id))
        total_size = ver_query.scalar() or 0

        # Type counts
        count_query = self.db.query(
            orm.DocumentORM.document_type, func.count(orm.DocumentORM.id)
        ).filter(
            orm.DocumentORM.deleted_at == None
        )
        if user_id:
            count_query = count_query.filter(orm.DocumentORM.user_id == uuid.UUID(user_id))
        counts = count_query.group_by(orm.DocumentORM.document_type).all()
        type_counts = {c[0]: c[1] for c in counts}

        return total_docs, total_size, type_counts
