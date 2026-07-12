from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: str
    room: str
    started_at: datetime
    ended_at: datetime | None


class ConversationMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
