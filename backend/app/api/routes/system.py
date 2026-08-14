from fastapi import APIRouter, Response

from app.schemas.common import HealthResponse, ReadinessResponse, VersionResponse, utc_now
from app.services.readiness_service import ReadinessService

router = APIRouter(tags=["system"])
readiness_service = ReadinessService()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    from app.core.config import get_settings

    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, environment=settings.environment, timestamp=utc_now())


@router.get("/ready", response_model=ReadinessResponse)
async def ready(response: Response) -> ReadinessResponse:
    result = readiness_service.check()
    if result["status"] != "ready":
        response.status_code = 503
    return ReadinessResponse(timestamp=utc_now(), **result)


@router.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    from app.core.config import get_settings

    settings = get_settings()
    return VersionResponse(name=settings.app_name, version="0.1.0", api_prefix=settings.api_prefix)
