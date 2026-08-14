from fastapi import APIRouter

from app.schemas.common import HealthResponse, VersionResponse, utc_now

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    from app.core.config import get_settings

    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, environment=settings.environment, timestamp=utc_now())


@router.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    from app.core.config import get_settings

    settings = get_settings()
    return VersionResponse(name=settings.app_name, version="0.1.0", api_prefix=settings.api_prefix)
