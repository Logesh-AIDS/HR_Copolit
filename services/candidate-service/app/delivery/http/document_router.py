# services/candidate-service/app/delivery/http/document_router.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, Query, Response, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.auth import get_current_user, UserIdentity
from services.common.responses import make_success_response, make_paginated_response
from app.adapter.db.document_repo import DocumentRepository
from app.domain import document_models
from app.domain.services.document_service import DocumentService, get_storage_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Document Management System"])

def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    repo = DocumentRepository(db)
    storage = get_storage_provider()
    return DocumentService(repo, storage)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str = Form(..., description="Document type, e.g. RESUME, COVER_LETTER, PORTFOLIO, JOB_DESCRIPTION"),
    file: UploadFile = File(...),
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Ingests and validates file uploads, saving binary payloads to storage and registering metadata inside DB.
    """
    file_bytes = await file.read()
    ip_address = None # Derived from request if available
    
    db_doc = service.upload_document(
        user_id=current_user.id,
        filename=file.filename,
        file_data=file_bytes,
        document_type=document_type,
        content_type=file.content_type,
        ip_address=ip_address
    )
    
    return make_success_response({
        "document_id": str(db_doc.id),
        "name": db_doc.name,
        "document_type": db_doc.document_type,
        "current_version": db_doc.current_version,
        "created_at": db_doc.created_at
    })


@router.get("/download/{document_id}")
def download_document(
    document_id: str,
    version: Optional[int] = Query(default=None, ge=1, description="Specify version number to retrieve"),
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Retrieves document binaries for the verified owner.
    """
    file_bytes, filename, mime_type = service.download_document(
        document_id=document_id,
        user_id=current_user.id,
        user_roles=current_user.roles,
        version_number=version
    )
    
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/preview/{document_id}")
def preview_document(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Renders documents inline (PDF/Images) directly inside client frames.
    """
    file_bytes, filename, mime_type = service.download_document(
        document_id=document_id,
        user_id=current_user.id,
        user_roles=current_user.roles
    )
    
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"inline; filename={filename}"
        }
    )


@router.post("/replace/{document_id}")
async def replace_document(
    document_id: str,
    file: UploadFile = File(...),
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Replaces document payload. Generates a new incremental version and updates pointers.
    """
    file_bytes = await file.read()
    ip_address = None
    
    db_doc = service.replace_document(
        document_id=document_id,
        user_id=current_user.id,
        user_roles=current_user.roles,
        filename=file.filename,
        file_data=file_bytes,
        content_type=file.content_type,
        ip_address=ip_address
    )
    
    return make_success_response({
        "document_id": str(db_doc.id),
        "name": db_doc.name,
        "new_version": db_doc.current_version,
        "updated_at": db_doc.updated_at
    })


@router.delete("/delete/{document_id}")
def delete_document(
    document_id: str,
    permanent: bool = Query(default=False),
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Deactivates (soft deletes) or purges (permanent delete) user documents.
    """
    service.delete_document(
        document_id=document_id,
        user_id=current_user.id,
        user_roles=current_user.roles,
        permanent=permanent
    )
    return make_success_response("Document deleted successfully.")


@router.post("/restore/{document_id}")
def restore_document(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Restores a soft-deleted document back to an active state.
    """
    db_doc = service.restore_document(
        document_id=document_id,
        user_id=current_user.id,
        user_roles=current_user.roles
    )
    return make_success_response({
        "document_id": str(db_doc.id),
        "status": "restored"
    })


@router.get("/")
def list_documents(
    filter_user_id: Optional[str] = Query(default=None, description="Admin only: filter by target user ID"),
    document_type: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Returns lists of active documents owned by the user. Administrators can filter across all users.
    """
    docs, total = service.list_documents(
        user_id=current_user.id,
        user_roles=current_user.roles,
        filter_user_id=filter_user_id,
        document_type=document_type,
        skip=skip,
        limit=limit
    )
    
    doc_list = [
        {
            "id": str(d.id),
            "user_id": str(d.user_id) if d.user_id else None,
            "name": d.name,
            "document_type": d.document_type,
            "current_version": d.current_version,
            "is_archived": d.is_archived,
            "created_at": d.created_at,
            "updated_at": d.updated_at
        } for d in docs
    ]
    
    return make_paginated_response(doc_list, total, skip, limit)


@router.get("/{document_id}/metadata")
def get_metadata(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Returns detailed properties and version logs for a document.
    """
    # Simply retrieves document details
    repo = service.repo
    db_doc = repo.get_document_with_versions(document_id)
    if not db_doc:
        from services.common.exceptions import NotFoundException
        raise NotFoundException("Document not found.")
        
    service._check_ownership(db_doc, current_user.id, current_user.roles)
    
    versions = [
        {
            "id": str(v.id),
            "version": v.version,
            "file_size": v.file_size,
            "mime_type": v.mime_type,
            "original_name": v.original_name,
            "created_at": v.created_at
        } for v in db_doc.versions
    ]
    
    return make_success_response({
        "id": str(db_doc.id),
        "user_id": str(db_doc.user_id) if db_doc.user_id else None,
        "name": db_doc.name,
        "document_type": db_doc.document_type,
        "current_version": db_doc.current_version,
        "is_archived": db_doc.is_archived,
        "created_at": db_doc.created_at,
        "updated_at": db_doc.updated_at,
        "versions": versions
    })


@router.get("/{document_id}/versions")
def get_version_history(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Lists the version history registry for a document.
    """
    versions = service.get_document_versions(
        document_id=document_id,
        user_id=current_user.id,
        user_roles=current_user.roles
    )
    
    version_list = [
        {
            "id": str(v.id),
            "version": v.version,
            "file_size": v.file_size,
            "mime_type": v.mime_type,
            "original_name": v.original_name,
            "created_at": v.created_at
        } for v in versions
    ]
    return make_success_response(version_list)


@router.get("/statistics", response_model=None)
def get_statistics(
    current_user: UserIdentity = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Returns aggregated document counts and storage size metrics.
    """
    stats = service.get_document_statistics(
        user_id=current_user.id,
        user_roles=current_user.roles
    )
    return make_success_response({
        "total_documents": stats.total_documents,
        "total_size_bytes": stats.total_size_bytes,
        "type_counts": stats.type_counts
    })
