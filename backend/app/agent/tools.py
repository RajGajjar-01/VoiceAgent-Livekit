from datetime import date, datetime

from livekit.agents.llm import Tool, Toolset, function_tool

from app.core.database import SessionLocal
from app.models.calendar_event import CalendarEvent
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services import calendar_service
from app.services.calendar_service import CalendarNotConnectedError


async def _find_event(calendar_repo: CalendarEventRepository, user_id: str, title: str) -> CalendarEvent | None:
    """Matches an existing event by title — voice users can't supply an event
    id, and spoken titles rarely come through transcription exactly. Prefers
    an exact (case-insensitive) match, falling back to substring, and picks
    the most recently created match when several fit."""
    events = await calendar_repo.list_for_user(user_id)
    matches = [e for e in events if e.title.lower() == title.lower()]
    if not matches:
        matches = [e for e in events if title.lower() in e.title.lower()]
    return matches[-1] if matches else None


def build_tools(user_id: str) -> list[Tool | Toolset]:
    """Builds the set of tools available to the agent for one conversation,
    each bound to this user via closure. The worker runs outside FastAPI's
    request/response cycle, so each tool opens its own short-lived DB
    session rather than sharing one across the whole conversation."""

    @function_tool
    async def list_tasks() -> str:
        """List the user's current tasks, including status and estimated duration."""
        async with SessionLocal() as session:
            tasks = await TaskRepository(session).list_for_user(user_id)
        if not tasks:
            return "You have no tasks."
        lines = []
        for t in tasks:
            parts = [t.title, f"({t.status}"]
            if t.duration_minutes:
                parts.append(f"{t.duration_minutes} min")
            parts[-1] += ")"
            lines.append(" ".join(parts))
        return "Your tasks: " + "; ".join(lines)

    @function_tool
    async def create_task(title: str, duration_minutes: int) -> str:
        """Create a new task. Always ask the user for the estimated duration
        before calling this tool — do not guess or make one up.

        Args:
            title: A short title describing the task.
            duration_minutes: Estimated time to complete, in minutes.
        """
        async with SessionLocal() as session:
            task = await TaskRepository(session).create(user_id=user_id, title=title, duration_minutes=duration_minutes)
        return f"Added task: {task.title}"

    @function_tool
    async def complete_task(title: str) -> str:
        """Mark an existing task as done, matching it by title.

        Args:
            title: The task's title, or a close match — spoken titles rarely
                come through transcription exactly.
        """
        async with SessionLocal() as session:
            repo = TaskRepository(session)
            task = await repo.find_by_title(user_id, title)
            if task is None:
                return f"I couldn't find a task matching '{title}'."
            done_task = await repo.set_status(str(task.id), user_id, "completed")
        if done_task is None:
            return f"I couldn't find a task matching '{title}'."
        return f"Marked '{done_task.title}' as done."

    @function_tool
    async def edit_task(title: str, new_title: str | None = None, new_duration_minutes: int | None = None) -> str:
        """Edit an existing task's title and/or estimated duration, matching
        the task by its current title. Omit whichever field the user did not
        ask to change.

        Args:
            title: The task's current title, or a close match — spoken titles
                rarely come through transcription exactly.
            new_title: The new title, if the user wants to rename the task.
            new_duration_minutes: The new estimated duration in minutes, if
                the user wants to change it.
        """
        if new_title is None and new_duration_minutes is None:
            return "I need something to change — a new title or a new duration."
        async with SessionLocal() as session:
            repo = TaskRepository(session)
            task = await repo.find_by_title(user_id, title)
            if task is None:
                return f"I couldn't find a task matching '{title}'."
            updated = await repo.update(
                str(task.id), user_id, title=new_title, duration_minutes=new_duration_minutes
            )
        if updated is None:
            return f"I couldn't find a task matching '{title}'."
        suffix = f" ({updated.duration_minutes} min)" if updated.duration_minutes else ""
        return f"Updated task: {updated.title}{suffix}"

    @function_tool
    async def delete_task(title: str) -> str:
        """Delete a task permanently, matching it by title.

        Args:
            title: The task's title, or a close match — spoken titles rarely
                come through transcription exactly.
        """
        async with SessionLocal() as session:
            repo = TaskRepository(session)
            task = await repo.find_by_title(user_id, title)
            if task is None:
                return f"I couldn't find a task matching '{title}'."
            await repo.delete(str(task.id), user_id)
        return f"Deleted task '{task.title}'."

    @function_tool
    async def book_calendar_event(
        title: str,
        start_time_iso: str,
        end_time_iso: str,
        attendee_emails: list[str] | None = None,
    ) -> str:
        """Book an event on the user's Google Calendar. Ask the user to
        clarify if the date, time, or duration is ambiguous rather than
        guessing. If the user wants to invite someone, always ask for that
        person's email address before calling this tool — never guess or
        make one up from just a name. If you have already successfully
        booked this event, do NOT call this tool again with the same details.

        Args:
            title: A short title for the event.
            start_time_iso: Start time as an ISO 8601 datetime with timezone offset.
            end_time_iso: End time as an ISO 8601 datetime with timezone offset.
            attendee_emails: Email addresses of people to invite, if any.
                Omit entirely if the user didn't ask to invite anyone.
        """
        try:
            start = datetime.fromisoformat(start_time_iso)
            end = datetime.fromisoformat(end_time_iso)
        except ValueError:
            return "I couldn't understand those times — could you repeat them?"

        async with SessionLocal() as session:
            calendar_repo = CalendarEventRepository(session)
            user_repo = UserRepository(session)

            # Check for any event with the same title near the requested time
            existing = await calendar_repo.find_by_title_and_time(
                user_id, title, start, threshold_minutes=30
            )
            if existing is not None:
                if attendee_emails:
                    updated = await calendar_service.add_attendees(
                        user_id=user_id,
                        event_id=str(existing.id),
                        attendee_emails=attendee_emails,
                        calendar_repo=calendar_repo,
                        user_repo=user_repo,
                    )
                    return (
                        f"Added {', '.join(attendee_emails)} to '{updated.title}' "
                        f"(already booked at that time)."
                    )
                return (
                    f"'{existing.title}' is already booked on your calendar "
                    f"at that time — no duplicate was created."
                )

            # Also check for ANY event overlapping the requested time window
            # to prevent double-booking even with different titles
            overlapping = await calendar_repo.find_overlapping(
                user_id, start, end
            )
            if overlapping:
                return (
                    f"You already have '{overlapping.title}' on your calendar "
                    f"at that time — I can't book '{title}' without overlapping."
                )

            try:
                event = await calendar_service.create_event(
                    user_id=user_id,
                    title=title,
                    start=start,
                    end=end,
                    calendar_repo=calendar_repo,
                    user_repo=user_repo,
                    attendee_emails=attendee_emails,
                )
            except CalendarNotConnectedError:
                return "Your Google Calendar isn't connected, so I can't book that. Please reconnect your account."
        if attendee_emails:
            return f"Booked '{event.title}' and invited {', '.join(attendee_emails)}."
        return f"Booked '{event.title}' on your calendar."

    @function_tool
    async def add_event_attendees(event_title: str, attendee_emails: list[str]) -> str:
        """Add attendees to an existing calendar event. Use this when the
        user asks to invite someone to an event that has already been
        booked, rather than booking a new event.

        Args:
            event_title: The title of the existing event to update.
            attendee_emails: Email addresses of people to invite.
        """
        if not attendee_emails:
            return "I need at least one email address to invite someone."

        async with SessionLocal() as session:
            calendar_repo = CalendarEventRepository(session)
            user_repo = UserRepository(session)
            event = await _find_event(calendar_repo, user_id, event_title)
            if event is None:
                return f"I couldn't find an existing event matching '{event_title}'."

            try:
                updated = await calendar_service.add_attendees(
                    user_id=user_id,
                    event_id=str(event.id),
                    attendee_emails=attendee_emails,
                    calendar_repo=calendar_repo,
                    user_repo=user_repo,
                )
            except CalendarNotConnectedError:
                return "Your Google Calendar isn't connected, so I can't update that event."
        existing_names = ", ".join(updated.attendees or [])
        return f"Added {', '.join(attendee_emails)} to '{updated.title}'. Attendees: {existing_names}."

    @function_tool
    async def list_schedule(day: str) -> str:
        """List calendar events for a specific day. Use this when the user
        asks about their schedule, what's on their calendar, or what
        meetings they have on a given day.

        Args:
            day: The date as YYYY-MM-DD (e.g. "2026-07-13").
        """
        try:
            parsed = date.fromisoformat(day)
        except ValueError:
            return "I couldn't understand that date. Please use YYYY-MM-DD format."

        async with SessionLocal() as session:
            repo = CalendarEventRepository(session)
            events = await repo.list_for_day(user_id, parsed)

        if not events:
            return f"You have no events on {day}."

        lines = []
        for e in events:
            start_str = e.start_time.strftime("%I:%M %p").lstrip("0")
            end_str = e.end_time.strftime("%I:%M %p").lstrip("0")
            parts = [f"{start_str} – {end_str}", e.title]
            if e.attendees:
                parts.append(f"(with {', '.join(e.attendees)})")
            lines.append(" ".join(parts))
        return f"Your schedule for {day}: " + "; ".join(lines)

    @function_tool
    async def reschedule_calendar_event(event_title: str, new_start_time_iso: str, new_end_time_iso: str) -> str:
        """Reschedule an existing calendar event to a new time, matching it
        by title. Ask the user to clarify if the new date or time is
        ambiguous rather than guessing.

        Args:
            event_title: The title of the existing event to reschedule.
            new_start_time_iso: New start time as an ISO 8601 datetime with timezone offset.
            new_end_time_iso: New end time as an ISO 8601 datetime with timezone offset.
        """
        try:
            new_start = datetime.fromisoformat(new_start_time_iso)
            new_end = datetime.fromisoformat(new_end_time_iso)
        except ValueError:
            return "I couldn't understand those times — could you repeat them?"

        async with SessionLocal() as session:
            calendar_repo = CalendarEventRepository(session)
            user_repo = UserRepository(session)
            event = await _find_event(calendar_repo, user_id, event_title)
            if event is None:
                return f"I couldn't find an existing event matching '{event_title}'."

            overlapping = await calendar_repo.find_overlapping(user_id, new_start, new_end)
            if overlapping is not None and str(overlapping.id) != str(event.id):
                return (
                    f"You already have '{overlapping.title}' on your calendar at that time "
                    f"— I can't reschedule '{event.title}' without overlapping."
                )

            try:
                updated = await calendar_service.reschedule_event(
                    user_id=user_id,
                    event_id=str(event.id),
                    start=new_start,
                    end=new_end,
                    calendar_repo=calendar_repo,
                    user_repo=user_repo,
                )
            except CalendarNotConnectedError:
                return "Your Google Calendar isn't connected, so I can't reschedule that."
        return f"Rescheduled '{updated.title}' to the new time."

    @function_tool
    async def delete_calendar_event(event_title: str) -> str:
        """Delete an existing calendar event permanently, matching it by title.

        Args:
            event_title: The title of the event to delete, or a close match.
        """
        async with SessionLocal() as session:
            calendar_repo = CalendarEventRepository(session)
            user_repo = UserRepository(session)
            event = await _find_event(calendar_repo, user_id, event_title)
            if event is None:
                return f"I couldn't find an existing event matching '{event_title}'."

            try:
                await calendar_service.delete_event(
                    user_id=user_id,
                    event_id=str(event.id),
                    calendar_repo=calendar_repo,
                    user_repo=user_repo,
                )
            except CalendarNotConnectedError:
                return "Your Google Calendar isn't connected, so I can't delete that."
        return f"Deleted '{event.title}' from your calendar."

    return [
        list_tasks,
        create_task,
        complete_task,
        edit_task,
        delete_task,
        book_calendar_event,
        add_event_attendees,
        list_schedule,
        reschedule_calendar_event,
        delete_calendar_event,
    ]
