# tests/test_jd_intelligence.py
import pytest
import uuid
import tempfile
from pathlib import Path

from services.common.exceptions import NotFoundException, ValidationException
from services.common.storage import LocalStorageProvider
from app.adapter.db.document_repo import DocumentRepository
from app.adapter.db.jd_intelligence_repo import JobIntelligenceRepository
from app.domain.services.jd_intelligence_service import JobIntelligenceService
from app.adapter.db import orm


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def jd_service(db_session, temp_storage_dir):
    jd_repo = JobIntelligenceRepository(db_session)
    doc_repo = DocumentRepository(db_session)
    storage = LocalStorageProvider(temp_storage_dir)
    return JobIntelligenceService(jd_repo, doc_repo, storage)


def test_jd_section_detection(jd_service):
    text = (
        "Lead Software Engineer JD\n\n"
        "About the role:\n"
        "We are looking for a backend software developer.\n\n"
        "Requirements:\n"
        "5+ years of software development experience.\n"
        "Proficient in Python, Kubernetes, and PostgreSQL.\n\n"
        "Responsibilities:\n"
        "Build and scale secure APIs.\n"
        "Orchestrate Docker containers.\n\n"
        "What we offer:\n"
        "Competitive salary and remote work option."
    )

    cleaned = jd_service._clean_text(text)
    sections = jd_service._detect_sections(cleaned)
    assert "backend software developer" in sections["SUMMARY"]
    assert "Python, Kubernetes" in sections["REQUIREMENTS"]
    assert "Build and scale" in sections["RESPONSIBILITIES"]
    assert "Competitive salary" in sections["BENEFITS"]


def test_jd_entity_and_seniority_extraction(jd_service):
    text = (
        "Senior Developer JD\n"
        "Minimum 5 years of experience required.\n"
        "Degree in Computer Science."
    )
    sections = {}
    entities = jd_service._extract_entities(text, sections)
    assert entities["experience_years_required"] == 5
    assert entities["expected_seniority"] == "SENIOR"
    assert entities["interview_difficulty"] == "HARD"
    assert "Degree" in entities["education_requirements"]


def test_jd_intelligence_pipeline_execution(jd_service, db_session):
    user_id = str(uuid.uuid4())
    doc_repo = jd_service.doc_repo

    # 1. Create document
    doc = doc_repo.create_document(user_id, "jd.txt", "JOB_DESCRIPTION")
    doc_repo.commit()

    # Write file content to mock storage path
    storage_key = f"documents/{user_id}/{doc.id}_v1.txt"
    jd_text = (
        "Principal Machine Learning Engineer JD\n"
        "Requirements:\n"
        "5+ years of experience in ML.\n"
        "Skills: PyTorch, Go, Docker\n"
        "Responsibilities:\n"
        "Deploy models in production."
    )
    jd_service.storage.upload_file(storage_key, jd_text.encode("utf-8"), "text/plain")

    # Add document version row
    doc_repo.add_document_version(
        document_id=str(doc.id),
        version=1,
        file_hash="dummy_hash_jd",
        file_size=len(jd_text),
        mime_type="text/plain",
        original_name="jd.txt",
        storage_path=storage_key,
        created_by=user_id
    )
    doc_repo.commit()

    # 2. Run Pipeline
    db_intel = jd_service.generate_job_intelligence(str(doc.id), user_id)
    assert db_intel is not None
    assert db_intel.title == "Principal Machine Learning Engineer JD"
    assert db_intel.experience_years_required == 5
    assert db_intel.expected_seniority == "SENIOR"
    assert db_intel.interview_difficulty == "HARD"
    assert len(db_intel.skills) == 3
    
    # Assert skills are categorised correctly
    skills_cat = {s.name: s.category for s in db_intel.skills}
    assert "PyTorch" in skills_cat
    assert skills_cat["PyTorch"] == "MACHINE_LEARNING"
    assert "Go" in skills_cat
    assert skills_cat["Go"] == "PROGRAMMING_LANGUAGE"
    assert "Docker" in skills_cat
    assert skills_cat["Docker"] == "DEVOPS"

    # Assert features
    assert db_intel.features.required_skills_count == 3
    assert db_intel.features.required_experience == 5.0
    assert db_intel.features.ai_requirement is True  # PyTorch
    assert db_intel.features.cloud_requirement is False
    assert db_intel.features.leadership_requirement is False

    # Check logs audit
    logs = jd_service.jd_repo.db.query(orm.JobAuditLogORM).filter(
        orm.JobAuditLogORM.job_intelligence_id == db_intel.id
    ).all()
    assert len(logs) > 0
    assert any("generated" in l.message.lower() for l in logs)


def test_jd_intelligence_deletion(jd_service, db_session):
    user_id = str(uuid.uuid4())
    doc_repo = jd_service.doc_repo

    # 1. Create document
    doc = doc_repo.create_document(user_id, "jd_temp.txt", "JOB_DESCRIPTION")
    doc_repo.commit()

    # Write file content
    storage_key = f"documents/{user_id}/{doc.id}_v1.txt"
    jd_text = "Junior Dev JD\nRequirements:\n1 year experience in Python."
    jd_service.storage.upload_file(storage_key, jd_text.encode("utf-8"), "text/plain")

    # Add document version row
    doc_repo.add_document_version(
        document_id=str(doc.id),
        version=1,
        file_hash="dummy_hash_jd_temp",
        file_size=len(jd_text),
        mime_type="text/plain",
        original_name="jd_temp.txt",
        storage_path=storage_key,
        created_by=user_id
    )
    doc_repo.commit()

    # Generate
    db_intel = jd_service.generate_job_intelligence(str(doc.id), user_id)
    assert db_intel is not None

    # Delete
    deleted = jd_service.jd_repo.delete_job_intelligence(str(doc.id))
    assert deleted is True

    # Assert cleared
    cleared = jd_service.jd_repo.get_job_intelligence_by_document(str(doc.id))
    assert cleared is None
