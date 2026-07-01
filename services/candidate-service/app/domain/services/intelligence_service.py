# services/candidate-service/app/domain/services/intelligence_service.py
import logging
import re
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.parser_repo import ParserRepository
from app.adapter.db.intelligence_repo import IntelligenceRepository
from app.adapter.db import orm
from app.domain import intelligence_models

logger = logging.getLogger(__name__)

# --- Base Taxonomy Definitions ---
BASE_TAXONOMY_NODES = [
    {"concept_name": "Machine Learning", "parent_concept_name": "Artificial Intelligence", "relation_type": "subconcept_of"},
    {"concept_name": "Natural Language Processing", "parent_concept_name": "Artificial Intelligence", "relation_type": "subconcept_of"},
    {"concept_name": "Deep Learning", "parent_concept_name": "Machine Learning", "relation_type": "subconcept_of"},
    {"concept_name": "Supervised Learning", "parent_concept_name": "Machine Learning", "relation_type": "subconcept_of"},
    {"concept_name": "Linear Regression", "parent_concept_name": "Supervised Learning", "relation_type": "subconcept_of"},
    {"concept_name": "Random Forest", "parent_concept_name": "Supervised Learning", "relation_type": "subconcept_of"},
    {"concept_name": "PyTorch", "parent_concept_name": "Deep Learning", "relation_type": "subconcept_of"},
    {"concept_name": "TensorFlow", "parent_concept_name": "Deep Learning", "relation_type": "subconcept_of"},
    {"concept_name": "Scikit-Learn", "parent_concept_name": "Supervised Learning", "relation_type": "subconcept_of"},
    {"concept_name": "PostgreSQL", "parent_concept_name": "Databases", "relation_type": "subconcept_of"},
    {"concept_name": "MongoDB", "parent_concept_name": "Databases", "relation_type": "subconcept_of"},
    {"concept_name": "Redis", "parent_concept_name": "Databases", "relation_type": "subconcept_of"},
    {"concept_name": "Qdrant", "parent_concept_name": "Databases", "relation_type": "subconcept_of"},
    {"concept_name": "Kubernetes", "parent_concept_name": "DevOps", "relation_type": "subconcept_of"},
    {"concept_name": "Docker", "parent_concept_name": "DevOps", "relation_type": "subconcept_of"},
    {"concept_name": "Python", "parent_concept_name": "Programming Languages", "relation_type": "subconcept_of"},
    {"concept_name": "Go", "parent_concept_name": "Programming Languages", "relation_type": "subconcept_of"}
]


