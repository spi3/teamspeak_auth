"""Authentication endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from .dependencies import get_auth_service
from .models import AuthResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("")
@router.post("")
@router.put("")
@router.delete("")
@router.patch("")
@router.head("")
async def forward_auth(request: Request):
    """
    ForwardAuth endpoint compatible with reverse proxies like Traefik.

    This endpoint is designed to work with Traefik's ForwardAuth middleware
    and other reverse proxy authentication systems.

    Returns:
        - 200 OK: If the requesting IP is authorized
        - 403 Forbidden: If the requesting IP is not authorized
        - 503 Service Unavailable: If the auth service is not available

    The client IP is extracted from X-Forwarded-For header (for reverse proxies)
    or falls back to the direct client IP.
    """
    auth_service = get_auth_service()

    # Extract client IP from X-Forwarded-For header or direct connection
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one (original client)
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        # Fallback to direct client IP
        client_ip = request.client.host

    # Check authorization
    is_authorized = auth_service.is_authorized(client_ip)

    if is_authorized:
        user_info = auth_service.get_authorized_user_info(client_ip)

        nickname = "localuser"
        if user_info:
            nickname = user_info.get("nickname")

        logger.info(f"Authorized request from {client_ip} (user: {nickname})")

        # Return 200 OK with user information in headers and body
        return JSONResponse(
            status_code=200,
            content={
                "status": "authorized",
                "ip": client_ip,
                "user": nickname,
            },
            headers={
                "X-Auth-User": nickname,
            },
        )
    else:
        logger.warning(f"Unauthorized request from {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden: IP address not authorized")


@router.get("/check", response_model=AuthResponse)
async def check_auth(request: Request):
    """
    Check if the requesting IP address is authorized.

    The IP address is automatically extracted from the request.
    """
    auth_service = get_auth_service()

    # Get client IP from request
    client_ip = request.client.host

    is_authorized = auth_service.is_authorized(client_ip)
    user_info = None

    if is_authorized:
        user_info = auth_service.get_authorized_user_info(client_ip)

    return AuthResponse(
        authorized=is_authorized,
        ip_address=client_ip,
        user_info=user_info,
    )


@router.get("/check/{ip_address}", response_model=AuthResponse)
async def check_auth_by_ip(ip_address: str):
    """
    Check if a specific IP address is authorized.

    Args:
        ip_address: The IP address to check.
    """
    auth_service = get_auth_service()

    is_authorized = auth_service.is_authorized(ip_address)
    user_info = None

    if is_authorized:
        user_info = auth_service.get_authorized_user_info(ip_address)

    return AuthResponse(
        authorized=is_authorized,
        ip_address=ip_address,
        user_info=user_info,
    )


@router.post("/refresh", response_model=dict)
async def refresh_auth():
    """
    Manually trigger a refresh of authorized users from TeamSpeak.

    This endpoint forces an immediate update instead of waiting for the
    scheduled cache refresh.
    """
    auth_service = get_auth_service()

    await auth_service.update_authorized_users()

    return {
        "status": "refreshed",
        "authorized_users_count": len(auth_service.authorized_ips),
        "cache_age_seconds": auth_service.get_cache_age(),
    }
