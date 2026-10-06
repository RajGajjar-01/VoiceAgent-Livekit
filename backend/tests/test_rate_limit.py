import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import rate_limit
from app.core.rate_limit import take_token
from app.main import app


@pytest.fixture(autouse=True)
async def _require_redis() -> None:
    # pytest-asyncio gives each test a fresh event loop; drop connections bound to the last one.
    rate_limit.redis.connection_pool.reset()
    try:
        await rate_limit.redis.ping()
    except Exception:
        pytest.skip("needs Redis at REDIS_URL (docker-compose up -d redis)")


async def test_bucket_allows_burst_then_denies_with_retry_after() -> None:
    key = f"test:{uuid.uuid4()}"
    results = [await take_token(key, capacity=3, per_seconds=60) for _ in range(4)]

    assert [allowed for allowed, _, _ in results] == [True, True, True, False]
    assert [remaining for _, remaining, _ in results[:3]] == [2, 1, 0]
    # 3 tokens/60s -> one token every 20s.
    assert 19 < results[3][2] <= 20


async def test_bucket_refills_over_time() -> None:
    key = f"test:{uuid.uuid4()}"
    for _ in range(2):
        await take_token(key, capacity=2, per_seconds=0.2)  # one token per 100ms
    assert (await take_token(key, capacity=2, per_seconds=0.2))[0] is False

    await asyncio.sleep(0.15)
    assert (await take_token(key, capacity=2, per_seconds=0.2))[0] is True


async def test_concurrent_requests_never_overspend() -> None:
    key = f"test:{uuid.uuid4()}"
    results = await asyncio.gather(*(take_token(key, capacity=5, per_seconds=60) for _ in range(20)))
    assert sum(allowed for allowed, _, _ in results) == 5


async def test_route_returns_429_with_retry_after() -> None:
    ip = f"10.{uuid.uuid4().int % 250}.0.1"
    await rate_limit.redis.delete(f"rl:/api/v1/auth/google/callback:{ip}")
    transport = ASGITransport(app=app, client=(ip, 1234))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        statuses = [
            (await client.get("/api/v1/auth/google/callback", params={"error": "access_denied"})).status_code
            for _ in range(11)
        ]
        last = await client.get("/api/v1/auth/google/callback", params={"error": "access_denied"})

    assert 429 not in statuses[:10]
    assert statuses[10] == 429
    assert last.status_code == 429
    assert int(last.headers["Retry-After"]) >= 1
    assert last.json()["error"]["title"] == "RATE_LIMITED"
