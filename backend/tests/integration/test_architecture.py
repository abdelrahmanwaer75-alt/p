from pathlib import Path


def test_main_is_wiring_only() -> None:
    source = Path(__file__).parents[2].joinpath("app", "main.py").read_text()
    assert len(source.splitlines()) < 160
    assert "@api." not in source
    assert "@application.get" not in source


def test_modular_boundaries_import() -> None:
    from app.api.routes import analyzer_router, auth_router, downloads_router, files_router, library_router, playlists_router
    from app.core.config import get_settings
    from app.db import Base, UserModel
    from app.queue import DownloadQueue
    from app.storage import StorageService

    assert all((analyzer_router, auth_router, downloads_router, files_router, library_router, playlists_router))
    assert get_settings is not None
    assert Base is not None and UserModel is not None
    assert DownloadQueue is not None and StorageService is not None
