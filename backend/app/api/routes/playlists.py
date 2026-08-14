from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user, get_playlist_repository
from app.schemas.auth import UserResponse
from app.schemas.playlists import Playlist, PlaylistCreate, PlaylistItemCreate, PlaylistMessage, PlaylistReorder, PlaylistUpdate
from app.services.playlist_service import PlaylistService

router = APIRouter(tags=["playlists"])


def _service(repository=Depends(get_playlist_repository)) -> PlaylistService:
    return PlaylistService(repository)


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=404, detail=message)


@router.get("/playlists", response_model=list[Playlist])
async def list_playlists(user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> list[Playlist]:
    return service.list(user.id)


@router.post("/playlists", response_model=Playlist, status_code=201)
async def create_playlist(payload: PlaylistCreate, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    return service.create(user.id, payload)


@router.get("/playlists/{playlist_id}", response_model=Playlist)
async def get_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    playlist = service.get(user.id, playlist_id)
    if playlist is None:
        raise _not_found("Playlist not found")
    return playlist


@router.patch("/playlists/{playlist_id}", response_model=Playlist)
async def update_playlist(playlist_id: UUID, payload: PlaylistUpdate, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    playlist = service.update(user.id, playlist_id, payload)
    if playlist is None:
        raise _not_found("Playlist not found")
    return playlist


@router.delete("/playlists/{playlist_id}", response_model=Playlist)
async def delete_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    playlist = service.delete(user.id, playlist_id)
    if playlist is None:
        raise _not_found("Playlist not found")
    return playlist


@router.post("/playlists/{playlist_id}/items", response_model=Playlist)
async def add_playlist_item(playlist_id: UUID, payload: PlaylistItemCreate, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    playlist = service.add_item(user.id, playlist_id, payload)
    if playlist is None:
        raise _not_found("Playlist or library item not found")
    return playlist


@router.delete("/playlists/{playlist_id}/items/{item_id}", response_model=Playlist)
async def remove_playlist_item(playlist_id: UUID, item_id: UUID, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    playlist = service.remove_item(user.id, playlist_id, item_id)
    if playlist is None:
        raise _not_found("Playlist or item not found")
    return playlist


@router.post("/playlists/{playlist_id}/reorder", response_model=Playlist)
async def reorder_playlist(playlist_id: UUID, payload: PlaylistReorder, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    playlist = service.reorder(user.id, playlist_id, payload.item_ids)
    if playlist is None:
        raise HTTPException(status_code=400, detail="Playlist item order is invalid")
    return playlist


@router.post("/playlists/{playlist_id}/play", response_model=Playlist)
async def play_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> Playlist:
    playlist = service.get(user.id, playlist_id)
    if playlist is None:
        raise _not_found("Playlist not found")
    return playlist


@router.post("/playlists/{playlist_id}/download", response_model=PlaylistMessage, status_code=202)
async def download_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user), service: PlaylistService = Depends(_service)) -> PlaylistMessage:
    if service.get(user.id, playlist_id) is None:
        raise _not_found("Playlist not found")
    raise HTTPException(status_code=501, detail="FEATURE_NOT_AVAILABLE: playlist downloads require an approved extractor implementation")
