from collections.abc import Awaitable, Callable

import structlog
from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

from app.core.config import settings

logger = structlog.get_logger()

# Shared client; redis-py connects lazily, so importing this opens no connection.
redis: Redis = Redis.from_url(settings.REDIS_URL)

# Token bucket with lazy refill. Runs atomically inside Redis, so concurrent
# requests across any number of API instances see one consistent bucket, and
# uses Redis's own clock so app servers with drifting clocks can't skew it.
# Bucket state is a hash {tokens, ts}; it expires once it would be full again,
# so idle clients cost no memory.
_TOKEN_BUCKET = redis.register_script("""
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])  -- tokens per millisecond
local t = redis.call('TIME')
local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

local bucket = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(bucket[1]) or capacity
local ts = tonumber(bucket[2]) or now
tokens = math.min(capacity, tokens + math.max(0, now - ts) * rate)

local allowed, retry_ms = 0, 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
else
  retry_ms = math.ceil((1 - tokens) / rate)
end

redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(capacity / rate))
return {allowed, math.floor(tokens), retry_ms}
""")


async def take_token(key: str, capacity: int, per_seconds: float) -> tuple[bool, int, float]:
    """Takes one token from the bucket at `key`. Returns (allowed, remaining, retry_after_seconds)."""
    rate = capacity / (per_seconds * 1000)
    allowed, remaining, retry_ms = await _TOKEN_BUCKET(keys=[key], args=[capacity, rate])
    return bool(allowed), int(remaining), int(retry_ms) / 1000


def rate_limit(capacity: int, per_seconds: float) -> Callable[[Request], Awaitable[None]]:
    """Dependency allowing bursts of `capacity` requests per client IP, refilled
    evenly over `per_seconds`. `rate_limit(10, 60)` ~= "10/minute"."""

    async def dependency(request: Request) -> None:
        # Real client IP: uvicorn rewrites request.client from X-Forwarded-For
        # when run with --proxy-headers (see Dockerfile.api).
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{request.scope['route'].path}:{ip}"
        try:
            allowed, _, retry_after = await take_token(key, capacity, per_seconds)
        except Exception:
            # ponytail: fails open so a Redis outage can't lock everyone out of login;
            # fail closed instead if a route ever guards something abuse-sensitive.
            logger.warning("rate_limit_redis_unavailable", exc_info=True)
            return
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"title": "RATE_LIMITED", "detail": "Too many requests, slow down."},
                headers={"Retry-After": str(max(1, round(retry_after)))},
            )

    return dependency
