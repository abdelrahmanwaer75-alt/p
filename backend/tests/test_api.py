from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_headers(email: str) -> dict[str, str]:
    client.post('/api/v1/auth/register', json={'email': email, 'password': 'CorrectHorseBattery12!'})
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': 'CorrectHorseBattery12!'})
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


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
    assert body["supported"] is False
    assert "configured yet" in body["message"]
    assert body["formats"] == []


def test_analyzer_preview_rejects_private_network_url() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "http://127.0.0.1:8000/health"})
    assert response.status_code == 422


def test_analyzer_preview_rejects_non_http_url() -> None:
    response = client.post("/api/v1/analyzer/preview", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422


def test_download_requires_authenticated_account() -> None:
    response = client.post(
        "/api/v1/downloads",
        json={"source_url": "https://example.com/video.mp4", "format_id": "mp4", "authorized": True},
    )
    assert response.status_code == 401


def test_download_requires_source_authorization() -> None:
    headers = auth_headers('unauthorized@example.com')
    response = client.post(
        "/api/v1/downloads",
        headers=headers,
        json={"source_url": "https://example.com/video.mp4", "format_id": "mp4", "authorized": False},
    )
    assert response.status_code == 403


def test_download_is_queued_without_fake_progress() -> None:
    headers = auth_headers('owner@example.com')
    response = client.post(
        "/api/v1/downloads",
        headers=headers,
        json={"source_url": "https://example.com/video.mp4", "format_id": "mp4", "authorized": True},
    )
    assert response.status_code == 202
    task = response.json()["task"]
    assert task["status"] == "queued"
    assert task["progress_percent"] is None
    assert task["progress_known"] is False

    run_response = client.post(f"/api/v1/downloads/{task['id']}/run", headers=headers)
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "queued"
    assert run_response.json()["progress_percent"] is None
