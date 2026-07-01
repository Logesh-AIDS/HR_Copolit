# services/candidate-service/app/domain/document_models.py
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentType(str, Enum):
    RESUME = "RESUME"
    COVER_LETTER = "COVER_LETTER"
    PORTFOLIO = "PORTFOLIO"
    CERTIFICATE = "CERTIFICATE"
    JOB_DESCRIPTION = "JOB_DESCRIPTION"
    COMPANY_DOCUMENT = "COMPANY_DOCUMENT"
    INTERVIEW_TEMPLATE = "INTERVIEW_TEMPLATE"


class DocumentVersionResponse(BaseModel):
    id: str
    version: int
    file_size: int
    mime_type: str
    original_name: str
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    document_type: str
    current_version: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    document_type: str
    current_version: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    versions: List[DocumentVersionResponse] = []

    class Config:
        from_attributes = True


class DocumentStatsResponse(BaseModel):
    total_documents: int
    total_size_bytes: int
    type_counts: dict
