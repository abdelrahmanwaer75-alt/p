from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Vidora API"


def test_version() -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["api_prefix"] == "/api/v1"


def test_analyzer_preview_detects_platform_without_fetching() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "https://www.youtube.com/watch?v=abc"})
    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "youtube"
    assert body["supported"] is True
    assert body["formats"] == []


def test_analyzer_preview_rejects_private_network_url() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "http://127.0.0.1:8000/health"})
    assert response.status_code == 422


def test_analyzer_preview_rejects_non_http_url() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422
