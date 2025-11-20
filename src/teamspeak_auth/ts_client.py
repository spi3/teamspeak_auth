"""TeamSpeak client for connecting and retrieving user data."""

import logging

import ts3

from .config import config

logger = logging.getLogger(__name__)


class TeamSpeakClient:
    """Client for interacting with TeamSpeak ServerQuery."""

    def __init__(self):
        """Initialize the TeamSpeak client."""
        self.connection: ts3.query.TS3Connection | None = None

    def connect(self) -> None:
        """Connect to the TeamSpeak ServerQuery interface."""
        try:
            self.connection = ts3.query.TS3Connection(config.ts_host, config.ts_port)
            self.connection.login(
                client_login_name=config.ts_user,
                client_login_password=config.ts_password,
            )
            self.connection.use(sid=config.ts_server_id)
            logger.info(f"Connected to TeamSpeak server at {config.ts_host}:{config.ts_port}")
        except Exception as e:
            logger.error(f"Failed to connect to TeamSpeak server: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from the TeamSpeak server."""
        if self.connection:
            try:
                self.connection.quit()
                logger.info("Disconnected from TeamSpeak server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.connection = None

    def get_connected_clients(self) -> list[dict]:
        """
        Get all connected clients with their details including IP addresses.

        Returns:
            List of client dictionaries containing client information.
        """
        if not self.connection:
            raise RuntimeError("Not connected to TeamSpeak server")

        try:
            # Get all clients with IP addresses (excluding query clients)
            # The -ip option tells TeamSpeak to include connection_client_ip in the response
            clients = self.connection.clientlist(ip=True)
            non_server_query_clients = [
                client
                for client in clients
                if client.get("client_type") == "0"  # Filter out query clients
            ]

            logger.info(f"Retrieved {len(non_server_query_clients)} connected clients")

            return non_server_query_clients
        except Exception as e:
            logger.error(f"Failed to retrieve client list: {e}")
            raise

    def get_client_server_groups(self, client_db_id: str) -> list[str]:
        """
        Get server groups for a specific client.

        Args:
            client_db_id: The database ID of the client.

        Returns:
            List of server group IDs the client belongs to.
        """
        if not self.connection:
            raise RuntimeError("Not connected to TeamSpeak server")

        try:
            groups = self.connection.servergroupsbyclientid(cldbid=client_db_id)
            return [group["sgid"] for group in groups]
        except Exception as e:
            logger.error(f"Failed to retrieve server groups for client {client_db_id}: {e}")
            return []

    def get_authorized_clients(self) -> dict[str, dict]:
        """
        Get all connected clients that have the required permissions.

        Returns:
            Dictionary mapping IP addresses to client information.
            Format: {ip_address: {nickname: str, groups: list[str]}}
        """
        authorized_clients = {}

        try:
            clients = self.get_connected_clients()

            for client in clients:
                logger.debug(f"Processing client: {client}")
                client_db_id = client.get("client_database_id")
                client_ip = client.get("connection_client_ip")
                nickname = client.get("client_nickname")

                if not client_db_id:
                    logger.warning(f"Client {nickname} missing database ID, skipping")
                    continue

                if not client_ip:
                    logger.warning(
                        f"Client {nickname} (ID: {client_db_id}) missing IP address, skipping. "
                        f"Available keys: {list(client.keys())}"
                    )
                    continue

                # Get client's server groups
                groups = self.get_client_server_groups(client_db_id)

                logger.debug(f"Client {nickname} ({client_ip}) groups: {groups}")

                # Check if client has any of the required groups
                if any(str(group) in map(str, config.required_server_groups) for group in groups):
                    authorized_clients[client_ip] = {
                        "nickname": nickname,
                        "groups": groups,
                        "client_id": client.get("clid"),
                        "client_db_id": client_db_id,
                    }
                    logger.debug(f"Authorized client: {nickname} ({client_ip})")

            logger.info(f"Found {len(authorized_clients)} authorized clients")
            return authorized_clients

        except Exception as e:
            logger.error(f"Failed to retrieve authorized clients: {e}")
            raise

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
