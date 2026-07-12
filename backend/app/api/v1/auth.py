import secrets
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import settings
from app.core.dependencies import get_current_user_id, get_user_repository
from app.core.rate_limit import login_rate_limiter
from app.core.response import error_response, success_response
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserProfileResponse
from app.schemas.common import ErrorResponse, MessageResponse, SuccessResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])


def _samesite() -> Literal["lax", "none"]:
    return "none" if settings.COOKIE_SECURE else "lax"


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    auth_url = auth_service.build_authorization_url(state)
    resp = RedirectResponse(auth_url)
    resp.set_cookie(
        "oauth_state", state, httponly=True, secure=settings.COOKIE_SECURE, samesite=_samesite(), max_age=600
    )
    return resp


@router.get("/google/callback", dependencies=[Depends(login_rate_limiter())])
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    user_repo: UserRepository = Depends(get_user_repository),
) -> RedirectResponse:
    if error is not None:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=consent_denied")

    expected_state = request.cookies.get("oauth_state")
    if not state or not code or state != expected_state:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=invalid_state")

    try:
        _, session_token = await auth_service.complete_google_login(code, user_repo)
    except Exception:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=token_exchange_failed")

    resp = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
    resp.set_cookie(
        "session_token",
        session_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=_samesite(),
        max_age=settings.JWT_EXPIRY_MINUTES * 60,
    )
    resp.delete_cookie("oauth_state")
    return resp


@router.post("/logout", responses={200: {"model": SuccessResponse[MessageResponse]}})
async def logout() -> JSONResponse:
    resp = success_response({"message": "Logged out"})
    resp.delete_cookie("session_token", httponly=True, secure=settings.COOKIE_SECURE, samesite=_samesite())
    return resp


@router.get(
    "/me",
    responses={
        200: {"model": SuccessResponse[UserProfileResponse]},
        404: {"model": ErrorResponse},
    },
)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    user = await user_repo.get_by_id(user_id)
    if user is None:
        return error_response(404, "USER_NOT_FOUND", "User not found")
    return success_response(
        UserProfileResponse(id=str(user.id), email=user.email, name=user.name, avatar_url=user.avatar_url).model_dump()
    )
