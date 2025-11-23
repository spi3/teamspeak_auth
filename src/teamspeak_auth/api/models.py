"""Pydantic models for API requests and responses."""

from pydantic import BaseModel


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
