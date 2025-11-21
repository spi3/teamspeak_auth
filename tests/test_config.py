"""Tests for configuration module."""

from teamspeak_auth.config import Config


def test_config_default_values(monkeypatch):
    """Test that config loads with default values."""
    # Clear all environment variables that could affect the config
    env_vars = [
        "TS_HOST",
        "TS_PORT",
        "TS_USER",
        "TS_PASSWORD",
        "TS_SERVER_ID",
        "REQUIRED_SERVER_GROUPS",
        "API_HOST",
        "API_PORT",
        "CACHE_TTL",
        "AUTHORIZED_SUBNETS",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    config = Config(_env_file=None)  # Don't load .env for this test

    assert config.ts_host == "localhost"
    assert config.ts_port == 10011
    assert config.ts_user == "serveradmin"
    assert config.ts_server_id == 1
    assert config.api_host == "0.0.0.0"
    assert config.api_port == 8000
    assert config.cache_ttl == 30


def test_config_required_server_groups_parsing(monkeypatch):
    """Test that REQUIRED_SERVER_GROUPS is parsed correctly."""
    # Clear environment variables
    env_vars = [
        "TS_HOST",
        "TS_PORT",
        "TS_USER",
        "TS_PASSWORD",
        "TS_SERVER_ID",
        "REQUIRED_SERVER_GROUPS",
        "API_HOST",
        "API_PORT",
        "CACHE_TTL",
        "AUTHORIZED_SUBNETS",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

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


def test_config_authorized_subnets_parsing(monkeypatch):
    """Test that AUTHORIZED_SUBNETS is parsed correctly."""
    # Clear environment variables
    env_vars = [
        "TS_HOST",
        "TS_PORT",
        "TS_USER",
        "TS_PASSWORD",
        "TS_SERVER_ID",
        "REQUIRED_SERVER_GROUPS",
        "API_HOST",
        "API_PORT",
        "CACHE_TTL",
        "AUTHORIZED_SUBNETS",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    config = Config(_env_file=None, authorized_subnets="192.168.1.0/24,10.0.0.0/8")

    # Should be parsed from string to list of strings
    assert isinstance(config.authorized_subnets, list)
    assert all(isinstance(x, str) for x in config.authorized_subnets)
    assert config.authorized_subnets == ["192.168.1.0/24", "10.0.0.0/8"]


def test_config_authorized_subnets_empty(monkeypatch):
    """Test that empty AUTHORIZED_SUBNETS results in empty list."""
    # Clear environment variables
    env_vars = [
        "TS_HOST",
        "TS_PORT",
        "TS_USER",
        "TS_PASSWORD",
        "TS_SERVER_ID",
        "REQUIRED_SERVER_GROUPS",
        "API_HOST",
        "API_PORT",
        "CACHE_TTL",
        "AUTHORIZED_SUBNETS",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    config = Config(_env_file=None, authorized_subnets="")

    assert config.authorized_subnets == []
