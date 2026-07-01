# tests/test_intelligence.py
import pytest
import uuid
from app.adapter.db.parser_repo import ParserRepository
from app.adapter.db.intelligence_repo import IntelligenceRepository
from app.domain.services.intelligence_service import IntelligenceService


@pytest.fixture
def intel_service(db_session):
    intel_repo = IntelligenceRepository(db_session)
    parser_repo = ParserRepository(db_session)
    return IntelligenceService(intel_repo, parser_repo)


def test_experience_duration_calculation(intel_service):
    # Test 24 months duration calculation
    dur_24 = intel_service._calculate_role_duration("2022-04", "2024-04", fallback_months=12)
    assert dur_24 == 24

    # Test "Present" ongoing duration calculation (should result in active years calculation, default to fallback or current diff)
    dur_ongoing = intel_service._calculate_role_duration("2025-01", "Present", fallback_months=6)
    assert dur_ongoing > 0


def test_skill_confidence_estimation(intel_service, db_session):
    user_id = str(uuid.uuid4())
    
    # Create document wrapper
    from app.adapter.db.document_repo import DocumentRepository
    d_repo = DocumentRepository(db_session)
    doc = d_repo.create_document(user_id, "resume.txt", "RESUME")
    d_repo.commit()

    # Seed parsed resume
    placeholder = intel_service.parser_repo.create_parsed_resume_placeholder(str(doc.id), user_id)
    d_repo.commit()

    from app.domain import parser_models
    payload = parser_models.ParsedResumeJSON(
        document_id=str(doc.id),
        user_id=user_id,
        first_name="John",
        last_name="Doe",
        email="john@doe.com",
        skills=[
            parser_models.ExtractedSkill(name="Python", category="PROGRAMMING_LANGUAGE"),
            parser_models.ExtractedSkill(name="Kubernetes", category="DEVOPS")
        ],
        experience=[
            parser_models.ExperienceDetail(
                company="Tech Corp",
                job_title="Lead Software Engineer",
                start_date="2022-04",
                end_date="Present",
                description="Built cloud backend servers using Python and Kubernetes.",
                duration_months=24
            )
        ],
        education=[
            parser_models.EducationDetail(institution="MIT", degree="Master of Science", graduation_year=2021)
        ],
        projects=[
            parser_models.ProjectDetail(
                title="Microservices",
                description="Orchestrated APIs using python and docker",
                technologies=["Python", "Docker"]
            )
        ],
        certifications=[
            parser_models.CertificationDetail(name="Certified Kubernetes Administrator")
        ],
        languages=[],
        parsing_confidence=0.9,
        status="COMPLETED"
    )

    intel_service.parser_repo.save_parsed_details(str(placeholder.id), payload, "raw resume text")

    # Generate Candidate Intelligence
    db_intel = intel_service.generate_candidate_intelligence(str(doc.id), user_id)
    assert db_intel is not None
    assert db_intel.career_level == "SENIOR"  # Due to "Lead" role or duration
    assert db_intel.career_focus == "Backend Software Engineering"

    # Assert skill confidence metrics
    skills_conf = {s.name: s.confidence_score for s in db_intel.skill_confidence}
    assert "Python" in skills_conf
    assert "Kubernetes" in skills_conf
    
    # Kubernetes has CKA cert and experience -> higher confidence
    assert skills_conf["Kubernetes"] >= 0.50

    # Assert experience summaries
    assert db_intel.experience_summary.total_experience_months >= 24
    assert db_intel.experience_summary.leadership_experience_months >= 24

    # Assert feature store vectors
    assert db_intel.features.skills_count == 2
    assert db_intel.features.projects_count == 1
    assert db_intel.features.education_score == 0.85  # Master of Science
    assert db_intel.features.cloud_exposure is False
    assert db_intel.features.deployment_experience is True  # Kubernetes in skills

    # Assert strengths/weaknesses
    str_values = [sw.value for sw in db_intel.strengths_weaknesses]
    assert len(str_values) > 0


def test_taxonomy_seeding_and_graph_intersection(intel_service):
    nodes = intel_service.intel_repo.list_taxonomy()
    assert len(nodes) > 0
    
    concept_names = {node.concept_name for node in nodes}
    assert "PyTorch" in concept_names
    assert "Kubernetes" in concept_names
