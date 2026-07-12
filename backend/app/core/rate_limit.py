from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate


def login_rate_limiter() -> RateLimiter:
    return RateLimiter(limiter=Limiter(Rate(10, Duration.MINUTE)))
