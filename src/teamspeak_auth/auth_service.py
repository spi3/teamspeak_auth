"""Authorization service for managing user authorization state."""

import asyncio
import ipaddress
import logging
import time

from .config import config
from .ts_client import TeamSpeakClient

logger = logging.getLogger(__name__)


class AuthorizationService:
    """Service for managing authorization state and checking user authorization."""

    def __init__(self):
        """Initialize the authorization service."""
        self.authorized_ips: dict[str, dict] = {}
        self.last_update: float = 0
        self.ts_client = TeamSpeakClient()
        self._update_lock = asyncio.Lock()
        self._background_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the authorization service and background update task."""
        logger.info("Starting authorization service")

        # Initial update
        await self.update_authorized_users()

        # Start background task for periodic updates
        self._background_task = asyncio.create_task(self._periodic_update())
        logger.info("Authorization service started")

    async def stop(self) -> None:
        """Stop the authorization service."""
        logger.info("Stopping authorization service")

        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

        self.ts_client.disconnect()
        logger.info("Authorization service stopped")

    async def _periodic_update(self) -> None:
        """Periodically update the list of authorized users."""
        while True:
            try:
                await asyncio.sleep(config.cache_ttl)
                await self.update_authorized_users()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic update: {e}")

    async def update_authorized_users(self) -> None:
        """Update the cached list of authorized users from TeamSpeak."""
        async with self._update_lock:
            try:
                # Run TeamSpeak operations in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                authorized_clients = await loop.run_in_executor(
                    None, self._fetch_authorized_clients
                )

                self.authorized_ips = authorized_clients
                self.last_update = time.time()

                logger.info(
                    f"Updated authorized users: {len(self.authorized_ips)} IP(s) authorized"
                )
                logger.debug(f"Authorized IPs: {list(self.authorized_ips.keys())}")
            except Exception as e:
                logger.error(f"Failed to update authorized users: {e}")

    def _fetch_authorized_clients(self) -> dict[str, dict]:
        """
        Fetch authorized clients from TeamSpeak (blocking operation).

        Returns:
            Dictionary mapping IP addresses to client information.
        """
        try:
            # Connect if not already connected
            if not self.ts_client.connection:
                self.ts_client.connect()

            return self.ts_client.get_authorized_clients()
        except Exception as e:
            logger.error(f"Error fetching authorized clients: {e}")
            # Try to reconnect on next attempt
            self.ts_client.disconnect()
            raise

    def _is_in_authorized_subnet(self, ip_address: str) -> bool:
        """
        Check if an IP address is in any of the authorized subnets.

        Args:
            ip_address: The IP address to check.

        Returns:
            True if the IP is in an authorized subnet, False otherwise.
        """
        if not config.authorized_subnets:
            return False

        try:
            ip = ipaddress.ip_address(ip_address)
            for subnet_str in config.authorized_subnets:
                try:
                    subnet = ipaddress.ip_network(subnet_str, strict=False)
                    if ip in subnet:
                        logger.debug(f"IP {ip_address} is in authorized subnet {subnet_str}")
                        return True
                except ValueError as e:
                    logger.warning(f"Invalid subnet configuration '{subnet_str}': {e}")
            return False
        except ValueError as e:
            logger.warning(f"Invalid IP address '{ip_address}': {e}")
            return False

    def is_authorized(self, ip_address: str) -> bool:
        """
        Check if an IP address is authorized.

        First checks if the IP is in an authorized subnet, then checks
        if the IP is in the list of authorized TeamSpeak clients.

        Args:
            ip_address: The IP address to check.

        Returns:
            True if the IP address is authorized, False otherwise.
        """
        # First check if IP is in an authorized subnet
        if self._is_in_authorized_subnet(ip_address):
            logger.debug(f"IP {ip_address} is authorized via subnet")
            return True

        # Then check if IP is in the TeamSpeak authorized list
        is_auth = ip_address in self.authorized_ips

        if is_auth:
            client_info = self.authorized_ips[ip_address]
            logger.debug(f"IP {ip_address} is authorized (user: {client_info.get('nickname')})")
        else:
            logger.debug(f"IP {ip_address} is not authorized")

        return is_auth

    def get_authorized_user_info(self, ip_address: str) -> dict | None:
        """
        Get information about an authorized user.

        Args:
            ip_address: The IP address to look up.

        Returns:
            User information dictionary if authorized, None otherwise.
        """
        return self.authorized_ips.get(ip_address)

    def get_all_authorized_ips(self) -> list[str]:
        """
        Get list of all currently authorized IP addresses.

        Returns:
            List of authorized IP addresses.
        """
        return list(self.authorized_ips.keys())

    def get_cache_age(self) -> float:
        """
        Get the age of the current cache in seconds.

        Returns:
            Seconds since last update.
        """
        return time.time() - self.last_update
