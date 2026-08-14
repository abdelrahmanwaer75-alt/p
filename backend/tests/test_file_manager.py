from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _account(prefix: str):
    email = f"{prefix}-{uuid4()}@example.com"
    password = "CorrectHorseBattery12!"
    assert client.post("/api/v1/auth/register", json={"email": email, "password": password}).status_code == 201
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_file_manager_create_metadata_rename_move_delete_and_traversal():
    headers = _account("file-manager")
    path = Path("backend/data/media/file-manager") / "original.mp4"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"verified bytes")
    try:
        created = client.post("/api/v1/library", headers=headers, json={"title": "Managed", "source_url": "https://vimeo.com/123", "media_path": str(path.resolve()), "filename": "original.mp4", "mime_type": "video/mp4", "file_size": 15})
        assert created.status_code == 201
        item_id = created.json()["id"]

        listed = client.get("/api/v1/files", headers=headers)
        assert listed.status_code == 200
        assert listed.json()[0]["filename"] == "original.mp4"
        assert listed.json()[0]["size"] == len(b"verified bytes")

        renamed = client.post(f"/api/v1/files/{item_id}/rename", headers=headers, json={"filename": "renamed.mp4"})
        assert renamed.status_code == 200
        assert renamed.json()["file"]["filename"] == "renamed.mp4"
        assert path.with_name("renamed.mp4").exists()

        moved = client.post(f"/api/v1/files/{item_id}/move", headers=headers, json={"folder": "archive"})
        assert moved.status_code == 200
        moved_path = Path("backend/data/media/archive/renamed.mp4")
        assert moved.json()["file"]["path"] == "archive/renamed.mp4"
        assert moved_path.exists()

        assert client.post(f"/api/v1/files/{item_id}/rename", headers=headers, json={"filename": "../escape.mp4"}).status_code == 400
        assert client.post(f"/api/v1/files/{item_id}/move", headers=headers, json={"folder": "../escape"}).status_code == 400

        assert client.delete(f"/api/v1/files/{item_id}", headers=headers).status_code == 200
        assert not moved_path.exists()
    finally:
        for candidate in [path, path.with_name("renamed.mp4"), Path("backend/data/media/archive/renamed.mp4")]:
            candidate.unlink(missing_ok=True)


def test_file_manager_isolation():
    owner = _account("file-owner")
    other = _account("file-other")
    path = Path("backend/data/media/isolated.mp4")
    path.write_bytes(b"private")
    try:
        created = client.post("/api/v1/library", headers=owner, json={"title": "Private", "source_url": "https://vimeo.com/456", "media_path": str(path.resolve())})
        item_id = created.json()["id"]
        assert client.get("/api/v1/files", headers=other).json() == []
        assert client.post(f"/api/v1/files/{item_id}/rename", headers=other, json={"filename": "stolen.mp4"}).status_code == 404
    finally:
        path.unlink(missing_ok=True)
