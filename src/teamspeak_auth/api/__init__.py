"""FastAPI server for authorization queries."""

import logging

from fastapi import FastAPI

from ..auth_service import AuthorizationService
from . import dependencies
from .auth import router as auth_router
from .ome import router as ome_router
from .root import router as root_router
from .status import router as status_router

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TeamSpeak Auth API",
    description="Authorization service based on TeamSpeak server connections and permissions",
    version="0.1.0",
)

# Register routers
app.include_router(root_router)
app.include_router(auth_router)
app.include_router(status_router)
app.include_router(ome_router)


@app.on_event("startup")
async def startup_event():
    """Initialize the authorization service on startup."""
    logger.info("Starting up FastAPI application")

    dependencies.auth_service = AuthorizationService()
    await dependencies.auth_service.start()

    logger.info("FastAPI application started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down FastAPI application")

    if dependencies.auth_service:
        await dependencies.auth_service.stop()

    logger.info("FastAPI application shut down")
