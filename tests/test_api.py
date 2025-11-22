"""Tests for API endpoints."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from teamspeak_auth.api import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Create a mock authorization service."""
    mock_service = Mock()
    mock_service.is_authorized.return_value = False
    mock_service.get_authorized_user_info.return_value = None
    mock_service.authorized_ips = {}
    mock_service.get_cache_age.return_value = 10.5
    return mock_service


def test_root_endpoint(client):
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "TeamSpeak Auth API"
    assert "endpoints" in data
    assert "/auth" in data["endpoints"]


def test_auth_endpoint_unauthorized(client, mock_auth_service):
    """Test /auth endpoint returns 403 for unauthorized IP."""
    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.get("/auth")
        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]


def test_auth_endpoint_authorized(client, mock_auth_service):
    """Test /auth endpoint returns 200 for authorized IP."""
    mock_auth_service.is_authorized.return_value = True
    mock_auth_service.get_authorized_user_info.return_value = {
        "nickname": "TestUser",
        "groups": ["6"],
    }

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.get("/auth")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "authorized"
        assert data["user"] == "TestUser"

        # Check that X-Auth-User header is set
        assert "X-Auth-User" in response.headers
        assert response.headers["X-Auth-User"] == "TestUser"


def test_auth_endpoint_authorized_via_subnet(client, mock_auth_service):
    """Test /auth endpoint returns 200 for subnet-authorized IP with default nickname."""
    mock_auth_service.is_authorized.return_value = True
    mock_auth_service.get_authorized_user_info.return_value = None  # No TeamSpeak user info

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.get("/auth")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "authorized"
        assert data["user"] == "localuser"

        # Check that X-Auth-User header is set with default nickname
        assert "X-Auth-User" in response.headers
        assert response.headers["X-Auth-User"] == "localuser"


def test_auth_endpoint_with_x_forwarded_for(client, mock_auth_service):
    """Test /auth endpoint uses X-Forwarded-For header."""
    mock_auth_service.is_authorized.return_value = True
    mock_auth_service.get_authorized_user_info.return_value = {
        "nickname": "TestUser",
        "groups": ["6"],
    }

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.get("/auth", headers={"X-Forwarded-For": "192.168.1.100"})
        assert response.status_code == 200

        # Verify the service was called with the forwarded IP
        mock_auth_service.is_authorized.assert_called_with("192.168.1.100")


def test_auth_check_endpoint(client, mock_auth_service):
    """Test /auth/check endpoint returns authorization status."""
    mock_auth_service.is_authorized.return_value = False

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.get("/auth/check")
        assert response.status_code == 200

        data = response.json()
        assert data["authorized"] is False
        assert "ip_address" in data


def test_auth_check_by_ip_endpoint(client, mock_auth_service):
    """Test /auth/check/{ip} endpoint checks specific IP."""
    mock_auth_service.is_authorized.return_value = True
    mock_auth_service.get_authorized_user_info.return_value = {
        "nickname": "TestUser",
        "groups": ["6", "9"],
    }

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.get("/auth/check/192.168.1.50")
        assert response.status_code == 200

        data = response.json()
        assert data["authorized"] is True
        assert data["ip_address"] == "192.168.1.50"
        assert data["user_info"]["nickname"] == "TestUser"


def test_status_endpoint(client, mock_auth_service):
    """Test /status endpoint returns service status."""
    mock_auth_service.authorized_ips = {"192.168.1.1": {}, "192.168.1.2": {}}
    mock_auth_service.get_cache_age.return_value = 15.3

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        with patch("teamspeak_auth.api.config") as mock_config:
            mock_config.cache_ttl = 30

            response = client.get("/status")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "running"
            assert data["authorized_users_count"] == 2
            assert data["cache_age_seconds"] == 15.3
            assert data["cache_ttl_seconds"] == 30


def test_ome_admission_opening_authorized(client, mock_auth_service):
    """Test OME admission webhook allows authorized IP."""
    mock_auth_service.is_authorized.return_value = True
    mock_auth_service.get_authorized_user_info.return_value = {
        "nickname": "TestUser",
        "groups": ["6"],
    }

    payload = {
        "client": {
            "address": "192.168.1.100",
            "port": 12345,
        },
        "request": {
            "direction": "outgoing",
            "protocol": "webrtc",
            "status": "opening",
            "url": "ws://stream.example.com:3333/app/stream",
            "time": "2025-11-21T00:00:00Z",
        },
    }

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.post("/ome/admission", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["allowed"] is True
        assert data["lifetime"] == 0


def test_ome_admission_opening_unauthorized(client, mock_auth_service):
    """Test OME admission webhook rejects unauthorized IP."""
    mock_auth_service.is_authorized.return_value = False

    payload = {
        "client": {
            "address": "192.168.1.200",
            "port": 12345,
        },
        "request": {
            "direction": "outgoing",
            "protocol": "webrtc",
            "status": "opening",
            "url": "ws://stream.example.com:3333/app/stream",
            "time": "2025-11-21T00:00:00Z",
        },
    }

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.post("/ome/admission", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["allowed"] is False
        assert data["reason"] == "IP address not authorized"


def test_ome_admission_closing(client, mock_auth_service):
    """Test OME admission webhook returns empty object for closing status."""
    payload = {
        "client": {
            "address": "192.168.1.100",
            "port": 12345,
        },
        "request": {
            "direction": "outgoing",
            "protocol": "webrtc",
            "status": "closing",
            "url": "ws://stream.example.com:3333/app/stream",
            "time": "2025-11-21T00:00:00Z",
        },
    }

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.post("/ome/admission", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data == {}


def test_ome_admission_uses_real_ip(client, mock_auth_service):
    """Test OME admission webhook uses real_ip when available."""
    mock_auth_service.is_authorized.return_value = True
    mock_auth_service.get_authorized_user_info.return_value = None

    payload = {
        "client": {
            "address": "10.0.0.1",
            "port": 12345,
            "real_ip": "192.168.1.100",
        },
        "request": {
            "direction": "incoming",
            "protocol": "rtmp",
            "status": "opening",
            "url": "rtmp://stream.example.com/app/stream",
            "time": "2025-11-21T00:00:00Z",
        },
    }

    with patch("teamspeak_auth.api.auth_service", mock_auth_service):
        response = client.post("/ome/admission", json=payload)
        assert response.status_code == 200

        # Verify is_authorized was called with real_ip, not address
        mock_auth_service.is_authorized.assert_called_with("192.168.1.100")
