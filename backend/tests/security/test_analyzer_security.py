import asyncio
import socket

import pytest
from fastapi.testclient import TestClient

from app.extractors.registry import registry
from app.schemas.analyzer import Platform
from app.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://www.reddit.com/r/test/comments/abc", "reddit"),
        ("https://vimeo.com/123456", "vimeo"),
        ("https://www.dailymotion.com/video/x123", "dailymotion"),
        ("https://soundcloud.com/artist/track", "soundcloud"),
        ("https://www.twitch.tv/videos/123456", "twitch"),
    ],
)
def test_allowed_platforms_are_detected_but_unavailable_adapters_are_truthful(url: str, platform: str) -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": url})
    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == platform
    assert body["supported"] is False
    assert body["formats"] == []
    assert body["audio_formats"] == []
    assert body["video_formats"] == []
    assert body["bitrate"] is None
    assert body["resolution"] is None
    assert body["fps"] is None
    assert body["title"] is None
    assert "configured yet" in body["message"]
    assert "fabricated" in body["message"]


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc",
        "https://www.instagram.com/p/abc",
        "https://www.facebook.com/video/abc",
        "https://www.tiktok.com/@user/video/123",
        "https://x.com/user/status/123",
        "https://twitter.com/user/status/123",
    ],
)
def test_prohibited_platforms_are_not_registered(url: str) -> None:
    response = client.post("/api/v1/analyze", json={"url": url})
    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "generic"
    assert body["supported"] is False
    assert body["formats"] == []
    assert "allowlist" in body["message"]


def test_invalid_scheme_is_rejected() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000/health",
        "http://127.0.0.1:8000/health",
        "http://10.0.0.1/resource",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://[::1]/health",
        "https://user:password@vimeo.com/123456",
    ],
)
def test_local_private_and_metadata_endpoints_are_rejected(url: str) -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": url})
    assert response.status_code == 422


def test_dns_rebinding_answer_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    def unsafe_resolution(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", unsafe_resolution)
    response = client.post("/api/v1/analyzer/preview", json={"url": "https://vimeo.com/123456"})
    assert response.status_code == 422
    assert "Private or reserved" in response.json()["detail"]


def test_missing_adapter_does_not_fabricate_formats() -> None:
    extractor = registry.get(Platform.REDDIT)
    assert extractor is not None
    result = asyncio.run(extractor.analyze("https://www.reddit.com/r/test/comments/abc"))
    assert result.supported is False
    assert result.formats == []
    assert result.audio_formats == []
    assert result.video_formats == []
    assert result.title is None
    assert "FEATURE_NOT_AVAILABLE" in result.message
    assert "No metadata" in result.message
    assert "metadata_unavailable" in result.limitations


def test_adapter_authorization_gate_is_explicit() -> None:
    extractor = registry.get(Platform.VIMEO)
    assert extractor is not None
    with pytest.raises(PermissionError):
        extractor.validate_authorization(False)
