"""Type definitions and protocols for RCLCO library."""

from dataclasses import dataclass
from typing import Literal

# Database types supported by the library
DatabaseType = Literal["azure_sql", "postgres"]


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for a database connection.

    Attributes:
        secret_name: Name of the secret in Azure Key Vault containing the connection string
        db_type: Type of database ("azure_sql" or "postgres")
        description: Human-readable description for documentation
    """

    secret_name: str
    db_type: DatabaseType
    description: str


@dataclass(frozen=True)
class APIConfig:
    """Configuration for an API endpoint.

    Supports two ways to specify the base URL:
    1. Hardcoded: Set `base_url` directly (for public APIs or static URLs)
    2. From Key Vault: Set `base_url_secret` to fetch URL from Key Vault

    At least one of `base_url` or `base_url_secret` must be provided.

    Attributes:
        base_url: Hardcoded base URL for the API (use for public/static URLs)
        base_url_secret: Name of secret in Key Vault containing the base URL
        api_key_secret: Name of secret in Key Vault for API key (None if no auth needed)
        description: Human-readable description for documentation

    Examples:
        # Public API with hardcoded URL, no auth
        APIConfig(
            base_url="https://api.census.gov/data",
            description="US Census Bureau API",
        )

        # Internal API with URL and key from Key Vault
        APIConfig(
            base_url_secret="internal-api-url",
            api_key_secret="internal-api-key",
            description="Internal data API",
        )

        # API with hardcoded URL but key from Key Vault
        APIConfig(
            base_url="https://api.example.com/v1",
            api_key_secret="example-api-key",
            description="Example API",
        )
    """

    description: str = ""
    base_url: str | None = None
    base_url_secret: str | None = None
    api_key_secret: str | None = None

    def __post_init__(self):
        """Validate that at least one URL source is provided."""
        if self.base_url is None and self.base_url_secret is None:
            raise ValueError(
                "APIConfig requires either 'base_url' or 'base_url_secret' to be set"
            )


@dataclass(frozen=True)
class BlobConfig:
    """Configuration for Azure Blob Storage.

    Attributes:
        account_url: Azure storage account URL
        container: Container name
        secret_name: Name of the secret in Key Vault for storage credential
        description: Human-readable description for documentation
    """

    account_url: str
    container: str
    secret_name: str
    description: str


@dataclass(frozen=True)
class SharePointConfig:
    """Configuration for SharePoint connection.

    Attributes:
        site_url: SharePoint site URL
        client_id: Azure AD application client ID
        tenant_id: Azure AD tenant ID
        client_secret_name: Name of the secret in Key Vault for client secret
        description: Human-readable description for documentation
    """

    site_url: str
    client_id: str
    tenant_id: str
    client_secret_name: str
    description: str
