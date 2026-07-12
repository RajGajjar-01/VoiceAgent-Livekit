from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies import get_calendar_event_repository, get_current_user_id
from app.core.response import success_response
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.schemas.calendar import CalendarEventResponse
from app.schemas.common import SuccessResponse

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
                id=str(e.id), title=e.title, start_time=e.start_time, end_time=e.end_time, created_at=e.created_at
            ).model_dump()
            for e in events
        ]
    )
