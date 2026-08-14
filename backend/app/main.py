import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.schemas.common import AnalyzeRequest, AnalyzeResponse, HealthResponse, VersionResponse, utc_now

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


@api.post("/analyzer/preview", response_model=AnalyzeResponse, status_code=202, tags=["analyzer"])
async def analyzer_preview(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Validate a URL without fetching it.

    Actual platform extraction belongs to a later phase and must be implemented
    behind a dedicated, policy-aware service abstraction.
    """
    return AnalyzeResponse(
        status="accepted",
        message="URL validated. Platform analysis service is not enabled in this phase.",
        url=payload.url,
    )


app.include_router(api)
