# TeamSpeak Auth

A Python project for managing user authorization based on TeamSpeak server connections and permissions. Provides a FastAPI server for querying user authorization status.

## Overview

TeamSpeak Auth connects to a TeamSpeak server to determine user authorization status. Users who are currently connected to the TeamSpeak server and possess certain permission levels are considered authorized.

The package initializes a FastAPI server where user authorization status can be queried. User authorization is based on IP address matching - a user is authorized if their IP address correlates with the IP address of an authorized TeamSpeak user.

## How It Works

1. Connects to the configured TeamSpeak server
2. Retrieves the list of currently connected users and their IP addresses
3. Checks each user's permission level
4. Determines authorization status based on configured permission requirements
5. Starts a FastAPI server that accepts authorization queries
6. When queried, matches the requesting IP address against authorized TeamSpeak users' IP addresses

## Requirements

- Python >=3.11
- Access to a TeamSpeak server

## Installation

```bash
uv sync
```

## Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your TeamSpeak server details:

- `TS_HOST`: TeamSpeak server hostname (default: localhost)
- `TS_PORT`: ServerQuery port (default: 10011)
- `TS_USER`: ServerQuery username (default: serveradmin)
- `TS_PASSWORD`: ServerQuery password
- `TS_SERVER_ID`: Virtual server ID (default: 1)
- `REQUIRED_SERVER_GROUPS`: Comma-separated list of server group IDs that grant authorization (default: 6,9)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `CACHE_TTL`: How often to refresh authorized users from TeamSpeak in seconds (default: 30)

## Usage

Start the FastAPI server:

```bash
# Run as a Python module
uv run python -m teamspeak_auth

# Or use the installed command
uv run teamspeak-auth
```

The server will start on `http://localhost:8000` by default.

## Testing

Run the test suite:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=teamspeak_auth --cov-report=html
```

## Development

### Quick Reference

```bash
# Run all checks (do this before committing)
uv run black --check src/ tests/ && uv run ruff check src/ tests/ && uv run pytest

# Auto-fix formatting and linting, then test
uv run black src/ tests/ && uv run ruff check --fix src/ tests/ && uv run pytest
```

### Code Formatting (Black)

```bash
# Format all code
uv run black src/ tests/

# Check formatting without changes
uv run black --check src/ tests/
```

### Linting (Ruff)

```bash
# Check for linting issues
uv run ruff check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/
```

## API Endpoints

The FastAPI server provides the following endpoints:

### `GET /`
Root endpoint with API information.

### `GET/POST/etc. /auth`
ForwardAuth endpoint compatible with reverse proxies like Traefik. This endpoint accepts any HTTP method and is designed to work with ForwardAuth middleware.

**Behavior:**
- Extracts client IP from `X-Forwarded-For` header (for reverse proxies) or direct connection
- Returns `200 OK` if the IP is authorized
- Returns `403 Forbidden` if the IP is not authorized

**Response (200 OK):**
```json
{
  "status": "authorized",
  "ip": "192.168.1.100",
  "user": "JohnDoe"
}
```

**Response (403 Forbidden):**
```json
{
  "detail": "Forbidden: IP address not authorized"
}
```

**Traefik Configuration Example:**
```yaml
http:
  middlewares:
    teamspeak-auth:
      forwardAuth:
        address: "http://teamspeak-auth:8000/auth"
        trustForwardHeader: true
```

### `GET /auth/check`
Check if the requesting IP address is authorized. The IP is automatically extracted from the request.

**Response:**
```json
{
  "authorized": true,
  "ip_address": "192.168.1.100",
  "user_info": {
    "nickname": "JohnDoe",
    "groups": ["6", "9"],
    "client_id": "123",
    "client_db_id": "456"
  }
}
```

### `GET /auth/check/{ip_address}`
Check if a specific IP address is authorized.

**Example:** `GET /auth/check/192.168.1.100`

### `POST /auth/refresh`
Manually trigger a refresh of authorized users from TeamSpeak (instead of waiting for the scheduled cache refresh).

### `GET /status`
Get the current status of the authorization service.

**Response:**
```json
{
  "status": "running",
  "authorized_users_count": 2,
  "cache_age_seconds": 15.3,
  "cache_ttl_seconds": 30
}
```
