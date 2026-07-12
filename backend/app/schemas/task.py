from datetime import datetime

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    title: str
    duration_minutes: int | None = None


class SetStatusRequest(BaseModel):
    status: str


class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    duration_minutes: int | None
    created_at: datetime
