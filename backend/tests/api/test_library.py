from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_library_favorites_and_history_flow() -> None:
    email = "library-test@example.com"
    password = "CorrectHorseBattery12!"
    assert client.post("/api/v1/auth/register", json={"email": email, "password": password}).status_code == 201
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/v1/library",
        headers=headers,
        json={"title": "Demo", "source_url": "https://example.com/demo.mp4", "media_type": "video"},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]
    assert client.post(f"/api/v1/library/{item_id}/favorite", headers=headers, json={"favorite": True}).status_code == 200
    assert len(client.get("/api/v1/favorites", headers=headers).json()) == 1
    assert client.post(f"/api/v1/library/{item_id}/view", headers=headers).status_code == 200
    assert len(client.get("/api/v1/history", headers=headers).json()) == 1


def test_library_requires_authentication() -> None:
    assert client.get("/api/v1/library").status_code == 401


def test_files_endpoint_returns_only_durable_media_records() -> None:
    email = "files-test@example.com"
    password = "CorrectHorseBattery12!"
    assert client.post("/api/v1/auth/register", json={"email": email, "password": password}).status_code == 201
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/v1/library", headers=headers, json={"title": "Pending", "source_url": "https://example.com/pending"})
    from pathlib import Path
    managed_file = Path("backend/data/media/outputs/stored.mp4")
    managed_file.parent.mkdir(parents=True, exist_ok=True)
    managed_file.write_bytes(b"real media bytes")
    client.post("/api/v1/library", headers=headers, json={"title": "Stored", "source_url": "https://example.com/stored", "media_path": str(managed_file.resolve())})
    response = client.get("/api/v1/files", headers=headers)
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Stored"]
