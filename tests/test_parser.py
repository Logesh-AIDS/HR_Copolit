# tests/test_parser.py
import pytest
import uuid
import tempfile
from pathlib import Path

from services.common.exceptions import ValidationException, UnauthorizedException, NotFoundException
from services.common.storage import LocalStorageProvider
from app.adapter.db.document_repo import DocumentRepository
from app.adapter.db.parser_repo import ParserRepository
from app.adapter.parser.spacy_parser import ExtractorFactory, MockOcrProvider
from app.domain import parser_models
from app.domain.services.parser_service import ParserService


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def parser_service(db_session, temp_storage_dir):
    parser_repo = ParserRepository(db_session)
    doc_repo = DocumentRepository(db_session)
    storage = LocalStorageProvider(temp_storage_dir)
    return ParserService(parser_repo, doc_repo, storage)


def test_text_extraction_strategies(parser_service):
    # Test plain text extractor
    extractor = ExtractorFactory.get_extractor("txt")
    text = extractor.extract_text(b"Hello plain text resume contents.")
    assert "plain text" in text

    # Test docx2txt fallback error wrapper
    extractor = ExtractorFactory.get_extractor("docx")
    with pytest.raises(RuntimeError):
        # Invalid zip file format bytes will cause docx2txt to raise a zip error
        extractor.extract_text(b"invalid docx content bytes")


def test_ocr_mock_provider():
    ocr = MockOcrProvider()
    text = ocr.perform_ocr(b"fake image bytes")
    assert "JOHN DOE" in text
    assert "Stanford University" in text
    assert "Python3" in text


def test_text_cleaning_and_section_detection(parser_service):
    raw_text = (
        "  JOHN DOE \n\n"
        "Summary:\n"
        "Expert python programmer. \n\n"
        "Work Experience:\n"
        "Developer at Google (2020 - 2022)\n\n"
        "Education:\n"
        "B.S. at Harvard"
    )

    cleaned = parser_service._clean_text(raw_text)
    assert "  JOHN DOE" not in cleaned  # leading spaces trimmed
    assert "JOHN DOE" in cleaned

    sections = parser_service._detect_sections(cleaned)
    assert "Google" in sections["EXPERIENCE"]
    assert "Harvard" in sections["EDUCATION"]
    assert "Expert python" in sections["SUMMARY"]


def test_skill_normalization_and_categorization(parser_service):
    # Test normalization map
    assert parser_service._normalize_skill("python3") == "Python"
    assert parser_service._normalize_skill("js") == "JavaScript"
    assert parser_service._normalize_skill("k8s") == "Kubernetes"
    
    # Test entity extraction skills alignment
    text = "Proficient in Python3, JS, K8s, and TensorFlow."
    sections = {}
    entities = parser_service._extract_entities(text, sections)
    
    skills = {s["name"]: s["category"] for s in entities["skills"]}
    assert "Python" in skills
    assert skills["Python"] == "PROGRAMMING_LANGUAGE"
    assert "JavaScript" in skills
    assert skills["JavaScript"] == "PROGRAMMING_LANGUAGE"
    assert "Kubernetes" in skills
    assert skills["Kubernetes"] == "DEVOPS"
    assert "TensorFlow" in skills
    assert skills["TensorFlow"] == "MACHINE_LEARNING"


def test_parsing_pipeline_execution(parser_service, db_session):
    user_id = str(uuid.uuid4())
    doc_repo = parser_service.doc_repo

    # 1. Create document
    doc = doc_repo.create_document(user_id, "resume.txt", "RESUME")
    doc_repo.commit()

    # Write file content to mock storage path
    storage_key = f"documents/{user_id}/{doc.id}_v1.txt"
    parser_service.storage.upload_file(storage_key, b"JOHN DOE\nEmail: john@doe.com\nSkills: python3, k8s", "text/plain")

    # Add document version row
    doc_repo.add_document_version(
        document_id=str(doc.id),
        version=1,
        file_hash="dummy_hash_txt",
        file_size=20,
        mime_type="text/plain",
        original_name="resume.txt",
        storage_path=storage_key,
        created_by=user_id
    )
    doc_repo.commit()

    # 2. Start parsing (create placeholder)
    placeholder = parser_service.parser_repo.create_parsed_resume_placeholder(str(doc.id), user_id)
    parser_service.parser_repo.commit()
    assert placeholder.status == "PENDING"

    # 3. Process pipeline synchronously to assert updates
    parser_service.process_resume_pipeline(str(doc.id), user_id, str(placeholder.id))

    # 4. Assert DB state has completed
    db_pr = parser_service.parser_repo.get_parsed_resume_by_document(str(doc.id))
    assert db_pr is not None
    assert db_pr.status == "COMPLETED"
    assert db_pr.email == "john@doe.com"
    assert len(db_pr.skills) == 2
    
    # Assert skills are standardized
    skill_names = [s.name for s in db_pr.skills]
    assert "Python" in skill_names
    assert "Kubernetes" in skill_names

    # Check logs audit
    logs = parser_service.parser_repo.get_parsing_logs(str(doc.id))
    assert len(logs) > 0
    log_messages = [l.message for l in logs]
    assert any("Started parsing pipeline" in m for m in log_messages)
    assert any("Saved parsed entities" in m for m in log_messages)


def test_parsing_deletion_and_reprocess(parser_service, db_session):
    user_id = str(uuid.uuid4())
    doc_repo = parser_service.doc_repo

    # 1. Create document
    doc = doc_repo.create_document(user_id, "resume.txt", "RESUME")
    doc_repo.commit()

    # Write file content
    storage_key = f"documents/{user_id}/{doc.id}_v1.txt"
    parser_service.storage.upload_file(storage_key, b"JOHN DOE\nEmail: john@doe.com\nSkills: python3", "text/plain")

    # Add document version row
    doc_repo.add_document_version(
        document_id=str(doc.id),
        version=1,
        file_hash="dummy_hash_txt_2",
        file_size=20,
        mime_type="text/plain",
        original_name="resume.txt",
        storage_path=storage_key,
        created_by=user_id
    )
    doc_repo.commit()

    # 2. Reprocess
    db_pr = parser_service.parser_repo.create_parsed_resume_placeholder(str(doc.id), user_id)
    parser_service.parser_repo.commit()

    parser_service.process_resume_pipeline(str(doc.id), user_id, str(db_pr.id))

    # Verify log reprocessing event entry works
    parser_service.parser_repo.log_parsing_event(str(doc.id), "INFO", "Reprocessing triggered.")
    logs = parser_service.parser_repo.get_parsing_logs(str(doc.id))
    assert any("Reprocessing triggered." in l.message for l in logs)

    # 3. Delete parsed data
    deleted = parser_service.parser_repo.delete_parsed_data(str(doc.id))
    assert deleted is True

    # Assert database relations have been cleared
    cleared = parser_service.parser_repo.get_parsed_resume_by_document(str(doc.id))
    assert cleared is None
