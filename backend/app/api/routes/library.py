from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user, get_library_repository
from app.schemas.auth import UserResponse
from app.schemas.library import FavoriteUpdate, LibraryItem, LibraryItemCreate
from app.services.library_service import LibraryService

router = APIRouter(tags=["library"])


def _service(repository=Depends(get_library_repository)) -> LibraryService:
    return LibraryService(repository)


@router.post("/library", response_model=LibraryItem, status_code=201)
async def create_library_item(payload: LibraryItemCreate, user: UserResponse = Depends(get_current_user), service: LibraryService = Depends(_service)) -> LibraryItem:
    return service.create(user.id, payload)


@router.get("/library", response_model=list[LibraryItem])
async def list_library(user: UserResponse = Depends(get_current_user), service: LibraryService = Depends(_service)) -> list[LibraryItem]:
    return service.list(user.id)


@router.get("/favorites", response_model=list[LibraryItem])
async def list_favorites(user: UserResponse = Depends(get_current_user), service: LibraryService = Depends(_service)) -> list[LibraryItem]:
    return service.list(user.id, favorites_only=True)


@router.get("/history", response_model=list[LibraryItem])
async def list_history(user: UserResponse = Depends(get_current_user), service: LibraryService = Depends(_service)) -> list[LibraryItem]:
    return service.list(user.id, history_only=True)


@router.post("/library/{item_id}/favorite", response_model=LibraryItem)
async def update_favorite(item_id: UUID, payload: FavoriteUpdate, user: UserResponse = Depends(get_current_user), service: LibraryService = Depends(_service)) -> LibraryItem:
    item = service.set_favorite(user.id, item_id, payload)
    if item is None:
        raise HTTPException(status_code=404, detail="Library item not found")
    return item


@router.post("/library/{item_id}/view", response_model=LibraryItem)
async def mark_library_viewed(item_id: UUID, user: UserResponse = Depends(get_current_user), service: LibraryService = Depends(_service)) -> LibraryItem:
    item = service.mark_viewed(user.id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Library item not found")
    return item
