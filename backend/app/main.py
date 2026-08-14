import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db import init_database
from uuid import UUID

from app.schemas.analyzer import AnalyzerResult
from app.schemas.auth import (
    ActionMessage,
    EmailVerificationConfirm,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import AnalyzeRequest, HealthResponse, VersionResponse, utc_now
from app.schemas.downloads import DownloadCancelResponse, DownloadTask, DownloadTaskAccepted, DownloadTaskCreate
from app.schemas.files import FileActionResponse, FileInfoResponse, FileItem, FileMoveRequest, FileRenameRequest, FileSort
from app.schemas.playlists import Playlist, PlaylistCreate, PlaylistItemCreate, PlaylistMessage, PlaylistReorder, PlaylistUpdate
from app.schemas.library import FavoriteUpdate, LibraryItem, LibraryItemCreate
from app.repositories.library import LibraryRepository
from app.repositories.playlists import PlaylistRepository
from app.services.analyzer import build_preview
from app.queue import DownloadQueue
from app.repositories.downloads import DownloadRepository
from app.services.auth import (
    bearer,
    confirm_email_verification,
    confirm_password_reset,
    current_user,
    current_user_from_token,
    login,
    logout,
    refresh,
    register,
    request_password_reset,
)
from app.services.downloads import get_download_service
from app.services.files import FileManagerService
from app.security import security_middleware

settings = get_settings()
library_repository = LibraryRepository()
file_manager = FileManagerService(library_repository)
playlist_repository = PlaylistRepository()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("vidora.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    if settings.auto_create_db:
        init_database()
    yield
    logger.info("Stopping %s", settings.app_name)


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
if settings.auto_create_db:
    init_database()
app.middleware("http")(security_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
)

api = APIRouter(prefix=settings.api_prefix)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("Validation error request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": "Request validation failed", "details": jsonable_encoder(exc.errors()), "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_json_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    detail = exc.detail if isinstance(exc.detail, str) else "Request rejected"
    code = "unauthorized" if exc.status_code == 401 else "forbidden" if exc.status_code == 403 else "request_rejected"
    return JSONResponse(status_code=exc.status_code, content={"detail": detail, "error": {"code": code, "message": detail, "request_id": request_id}}, headers={**(exc.headers or {}), "X-Request-ID": request_id})


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Database error request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "database_unavailable", "message": "The service is temporarily unavailable", "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled request error request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Internal server error", "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, environment=settings.environment, timestamp=utc_now())


@api.get("/version", response_model=VersionResponse, tags=["system"])
async def version() -> VersionResponse:
    return VersionResponse(name=settings.app_name, version=app.version, api_prefix=settings.api_prefix)


@api.post("/auth/register", response_model=UserResponse, status_code=201, tags=["auth"])
async def register_account(payload: RegisterRequest) -> UserResponse:
    return register(payload)


@api.post("/auth/login", response_model=TokenResponse, tags=["auth"])
async def login_account(payload: LoginRequest, request: Request) -> TokenResponse:
    return login(payload, user_agent=request.headers.get("user-agent"), ip_address=request.client.host if request.client else None)


@api.post("/auth/refresh", response_model=TokenResponse, tags=["auth"])
async def refresh_tokens(payload: RefreshTokenRequest, request: Request) -> TokenResponse:
    return refresh(payload.refresh_token, user_agent=request.headers.get("user-agent"), ip_address=request.client.host if request.client else None)


@api.post("/auth/password-reset/request", response_model=ActionMessage, tags=["auth"])
async def password_reset_request(payload: PasswordResetRequest) -> ActionMessage:
    request_password_reset(payload)
    return ActionMessage(message="If the account exists, password reset instructions will be sent")


@api.post("/auth/password-reset/confirm", response_model=ActionMessage, tags=["auth"])
async def password_reset_confirmation(payload: PasswordResetConfirm) -> ActionMessage:
    confirm_password_reset(payload)
    return ActionMessage(message="Password reset completed")


@api.post("/auth/verify-email", response_model=ActionMessage, tags=["auth"])
async def verify_email(payload: EmailVerificationConfirm) -> ActionMessage:
    confirm_email_verification(payload)
    return ActionMessage(message="Email verified successfully")


@api.get("/user/me", response_model=UserResponse, tags=["auth"])
@api.get("/auth/me", response_model=UserResponse, tags=["auth"])
async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> UserResponse:
    user = current_user(credentials)
    request.state.user_id = str(user.id)
    return user


@api.post("/auth/logout", response_model=ActionMessage, tags=["auth"])
async def logout_account(payload: LogoutRequest, user: UserResponse = Depends(get_current_user)) -> ActionMessage:
    logout(payload.refresh_token, user.id)
    return ActionMessage(message="Logged out successfully")


@api.post("/analyze", response_model=AnalyzerResult, tags=["analyzer"])
@api.post("/analyzer/preview", response_model=AnalyzerResult, tags=["analyzer"])
async def analyzer_preview(payload: AnalyzeRequest) -> AnalyzerResult:
    """Validate a public URL and identify its platform without fetching content."""
    return await build_preview(str(payload.url))


@api.get("/playlists", response_model=list[Playlist], tags=["playlists"])
async def list_playlists(user: UserResponse = Depends(get_current_user)) -> list[Playlist]:
    return playlist_repository.list(user.id)


@api.post("/playlists", response_model=Playlist, status_code=201, tags=["playlists"])
async def create_playlist(payload: PlaylistCreate, user: UserResponse = Depends(get_current_user)) -> Playlist:
    return playlist_repository.create(user.id, payload)


@api.get("/playlists/{playlist_id}", response_model=Playlist, tags=["playlists"])
async def get_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user)) -> Playlist:
    playlist = playlist_repository.get(user.id, playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


@api.patch("/playlists/{playlist_id}", response_model=Playlist, tags=["playlists"])
async def update_playlist(playlist_id: UUID, payload: PlaylistUpdate, user: UserResponse = Depends(get_current_user)) -> Playlist:
    playlist = playlist_repository.update(user.id, playlist_id, payload)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


@api.delete("/playlists/{playlist_id}", response_model=Playlist, tags=["playlists"])
async def delete_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user)) -> Playlist:
    playlist = playlist_repository.delete(user.id, playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


@api.post("/playlists/{playlist_id}/items", response_model=Playlist, tags=["playlists"])
async def add_playlist_item(playlist_id: UUID, payload: PlaylistItemCreate, user: UserResponse = Depends(get_current_user)) -> Playlist:
    playlist = playlist_repository.add_item(user.id, playlist_id, payload)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist or library item not found")
    return playlist


@api.delete("/playlists/{playlist_id}/items/{item_id}", response_model=Playlist, tags=["playlists"])
async def remove_playlist_item(playlist_id: UUID, item_id: UUID, user: UserResponse = Depends(get_current_user)) -> Playlist:
    playlist = playlist_repository.remove_item(user.id, playlist_id, item_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist or item not found")
    return playlist


@api.post("/playlists/{playlist_id}/reorder", response_model=Playlist, tags=["playlists"])
async def reorder_playlist(playlist_id: UUID, payload: PlaylistReorder, user: UserResponse = Depends(get_current_user)) -> Playlist:
    playlist = playlist_repository.reorder(user.id, playlist_id, payload.item_ids)
    if playlist is None:
        raise HTTPException(status_code=400, detail="Playlist item order is invalid")
    return playlist


@api.post("/playlists/{playlist_id}/play", response_model=Playlist, tags=["playlists"])
async def play_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user)) -> Playlist:
    playlist = playlist_repository.get(user.id, playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


@api.post("/playlists/{playlist_id}/download", response_model=PlaylistMessage, status_code=202, tags=["playlists"])
async def download_playlist(playlist_id: UUID, user: UserResponse = Depends(get_current_user)) -> PlaylistMessage:
    playlist = playlist_repository.get(user.id, playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    raise HTTPException(status_code=501, detail="FEATURE_NOT_AVAILABLE: playlist downloads require an approved extractor implementation")


@api.post("/library", response_model=LibraryItem, status_code=201, tags=["library"])
async def create_library_item(payload: LibraryItemCreate, user: UserResponse = Depends(get_current_user)) -> LibraryItem:
    return library_repository.create(user.id, payload)


@api.get("/library", response_model=list[LibraryItem], tags=["library"])
async def list_library(user: UserResponse = Depends(get_current_user)) -> list[LibraryItem]:
    return library_repository.list(user.id)


@api.get("/files", response_model=list[FileItem], tags=["files"])
async def list_files(
    search: str | None = Query(default=None, max_length=200),
    sort: FileSort = FileSort.DATE,
    descending: bool = True,
    user: UserResponse = Depends(get_current_user),
) -> list[FileItem]:
    return file_manager.list(user.id, search=search, sort=sort.value, descending=descending)


@api.get("/files/{item_id}", response_model=FileInfoResponse, tags=["files"])
async def file_info(item_id: UUID, user: UserResponse = Depends(get_current_user)) -> FileInfoResponse:
    result = file_manager.info(user.id, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@api.post("/files/{item_id}/rename", response_model=FileActionResponse, tags=["files"])
async def rename_file(item_id: UUID, payload: FileRenameRequest, user: UserResponse = Depends(get_current_user)) -> FileActionResponse:
    try:
        result = file_manager.rename(user.id, item_id, payload.filename)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@api.post("/files/{item_id}/move", response_model=FileActionResponse, tags=["files"])
async def move_file(item_id: UUID, payload: FileMoveRequest, user: UserResponse = Depends(get_current_user)) -> FileActionResponse:
    try:
        result = file_manager.move(user.id, item_id, payload.folder)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@api.delete("/files/{item_id}", response_model=FileActionResponse, tags=["files"])
async def delete_file(item_id: UUID, user: UserResponse = Depends(get_current_user)) -> FileActionResponse:
    try:
        result = file_manager.delete(user.id, item_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@api.post("/files/{item_id}/open", response_model=FileInfoResponse, tags=["files"])
async def open_file(item_id: UUID, user: UserResponse = Depends(get_current_user)) -> FileInfoResponse:
    result = file_manager.open(user.id, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@api.post("/files/{item_id}/share", response_model=FileInfoResponse, tags=["files"])
async def share_file(item_id: UUID, user: UserResponse = Depends(get_current_user)) -> FileInfoResponse:
    result = file_manager.share(user.id, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@api.get("/favorites", response_model=list[LibraryItem], tags=["library"])
async def list_favorites(user: UserResponse = Depends(get_current_user)) -> list[LibraryItem]:
    return library_repository.list(user.id, favorites_only=True)


@api.get("/history", response_model=list[LibraryItem], tags=["library"])
async def list_history(user: UserResponse = Depends(get_current_user)) -> list[LibraryItem]:
    return library_repository.list(user.id, history_only=True)


@api.post("/library/{item_id}/favorite", response_model=LibraryItem, tags=["library"])
async def update_favorite(item_id: UUID, payload: FavoriteUpdate, user: UserResponse = Depends(get_current_user)) -> LibraryItem:
    item = library_repository.set_favorite(user.id, item_id, payload.favorite)
    if item is None:
        raise HTTPException(status_code=404, detail="Library item not found")
    return item


@api.post("/library/{item_id}/view", response_model=LibraryItem, tags=["library"])
async def mark_library_viewed(item_id: UUID, user: UserResponse = Depends(get_current_user)) -> LibraryItem:
    item = library_repository.mark_viewed(user.id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Library item not found")
    return item


@api.post("/downloads", response_model=DownloadTaskAccepted, status_code=202, tags=["downloads"])
async def create_download(
    payload: DownloadTaskCreate,
    user: UserResponse = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> DownloadTaskAccepted:
    task = get_download_service().create(payload, user.id, idempotency_key=idempotency_key)
    return DownloadTaskAccepted(task=task, message="Download queued for the authenticated account. A background worker will process it when an authorized adapter is available.")


@api.get("/downloads", response_model=list[DownloadTask], tags=["downloads"])
async def list_downloads(user: UserResponse = Depends(get_current_user)) -> list[DownloadTask]:
    return get_download_service().list(user.id)


@api.get("/downloads/{task_id}", response_model=DownloadTask, tags=["downloads"])
async def get_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().get(task_id, user.id)


@api.post("/downloads/{task_id}/run", response_model=DownloadTask, tags=["downloads"])
async def run_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().requeue(task_id, user.id)


@api.post("/downloads/{task_id}/cancel", response_model=DownloadCancelResponse, tags=["downloads"])
async def cancel_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadCancelResponse:
    task = get_download_service().cancel(task_id, user.id)
    return DownloadCancelResponse(task=task, message=f"Download is {task.status.value}")


@api.post("/downloads/{task_id}/pause", response_model=DownloadTask, tags=["downloads"])
async def pause_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().pause(task_id, user.id)


@api.post("/downloads/{task_id}/resume", response_model=DownloadTask, tags=["downloads"])
async def resume_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().resume(task_id, user.id)


@api.post("/downloads/{task_id}/retry", response_model=DownloadTask, tags=["downloads"])
async def retry_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().retry(task_id, user.id)


@api.post("/downloads/{task_id}/open", response_model=DownloadTask, tags=["downloads"])
async def open_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().open(task_id, user.id)


@api.delete("/downloads/{task_id}", response_model=DownloadTask, tags=["downloads"])
async def delete_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().delete(task_id, user.id)


@app.websocket("/api/v1/ws/downloads")
async def download_events(websocket: WebSocket) -> None:
    authorization = websocket.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        await websocket.close(code=4401)
        return
    try:
        user = current_user_from_token(authorization[7:].strip())
    except HTTPException:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    queue = DownloadQueue()
    repository = DownloadRepository()
    last_id = "$"
    try:
        while True:
            response = await asyncio.to_thread(queue.redis.xread, {queue.event_stream: last_id}, count=50, block=25_000)
            if not response:
                await websocket.send_json({"event": "heartbeat"})
                continue
            _, messages = response[0]
            for message_id, fields in messages:
                last_id = message_id
                task_id = fields.get("task_id")
                if not task_id:
                    continue
                task = repository.get_any(UUID(task_id))
                if task is None or task.owner_id != user.id:
                    continue
                payload = {"task_id": task_id, "event": fields.get("event", "download.updated")}
                for key, value in fields.items():
                    if key not in {"task_id", "event", "published_at"}:
                        payload[key] = value
                await websocket.send_json(payload)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close(code=1011)


app.include_router(api)
