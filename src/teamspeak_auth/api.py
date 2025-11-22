"""FastAPI server for authorization queries."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .auth_service import AuthorizationService
from .config import config

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TeamSpeak Auth API",
    description="Authorization service based on TeamSpeak server connections and permissions",
    version="0.1.0",
)

# Global authorization service instance
auth_service: AuthorizationService | None = None


class AuthResponse(BaseModel):
    """Response model for authorization check."""

    authorized: bool
    ip_address: str
    user_info: dict | None = None


class StatusResponse(BaseModel):
    """Response model for service status."""

    status: str
    authorized_users_count: int
    cache_age_seconds: float
    cache_ttl_seconds: int


# OvenMediaEngine Admission Webhook models
class OMEClientInfo(BaseModel):
    """Client information from OvenMediaEngine webhook."""

    address: str
    port: int
    real_ip: str | None = None
    user_agent: str | None = None


class OMERequestInfo(BaseModel):
    """Request information from OvenMediaEngine webhook."""

    direction: str  # "incoming" (publish) or "outgoing" (playback)
    protocol: str  # "webrtc", "rtmp", "srt", "llhls", "thumbnail"
    status: str  # "opening" or "closing"
    url: str
    new_url: str | None = None
    time: str  # ISO8601 timestamp


class OMEAdmissionRequest(BaseModel):
    """Request model for OvenMediaEngine Admission Webhook."""

    client: OMEClientInfo
    request: OMERequestInfo


class OMEAdmissionResponse(BaseModel):
    """Response model for OvenMediaEngine Admission Webhook."""

    allowed: bool | None = None
    new_url: str | None = None
    lifetime: int | None = None  # milliseconds, 0 = infinity
    reason: str | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize the authorization service on startup."""
    global auth_service
    logger.info("Starting up FastAPI application")

    auth_service = AuthorizationService()
    await auth_service.start()

    logger.info("FastAPI application started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global auth_service
    logger.info("Shutting down FastAPI application")

    if auth_service:
        await auth_service.stop()

    logger.info("FastAPI application shut down")


@app.get("/", response_model=dict)
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


@app.get("/auth")
@app.post("/auth")
@app.put("/auth")
@app.delete("/auth")
@app.patch("/auth")
@app.head("/auth")
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
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authorization service not available")

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


@app.get("/auth/check", response_model=AuthResponse)
async def check_auth(request: Request):
    """
    Check if the requesting IP address is authorized.

    The IP address is automatically extracted from the request.
    """
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authorization service not available")

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


@app.get("/auth/check/{ip_address}", response_model=AuthResponse)
async def check_auth_by_ip(ip_address: str):
    """
    Check if a specific IP address is authorized.

    Args:
        ip_address: The IP address to check.
    """
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authorization service not available")

    is_authorized = auth_service.is_authorized(ip_address)
    user_info = None

    if is_authorized:
        user_info = auth_service.get_authorized_user_info(ip_address)

    return AuthResponse(
        authorized=is_authorized,
        ip_address=ip_address,
        user_info=user_info,
    )


@app.post("/auth/refresh", response_model=dict)
async def refresh_auth():
    """
    Manually trigger a refresh of authorized users from TeamSpeak.

    This endpoint forces an immediate update instead of waiting for the
    scheduled cache refresh.
    """
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authorization service not available")

    await auth_service.update_authorized_users()

    return {
        "status": "refreshed",
        "authorized_users_count": len(auth_service.authorized_ips),
        "cache_age_seconds": auth_service.get_cache_age(),
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get the current status of the authorization service.

    Returns information about the service state and cache statistics.
    """
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authorization service not available")

    return StatusResponse(
        status="running",
        authorized_users_count=len(auth_service.authorized_ips),
        cache_age_seconds=auth_service.get_cache_age(),
        cache_ttl_seconds=config.cache_ttl,
    )


@app.post("/ome/admission")
async def ome_admission_webhook(payload: OMEAdmissionRequest):
    """
    OvenMediaEngine Admission Webhook endpoint.

    This endpoint implements the OvenMediaEngine Admission Webhooks spec:
    https://docs.ovenmediaengine.com/access-control/admission-webhooks

    For "opening" requests, checks if the client IP is authorized and returns
    an appropriate response. For "closing" requests, returns an empty object.

    Returns:
        - For opening: {"allowed": true/false, "reason": "..."}
        - For closing: {}
    """
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authorization service not available")

    # For closing status, return empty object
    if payload.request.status == "closing":
        logger.debug(
            f"OME closing: {payload.client.address} - {payload.request.direction} "
            f"{payload.request.protocol} {payload.request.url}"
        )
        return {}

    # For opening status, check authorization
    # Use real_ip if available (forwarded), otherwise use address
    client_ip = payload.client.real_ip or payload.client.address

    is_authorized = auth_service.is_authorized(client_ip)

    if is_authorized:
        user_info = auth_service.get_authorized_user_info(client_ip)
        nickname = user_info.get("nickname") if user_info else "localuser"

        logger.info(
            f"OME authorized: {client_ip} (user: {nickname}) - {payload.request.direction} "
            f"{payload.request.protocol} {payload.request.url}"
        )

        return OMEAdmissionResponse(
            allowed=True,
            lifetime=0,  # No timeout
        )
    else:
        logger.warning(
            f"OME rejected: {client_ip} - {payload.request.direction} "
            f"{payload.request.protocol} {payload.request.url}"
        )

        return OMEAdmissionResponse(
            allowed=False,
            reason="IP address not authorized",
        )
