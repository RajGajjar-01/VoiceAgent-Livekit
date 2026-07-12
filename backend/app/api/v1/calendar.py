from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies import get_calendar_event_repository, get_current_user_id
from app.core.response import error_response, success_response
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.schemas.calendar import CalendarEventResponse
from app.schemas.common import ErrorResponse, SuccessResponse

router = APIRouter(tags=["calendar"])


@router.get("/events", responses={200: {"model": SuccessResponse[list[CalendarEventResponse]]}})
async def list_calendar_events(
    user_id: str = Depends(get_current_user_id),
    calendar_repo: CalendarEventRepository = Depends(get_calendar_event_repository),
) -> JSONResponse:
    events = await calendar_repo.list_for_user(user_id)
    return success_response(
        [
            CalendarEventResponse(
                id=str(e.id),
                title=e.title,
                start_time=e.start_time,
                end_time=e.end_time,
                created_at=e.created_at,
                html_link=e.html_link,
                attendees=e.attendees or [],
            ).model_dump()
            for e in events
        ]
    )


@router.delete(
    "/events/{event_id}",
    status_code=204,
    responses={204: {"description": "Event deleted"}, 404: {"model": ErrorResponse}},
)
async def delete_calendar_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
    calendar_repo: CalendarEventRepository = Depends(get_calendar_event_repository),
) -> JSONResponse:
    deleted = await calendar_repo.delete(event_id, user_id)
    if not deleted:
        return error_response(404, "EVENT_NOT_FOUND", "Event not found")
    return JSONResponse(status_code=204, content=None)
