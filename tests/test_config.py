"""Tests for configuration module."""

from teamspeak_auth.config import Config


def test_config_default_values():
    """Test that config loads with default values."""
    config = Config(_env_file=None)  # Don't load .env for this test

    assert config.ts_host == "localhost"
    assert config.ts_port == 10011
    assert config.ts_user == "serveradmin"
    assert config.ts_server_id == 1
    assert config.api_host == "0.0.0.0"
    assert config.api_port == 8000
    assert config.cache_ttl == 30


def test_config_required_server_groups_parsing():
    """Test that REQUIRED_SERVER_GROUPS is parsed correctly."""
    config = Config(_env_file=None)

    # Should be parsed from string to list of ints
    assert isinstance(config.required_server_groups, list)
    assert all(isinstance(x, int) for x in config.required_server_groups)
    assert config.required_server_groups == [6, 9]


def test_config_custom_values():
    """Test that config accepts custom values."""
    config = Config(
        _env_file=None,
        ts_host="192.168.1.100",
        ts_port=10022,
        api_port=9000,
    )

    assert config.ts_host == "192.168.1.100"
    assert config.ts_port == 10022
    assert config.api_port == 9000


def test_config_server_groups_from_string():
    """Test that server groups can be set from string."""
    config = Config(
        _env_file=None,
        required_server_groups="10,20,30",
    )

    assert config.required_server_groups == [10, 20, 30]
