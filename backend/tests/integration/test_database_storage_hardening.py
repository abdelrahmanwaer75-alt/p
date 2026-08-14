from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.storage import MediaStorage


def test_production_rejects_sqlite_and_auto_create() -> None:
    with pytest.raises(ValueError, match="SQLite"):
        Settings(
            environment="production",
            database_url="sqlite:///./isolated.db",
            auto_create_db=False,
            jwt_secret="x" * 64,
            allowed_origins="https://vidora.example",
        )


def test_media_storage_rejects_symlink_escape(tmp_path: Path) -> None:
    managed = tmp_path / "media"
    outside = tmp_path / "outside"
    managed.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    (managed / "escape").symlink_to(outside, target_is_directory=True)
    storage = MediaStorage(str(managed))
    with pytest.raises(ValueError, match="escapes"):
        storage.get_path("escape/secret.txt")


def test_health_endpoint_is_liveness_only() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
