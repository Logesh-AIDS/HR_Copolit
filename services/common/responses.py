# services/common/responses.py
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class BaseResponse(BaseModel):
    success: bool


class APIResponse(BaseResponse, Generic[T]):
    """
    Standard envelope format enclosing all positive API returns.
    """
    success: bool = True
    data: Optional[T] = None


class PaginationMetadata(BaseModel):
    total: int = Field(..., description="Total items matching query filters.")
    skip: int = Field(..., description="Items skipped in current cursor window.")
    limit: int = Field(..., description="Max limit items returned.")
    has_next: bool = Field(..., description="Flag indicating if next pages exist.")


class PaginatedResponse(BaseResponse, Generic[T]):
    """
    Standard envelope format enclosing all paginated database listings.
    """
    success: bool = True
    data: List[T] = []
    meta: PaginationMetadata


def make_success_response(data: Any) -> dict:
    """
    Fast utility builder returning dictionary representations.
    """
    return {
        "success": True,
        "data": data
    }


def make_paginated_response(data: List[Any], total: int, skip: int, limit: int) -> dict:
    """
    Fast utility builder formatting paginated elements.
    """
    has_next = (skip + limit) < total
    return {
        "success": True,
        "data": data,
        "meta": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": has_next
        }
    }
