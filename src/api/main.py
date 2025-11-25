"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import factors, health, screening
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting Vietnam Quant Platform API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    yield

    # Shutdown
    logger.info("Shutting down Vietnam Quant Platform API")


# Create FastAPI application
app = FastAPI(
    title="Vietnam Quant Platform API",
    description="Quantitative investment research and trading platform for Vietnam stock market",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc) -> JSONResponse:  # type: ignore
    """Global exception handler.

    Args:
        request: Request object
        exc: Exception

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(screening.router, prefix="/api/v1", tags=["Screening"])
app.include_router(factors.router, prefix="/api/v1", tags=["Factors"])


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint.

    Returns:
        API information
    """
    return {
        "name": "Vietnam Quant Platform API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
