from datetime import datetime

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    title: str


class TaskResponse(BaseModel):
    id: str
    title: str
    done: bool
    created_at: datetime
