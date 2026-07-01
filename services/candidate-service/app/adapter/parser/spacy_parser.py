# services/candidate-service/app/adapter/parser/spacy_parser.py
import io
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# --- OCR Provider Abstraction ---

class OcrProvider(ABC):
    @abstractmethod
    def perform_ocr(self, file_bytes: bytes) -> str:
        pass


class MockOcrProvider(OcrProvider):
    """
    Mock OCR engine returning static templates for testing and local runs without system binaries.
    """
    def perform_ocr(self, file_bytes: bytes) -> str:
        logger.info("Executing Mock OCR Engine fallback.")
        return (
            "JOHN DOE\n"
            "Email: john.doe@email.com\n"
            "Phone: +1 555-0199\n"
            "Location: San Francisco, CA\n"
            "LinkedIn: linkedin.com/in/johndoe\n\n"
            "SUMMARY\n"
            "Experienced software developer working on cloud technologies.\n\n"
            "EXPERIENCE\n"
            "Senior Engineer at Tech Corp (2022-04 to present)\n"
            "Developed cloud orchestration services using Python and Kubernetes.\n\n"
            "EDUCATION\n"
            "Bachelor of Science in Computer Science at Stanford University (Graduation: 2021)\n\n"
            "SKILLS\n"
            "Python3, Go, Kubernetes, Docker, PostgreSQL\n"
        )


class TesseractOcrProvider(OcrProvider):
    """
    Integrates with pytesseract to perform OCR on image buffers or scanned PDFs.
    """
    def perform_ocr(self, file_bytes: bytes) -> str:
        try:
            from PIL import Image
            import pytesseract
            
            image = Image.open(io.BytesIO(file_bytes))
            # Perform OCR text extraction
            text = pytesseract.image_to_string(image)
            logger.info("Tesseract OCR completed successfully.")
            return text
        except Exception as e:
            logger.error(f"Tesseract OCR execution failed: {e}. Falling back to Mock OCR.")
            return MockOcrProvider().perform_ocr(file_bytes)


# --- Text Extractor Abstraction ---

class TextExtractor(ABC):
    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        pass


class PdfExtractor(TextExtractor):
    """
    Extracts text from PDFs using PyMuPDF (fitz).
    """
    def extract_text(self, file_bytes: bytes) -> str:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"PyMuPDF PDF extraction failed: {e}")
            raise RuntimeError(f"Failed to extract PDF contents: {e}")


class DocxExtractor(TextExtractor):
    """
    Extracts text from Word documents (.docx) using docx2txt.
    """
    def extract_text(self, file_bytes: bytes) -> str:
        try:
            import docx2txt
            # Process bytes in memory
            fp = io.BytesIO(file_bytes)
            text = docx2txt.process(fp)
            return text
        except Exception as e:
            logger.error(f"docx2txt extraction failed: {e}")
            raise RuntimeError(f"Failed to extract DOCX contents: {e}")


class TxtExtractor(TextExtractor):
    """
    Extracts plain text.
    """
    def extract_text(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1")
            except Exception as e:
                logger.error(f"Plaintext extraction failed: {e}")
                raise RuntimeError(f"Failed to parse plaintext: {e}")


# --- Factory for Strategy Resolution ---

class ExtractorFactory:
    @staticmethod
    def get_extractor(extension: str) -> TextExtractor:
        ext = extension.lower().lstrip(".")
        if ext == "pdf":
            return PdfExtractor()
        elif ext == "docx":
            return DocxExtractor()
        elif ext in {"txt", "csv", "log"}:
            return TxtExtractor()
        else:
            raise ValueError(f"No text extractor matches extension: .{ext}")


class ResumeParser:
    """
    Legacy compatibility wrapper for previous stage routing handlers.
    """
    def __init__(self):
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
        return PdfExtractor().extract_text(file_bytes)

    def parse_resume(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        extracted_skills = []

        for skill in self.skill_dictionary:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                extracted_skills.append(skill)

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else "unknown@candidate.com"

        phone_match = re.search(r'\+?\d[\d -]{8,12}\d', text)
        phone = phone_match.group(0) if phone_match else ""

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
        if not candidate_skills:
            return 0.0

        jd_lower = job_description.lower()
        matched_skills = 0

        for skill in candidate_skills:
            if skill in jd_lower:
                matched_skills += 1

        return round((matched_skills / len(candidate_skills)) * 100, 2)
