"""Status endpoint."""

from fastapi import APIRouter, Response

from ..config import config
from .dependencies import get_auth_service
from .models import StatusResponse

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status(response: Response):
    """
    Get the current status of the authorization service.

    Returns information about the service state and cache statistics.
    Returns 503 if TeamSpeak is not connected.
    """
    auth_service = get_auth_service()
    is_connected = auth_service.ts_client.connection is not None

    if not is_connected:
        response.status_code = 503

    return StatusResponse(
        status="running" if is_connected else "degraded",
        teamspeak_connected=is_connected,
        authorized_users_count=len(auth_service.authorized_ips),
        cache_age_seconds=auth_service.get_cache_age(),
        cache_ttl_seconds=config.cache_ttl,
    )
