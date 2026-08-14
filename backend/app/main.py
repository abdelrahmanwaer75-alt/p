import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from uuid import UUID

from app.schemas.analyzer import AnalyzerResult
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.common import AnalyzeRequest, HealthResponse, VersionResponse, utc_now
from app.schemas.downloads import DownloadTask, DownloadTaskAccepted, DownloadTaskCreate
from app.schemas.library import FavoriteUpdate, LibraryItem, LibraryItemCreate
from app.repositories.library import LibraryRepository
from app.services.analyzer import build_preview
from app.services.auth import bearer, current_user, login, register
from app.services.downloads import get_download_service

settings = get_settings()
library_repository = LibraryRepository(settings.download_db_path)
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("vidora.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    yield
    logger.info("Stopping %s", settings.app_name)


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

api = APIRouter(prefix=settings.api_prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled request error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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
async def login_account(payload: LoginRequest) -> TokenResponse:
    return login(payload)


@api.get("/user/me", response_model=UserResponse, tags=["auth"])
@api.get("/auth/me", response_model=UserResponse, tags=["auth"])
async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> UserResponse:
    return current_user(credentials)


@api.post("/analyze", response_model=AnalyzerResult, tags=["analyzer"])
@api.post("/analyzer/preview", response_model=AnalyzerResult, tags=["analyzer"])
async def analyzer_preview(payload: AnalyzeRequest) -> AnalyzerResult:
    """Validate a public URL and identify its platform without fetching content."""
    return build_preview(str(payload.url))


@api.post("/library", response_model=LibraryItem, status_code=201, tags=["library"])
async def create_library_item(payload: LibraryItemCreate, user: UserResponse = Depends(get_current_user)) -> LibraryItem:
    return library_repository.create(user.id, payload)


@api.get("/library", response_model=list[LibraryItem], tags=["library"])
async def list_library(user: UserResponse = Depends(get_current_user)) -> list[LibraryItem]:
    return library_repository.list(user.id)


@api.get("/files", response_model=list[LibraryItem], tags=["library"])
async def list_files(user: UserResponse = Depends(get_current_user)) -> list[LibraryItem]:
    return library_repository.list(user.id, files_only=True)


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
async def create_download(payload: DownloadTaskCreate, user: UserResponse = Depends(get_current_user)) -> DownloadTaskAccepted:
    task = get_download_service().create(payload, user.id)
    return DownloadTaskAccepted(task=task, message="Download queued for the authenticated account. A background worker will process it when an authorized adapter is available.")


@api.get("/downloads", response_model=list[DownloadTask], tags=["downloads"])
async def list_downloads(user: UserResponse = Depends(get_current_user)) -> list[DownloadTask]:
    return get_download_service().list(user.id)


@api.get("/downloads/{task_id}", response_model=DownloadTask, tags=["downloads"])
async def get_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return get_download_service().get(task_id, user.id)


@api.post("/downloads/{task_id}/run", response_model=DownloadTask, tags=["downloads"])
async def run_download(task_id: UUID, user: UserResponse = Depends(get_current_user)) -> DownloadTask:
    return await get_download_service().run(task_id, user.id)


app.include_router(api)
