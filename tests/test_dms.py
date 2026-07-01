# tests/test_dms.py
import pytest
import uuid
import tempfile
from pathlib import Path
from services.common.exceptions import ValidationException, UnauthorizedException
from services.common.storage import LocalStorageProvider
from app.adapter.db.document_repo import DocumentRepository
from app.adapter.db import orm
from app.domain import document_models
from app.domain.services.document_service import DocumentService


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def document_service(db_session, temp_storage_dir):
    repo = DocumentRepository(db_session)
    storage = LocalStorageProvider(temp_storage_dir)
    return DocumentService(repo, storage)


def test_file_type_and_size_validation(document_service):
    user_id = str(uuid.uuid4())
    
    # 1. Valid PDF file upload
    doc = document_service.upload_document(
        user_id=user_id,
        filename="resume.pdf",
        file_data=b"%PDF-1.4 test data",
        document_type="RESUME",
        content_type="application/pdf",
        ip_address="127.0.0.1"
    )
    assert doc.name == "resume.pdf"
    assert doc.document_type == "RESUME"
    assert doc.current_version == 1

    # 2. Block unsupported file types (e.g. ZIP)
    with pytest.raises(ValidationException) as exc:
        document_service.upload_document(
            user_id=user_id,
            filename="malicious.zip",
            file_data=b"zip binary data",
            document_type="RESUME",
            content_type="application/zip",
            ip_address="127.0.0.1"
        )
    assert "Unsupported file extension" in str(exc.value)

    # 3. Block empty files
    with pytest.raises(ValidationException) as exc:
        document_service.upload_document(
            user_id=user_id,
            filename="empty.pdf",
            file_data=b"",
            document_type="RESUME",
            content_type="application/pdf",
            ip_address="127.0.0.1"
        )
    assert "empty" in str(exc.value).lower()


def test_duplicate_upload_prevention(document_service):
    user_id = str(uuid.uuid4())
    file_bytes = b"identical resume file content"

    # Upload first time
    document_service.upload_document(
        user_id=user_id,
        filename="my_resume.pdf",
        file_data=file_bytes,
        document_type="RESUME",
        content_type="application/pdf",
        ip_address="127.0.0.1"
    )

    # Attempt duplicate upload of identical file bytes (should trigger exception)
    with pytest.raises(ValidationException) as exc:
        document_service.upload_document(
            user_id=user_id,
            filename="copy_resume.pdf",
            file_data=file_bytes,
            document_type="RESUME",
            content_type="application/pdf",
            ip_address="127.0.0.1"
        )
    assert "Duplicate upload detected" in str(exc.value)


def test_document_versioning_and_replace(document_service):
    user_id = str(uuid.uuid4())
    roles = ["CANDIDATE"]

    # Initial Upload (Version 1)
    doc = document_service.upload_document(
        user_id=user_id,
        filename="cv.pdf",
        file_data=b"version 1 cv",
        document_type="RESUME",
        content_type="application/pdf",
        ip_address="127.0.0.1"
    )
    assert doc.current_version == 1

    # Replace Upload (Version 2)
    updated_doc = document_service.replace_document(
        document_id=str(doc.id),
        user_id=user_id,
        user_roles=roles,
        filename="cv_new.pdf",
        file_data=b"version 2 cv content",
        content_type="application/pdf",
        ip_address="127.0.0.1"
    )
    assert updated_doc.current_version == 2
    assert updated_doc.name == "cv_new.pdf"
    assert len(updated_doc.versions) == 2


def test_ownership_access_guards(document_service):
    owner_id = str(uuid.uuid4())
    stranger_id = str(uuid.uuid4())

    # Upload document by owner
    doc = document_service.upload_document(
        user_id=owner_id,
        filename="private_doc.pdf",
        file_data=b"highly sensitive information",
        document_type="RESUME",
        content_type="application/pdf",
        ip_address="127.0.0.1"
    )

    # 1. Owner downloads successfully
    content, name, mime = document_service.download_document(
        document_id=str(doc.id),
        user_id=owner_id,
        user_roles=["CANDIDATE"]
    )
    assert content == b"highly sensitive information"

    # 2. Stranger tries to download (Access Denied)
    with pytest.raises(UnauthorizedException) as exc:
        document_service.download_document(
            document_id=str(doc.id),
            user_id=stranger_id,
            user_roles=["CANDIDATE"]
        )
    assert "Access denied" in str(exc.value)

    # 3. Administrator bypasses and downloads successfully
    admin_content, _, _ = document_service.download_document(
        document_id=str(doc.id),
        user_id=stranger_id,
        user_roles=["ADMINISTRATOR"]
    )
    assert admin_content == b"highly sensitive information"


def test_soft_delete_and_restore(document_service):
    user_id = str(uuid.uuid4())
    roles = ["CANDIDATE"]

    doc = document_service.upload_document(
        user_id=user_id,
        filename="temp.pdf",
        file_data=b"temp file content",
        document_type="RESUME",
        content_type="application/pdf",
        ip_address="127.0.0.1"
    )

    # Soft Delete
    document_service.delete_document(str(doc.id), user_id, roles, permanent=False)
    
    # Try downloading (should fail as not found)
    with pytest.raises(NotFoundException):
        document_service.download_document(str(doc.id), user_id, roles)

    # Restore
    restored_doc = document_service.restore_document(str(doc.id), user_id, roles)
    assert restored_doc.deleted_at is None

    # Download after restore (Success)
    content, _, _ = document_service.download_document(str(doc.id), user_id, roles)
    assert content == b"temp file content"
