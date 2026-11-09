import asyncio

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import engine
from app.core.rate_limit import redis
from app.core.response import success_response
from app.schemas.common import SuccessResponse
from app.schemas.health import LivenessData, ReadinessData

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


async def _check_postgres() -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "healthy"
    except Exception:
        logger.warning("postgres_health_check_failed", exc_info=True)
        return "unhealthy"


async def _check_redis() -> str:
    try:
        await redis.ping()
        return "healthy"
    except Exception:
        logger.warning("redis_health_check_failed", exc_info=True)
        return "unhealthy"


@router.get("/live", responses={200: {"model": SuccessResponse[LivenessData]}})
async def liveness() -> JSONResponse:
    return success_response({"status": "alive"})


@router.get("/health", responses={200: {"model": SuccessResponse[ReadinessData]}})
async def readiness() -> JSONResponse:
    postgres, redis = await asyncio.gather(_check_postgres(), _check_redis())
    overall = "healthy" if postgres == "healthy" and redis == "healthy" else "unhealthy"
    return success_response(
        {"status": overall, "postgres": postgres, "redis": redis},
        status_code=200 if overall == "healthy" else 503,
    )
