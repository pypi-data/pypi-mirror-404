"""
Blob storage access module.

Provides simple factory function to get configured Azure Blob Storage clients.

Usage:
    from rclco.storage import get_storage

    storage = get_storage("data_lake")
    
    # List files
    files = storage.list_blobs("raw/2024/")
    
    # Download/upload DataFrames
    df = storage.download_dataframe("data.parquet")
    storage.upload_dataframe("output.parquet", df)
    
    # Raw file operations
    data = storage.download("file.txt")
    storage.upload("file.txt", b"content")

Prerequisites:
    - User must be authenticated to Azure (run `az login` or use Managed Identity)
    - Storage must be registered in rclco/config/settings.py
    - Storage credentials must exist in Azure Key Vault
"""

from rclco.config.settings import BLOB_REGISTRY
from rclco.config.vault import credentials
from rclco.connectors.storage import AzureBlobConnector
from rclco.core.exceptions import ConfigurationError


def get_storage(name: str) -> AzureBlobConnector:
    """Get a configured blob storage client by name.

    Args:
        name: Name of the storage from BLOB_REGISTRY (e.g., "data_lake")

    Returns:
        A blob storage connector with upload/download methods

    Raises:
        ConfigurationError: If the storage is not registered

    Example:
        storage = get_storage("data_lake")
        df = storage.download_dataframe("data.parquet")
        storage.upload_dataframe("output.parquet", df)
    """
    if name not in BLOB_REGISTRY:
        available = ", ".join(BLOB_REGISTRY.keys()) or "(none configured)"
        raise ConfigurationError(
            f"Unknown storage: '{name}'. Available: {available}"
        )

    config = BLOB_REGISTRY[name]
    credential = credentials.get_blob_credential(name)

    return AzureBlobConnector(
        account_url=config.account_url,
        container=config.container,
        credential=credential,
    )


def list_storage() -> list[str]:
    """List all available storage names.

    Returns:
        List of registered storage names
    """
    return list(BLOB_REGISTRY.keys())


def get_storage_info(name: str) -> dict[str, str]:
    """Get information about a registered storage account.

    Args:
        name: Name of the storage

    Returns:
        Dictionary with storage information

    Raises:
        ConfigurationError: If the storage is not registered
    """
    if name not in BLOB_REGISTRY:
        available = ", ".join(BLOB_REGISTRY.keys()) or "(none)"
        raise ConfigurationError(
            f"Unknown storage: '{name}'. Available: {available}"
        )

    config = BLOB_REGISTRY[name]
    return {
        "name": name,
        "account_url": config.account_url,
        "container": config.container,
        "description": config.description,
    }


__all__ = ["get_storage", "list_storage", "get_storage_info"]
