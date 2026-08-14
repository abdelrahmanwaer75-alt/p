from __future__ import annotations

import logging
import re
import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger("vidora.security")
settings = get_settings()


class RateLimiter:
    def __init__(self) -> None:
        self._local: dict[str, deque[float]] = defaultdict(deque)
        self._redis: Redis | None = None
        try:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            self._redis = None

    async def allowed(self, key: str, limit: int) -> tuple[bool, int]:
        now = int(time.time())
        redis_key = f"vidora:ratelimit:{now // 60}:{key}"
        if self._redis is not None:
            try:
                count = int(await self._redis.incr(redis_key))
                if count == 1:
                    await self._redis.expire(redis_key, 65)
                return count <= limit, max(0, limit - count)
            except Exception:
                logger.warning("Rate-limit backend unavailable; using bounded local fallback")
        bucket = self._local[key]
        cutoff = time.monotonic() - 60
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return False, 0
        bucket.append(time.monotonic())
        return True, max(0, limit - len(bucket))


rate_limiter = RateLimiter()


def _client_key(request: Request) -> str:
    client = request.client.host if request.client else "unknown"
    return client.replace("/", "_")[:128]


async def security_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    path = request.url.path
    task_match = re.search(r"/downloads/([0-9a-fA-F-]{36})", path)
    request.state.task_id = task_match.group(1) if task_match else None
    is_auth = path.startswith("/api/v1/auth/")
    limit = settings.auth_rate_limit_per_minute if is_auth else settings.rate_limit_per_minute
    allowed, remaining = await rate_limiter.allowed(f"{_client_key(request)}:{'auth' if is_auth else 'api'}", limit)
    if not allowed:
        response = JSONResponse(status_code=429, content={"error": {"code": "rate_limited", "message": "Too many requests", "request_id": request_id}}, headers={"Retry-After": "60", "X-Request-ID": request_id, "X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0"})
    else:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled request failure request_id=%s path=%s", request_id, path)
            raise
        logger.info("request_complete request_id=%s user_id=%s task_id=%s method=%s path=%s status=%s", request_id, getattr(request.state, "user_id", "anonymous"), getattr(request.state, "task_id", None), request.method, path, response.status_code)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store" if is_auth else "private, no-cache"
    if settings.environment.lower() in {"production", "prod"}:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
