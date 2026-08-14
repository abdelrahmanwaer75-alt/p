from pathlib import Path

import pytest

from app.services.storage import StorageService


def test_storage_save_metadata_rename_move_delete(tmp_path: Path):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"real media")
    storage = StorageService(str(tmp_path / "managed"))

    saved = storage.save(source, "video.mp4")
    assert storage.exists(saved.path)
    assert saved.size == len(b"real media")
    assert saved.mime_type == "video/mp4"

    renamed = storage.rename(saved.path, "renamed.mp4")
    assert renamed.filename == "renamed.mp4"
    moved = storage.move(renamed.path, "folder/renamed.mp4")
    assert moved.filename == "renamed.mp4"
    assert storage.exists(moved.path)
    assert storage.available_space() > 0

    storage.delete(moved.path)
    assert not storage.exists(moved.path)


def test_storage_rejects_path_traversal_and_absolute_escape(tmp_path: Path):
    storage = StorageService(str(tmp_path / "managed"))
    source = tmp_path / "source.mp4"
    source.write_bytes(b"x")
    with pytest.raises(ValueError):
        storage.save(source, "../escape.mp4")
    with pytest.raises(ValueError):
        storage.move("missing.mp4", "/tmp/escape.mp4")
    with pytest.raises(ValueError):
        storage.metadata(tmp_path / "source.mp4")


def test_storage_reports_missing_file_errors(tmp_path: Path):
    storage = StorageService(str(tmp_path / "managed"))
    with pytest.raises(FileNotFoundError):
        storage.delete("missing.mp4")
    with pytest.raises(FileNotFoundError):
        storage.rename("missing.mp4", "new.mp4")
