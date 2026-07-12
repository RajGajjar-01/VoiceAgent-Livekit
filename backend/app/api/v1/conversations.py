from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response

from app.core.dependencies import get_conversation_repository, get_current_user_id
from app.core.response import error_response, success_response
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.conversation import ConversationMessageResponse, ConversationResponse

router = APIRouter(tags=["conversations"])


@router.get("", responses={200: {"model": SuccessResponse[list[ConversationResponse]]}})
async def list_conversations(
    user_id: str = Depends(get_current_user_id),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
) -> JSONResponse:
    conversations = await conversation_repo.list_for_user(user_id)
    return success_response(
        [
            ConversationResponse(
                id=str(c.id), room=c.room, started_at=c.started_at, ended_at=c.ended_at
            ).model_dump()
            for c in conversations
        ]
    )


@router.get(
    "/{conversation_id}/messages",
    responses={200: {"model": SuccessResponse[list[ConversationMessageResponse]]}, 404: {"model": ErrorResponse}},
)
async def get_conversation_messages(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
) -> JSONResponse:
    messages = await conversation_repo.get_messages(conversation_id, user_id)
    if messages is None:
        return error_response(404, "CONVERSATION_NOT_FOUND", "Conversation not found")
    return success_response(
        [
            ConversationMessageResponse(
                id=str(m.id), role=m.role, content=m.content, created_at=m.created_at
            ).model_dump()
            for m in messages
        ]
    )


@router.delete(
    "/{conversation_id}",
    status_code=204,
    responses={204: {"description": "Conversation deleted"}, 404: {"model": ErrorResponse}},
)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
) -> JSONResponse:
    deleted = await conversation_repo.delete(conversation_id, user_id)
    if not deleted:
        return error_response(404, "CONVERSATION_NOT_FOUND", "Conversation not found")
    return Response(status_code=204)
