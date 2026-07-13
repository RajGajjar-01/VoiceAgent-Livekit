from collections.abc import AsyncGenerator

import structlog
from fastapi import Depends, HTTPException, Request, status
from jwt import ExpiredSignatureError, PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository

logger = structlog.get_logger()


async def get_current_user_id(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        logger.info("access_token_missing", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "NOT_AUTHENTICATED", "detail": "Not authenticated"},
        )
    try:
        payload = verify_access_token(token)
    except ExpiredSignatureError:
        # The expected case once JWT_EXPIRY_MINUTES elapses — the frontend's
        # axios interceptor is supposed to catch this 401 and transparently
        # refresh, so seeing many of these with no matching
        # "access_token_refreshed" right after is a sign the refresh call
        # itself is failing, not that expiry is the bug.
        logger.info("access_token_expired", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "TOKEN_EXPIRED", "detail": "Session expired"},
        ) from None
    except PyJWTError as e:
        # Malformed/invalid-signature token — a different failure mode than
        # plain expiry (e.g. JWT_SECRET changed, or a corrupted cookie), and
        # one the refresh flow can't recover from since the token is not
        # just stale, it's not decodable as ours at all.
        logger.warning("access_token_invalid", path=request.url.path, reason=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "TOKEN_INVALID", "detail": "Invalid session"},
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
