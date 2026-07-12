from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies import get_current_user_id, get_task_repository
from app.core.response import error_response, success_response
from app.repositories.task_repository import TaskRepository
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.task import CreateTaskRequest, SetStatusRequest, TaskResponse

router = APIRouter(tags=["tasks"])


@router.get("", responses={200: {"model": SuccessResponse[list[TaskResponse]]}})
async def list_tasks(
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    tasks = await task_repo.list_for_user(user_id)
    return success_response(
        [
            TaskResponse(id=str(t.id), title=t.title, status=t.status, duration_minutes=t.duration_minutes, created_at=t.created_at).model_dump()
            for t in tasks
        ]
    )


@router.post("", status_code=201, responses={201: {"model": SuccessResponse[TaskResponse]}})
async def create_task(
    body: CreateTaskRequest,
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    task = await task_repo.create(user_id=user_id, title=body.title, duration_minutes=body.duration_minutes)
    return success_response(
        TaskResponse(id=str(task.id), title=task.title, status=task.status, duration_minutes=task.duration_minutes, created_at=task.created_at).model_dump(),
        status_code=201,
    )


@router.patch(
    "/{task_id}/status",
    responses={200: {"model": SuccessResponse[TaskResponse]}, 404: {"model": ErrorResponse}},
)
async def set_task_status(
    task_id: str,
    body: SetStatusRequest,
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    task = await task_repo.set_status(task_id, user_id, body.status)
    if task is None:
        return error_response(404, "TASK_NOT_FOUND", "Task not found")
    return success_response(
        TaskResponse(id=str(task.id), title=task.title, status=task.status, duration_minutes=task.duration_minutes, created_at=task.created_at).model_dump()
    )


@router.delete(
    "/{task_id}",
    status_code=204,
    responses={204: {"description": "Task deleted"}, 404: {"model": ErrorResponse}},
)
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    deleted = await task_repo.delete(task_id, user_id)
    if not deleted:
        return error_response(404, "TASK_NOT_FOUND", "Task not found")
    return JSONResponse(status_code=204, content=None)
