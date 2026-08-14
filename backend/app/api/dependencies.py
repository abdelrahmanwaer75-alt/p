from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories.library import LibraryRepository
from app.repositories.playlists import PlaylistRepository
from app.schemas.auth import UserResponse
from app.services.auth import current_user
from app.services.downloads import DownloadService, get_download_service
from app.services.files import FileManagerService

bearer = HTTPBearer(auto_error=False)
library_repository = LibraryRepository()
playlist_repository = PlaylistRepository()
file_manager = FileManagerService(library_repository)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> UserResponse:
    user = current_user(credentials)
    request.state.user_id = str(user.id)
    return user


def get_library_repository() -> LibraryRepository:
    return library_repository


def get_playlist_repository() -> PlaylistRepository:
    return playlist_repository


def get_file_manager() -> FileManagerService:
    return file_manager


def get_download_service_dependency() -> DownloadService:
    return get_download_service()


__all__ = [
    "bearer",
    "get_current_user",
    "get_library_repository",
    "get_playlist_repository",
    "get_file_manager",
    "get_download_service_dependency",
]
