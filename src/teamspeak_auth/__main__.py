"""Main entry point for TeamSpeak Auth application."""

import logging

import uvicorn

from .config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Start the FastAPI server."""
    logger.info("Starting TeamSpeak Auth API server")
    logger.info(f"Server will run on {config.api_host}:{config.api_port}")
    logger.info(f"TeamSpeak server: {config.ts_host}:{config.ts_port}")
    logger.info(f"Required server groups: {config.required_server_groups}")
    logger.info(f"Cache TTL: {config.cache_ttl} seconds")

    # Run the FastAPI application with uvicorn
    uvicorn.run(
        "teamspeak_auth.api:app",
        host=config.api_host,
        port=config.api_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
