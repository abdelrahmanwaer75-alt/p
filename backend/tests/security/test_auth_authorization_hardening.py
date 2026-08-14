from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.queue import DownloadQueue
from app.repositories.downloads import DownloadRepository
from app.core.security import middleware
from app.main import app
from app.services.notification_service import NotificationService
from redis.asyncio import Redis


client = TestClient(app)
PASSWORD = "CorrectHorseBattery12!"


def create_account(prefix: str) -> tuple[dict, dict[str, str]]:
    email = f"{prefix}-{uuid4().hex}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    assert registered.status_code == 201, registered.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200, login.text
    tokens = login.json()
    return tokens, {"Authorization": f"Bearer {tokens['access_token']}"}


def forge_access_token(token: str, **changes: object) -> str:
    settings = get_settings()
    payload = jwt.decode(token, options={"verify_signature": False})
    payload.update(changes)
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@pytest.mark.parametrize(
    ("claim", "value"),
    [("aud", "wrong-client"), ("iss", "wrong-issuer")],
)
def test_access_token_rejects_wrong_audience_or_issuer(claim: str, value: str) -> None:
    tokens, _ = create_account(f"wrong-{claim}")
    forged = forge_access_token(tokens["access_token"], **{claim: value})
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert response.status_code == 401


def test_access_token_rejects_malformed_and_wrong_token_type() -> None:
    tokens, _ = create_account("malformed")
    wrong_type = forge_access_token(tokens["access_token"], typ="refresh")
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {wrong_type}"},
    ).status_code == 401
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.jwt"},
    ).status_code == 401


def test_refresh_token_reuse_after_rotation_is_rejected() -> None:
    tokens, _ = create_account("reuse")
    rotated = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert rotated.status_code == 200
    reused = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert reused.status_code == 401


def test_rate_limit_policies_are_endpoint_specific() -> None:
    assert middleware._rate_limit_policy("/api/v1/auth/login", "POST")[0] == "auth"
    assert middleware._rate_limit_policy("/api/v1/analyzer/preview", "POST")[0] == "analyzer"
    assert middleware._rate_limit_policy("/api/v1/analyze", "POST")[0] == "analyzer"
    assert middleware._rate_limit_policy("/api/v1/downloads", "POST")[0] == "download_create"
    assert middleware._rate_limit_policy("/api/v1/downloads", "GET")[0] == "api"


def test_login_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    class DenyLimiter:
        async def allowed(self, key: str, limit: int) -> tuple[bool, int]:
            assert key.endswith(":auth")
            assert limit == get_settings().auth_rate_limit_per_minute
            return False, 0

    monkeypatch.setattr(middleware, "rate_limiter", DenyLimiter())
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "attempt@example.com", "password": PASSWORD},
    )
    assert response.status_code == 429
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.json()["error"]["code"] == "rate_limited"


def test_production_rate_limiting_fails_closed_without_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenRedis:
        async def incr(self, key: str) -> int:
            raise RuntimeError("redis unavailable")

    limiter = middleware.RateLimiter()
    limiter._redis = cast(Redis, BrokenRedis())
    monkeypatch.setattr(middleware.settings, "environment", "production")

    with pytest.raises(middleware.RateLimitBackendUnavailable):
        import asyncio

        asyncio.run(limiter.allowed("production-security", 10))


class _FakeRedis:
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self.calls = 0

    def xread(self, streams: dict[str, str], count: int, block: int):
        self.calls += 1
        if self.calls == 1:
            return [["events", [("1-0", {"task_id": self.task_id, "event": "download.completed"})]]]
        raise WebSocketDisconnect()


class _FakeQueue:
    event_stream = "events"

    def __init__(self, task_id: str) -> None:
        self.redis = _FakeRedis(task_id)


class _FakeRepository:
    def __init__(self, owner_id: UUID) -> None:
        self.owner_id = owner_id

    def get_any(self, task_id: UUID):
        return SimpleNamespace(owner_id=self.owner_id)


class _FakeWebSocket:
    def __init__(self, token: str) -> None:
        self.headers = {"authorization": f"Bearer {token}"}
        self.sent: list[dict] = []
        self.closed: list[int] = []

    async def accept(self) -> None:
        return None

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)

    async def close(self, code: int) -> None:
        self.closed.append(code)


def test_websocket_does_not_forward_foreign_user_events() -> None:
    user_a_tokens, _ = create_account("websocket-a")
    user_b_tokens, _ = create_account("websocket-b")
    user_a = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_a_tokens['access_token']}"},
    ).json()
    user_b = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_b_tokens['access_token']}"},
    ).json()
    foreign_task_id = str(uuid4())
    websocket = _FakeWebSocket(user_a_tokens["access_token"])
    service = NotificationService(
        queue=cast(DownloadQueue, _FakeQueue(foreign_task_id)),
        repository=cast(DownloadRepository, _FakeRepository(UUID(user_b["id"]))),
    )

    import asyncio

    asyncio.run(service.stream_downloads(cast(WebSocket, websocket)))
    assert websocket.closed == []
    assert websocket.sent == []
    assert user_a["id"] != user_b["id"]


def test_playlist_and_file_routes_enforce_owner_scope() -> None:
    _, user_a_headers = create_account("scope-a")
    _, user_b_headers = create_account("scope-b")
    created = client.post(
        "/api/v1/playlists",
        headers=user_a_headers,
        json={"name": "Private playlist"},
    )
    assert created.status_code == 201
    playlist_id = created.json()["id"]

    assert client.get(f"/api/v1/playlists/{playlist_id}", headers=user_b_headers).status_code == 404
    assert client.patch(
        f"/api/v1/playlists/{playlist_id}",
        headers=user_b_headers,
        json={"name": "stolen"},
    ).status_code == 404
    assert client.delete(
        f"/api/v1/playlists/{playlist_id}",
        headers=user_b_headers,
    ).status_code == 404

    private_item = client.post(
        "/api/v1/library",
        headers=user_a_headers,
        json={
            "title": "Private file metadata",
            "source_url": "https://example.com/private.mp4",
            "media_type": "video",
        },
    )
    assert private_item.status_code == 201
    item_id = private_item.json()["id"]
    assert client.get(f"/api/v1/files/{item_id}", headers=user_b_headers).status_code == 404
    assert client.post(
        f"/api/v1/files/{item_id}/share",
        headers=user_b_headers,
    ).status_code == 404
