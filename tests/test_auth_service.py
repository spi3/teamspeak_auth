"""Tests for authorization service."""

from unittest.mock import Mock

import pytest

from teamspeak_auth.auth_service import AuthorizationService


@pytest.fixture
def mock_ts_client():
    """Create a mock TeamSpeak client."""
    mock_client = Mock()
    mock_client.connection = None
    return mock_client


def test_authorization_service_init():
    """Test that AuthorizationService initializes correctly."""
    service = AuthorizationService()

    assert service.authorized_ips == {}
    assert service.last_update == 0
    assert service.ts_client is not None


def test_is_authorized_returns_false_for_unknown_ip():
    """Test that is_authorized returns False for unknown IPs."""
    service = AuthorizationService()
    service.authorized_ips = {"192.168.1.100": {"nickname": "User1"}}

    assert service.is_authorized("192.168.1.200") is False


def test_is_authorized_returns_true_for_known_ip():
    """Test that is_authorized returns True for authorized IPs."""
    service = AuthorizationService()
    service.authorized_ips = {"192.168.1.100": {"nickname": "User1"}}

    assert service.is_authorized("192.168.1.100") is True


def test_get_authorized_user_info():
    """Test getting user info for authorized IP."""
    service = AuthorizationService()
    user_data = {
        "nickname": "TestUser",
        "groups": ["6", "9"],
        "client_id": "123",
    }
    service.authorized_ips = {"192.168.1.100": user_data}

    result = service.get_authorized_user_info("192.168.1.100")
    assert result == user_data


def test_get_authorized_user_info_returns_none_for_unknown():
    """Test that get_authorized_user_info returns None for unknown IPs."""
    service = AuthorizationService()
    service.authorized_ips = {}

    result = service.get_authorized_user_info("192.168.1.100")
    assert result is None


def test_get_all_authorized_ips():
    """Test getting list of all authorized IPs."""
    service = AuthorizationService()
    service.authorized_ips = {
        "192.168.1.100": {"nickname": "User1"},
        "192.168.1.101": {"nickname": "User2"},
    }

    ips = service.get_all_authorized_ips()
    assert len(ips) == 2
    assert "192.168.1.100" in ips
    assert "192.168.1.101" in ips


def test_get_cache_age():
    """Test getting cache age."""
    import time

    service = AuthorizationService()
    service.last_update = time.time() - 10.5

    age = service.get_cache_age()
    assert age >= 10.5
    assert age < 11.0  # Should be close to 10.5
