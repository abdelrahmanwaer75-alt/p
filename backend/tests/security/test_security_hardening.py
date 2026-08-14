
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app
from app.security import RateLimiter

client = TestClient(app)


def test_security_headers_and_request_id_are_present():
    response = client.get("/health", headers={"X-Request-ID": "security-test-1"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "security-test-1"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_validation_errors_are_structured_and_include_request_id():
    response = client.post("/api/v1/auth/register", json={"email": "bad", "password": "short"}, headers={"X-Request-ID": "validation-security"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["request_id"] == "validation-security"


def test_production_rejects_insecure_cors_and_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="change-me-in-development-secret-32", allowed_origins="https://app.example")
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="a" * 64, allowed_origins="http://app.example")


def test_rate_limiter_is_bounded():
    limiter = RateLimiter()

    async def exercise():
        first, _ = await limiter.allowed("security-test", 1)
        second, _ = await limiter.allowed("security-test", 1)
        return first, second

    import asyncio
    first, second = asyncio.run(exercise())
    assert first is True
    assert second is False


def test_cors_does_not_allow_unknown_origin():
    response = client.options("/api/v1/version", headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in response.headers


def test_invalid_scheme_and_ssrf_urls_are_rejected():
    for url in ("file:///etc/passwd", "ftp://example.com/a", "http://127.0.0.1/x", "http://169.254.169.254/latest/meta-data"):
        response = client.post("/api/v1/analyzer/preview", json={"url": url})
        assert response.status_code == 422
