from datetime import datetime

from pydantic import BaseModel


class CalendarEventResponse(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    created_at: datetime
    html_link: str | None
    attendees: list[str]
