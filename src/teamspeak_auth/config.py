"""Configuration settings for TeamSpeak Auth."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration for TeamSpeak connection and authorization."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # TeamSpeak ServerQuery connection settings
    ts_host: str = Field(
        default="localhost",
        description="TeamSpeak server hostname",
    )
    ts_port: int = Field(
        default=10011,
        description="TeamSpeak ServerQuery port",
    )
    ts_user: str = Field(
        default="serveradmin",
        description="TeamSpeak ServerQuery username",
    )
    ts_password: str = Field(
        default="",
        description="TeamSpeak ServerQuery password",
    )
    ts_server_id: int = Field(
        default=1,
        description="TeamSpeak virtual server ID",
    )

    # Required permission(s) for authorization
    # Stored as string from env, converted to list[int] by validator
    required_server_groups: str = Field(
        default="6,9",
        description="Comma-separated list of server group IDs that grant authorization",
    )

    # FastAPI server settings
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host address",
    )
    api_port: int = Field(
        default=8000,
        description="API server port",
    )

    # Cache settings
    cache_ttl: int = Field(
        default=30,
        description="How long to cache TeamSpeak user data in seconds",
    )

    # Authorization settings
    authorized_subnets: str = Field(
        default="",
        description="Comma-separated list of IP subnets (CIDR notation) that are always authorized",
    )

    @field_validator("required_server_groups", mode="after")
    @classmethod
    def parse_server_groups(cls, v: str) -> list[int]:
        """Parse comma-separated server group IDs into a list of integers."""
        if isinstance(v, list):
            return v
        return [int(x.strip()) for x in v.split(",")]

    @field_validator("authorized_subnets", mode="after")
    @classmethod
    def parse_authorized_subnets(cls, v: str) -> list[str]:
        """Parse comma-separated subnet CIDRs into a list of strings."""
        if isinstance(v, list):
            return v
        if not v or v.strip() == "":
            return []
        return [x.strip() for x in v.split(",") if x.strip()]


config = Config()
