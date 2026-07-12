from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.dependencies import get_current_user_id, get_user_repository
from app.core.response import error_response, success_response
from app.repositories.user_repository import UserRepository
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.livekit import LiveKitTokenResponse
from app.services import livekit_service

router = APIRouter(tags=["livekit"])


@router.post(
    "/token",
    responses={200: {"model": SuccessResponse[LiveKitTokenResponse]}, 404: {"model": ErrorResponse}},
)
async def create_livekit_token(
    user_id: str = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    user = await user_repo.get_by_id(user_id)
    if user is None:
        return error_response(404, "USER_NOT_FOUND", "User not found")
    token, room = livekit_service.mint_token(user_id, user.email)
    return success_response(LiveKitTokenResponse(token=token, url=settings.LIVEKIT_URL, room=room).model_dump())
