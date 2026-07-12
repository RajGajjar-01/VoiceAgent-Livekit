from datetime import datetime

from livekit.agents.llm import Tool, Toolset, function_tool

from app.core.database import SessionLocal
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services import calendar_service
from app.services.calendar_service import CalendarNotConnectedError


def build_tools(user_id: str) -> list[Tool | Toolset]:
    """Builds the set of tools available to the agent for one conversation,
    each bound to this user via closure. The worker runs outside FastAPI's
    request/response cycle, so each tool opens its own short-lived DB
    session rather than sharing one across the whole conversation."""

    @function_tool
    async def list_tasks() -> str:
        """List the user's current tasks, including whether each is done."""
        async with SessionLocal() as session:
            tasks = await TaskRepository(session).list_for_user(user_id)
        if not tasks:
            return "You have no tasks."
        lines = [f"{t.title} ({'done' if t.done else 'not done'})" for t in tasks]
        return "Your tasks: " + "; ".join(lines)

    @function_tool
    async def create_task(title: str) -> str:
        """Create a new task.

        Args:
            title: A short title describing the task.
        """
        async with SessionLocal() as session:
            task = await TaskRepository(session).create(user_id=user_id, title=title)
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
            done_task = await repo.mark_done(str(task.id), user_id)
        if done_task is None:
            return f"I couldn't find a task matching '{title}'."
        return f"Marked '{done_task.title}' as done."

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
        make one up from just a name.

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

    return [list_tasks, create_task, complete_task, book_calendar_event]
