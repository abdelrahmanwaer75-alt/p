from .analyzer import router as analyzer_router
from .auth import router as auth_router
from .downloads import router as downloads_router
from .files import router as files_router
from .library import router as library_router
from .playlists import router as playlists_router
from .system import router as system_router
from .websocket import router as websocket_router

__all__ = [
    "auth_router",
    "analyzer_router",
    "downloads_router",
    "files_router",
    "library_router",
    "playlists_router",
    "system_router",
    "websocket_router",
]
