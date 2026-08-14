from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db import SessionLocal, UserModel
from app.main import app


client = TestClient(app)
PASSWORD = "CorrectHorseBattery12!"


def create_account(prefix: str) -> tuple[str, dict, dict[str, str]]:
    email = f"{prefix}-{uuid4().hex}@example.com"
    registered = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert registered.status_code == 201, registered.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    tokens = login.json()
    return email, tokens, {"Authorization": f"Bearer {tokens['access_token']}"}


def test_register_login_and_argon2_hash() -> None:
    email, tokens, _ = create_account("register")
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"
    with SessionLocal() as session:
        user = session.scalar(select(UserModel).where(UserModel.email == email))
        assert user is not None
        assert user.password_hash != PASSWORD
        assert user.password_hash.startswith("$argon2")


def test_wrong_password_is_rejected() -> None:
    email, _, _ = create_account("wrong-password")
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})
    assert response.status_code == 401


def test_current_user_rejects_missing_and_invalid_tokens() -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}).status_code == 401


def test_expired_access_token_is_rejected() -> None:
    _, tokens, _ = create_account("expired")
    user_id = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()["id"]
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": user_id,
            "typ": "access",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "ver": 0,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_refresh_rotates_and_logout_revokes_access() -> None:
    _, tokens, headers = create_account("refresh")
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    rotated = refreshed.json()
    assert rotated["refresh_token"] != tokens["refresh_token"]
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {rotated['access_token']}"},
        json={"refresh_token": rotated["refresh_token"]},
    )
    assert logout.status_code == 200
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {rotated['access_token']}"}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}).status_code == 401


def test_user_isolation_for_library_favorites_history_and_downloads() -> None:
    _, _, user_a_headers = create_account("owner-a")
    _, _, user_b_headers = create_account("owner-b")

    created = client.post(
        "/api/v1/library",
        headers=user_a_headers,
        json={"title": "Private media", "source_url": "https://example.com/private.mp4", "media_type": "video"},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]
    assert client.get("/api/v1/library", headers=user_b_headers).json() == []
    assert client.post(f"/api/v1/library/{item_id}/favorite", headers=user_b_headers, json={"favorite": True}).status_code == 404
    assert client.post(f"/api/v1/library/{item_id}/view", headers=user_b_headers).status_code == 404
    assert client.get("/api/v1/favorites", headers=user_b_headers).json() == []
    assert client.get("/api/v1/history", headers=user_b_headers).json() == []

    download = client.post(
        "/api/v1/downloads",
        headers=user_a_headers,
        json={"source_url": "https://example.com/private.mp4", "format_id": "mp4", "authorized": True},
    )
    assert download.status_code == 501
    assert download.json()["detail"] == "FEATURE_NOT_AVAILABLE"
    assert client.get("/api/v1/downloads", headers=user_b_headers).json() == []


def test_password_reset_request_is_non_enumerating() -> None:
    response = client.post("/api/v1/auth/password-reset/request", json={"email": "not-found@example.com"})
    assert response.status_code == 200
    assert "If the account exists" in response.json()["message"]


def test_production_rejects_default_jwt_secret() -> None:
    from pydantic import ValidationError
    from app.core.config import DEFAULT_DEV_JWT_SECRET, Settings

    try:
        Settings(environment="production", jwt_secret=DEFAULT_DEV_JWT_SECRET)
    except ValidationError:
        return
    raise AssertionError("production settings accepted the default JWT secret")
