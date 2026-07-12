from datetime import datetime

from sqlalchemy import select

from app.models.calendar_event import CalendarEvent
from app.repositories.base import BaseRepository


class CalendarEventRepository(BaseRepository):
    async def create(
        self,
        user_id: str,
        google_event_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        html_link: str | None = None,
        attendees: list[str] | None = None,
    ) -> CalendarEvent:
        event = CalendarEvent(
            user_id=user_id,
            google_event_id=google_event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            html_link=html_link,
            attendees=attendees,
        )
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def list_for_user(self, user_id: str) -> list[CalendarEvent]:
        result = await self._session.execute(
            select(CalendarEvent).where(CalendarEvent.user_id == user_id).order_by(CalendarEvent.start_time.asc())
        )
        return list(result.scalars().all())
