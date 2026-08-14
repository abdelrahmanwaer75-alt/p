from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import (
    analyzer_router,
    auth_router,
    downloads_router,
    files_router,
    library_router,
    playlists_router,
    system_router,
    websocket_router,
)
from app.core.config import get_settings
from app.core.security import security_middleware
from app.db import init_database

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("vidora.api")


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    if settings.auto_create_db:
        init_database()
    yield
    logger.info("Stopping %s", settings.app_name)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    application.middleware("http")(security_middleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
    )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = _request_id(request)
        logger.warning("Validation error request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed",
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": jsonable_encoder(exc.errors()),
                    "request_id": request_id,
                },
            },
            headers={"X-Request-ID": request_id},
        )

    @application.exception_handler(HTTPException)
    async def http_exception_json_handler(request: Request, exc: HTTPException):
        request_id = _request_id(request)
        detail = exc.detail if isinstance(exc.detail, str) else "Request rejected"
        code = "unauthorized" if exc.status_code == 401 else "forbidden" if exc.status_code == 403 else "request_rejected"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail, "error": {"code": code, "message": detail, "request_id": request_id}},
            headers={**(exc.headers or {}), "X-Request-ID": request_id},
        )

    @application.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        request_id = _request_id(request)
        logger.exception("Database error request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "database_unavailable", "message": "The service is temporarily unavailable", "request_id": request_id}},
            headers={"X-Request-ID": request_id},
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = _request_id(request)
        logger.exception("Unhandled request error request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Internal server error", "request_id": request_id}},
            headers={"X-Request-ID": request_id},
        )

    api = APIRouter(prefix=settings.api_prefix)
    api.include_router(system_router)
    api.include_router(auth_router)
    api.include_router(analyzer_router)
    api.include_router(downloads_router)
    api.include_router(files_router)
    api.include_router(library_router)
    api.include_router(playlists_router)
    api.include_router(websocket_router)
    application.include_router(api)
    application.include_router(system_router)
    return application


app = create_app()
if settings.auto_create_db:
    init_database()
