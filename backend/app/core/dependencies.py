from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository


async def get_current_user_id(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "NOT_AUTHENTICATED", "detail": "Not authenticated"},
        )
    try:
        payload = verify_access_token(token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "TOKEN_EXPIRED", "detail": "Invalid or expired session"},
        ) from None
    return str(payload["sub"])


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[UserRepository]:
    yield UserRepository(db)


async def get_task_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[TaskRepository]:
    yield TaskRepository(db)


async def get_calendar_event_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[CalendarEventRepository]:
    yield CalendarEventRepository(db)


async def get_conversation_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[ConversationRepository]:
    yield ConversationRepository(db)