class IntelligenceService:
    """
    Business service layer managing calculations for candidate profile intelligence.
    """
    def __init__(self, intel_repo: IntelligenceRepository, parser_repo: ParserRepository):
        self.intel_repo = intel_repo
        self.parser_repo = parser_repo
        # Initialize base taxonomy relations
        self.intel_repo.seed_taxonomy_if_empty(BASE_TAXONOMY_NODES)

    def _parse_date_string(self, date_str: Optional[str], default_date: datetime) -> datetime:
        if not date_str:
            return default_date
        
        cleaned = date_str.strip().lower()
        if cleaned in {"present", "ongoing", "current", "now", ""}:
            return default_date

        # Try YYYY-MM
        match_ym = re.match(r'^(\d{4})[-/](\d{1,2})', cleaned)
        if match_ym:
            return datetime(int(match_ym.group(1)), int(match_ym.group(2)), 1, tzinfo=timezone.utc)
            
        # Try YYYY
        match_y = re.match(r'^(\d{4})', cleaned)
        if match_y:
            return datetime(int(match_y.group(1)), 1, 1, tzinfo=timezone.utc)
            
        return default_date

    def _calculate_role_duration(self, start_str: Optional[str], end_str: Optional[str], fallback_months: int) -> int:
        """
        Parses start and end date strings and returns duration in months.
        """
        now = datetime.now(timezone.utc)
        try:
            start = self._parse_date_string(start_str, now)
            end = self._parse_date_string(end_str, now)
            
            diff_days = (end - start).days
            months = round(diff_days / 30.44)
            return max(1, months)
        except Exception:
            return fallback_months

    # --- Intelligence Engine Logic Pipeline ---

    def generate_candidate_intelligence(self, document_id: str, user_id: str) -> orm.CandidateIntelligenceORM:
        db_pr = self.parser_repo.get_parsed_resume_by_document(document_id)
        if not db_pr or db_pr.status != "COMPLETED":
            raise NotFoundException("Completed parsed resume data not found.")

        # Create or clear root CandidateIntelligence row
        db_intel = self.intel_repo.create_or_clear_intelligence(str(db_pr.id), user_id, document_id)
        self.intel_repo.commit()

        # --- A. EXPERIENCE CALCULATIONS ---
        total_exp = 0
        leadership_exp = 0
        relevant_exp = 0
        project_exp_months = len(db_pr.projects) * 3  # Estimate 3 months per project listed

        for exp in db_pr.experience:
            months = self._calculate_role_duration(exp.start_date, exp.end_date, exp.duration_months or 12)
            total_exp += months
            
            # Identify leadership roles
            title_lower = (exp.job_title or "").lower()
            if any(k in title_lower for k in {"lead", "manager", "architect", "principal", "chief", "head"}):
                leadership_exp += months

        # Heuristic relevant experience (assume 75% of total exp is relevant)
        relevant_exp = int(total_exp * 0.75)

        exp_summary_data = {
            "total_experience_months": total_exp,
            "relevant_experience_months": relevant_exp,
            "leadership_experience_months": leadership_exp,
            "internship_experience_months": int(total_exp * 0.10),
            "project_experience_months": project_exp_months
        }

        # --- B. SKILL CONFIDENCE ESTIMATIONS ---
        skill_conf_data = []
        extracted_skills = db_pr.skills or []
        
        # Build tech breadth categories count
        breadth_cats = set()
        max_depth_count = 0
        depth_dict = {}

        for skill in extracted_skills:
            # 1. Experience Years: search experience blocks mentioning the skill
            skill_exp_years = 0.0
            recency = False
            for exp in db_pr.experience:
                desc_lower = (exp.description or "").lower()
                title_lower = (exp.job_title or "").lower()
                if skill.name.lower() in desc_lower or skill.name.lower() in title_lower:
                    months = self._calculate_role_duration(exp.start_date, exp.end_date, exp.duration_months or 12)
                    skill_exp_years += (months / 12.0)
                    if not exp.end_date or exp.end_date.strip().lower() in {"present", "ongoing", "current"}:
                        recency = True

            # 2. Project Frequency: count matching projects
            proj_count = 0
            for proj in db_pr.projects:
                techs = [t.lower() for t in (proj.technologies or [])]
                desc_lower = (proj.description or "").lower()
                title_lower = (proj.title or "").lower()
                if skill.name.lower() in techs or skill.name.lower() in desc_lower or skill.name.lower() in title_lower:
                    proj_count += 1

            # 3. Certifications
            has_cert = False
            for cert in db_pr.certifications:
                if skill.name.lower() in cert.name.lower():
                    has_cert = True

            # 4. Score Math
            recency_score = 0.3 if recency else 0.0
            cert_multiplier = 0.2 if has_cert else 0.0
            raw_score = (skill_exp_years * 0.15) + (proj_count * 0.10) + recency_score + cert_multiplier
            confidence = min(0.98, max(0.30, round(raw_score, 2)))

            skill_conf_data.append({
                "name": skill.name,
                "confidence_score": confidence,
                "experience_years": skill_exp_years,
                "project_count": proj_count,
                "recency_score": recency_score,
                "has_certification": has_cert
            })

            # Breadth/Depth calculations helpers
            breadth_cats.add(skill.category)
            depth_dict[skill.category] = depth_dict.get(skill.category, 0) + 1

        if depth_dict:
            max_depth_count = max(depth_dict.values())

        # --- C. STRENGTHS, WEAKNESSES, GROWTH AREAS ---
        str_weak_data = []
        
        # Strengths: high confidence skills (>80%)
        strengths = [s["name"] for s in skill_conf_data if s["confidence_score"] >= 0.80]
        for s in strengths[:3]:
            str_weak_data.append({"type": "STRENGTH", "value": f"Strong core technical expertise in {s}."})

        # Weaknesses: skills with low confidence (<45%)
        weaknesses = [s["name"] for s in skill_conf_data if s["confidence_score"] < 0.45]
        for w in weaknesses[:2]:
            str_weak_data.append({"type": "WEAKNESS", "value": f"Limited project exposure in {w}."})

        # Strong domains
        if "MACHINE_LEARNING" in depth_dict and depth_dict["MACHINE_LEARNING"] >= 2:
            str_weak_data.append({"type": "STRONG_DOMAIN", "value": "Strong credentials in Machine Learning systems."})
        else:
            str_weak_data.append({"type": "STRONG_DOMAIN", "value": "Backend API infrastructure engineering."})

        # Learning Gaps (missing DevOps concepts)
        skill_names_lower = [sk.name.lower() for sk in extracted_skills]
        if "kubernetes" not in skill_names_lower and "docker" not in skill_names_lower:
            str_weak_data.append({"type": "LEARNING_GAP", "value": "Add Kubernetes / Docker orchestration experience."})

        # Growth Areas
        str_weak_data.append({"type": "GROWTH_AREA", "value": "Expose to production deployment workflows."})

        # --- D. FEATURE STORE METRICS ---
        avg_complexity = 0.5
        if db_pr.projects:
            # Complexity scored on average tech stack count
            avg_complexity = min(1.0, sum(len(p.technologies) for p in db_pr.projects) / (len(db_pr.projects) * 5.0))

        edu_score = 0.5
        for edu in db_pr.education:
            deg_lower = (edu.degree or "").lower()
            if any(k in deg_lower for k in {"phd", "ph.d", "doctor"}):
                edu_score = 1.0
            elif any(k in deg_lower for k in {"master", "ms", "m.s", "m.sc"}):
                edu_score = 0.85

        cert_score = min(1.0, len(db_pr.certifications) * 0.25)
        
        # Skill diversity (entropy based or count of unique categories)
        diversity = len(breadth_cats) / 8.0  # normalize by max categories
        
        cloud_exp = any(sk.name.lower() in {"aws", "gcp", "azure"} for sk in extracted_skills)
        deploy_exp = any(sk.name.lower() in {"kubernetes", "docker", "gvisor"} for sk in extracted_skills)

        # Career focus
        focus = "Backend Software Engineering"
        level = "JUNIOR"
        if total_exp >= 60:
            level = "SENIOR"
        elif total_exp >= 24:
            level = "MID"

        if "MACHINE_LEARNING" in depth_dict and depth_dict["MACHINE_LEARNING"] >= max_depth_count:
            focus = "Machine Learning Engineering"

        # Resume completeness: score how many profile coordinates are filled
        completeness = 0.2  # baseline
        if db_pr.email: completeness += 0.2
        if db_pr.phone: completeness += 0.1
        if db_pr.skills: completeness += 0.2
        if db_pr.experience: completeness += 0.2
        if db_pr.education: completeness += 0.1

        features_data = {
            "skills_count": len(extracted_skills),
            "projects_count": len(db_pr.projects),
            "avg_project_complexity": round(avg_complexity, 2),
            "years_experience": round(total_exp / 12.0, 1),
            "education_score": edu_score,
            "certification_score": cert_score,
            "skill_diversity": round(diversity, 2),
            "tech_breadth": float(len(breadth_cats)),
            "tech_depth": float(max_depth_count),
            "leadership_score": round(leadership_exp / 12.0, 1),
            "cloud_exposure": cloud_exp,
            "deployment_experience": deploy_exp
        }

        # Save to Database
        db_intel = self.intel_repo.save_intelligence_details(
            intelligence_id=str(db_intel.id),
            career_level=level,
            career_focus=focus,
            preferred_roles=[focus, "Software Engineer"],
            resume_completeness=completeness,
            exp_summary_data=exp_summary_data,
            skill_conf_data=skill_conf_data,
            features_data=features_data,
            str_weak_data=str_weak_data
        )

        logger.info(
            f"[EVENT: CandidateIntelligenceGenerated] ID: {db_intel.id}, User: {user_id}, "
            f"Level: {level}, Skills: {len(skill_conf_data)}"
        )

        return db_intel

    def get_candidate_skill_graph(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Intersects global taxonomy with the candidate's active skills to build their tailored skill graph.
        """
        db_pr = self.parser_repo.get_parsed_resume_by_document(document_id)
        if not db_pr:
            return []

        active_skills = {s.name.lower() for s in db_pr.skills}
        global_nodes = self.intel_repo.list_taxonomy()

        sub_graph = []
        for node in global_nodes:
            # Include nodes where candidate has the concept, or where the parent is relevant
            if node.concept_name.lower() in active_skills:
                sub_graph.append({
                    "concept_name": node.concept_name,
                    "parent_concept_name": node.parent_concept_name,
                    "relation_type": node.relation_type
                })
        return sub_graph
