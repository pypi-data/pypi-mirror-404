"""Configuration for the MCP server."""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv(verbose=True)


def _derive_mcp_url_from_base(base_url: str) -> str:
    """Derive the MCP URL from the API base URL.

    Extracts the scheme and host from the base URL and appends /api/mcp.
    Example: https://dev.platform.minitap.ai/api/v1 -> https://dev.platform.minitap.ai/api/mcp/
    """
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/api/mcp/"


def _derive_daas_url_from_base(base_url: str) -> str:
    """Derive the DaaS API URL from the API base URL.

    Extracts the scheme and host from the base URL and appends /api/daas.
    Example: https://dev.platform.minitap.ai/api/v1 -> https://dev.platform.minitap.ai/api/daas/
    """
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/api/daas"


def _derive_platform_base_url(api_base_url: str) -> str:
    """Derive the platform base URL from the API base URL.

    Extracts the scheme and host from the API URL (strips /api/v1 path).
    Example: https://dev.platform.minitap.ai/api/v1 -> https://dev.platform.minitap.ai
    """
    parsed = urlparse(api_base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


class MCPSettings(BaseSettings):
    """Configuration class for MCP server."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Minitap API configuration
    MINITAP_API_KEY: SecretStr | None = Field(default=None)
    MINITAP_API_BASE_URL: str = Field(default="https://platform.minitap.ai/api/v1")

    # These URLs can be set explicitly, or will be derived from MINITAP_API_BASE_URL
    MINITAP_DAAS_API: str | None = Field(default=None)
    MINITAP_API_MCP_BASE_URL: str | None = Field(default=None)

    OPEN_ROUTER_API_KEY: SecretStr | None = Field(default=None)

    VISION_MODEL: str = Field(default="google/gemini-3-flash-preview")

    # MCP server configuration (optional, for remote access)
    MCP_SERVER_HOST: str = Field(default="0.0.0.0")
    MCP_SERVER_PORT: int = Field(default=8000)

    # Cloud Mobile configuration
    # When set, the MCP server runs in cloud mode connecting to a Minitap cloud mobile
    # instead of requiring a local device. Value can be a device name.
    # Create cloud mobiles at https://platform.minitap.ai/cloud-mobiles
    CLOUD_MOBILE_NAME: str | None = Field(default=None)

    # Trajectory GIF download configuration
    # When set, downloads the trajectory GIF after task execution to the specified folder.
    # The folder is a directory where the GIF will be saved with the task run ID as filename.
    TRAJECTORY_GIF_DOWNLOAD_FOLDER: str | None = Field(default=None)

    # App package name override for uploads
    # When set, uploaded APK/IPA files will use this name instead of a random UUID.
    # The original file extension is preserved. Example: "my_app" -> "my_app.apk"
    APP_PACKAGE_NAME: str | None = Field(default=None)

    @model_validator(mode="after")
    def derive_urls_from_base(self) -> "MCPSettings":
        """Derive MCP and DaaS URLs from base URL if not explicitly set.

        This ensures that setting MINITAP_API_BASE_URL to a different environment
        (e.g., dev) automatically updates all related URLs.
        """
        if self.MINITAP_API_MCP_BASE_URL is None:
            # Use object.__setattr__ to bypass Pydantic's frozen model protection
            object.__setattr__(
                self,
                "MINITAP_API_MCP_BASE_URL",
                _derive_mcp_url_from_base(self.MINITAP_API_BASE_URL),
            )

        if self.MINITAP_DAAS_API is None:
            object.__setattr__(
                self,
                "MINITAP_DAAS_API",
                _derive_daas_url_from_base(self.MINITAP_API_BASE_URL),
            )

        # Set MINITAP_BASE_URL in environment for mobile-use SDK compatibility.
        # The SDK uses MINITAP_BASE_URL (e.g., https://dev.platform.minitap.ai) while
        # MCP uses MINITAP_API_BASE_URL (e.g., https://dev.platform.minitap.ai/api/v1).
        os.environ["MINITAP_BASE_URL"] = _derive_platform_base_url(self.MINITAP_API_BASE_URL)

        return self


settings = MCPSettings()  # type: ignore
