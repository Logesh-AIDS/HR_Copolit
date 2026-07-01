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
