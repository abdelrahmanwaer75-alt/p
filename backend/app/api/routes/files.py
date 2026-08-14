from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException

from app.api.dependencies import get_current_user, get_file_manager
from app.schemas.auth import UserResponse
from app.schemas.files import FileActionResponse, FileInfoResponse, FileItem, FileMoveRequest, FileRenameRequest, FileSort
from app.services.file_service import FileService

router = APIRouter(tags=["files"])


def _service(manager=Depends(get_file_manager)) -> FileService:
    return FileService(manager.library, manager.storage)


@router.get("/files", response_model=list[FileItem])
async def list_files(
    search: str | None = Query(default=None),
    sort: FileSort = Query(default=FileSort.DATE),
    descending: bool = Query(default=True),
    user: UserResponse = Depends(get_current_user),
    service: FileService = Depends(_service),
) -> list[FileItem]:
    return service.list(user.id, search=search, sort=sort.value, descending=descending)


@router.get("/files/{item_id}", response_model=FileInfoResponse)
async def file_info(item_id: UUID, user: UserResponse = Depends(get_current_user), service: FileService = Depends(_service)) -> FileInfoResponse:
    result = service.info(user.id, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.post("/files/{item_id}/rename", response_model=FileActionResponse)
async def rename_file(item_id: UUID, payload: FileRenameRequest, user: UserResponse = Depends(get_current_user), service: FileService = Depends(_service)) -> FileActionResponse:
    try:
        result = service.rename(user.id, item_id, payload.filename)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.post("/files/{item_id}/move", response_model=FileActionResponse)
async def move_file(item_id: UUID, payload: FileMoveRequest, user: UserResponse = Depends(get_current_user), service: FileService = Depends(_service)) -> FileActionResponse:
    try:
        result = service.move(user.id, item_id, payload.folder)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.delete("/files/{item_id}", response_model=FileActionResponse)
async def delete_file(item_id: UUID, user: UserResponse = Depends(get_current_user), service: FileService = Depends(_service)) -> FileActionResponse:
    try:
        result = service.delete(user.id, item_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.post("/files/{item_id}/open", response_model=FileInfoResponse)
async def open_file(item_id: UUID, user: UserResponse = Depends(get_current_user), service: FileService = Depends(_service)) -> FileInfoResponse:
    result = service.open(user.id, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.post("/files/{item_id}/share", response_model=FileInfoResponse)
async def share_file(item_id: UUID, user: UserResponse = Depends(get_current_user), service: FileService = Depends(_service)) -> FileInfoResponse:
    result = service.share(user.id, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result
