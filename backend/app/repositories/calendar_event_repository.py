from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.models.calendar_event import CalendarEvent
from app.repositories.base import BaseRepository


class CalendarEventRepository(BaseRepository):
    async def get(self, event_id: str) -> CalendarEvent | None:
        return await self._session.get(CalendarEvent, event_id)

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

    async def list_for_day(self, user_id: str, day: date) -> list[CalendarEvent]:
        day_start = datetime.combine(day, datetime.min.time(), tzinfo=None)
        day_end = datetime.combine(day, datetime.max.time(), tzinfo=None)
        result = await self._session.execute(
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= day_start,
                CalendarEvent.start_time < day_end,
            )
            .order_by(CalendarEvent.start_time.asc())
        )
        return list(result.scalars().all())

    async def find_by_title_and_time(
        self, user_id: str, title: str, start_time: datetime, threshold_minutes: int = 30
    ) -> CalendarEvent | None:
        window_start = start_time - timedelta(minutes=threshold_minutes)
        window_end = start_time + timedelta(minutes=threshold_minutes)
        result = await self._session.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.title.ilike(title),
                CalendarEvent.start_time >= window_start,
                CalendarEvent.start_time <= window_end,
            )
        )
        return result.scalar_one_or_none()

    async def find_overlapping(
        self, user_id: str, start_time: datetime, end_time: datetime
    ) -> CalendarEvent | None:
        result = await self._session.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time < end_time,
                CalendarEvent.end_time > start_time,
            )
        )
        return result.scalar_one_or_none()

    async def update_attendees(self, event_id: str, attendees: list[str]) -> CalendarEvent | None:
        event = await self._session.get(CalendarEvent, event_id)
        if event is None:
            return None
        event.attendees = attendees
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def delete(self, event_id: str, user_id: str) -> bool:
        event = await self._session.get(CalendarEvent, event_id)
        if event is None or str(event.user_id) != user_id:
            return False
        await self._session.delete(event)
        await self._session.commit()
        return True
