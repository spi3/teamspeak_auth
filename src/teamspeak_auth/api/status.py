"""Status endpoint."""

from fastapi import APIRouter

from ..config import config
from .dependencies import get_auth_service
from .models import StatusResponse

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get the current status of the authorization service.

    Returns information about the service state and cache statistics.
    """
    auth_service = get_auth_service()

    return StatusResponse(
        status="running",
        authorized_users_count=len(auth_service.authorized_ips),
        cache_age_seconds=auth_service.get_cache_age(),
        cache_ttl_seconds=config.cache_ttl,
    )
