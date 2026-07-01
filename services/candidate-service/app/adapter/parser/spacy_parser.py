# services/candidate-service/app/adapter/parser/spacy_parser.py
import re
from typing import List, Dict, Any

class ResumeParser:
    def __init__(self):
        # A dictionary of key skills we track in our platform taxonomy
        self.skill_dictionary = [
            "python", "golang", "go", "java", "c++", "rust", "typescript", "javascript",
            "react", "next.js", "angular", "vue", "html", "css",
            "kubernetes", "docker", "gvisor", "firecracker", "aws", "gcp", "azure",
            "postgresql", "postgres", "mysql", "mongodb", "redis", "qdrant", "pinecone",
            "grpc", "rest", "websockets", "kafka", "rabbitmq", "webrtc",
            "machine learning", "nlp", "speech-to-text", "text-to-speech", "whisper",
            "scikit-learn", "tensorflow", "pytorch", "transformers", "llm"
        ]

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """
        Extract raw text from PDF bytes using PyMuPDF (fitz).
        Fallback to basic decode if fitz is not installed or errors.
        """
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            # Fallback text representation if library not ready
            return file_bytes.decode('utf-8', errors='ignore')

    def parse_resume(self, text: str) -> Dict[str, Any]:
        """
        Parse text to extract skills using simple token matching.
        """
        text_lower = text.lower()
        extracted_skills = []

        for skill in self.skill_dictionary:
            # Match boundary to prevent partial matches e.g. "go" in "good"
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                extracted_skills.append(skill)

        # Extract basic contact details
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else "unknown@candidate.com"

        phone_match = re.search(r'\+?\d[\d -]{8,12}\d', text)
        phone = phone_match.group(0) if phone_match else ""

        # Basic name extraction from first line of text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        name = lines[0] if lines else "Candidate Name"
        name_parts = name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else "Candidate"
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"

        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "skills": extracted_skills,
            "phone": phone
        }

    def calculate_match_score(self, candidate_skills: List[str], job_description: str) -> float:
        """
        Compute direct overlap of skills against the job description text.
        """
        if not candidate_skills:
            return 0.0

        jd_lower = job_description.lower()
        matched_skills = 0

        for skill in candidate_skills:
            if skill in jd_lower:
                matched_skills += 1

        return round((matched_skills / len(candidate_skills)) * 100, 2)
