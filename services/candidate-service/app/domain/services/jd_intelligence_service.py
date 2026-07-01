# services/candidate-service/app/domain/services/jd_intelligence_service.py
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from services.common.exceptions import NotFoundException, ValidationException
from services.common.storage import StorageProvider
from app.adapter.db.document_repo import DocumentRepository
from app.adapter.db.jd_intelligence_repo import JobIntelligenceRepository
from app.adapter.parser.spacy_parser import ExtractorFactory
from app.domain.services.parser_service import SKILL_TAXONOMY, SKILL_NORMALIZATION_MAP
from app.adapter.db import orm
from app.domain import jd_intelligence_models

logger = logging.getLogger(__name__)

class JobIntelligenceService:
    """
    Business service layer managing calculations for Job Description Intelligence profiles.
    """
    def __init__(self, jd_repo: JobIntelligenceRepository, doc_repo: DocumentRepository, storage: StorageProvider):
        self.jd_repo = jd_repo
        self.doc_repo = doc_repo
        self.storage = storage

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\r", "\n").replace("\t", " ")
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219\u25CB]', '-', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()

    def _detect_sections(self, text: str) -> Dict[str, str]:
        """
        Segments JD text into logical sections based on keyword indicators.
        """
        sections = {
            "SUMMARY": "",
            "REQUIREMENTS": "",
            "RESPONSIBILITIES": "",
            "BENEFITS": ""
        }
        
        triggers = {
            r'\b(summary|overview|about\s+the\s+role|about\s+us)\b': "SUMMARY",
            r'\b(requirements|qualifications|what\s+you\s+need|skills\s+required|requirements|experience)\b': "REQUIREMENTS",
            r'\b(responsibilities|what\s+you\s+will\s+do|duties|role|tasks)\b': "RESPONSIBILITIES",
            r'\b(benefits|what\s+we\s+offer|compensation|perks)\b': "BENEFITS"
        }

        lines = text.split("\n")
        current_section = "SUMMARY"
        section_lines = {sec: [] for sec in sections.keys()}

        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                continue

            matched_sec = None
            if len(line_strip) < 40:
                for regex, sec_name in triggers.items():
                    if re.search(regex, line_strip.lower()):
                        matched_sec = sec_name
                        break

            if matched_sec:
                current_section = matched_sec
            else:
                section_lines[current_section].append(line_strip)

        for sec, lines_list in section_lines.items():
            sections[sec] = "\n".join(lines_list)

        return sections

    def _extract_entities(self, text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Applies Regex and heuristic parsing rules to extract job entities.
        """
        entities = {
            "title": "Software Engineer",
            "company": "Tech Corp",
            "location": "Remote",
            "employment_type": "Full-Time",
            "experience_years_required": 3,
            "expected_seniority": "MID",
            "interview_difficulty": "MEDIUM",
            "education_requirements": "Bachelor of Science",
            "skills": [],
            "responsibilities": [],
            "metadata_items": []
        }

        # 1. Parse required experience years (e.g. 5+ years, 3 years, 2-5 years)
        exp_match = re.search(r'\b(\d+)\s*\+?\s*(years?|yrs?)\b\s*(of\s+)?experience', text, re.IGNORECASE)
        if exp_match:
            entities["experience_years_required"] = int(exp_match.group(1))
        else:
            # Fallback range check
            range_match = re.search(r'\b(\d+)\s*-\s*(\d+)\s*(years?|yrs?)\b', text, re.IGNORECASE)
            if range_match:
                entities["experience_years_required"] = int(range_match.group(1))

        # Determine Seniority and Interview Difficulty
        years = entities["experience_years_required"]
        if years >= 5:
            entities["expected_seniority"] = "SENIOR"
            entities["interview_difficulty"] = "HARD"
        elif years >= 2:
            entities["expected_seniority"] = "MID"
            entities["interview_difficulty"] = "MEDIUM"
        else:
            entities["expected_seniority"] = "JUNIOR"
            entities["interview_difficulty"] = "EASY"

        # 2. Extract Job Title (Heuristic: first non-empty line of text)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines:
            entities["title"] = lines[0][:100]

        # 3. Extract Education requirements
        edu_match = re.search(r'\b(bachelor|master|phd|ph\.d|degree|b\.s|bs|ms|m\.s)\b', text, re.IGNORECASE)
        if edu_match:
            entities["education_requirements"] = f"Degree in {edu_match.group(1).capitalize() or 'Computer Science'}"

        # 4. Extract Skills (Mapping to global Stage 6 taxonomy)
        text_lower = text.lower()
        skills_set = set()
        for skill_key, category in SKILL_TAXONOMY.items():
            pattern = r'\b' + re.escape(skill_key.lower()) + r'\b'
            if re.search(pattern, text_lower):
                skills_set.add((skill_key, category))

        # Check normalization keys
        for norm_key in SKILL_NORMALIZATION_MAP.keys():
            pattern = r'\b' + re.escape(norm_key) + r'\b'
            if re.search(pattern, text_lower):
                normalized = SKILL_NORMALIZATION_MAP[norm_key]
                category = SKILL_TAXONOMY.get(normalized, "OTHER")
                skills_set.add((normalized, category))

        # Flag skill requirements as mandatory if found in the Requirements section
        req_lower = sections.get("REQUIREMENTS", "").lower()
        for sk in skills_set:
            is_mandatory = True
            # If skill is only mentioned in summary/perks but not requirements, flag optional
            if sk[0].lower() not in req_lower and len(req_lower) > 0:
                is_mandatory = False
            entities["skills"].append({
                "name": sk[0],
                "category": sk[1],
                "is_mandatory": is_mandatory
            })

        # 5. Extract Responsibilities list (bullet points from Responsibilities section)
        resp_text = sections.get("RESPONSIBILITIES", "")
        if resp_text:
            resp_lines = [l.strip().lstrip("-* ").strip() for l in resp_text.split("\n") if l.strip()]
            entities["responsibilities"] = [l[:500] for l in resp_lines[:6]]
        else:
            entities["responsibilities"] = ["Design and build software modules.", "Collaborate with product developers."]

        # 6. Extract Location and Company indicators
        loc_match = re.search(r'\b(remote|san\s+francisco|new\s+york|hybrid|london|boston)\b', text, re.IGNORECASE)
        if loc_match:
            entities["location"] = loc_match.group(1).capitalize()

        return entities

    # --- Ingest/Generate Job Intelligence Profile ---

    def generate_job_intelligence(self, document_id: str, user_id: str) -> orm.JobIntelligenceORM:
        # 1. Retrieve document metadata
        doc = self.doc_repo.get_document_with_versions(document_id)
        if not doc or not doc.versions:
            raise NotFoundException("Target Job Description document version not found.")

        # Find or create a matching logical parent JobORM in database
        db = self.jd_repo.db
        recruiter_profile = db.query(orm.RecruiterProfileORM).first()
        if not recruiter_profile:
            # Seed default recruiter profile for connection
            recruiter_profile = orm.RecruiterProfileORM(
                user_id=doc.user_id,
                company_name="Tech Corp",
                company_website="techcorp.com",
                bio="Technical recruitment managers."
            )
            db.add(recruiter_profile)
            db.commit()

        # Find if a JobORM is already linked to this document
        job_orm = db.query(orm.JobORM).filter(orm.JobORM.title == doc.name).first()
        if not job_orm:
            job_orm = orm.JobORM(
                recruiter_id=recruiter_profile.user_id,
                title=doc.name,
                description="Parsed job description details.",
                experience_level="MID"
            )
            db.add(job_orm)
            db.commit()

        # 2. Extract Raw file content from storage provider
        latest_ver = doc.versions[0]
        file_bytes = self.storage.download_file(latest_ver.storage_path)

        ext = latest_ver.original_name.split(".")[-1].lower()
        extractor = ExtractorFactory.get_extractor(ext)
        raw_text = extractor.extract_text(file_bytes)

        if not raw_text:
            raise ValidationException("Job description document contains no readable text.")

        # Emit parsed log
        logger.info(f"[EVENT: JobParsed] Document: {document_id}")

        # 3. Process Pipeline Cleanings
        cleaned_text = self._clean_text(raw_text)
        sections = self._detect_sections(cleaned_text)
        entities = self._extract_entities(cleaned_text, sections)

        # Update parent Job details
        job_orm.title = entities["title"]
        job_orm.experience_level = entities["expected_seniority"]
        db.commit()

        # Create/Clear JobIntelligence record
        db_intel = self.jd_repo.create_or_clear_job_intelligence(str(job_orm.id), document_id)
        self.jd_repo.commit()

        # --- A. FEATURE STORE METRICS ---
        required_skills = [sk for sk in entities["skills"] if sk["is_mandatory"]]
        categories = {sk["category"] for sk in required_skills}
        
        # Skill Diversity
        diversity = len(categories) / 8.0 if categories else 0.0
        
        cloud_req = any(sk["name"].lower() in {"aws", "gcp", "azure"} for sk in required_skills)
        leadership_req = any(sk["name"].lower() in {"leadership", "communication"} for sk in required_skills)
        ai_req = any(sk["name"].lower() in {"tensorflow", "pytorch", "llm", "nlp"} for sk in required_skills)
        
        features_data = {
            "required_skills_count": len(required_skills),
            "skill_diversity": round(diversity, 2),
            "required_experience": float(entities["experience_years_required"]),
            "cloud_requirement": cloud_req,
            "leadership_requirement": leadership_req,
            "ai_requirement": ai_req,
            "programming_depth": float(len(required_skills) * 0.25),
            "technology_breadth": float(len(categories))
        }

        # 4. Save details
        db_intel = self.jd_repo.save_job_intelligence_details(
            job_intelligence_id=str(db_intel.id),
            title=entities["title"],
            department="Engineering",
            company=entities["company"],
            location=entities["location"],
            employment_type=entities["employment_type"],
            experience_years_required=entities["experience_years_required"],
            expected_seniority=entities["expected_seniority"],
            interview_difficulty=entities["interview_difficulty"],
            education_requirements=entities["education_requirements"],
            skills_data=entities["skills"],
            responsibilities_data=entities["responsibilities"],
            features_data=features_data,
            metadata_data=[{"key": "parsed_by", "value": "JobDescriptionIntelligenceEngine"}]
        )

        # Log audit log
        self.jd_repo.log_job_audit_event(
            job_intelligence_id=str(db_intel.id),
            action="GENERATE",
            message=f"Job intelligence profile generated for job: {entities['title']}."
        )

        logger.info(f"[EVENT: JobIntelligenceGenerated] ID: {db_intel.id}")

        return db_intel
