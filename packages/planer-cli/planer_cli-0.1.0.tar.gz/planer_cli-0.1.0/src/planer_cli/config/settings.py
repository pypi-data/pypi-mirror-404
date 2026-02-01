"""Configuration management using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
)

# Default config file location
CONFIG_FILE_PATH = Path.home() / ".config" / "planer-cli" / "config.yaml"


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Custom settings source that loads from YAML config file."""

    def get_field_value(
        self, field: Any, field_name: str
    ) -> tuple[Any, str, bool]:
        """Get field value from YAML config."""
        yaml_data = self._load_yaml()
        field_value = yaml_data.get(field_name)
        return field_value, field_name, False

    def _load_yaml(self) -> dict[str, Any]:
        """Load YAML config file."""
        if not hasattr(self, "_yaml_data"):
            self._yaml_data: dict[str, Any] = {}
            if CONFIG_FILE_PATH.exists():
                with open(CONFIG_FILE_PATH) as f:
                    data = yaml.safe_load(f)
                    if data:
                        self._yaml_data = data
        return self._yaml_data

    def __call__(self) -> dict[str, Any]:
        """Return all settings from YAML."""
        return self._load_yaml()


class Settings(BaseSettings):
    """Application settings loaded from config file and environment variables.

    Priority (highest to lowest):
    1. Environment variables (PLANER_*)
    2. .env file
    3. YAML config file (~/.config/planer-cli/config.yaml)
    4. Default values
    """

    # Azure AD / MSAL configuration
    client_id: str = ""
    tenant_id: str = "common"
    authority: str = "https://login.microsoftonline.com"

    # Microsoft Graph
    graph_endpoint: str = "https://graph.microsoft.com/v1.0"
    scopes: list[str] = ["Tasks.ReadWrite", "Group.Read.All", "User.Read", "User.ReadBasic.All"]

    # Local paths
    config_dir: Path = Path.home() / ".planer-cli"

    # Output
    output_format: str = "table"
    log_level: str = "INFO"

    # Quick-add defaults
    default_plan_id: str = ""

    # Watch mode
    watch_interval: int = 60  # seconds

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to include YAML config.

        Priority order (first = highest priority):
        1. init_settings (passed to constructor)
        2. env_settings (environment variables)
        3. dotenv_settings (.env file)
        4. yaml_settings (config.yaml file)
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
        )

    class Config:
        """Pydantic settings configuration."""

        env_prefix = "PLANER_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def token_cache_file(self) -> Path:
        """Path to the token cache file."""
        return self.config_dir / "token_cache.json"

    @property
    def full_authority(self) -> str:
        """Full authority URL for MSAL."""
        return f"{self.authority}/{self.tenant_id}"

    @model_validator(mode="after")
    def ensure_config_dir(self) -> "Settings":
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        return self

    def validate_client_id(self) -> None:
        """Validate that client_id is configured.

        Raises:
            ValueError: If client_id is not set.
        """
        if not self.client_id:
            raise ValueError(
                "client_id is required. Set PLANER_CLIENT_ID environment variable "
                "or add client_id to ~/.config/planer-cli/config.yaml"
            )


def get_config_file_path() -> Path:
    """Get the config file path."""
    return CONFIG_FILE_PATH


def create_config_template() -> str:
    """Create a YAML config template."""
    return """# Planer CLI Configuration
# Environment variables (PLANER_*) override these settings

# Azure AD App Registration (required)
client_id: ""

# Azure AD Tenant (default: common)
# tenant_id: common

# Default output format: table or json
# output_format: table

# Default plan ID for quick-add command
# default_plan_id: ""

# Watch mode polling interval in seconds
# watch_interval: 60

# Log level: DEBUG, INFO, WARNING, ERROR
# log_level: INFO
"""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
