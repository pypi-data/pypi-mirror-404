"""Azure Key Vault credential manager with eager loading."""

from __future__ import annotations

from rclco.core.exceptions import AuthenticationError, ConfigurationError
from rclco.core.logging import get_logger
from rclco.config.settings import (
    AZURE_KEYVAULT_URL,
    DATABASE_REGISTRY,
    API_REGISTRY,
    BLOB_REGISTRY,
    SHAREPOINT_CONFIG,
)

logger = get_logger("config.vault")


class CredentialManager:
    """Singleton that manages all credentials from Azure Key Vault.

    This class eagerly loads all registered secrets from Azure Key Vault
    on first access. Credentials are cached in memory for the session.

    The singleton pattern ensures we only authenticate and fetch secrets once,
    even if multiple modules import from this file.

    Example:
        from rclco.config.vault import credentials

        # Get a database connection string
        conn_str = credentials.get_secret("analytics")

        # Get an API key
        api_key = credentials.get_secret("internal-api-key")
    """

    _instance: CredentialManager | None = None
    _initialized: bool = False

    def __new__(cls) -> CredentialManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if CredentialManager._initialized:
            return

        self._secrets: dict[str, str] = {}
        self._secret_client = None
        self._load_all_secrets()
        CredentialManager._initialized = True

    def _get_secret_client(self):
        """Lazily create the Azure Key Vault client."""
        if self._secret_client is None:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
            except ImportError as e:
                raise ConfigurationError(
                    "Azure SDK not installed. Run: pip install azure-identity azure-keyvault-secrets"
                ) from e

            try:
                credential = DefaultAzureCredential()
                self._secret_client = SecretClient(
                    vault_url=AZURE_KEYVAULT_URL,
                    credential=credential,
                )
                logger.debug(f"Connected to Key Vault: {AZURE_KEYVAULT_URL}")
            except Exception as e:
                raise AuthenticationError(
                    f"Failed to authenticate to Azure. "
                    f"Make sure you are logged in (run 'az login') or have Managed Identity configured. "
                    f"Error: {e}"
                ) from e

        return self._secret_client

    def _load_all_secrets(self) -> None:
        """Fetch all registered secrets from Key Vault.

        This method collects all secret names from the registries and
        fetches them in a batch. Secrets are cached by their Key Vault name.
        """
        # Collect all secret names we need to fetch
        secret_names: set[str] = set()

        for config in DATABASE_REGISTRY.values():
            secret_names.add(config.secret_name)

        for config in API_REGISTRY.values():
            if config.base_url_secret:  # URL stored in Key Vault
                secret_names.add(config.base_url_secret)
            if config.api_key_secret:  # API key stored in Key Vault
                secret_names.add(config.api_key_secret)

        for config in BLOB_REGISTRY.values():
            secret_names.add(config.secret_name)

        if SHAREPOINT_CONFIG:
            secret_names.add(SHAREPOINT_CONFIG.client_secret_name)

        if not secret_names:
            logger.debug("No secrets configured in registries, skipping Key Vault fetch")
            return

        logger.debug(f"Loading {len(secret_names)} secrets from Key Vault")

        client = self._get_secret_client()

        for name in secret_names:
            try:
                secret = client.get_secret(name)
                self._secrets[name] = secret.value
                logger.debug(f"Loaded secret: {name}")
            except Exception as e:
                logger.warning(f"Failed to load secret '{name}': {e}")
                # Don't fail completely - allow partial loading
                # The error will surface when the specific secret is requested

    def get_secret(self, name: str) -> str:
        """Get a secret value by its Key Vault name.

        Args:
            name: The name of the secret in Azure Key Vault

        Returns:
            The secret value

        Raises:
            ConfigurationError: If the secret is not found or failed to load
        """
        if name not in self._secrets:
            # Try to fetch it directly (might not have been in a registry)
            try:
                client = self._get_secret_client()
                secret = client.get_secret(name)
                self._secrets[name] = secret.value
                logger.debug(f"Loaded secret on-demand: {name}")
            except Exception as e:
                raise ConfigurationError(
                    f"Secret '{name}' not found in Key Vault. "
                    f"Make sure the secret exists and you have access. Error: {e}"
                ) from e

        return self._secrets[name]

    def get_connection_string(self, db_name: str) -> str:
        """Get a database connection string by its friendly name.

        Args:
            db_name: The friendly name from DATABASE_REGISTRY (e.g., "analytics")

        Returns:
            The connection string

        Raises:
            ConfigurationError: If the database is not registered or secret not found
        """
        if db_name not in DATABASE_REGISTRY:
            available = ", ".join(DATABASE_REGISTRY.keys()) or "(none configured)"
            raise ConfigurationError(
                f"Unknown database: '{db_name}'. Available databases: {available}"
            )

        config = DATABASE_REGISTRY[db_name]
        return self.get_secret(config.secret_name)

    def get_api_key(self, api_name: str) -> str | None:
        """Get an API key by its friendly name.

        Args:
            api_name: The friendly name from API_REGISTRY (e.g., "internal_api")

        Returns:
            The API key, or None if the API doesn't require authentication

        Raises:
            ConfigurationError: If the API is not registered or secret not found
        """
        if api_name not in API_REGISTRY:
            available = ", ".join(API_REGISTRY.keys()) or "(none configured)"
            raise ConfigurationError(
                f"Unknown API: '{api_name}'. Available APIs: {available}"
            )

        config = API_REGISTRY[api_name]
        if config.api_key_secret is None:
            return None

        return self.get_secret(config.api_key_secret)

    def get_api_base_url(self, api_name: str) -> str:
        """Get an API base URL by its friendly name.

        Resolves the URL from either the hardcoded value or Key Vault secret.

        Args:
            api_name: The friendly name from API_REGISTRY (e.g., "internal_api")

        Returns:
            The API base URL

        Raises:
            ConfigurationError: If the API is not registered or URL cannot be resolved
        """
        if api_name not in API_REGISTRY:
            available = ", ".join(API_REGISTRY.keys()) or "(none configured)"
            raise ConfigurationError(
                f"Unknown API: '{api_name}'. Available APIs: {available}"
            )

        config = API_REGISTRY[api_name]

        # Prefer hardcoded URL if provided
        if config.base_url is not None:
            return config.base_url

        # Otherwise fetch from Key Vault
        if config.base_url_secret is not None:
            return self.get_secret(config.base_url_secret)

        # This shouldn't happen due to APIConfig validation, but just in case
        raise ConfigurationError(
            f"API '{api_name}' has no base_url or base_url_secret configured"
        )

    def get_blob_credential(self, storage_name: str) -> str:
        """Get a blob storage credential by its friendly name.

        Args:
            storage_name: The friendly name from BLOB_REGISTRY (e.g., "data_lake")

        Returns:
            The storage credential (SAS token or access key)

        Raises:
            ConfigurationError: If the storage is not registered or secret not found
        """
        if storage_name not in BLOB_REGISTRY:
            available = ", ".join(BLOB_REGISTRY.keys()) or "(none configured)"
            raise ConfigurationError(
                f"Unknown storage: '{storage_name}'. Available storage: {available}"
            )

        config = BLOB_REGISTRY[storage_name]
        return self.get_secret(config.secret_name)

    def get_sharepoint_secret(self) -> str:
        """Get the SharePoint client secret.

        Returns:
            The SharePoint client secret

        Raises:
            ConfigurationError: If SharePoint is not configured or secret not found
        """
        if SHAREPOINT_CONFIG is None:
            raise ConfigurationError(
                "SharePoint is not configured. Update SHAREPOINT_CONFIG in settings.py"
            )

        return self.get_secret(SHAREPOINT_CONFIG.client_secret_name)


# Global singleton instance - created on first import
# This triggers eager loading of all secrets
credentials = CredentialManager()
