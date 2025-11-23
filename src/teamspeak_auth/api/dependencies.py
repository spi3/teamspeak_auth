"""Shared dependencies for API endpoints."""

from fastapi import HTTPException

from ..auth_service import AuthorizationService

# Global authorization service instance
auth_service: AuthorizationService | None = None


def get_auth_service() -> AuthorizationService:
    """Get the authorization service, raising an error if not available."""
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authorization service not available")
    return auth_service
