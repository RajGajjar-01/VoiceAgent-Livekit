from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies import get_current_user_id, get_task_repository
from app.core.response import error_response, success_response
from app.repositories.task_repository import TaskRepository
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.task import CreateTaskRequest, TaskResponse

router = APIRouter(tags=["tasks"])


@router.get("", responses={200: {"model": SuccessResponse[list[TaskResponse]]}})
async def list_tasks(
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    tasks = await task_repo.list_for_user(user_id)
    return success_response(
        [TaskResponse(id=str(t.id), title=t.title, done=t.done, created_at=t.created_at).model_dump() for t in tasks]
    )


@router.post("", status_code=201, responses={201: {"model": SuccessResponse[TaskResponse]}})
async def create_task(
    body: CreateTaskRequest,
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    task = await task_repo.create(user_id=user_id, title=body.title)
    return success_response(
        TaskResponse(id=str(task.id), title=task.title, done=task.done, created_at=task.created_at).model_dump(),
        status_code=201,
    )


@router.patch(
    "/{task_id}/done",
    responses={200: {"model": SuccessResponse[TaskResponse]}, 404: {"model": ErrorResponse}},
)
async def mark_task_done(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    task = await task_repo.mark_done(task_id, user_id)
    if task is None:
        return error_response(404, "TASK_NOT_FOUND", "Task not found")
    return success_response(
        TaskResponse(id=str(task.id), title=task.title, done=task.done, created_at=task.created_at).model_dump()
    )
