"""Root endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "service": "TeamSpeak Auth API",
        "version": "0.1.0",
        "endpoints": {
            "/auth": "ForwardAuth endpoint for reverse proxies (Traefik, etc.)",
            "/auth/check": "Check if requesting IP is authorized",
            "/auth/check/{ip}": "Check if specific IP is authorized",
            "/ome/admission": "OvenMediaEngine Admission Webhook endpoint",
            "/status": "Service status and statistics",
        },
    }
