from fastapi import Request

from app.core.exceptions import RateLimitExceededError
from app.core.redis_client import redis_client


def rate_limiter(max_requests: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{request.url.path}:{client_ip}"

        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)

        if current > max_requests:
            raise RateLimitExceededError()

    return dependency
