import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from uuid import UUID

from app.schemas.analyzer import AnalyzerResult
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.common import AnalyzeRequest, HealthResponse, VersionResponse, utc_now
from app.schemas.downloads import DownloadTask, DownloadTaskAccepted, DownloadTaskCreate
from app.services.analyzer import build_preview
from app.services.auth import bearer, current_user, login, register
from app.services.downloads import get_download_service

settings = get_settings()
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


@api.get("/auth/me", response_model=UserResponse, tags=["auth"])
async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> UserResponse:
    return current_user(credentials)


@api.post("/analyzer/preview", response_model=AnalyzerResult, tags=["analyzer"])
async def analyzer_preview(payload: AnalyzeRequest) -> AnalyzerResult:
    """Validate a public URL and identify its platform without fetching content."""
    return build_preview(str(payload.url))


@api.post("/downloads", response_model=DownloadTaskAccepted, status_code=202, tags=["downloads"])
async def create_download(payload: DownloadTaskCreate) -> DownloadTaskAccepted:
    task = get_download_service().create(payload)
    return DownloadTaskAccepted(task=task, message="Download queued. No worker adapter is enabled in this phase.")


@api.get("/downloads", response_model=list[DownloadTask], tags=["downloads"])
async def list_downloads() -> list[DownloadTask]:
    return get_download_service().list()


@api.get("/downloads/{task_id}", response_model=DownloadTask, tags=["downloads"])
async def get_download(task_id: UUID) -> DownloadTask:
    return get_download_service().get(task_id)


@api.post("/downloads/{task_id}/run", response_model=DownloadTask, tags=["downloads"])
async def run_download(task_id: UUID) -> DownloadTask:
    return await get_download_service().run(task_id)


app.include_router(api)
