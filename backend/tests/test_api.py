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


def test_analyzer_preview_validates_http_url_without_fetching() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "https://example.com/video"})
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


def test_analyzer_preview_rejects_non_http_url() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422
