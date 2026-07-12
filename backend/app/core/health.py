import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
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
    redis: Redis = Redis.from_url(settings.REDIS_URL)
    try:
        await redis.ping()
        return "healthy"
    except Exception:
        logger.warning("redis_health_check_failed", exc_info=True)
        return "unhealthy"
    finally:
        await redis.aclose()


@router.get("/live", responses={200: {"model": SuccessResponse[LivenessData]}})
async def liveness() -> JSONResponse:
    return success_response({"status": "alive"})


@router.get("/health", responses={200: {"model": SuccessResponse[ReadinessData]}})
async def readiness() -> JSONResponse:
    postgres = await _check_postgres()
    redis = await _check_redis()
    overall = "healthy" if postgres == "healthy" and redis == "healthy" else "unhealthy"
    return success_response(
        {"status": overall, "postgres": postgres, "redis": redis},
        status_code=200 if overall == "healthy" else 503,
    )
