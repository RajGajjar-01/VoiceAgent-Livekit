import secrets
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from jwt import PyJWTError

from app.core.config import settings
from app.core.dependencies import get_current_user_id, get_user_repository
from app.core.rate_limit import limiter
from app.core.response import error_response, success_response
from app.core.security import create_access_token, verify_refresh_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserProfileResponse
from app.schemas.common import ErrorResponse, MessageResponse, SuccessResponse
from app.services import auth_service

logger = structlog.get_logger()

router = APIRouter(tags=["auth"])

_REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"


def _samesite() -> Literal["lax", "none"]:
    return "none" if settings.COOKIE_SECURE else "lax"


def _set_access_token_cookie(resp: JSONResponse | RedirectResponse, access_token: str) -> None:
    resp.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=_samesite(),
        max_age=settings.JWT_EXPIRY_MINUTES * 60,
    )


def _set_refresh_token_cookie(resp: JSONResponse | RedirectResponse, refresh_token: str) -> None:
    resp.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=_samesite(),
        max_age=settings.REFRESH_TOKEN_EXPIRY_DAYS * 86400,
        path=_REFRESH_COOKIE_PATH,
    )


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    auth_url = auth_service.build_authorization_url(state)
    resp = RedirectResponse(auth_url)
    resp.set_cookie(
        "oauth_state", state, httponly=True, secure=settings.COOKIE_SECURE, samesite=_samesite(), max_age=600
    )
    return resp


@router.get("/google/callback")
@limiter.limit("10/minute")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    user_repo: UserRepository = Depends(get_user_repository),
) -> RedirectResponse:
    if error is not None:
        logger.info("oauth_consent_denied", reason=error)
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=consent_denied")

    expected_state = request.cookies.get("oauth_state")
    if not state or not code or state != expected_state:
        logger.warning("oauth_invalid_state", had_state=bool(state), had_code=bool(code))
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=invalid_state")

    try:
        user, access_token, refresh_token = await auth_service.complete_google_login(code, user_repo)
    except Exception:
        logger.exception("oauth_token_exchange_failed")
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=token_exchange_failed")

    logger.info("google_login_completed", user_id=str(user.id))
    resp = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
    _set_access_token_cookie(resp, access_token)
    _set_refresh_token_cookie(resp, refresh_token)
    resp.delete_cookie("oauth_state")
    return resp


@router.post("/refresh", responses={200: {"model": SuccessResponse[MessageResponse]}})
async def refresh(request: Request) -> JSONResponse:
    token = request.cookies.get("refresh_token")
    if not token:
        logger.info("refresh_failed", reason="no_refresh_cookie")
        return error_response(401, "NOT_AUTHENTICATED", "Not authenticated")
    try:
        payload = verify_refresh_token(token)
    except PyJWTError:
        logger.info("refresh_failed", reason="invalid_or_expired_token")
        return error_response(401, "TOKEN_EXPIRED", "Invalid or expired refresh token")

    user_id = str(payload["sub"])
    access_token = create_access_token(user_id=user_id)
    logger.info("access_token_refreshed", user_id=user_id)
    resp = success_response({"message": "Refreshed"})
    _set_access_token_cookie(resp, access_token)
    return resp


@router.post("/logout", responses={200: {"model": SuccessResponse[MessageResponse]}})
async def logout() -> JSONResponse:
    logger.info("logout")
    resp = success_response({"message": "Logged out"})
    resp.delete_cookie("access_token", httponly=True, secure=settings.COOKIE_SECURE, samesite=_samesite())
    resp.delete_cookie(
        "refresh_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=_samesite(),
        path=_REFRESH_COOKIE_PATH,
    )
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
