"""OvenMediaEngine Admission Webhook endpoint."""

import logging

from fastapi import APIRouter

from .dependencies import get_auth_service
from .models import OMEAdmissionRequest, OMEAdmissionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ome", tags=["ome"])


@router.post("/admission")
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
    auth_service = get_auth_service()

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
