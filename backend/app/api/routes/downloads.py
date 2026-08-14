from uuid import UUID

from fastapi import APIRouter, Depends, Header

from app.api.dependencies import get_current_user, get_download_service_dependency
from app.schemas.auth import UserResponse
from app.schemas.downloads import DownloadCancelResponse, DownloadTask, DownloadTaskAccepted, DownloadTaskCreate
from app.services.downloads import DownloadService

router = APIRouter(tags=["downloads"])


@router.post("/downloads", response_model=DownloadTaskAccepted, status_code=202)
async def create_download(
    payload: DownloadTaskCreate,
    user: UserResponse = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: DownloadService = Depends(get_download_service_dependency),
) -> DownloadTaskAccepted:
    task = service.create(payload, user.id, idempotency_key=idempotency_key)
    return DownloadTaskAccepted(task=task, message="Download queued for the authenticated account. A background worker will process it when an authorized adapter is available.")


@router.get("/downloads", response_model=list[DownloadTask])
async def list_downloads(user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> list[DownloadTask]:
    return service.list(user.id)


@router.get("/downloads/{task_id}", response_model=DownloadTask)
async def get_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadTask:
    return service.get(task_id, user.id)


@router.post("/downloads/{task_id}/run", response_model=DownloadTask)
async def run_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadTask:
    return service.requeue(task_id, user.id)


@router.post("/downloads/{task_id}/cancel", response_model=DownloadCancelResponse)
async def cancel_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadCancelResponse:
    task = service.cancel(task_id, user.id)
    return DownloadCancelResponse(task=task, message=f"Download is {task.status.value}")


@router.post("/downloads/{task_id}/pause", response_model=DownloadTask)
async def pause_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadTask:
    return service.pause(task_id, user.id)


@router.post("/downloads/{task_id}/resume", response_model=DownloadTask)
async def resume_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadTask:
    return service.resume(task_id, user.id)


@router.post("/downloads/{task_id}/retry", response_model=DownloadTask)
async def retry_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadTask:
    return service.retry(task_id, user.id)


@router.post("/downloads/{task_id}/open", response_model=DownloadTask)
async def open_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadTask:
    return service.open(task_id, user.id)


@router.delete("/downloads/{task_id}", response_model=DownloadTask)
async def delete_download(task_id: UUID, user: UserResponse = Depends(get_current_user), service: DownloadService = Depends(get_download_service_dependency)) -> DownloadTask:
    return service.delete(task_id, user.id)
