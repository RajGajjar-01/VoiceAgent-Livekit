from typing import Any

from pydantic import BaseModel


class SuccessResponse[T](BaseModel):
    data: T
    meta: Any = None


class ErrorDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
    meta: Any = None


class MessageResponse(BaseModel):
    message: str
