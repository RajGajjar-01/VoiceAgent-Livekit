from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.livekit import router as livekit_router
from app.api.v1.tasks import router as tasks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(tasks_router, prefix="/tasks")
api_router.include_router(livekit_router, prefix="/livekit")
api_router.include_router(calendar_router, prefix="/calendar")
