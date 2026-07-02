# services/interview-engine/app/delivery/http/coding_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.coding_repo import CodingRepository
from app.domain.services.coding_service import CodingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coding", tags=["Intelligent Coding Assessment Engine"])

def get_coding_service(db: Session = Depends(get_db)) -> CodingService:
    repo = CodingRepository(db)
    return CodingService(repo)


class CodeRunPayload(BaseModel):
    code: str = Field(..., description="Source code")
    language: str = Field(..., description="Target compiler language")
    input_data: str = Field("", description="Standard input")


class CodeSubmitPayload(BaseModel):
    session_id: str = Field(..., description="Active session identity")
    question_id: str = Field(..., description="Problem UUID")
    code: str = Field(..., description="Source code")
    language: str = Field(..., description="Target compiler language")


class ProblemCreatePayload(BaseModel):
    title: str = Field(..., description="Challenge title")
    statement: str = Field(..., description="Problem description text")
    time_limit_ms: int = Field(2000, description="Time limit constraint")
    memory_limit_bytes: int = Field(268435456, description="Memory size limit")
    reference_solution: Optional[str] = Field(None, description="Solution template")
    test_cases: List[dict] = Field(default=[], description="List of expected inputs/outputs dictionaries")


@router.post("/run")
def run_code(
    payload: CodeRunPayload,
    service: CodingService = Depends(get_coding_service)
):
    try:
        res = service.run_code(payload.code, payload.language, payload.input_data)
        return make_success_response(res)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_code(
    payload: CodeSubmitPayload,
    service: CodingService = Depends(get_coding_service)
):
    try:
        sub = service.submit_code(
            session_id=payload.session_id,
            question_id=payload.question_id,
            code=payload.code,
            language=payload.language
        )
        return make_success_response({
            "submission_id": str(sub.id),
            "test_cases_passed": sub.test_cases_passed,
            "total_test_cases": sub.total_test_cases,
            "execution_time_ms": sub.execution_time_ms,
            "error_message": sub.error_message
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{session_id}/{question_id}")
def get_submission_history(
    session_id: str,
    question_id: str,
    service: CodingService = Depends(get_coding_service)
):
    subs = service.get_history(session_id, question_id)
    return make_success_response([
        {
            "submission_id": str(s.id),
            "language": s.language,
            "test_cases_passed": s.test_cases_passed,
            "total_test_cases": s.total_test_cases,
            "execution_time_ms": s.execution_time_ms,
            "created_at": s.created_at.isoformat()
        } for s in subs
    ])


@router.get("/report/{submission_id}")
def get_execution_report(
    submission_id: str,
    service: CodingService = Depends(get_coding_service)
):
    try:
        rep = service.get_report(submission_id)
        return make_success_response(rep)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/problem/create", status_code=status.HTTP_201_CREATED)
def create_problem(
    payload: ProblemCreatePayload,
    service: CodingService = Depends(get_coding_service)
):
    try:
        prob = service.repo.create_coding_problem(
            title=payload.title,
            statement=payload.statement,
            time_limit_ms=payload.time_limit_ms,
            memory_limit_bytes=payload.memory_limit_bytes,
            reference_solution=payload.reference_solution
        )
        
        # Seed test cases
        for tc in payload.test_cases:
            service.repo.create_test_case(
                problem_id=str(prob.id),
                input_data=tc.get("input", ""),
                expected_output=tc.get("output", ""),
                is_hidden=tc.get("is_hidden", False)
            )
            
        service.repo.commit()
        return make_success_response({
            "problem_id": str(prob.id),
            "title": prob.title,
            "status": "CREATED"
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/problem/{problem_id}")
def get_problem(
    problem_id: str,
    service: CodingService = Depends(get_coding_service)
):
    prob = service.repo.get_coding_problem(problem_id)
    if not prob:
        raise HTTPException(status_code=404, detail="Coding challenge not found.")
        
    test_cases = service.repo.get_test_cases(problem_id)
    return make_success_response({
        "id": str(prob.id),
        "title": prob.title,
        "statement": prob.statement,
        "input_format": prob.input_format,
        "output_format": prob.output_format,
        "constraints": prob.constraints,
        "time_limit_ms": prob.time_limit_ms,
        "memory_limit_bytes": prob.memory_limit_bytes,
        "sample_test_cases": [
            {
                "input": tc.input,
                "output": tc.expected_output
            } for tc in test_cases if not tc.is_hidden
        ]
    })
