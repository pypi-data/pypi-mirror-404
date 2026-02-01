"""
PyStator API - FastAPI Application

REST API for FSM operations using PyStator.

Usage:
    # Development server
    uvicorn pystator.api.main:app --reload

    # Production server
    uvicorn pystator.api.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pystator import __version__ as pystator_version

from pystator.api.routes.v1 import machines, process, settings, templates

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI application."""
    yield


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="PyStator API",
        description="REST API for PyStator FSM operations",
        version=pystator_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()
    cors_origins = (
        [o.strip() for o in cors_origins_env.split(",") if o.strip()]
        if cors_origins_env
        else []
    )
    is_production = os.getenv("ENVIRONMENT") == "production"
    if not cors_origins and not is_production:
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ]
    use_credentials = bool(cors_origins and "*" not in cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],
        allow_credentials=use_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(
        process.router,
        prefix=API_PREFIX,
        tags=["Process"],
    )
    app.include_router(
        machines.router,
        prefix=API_PREFIX,
        tags=["Machines"],
    )
    app.include_router(
        settings.router,
        prefix=API_PREFIX,
        tags=["Settings"],
    )
    app.include_router(
        templates.router,
        prefix=API_PREFIX,
        tags=["Templates"],
    )

    # Root
    @app.get("/", summary="API Information", tags=["General"])
    async def root() -> dict:
        return {
            "name": "PyStator API",
            "version": pystator_version,
            "api_version": API_VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    # Health
    @app.get("/health", summary="Health Check", tags=["General"])
    async def health_check() -> dict:
        return {"status": "healthy", "version": pystator_version}

    # Validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        def serialize_error(error: dict) -> dict:
            serialized = {}
            for key, value in error.items():
                if isinstance(value, Exception):
                    serialized[key] = str(value)
                elif isinstance(value, dict):
                    serialized[key] = serialize_error(value)
                elif isinstance(value, (list, tuple)):
                    serialized[key] = [
                        serialize_error(item) if isinstance(item, dict) else (
                            str(item) if isinstance(item, Exception) else item
                        )
                        for item in value
                    ]
                else:
                    serialized[key] = value
            return serialized

        errors = [serialize_error(err) for err in exc.errors()]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Validation error", "details": errors},
        )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        is_development = os.getenv("ENVIRONMENT") == "development"
        error_detail: dict = {"error": "Internal server error"}
        if is_development:
            error_detail["message"] = str(exc)
            error_detail["type"] = type(exc).__name__
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_detail,
        )

    # OpenAPI schema error handling (Pydantic v2 unhashable workaround)
    original_openapi = app.openapi

    def openapi_with_error_handling():
        try:
            return original_openapi()
        except TypeError as e:
            if "unhashable type" in str(e):
                import logging
                logging.getLogger(__name__).warning(
                    "OpenAPI schema generation issue: %s. Returning minimal schema.", e
                )
                return {
                    "openapi": "3.1.0",
                    "info": {
                        "title": app.title,
                        "version": app.version,
                        "description": app.description,
                    },
                    "paths": {},
                    "components": {"schemas": {}},
                }
            raise

    app.openapi = openapi_with_error_handling

    return app


app = create_application()


def main() -> None:
    """Entry point for running the API server."""
    import uvicorn
    uvicorn.run(
        "pystator.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
