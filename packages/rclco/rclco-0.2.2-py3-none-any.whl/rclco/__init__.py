"""
RCLCO Python Library - Core data connectivity for the organization.

This library provides simple access to databases, APIs, storage, and SharePoint.
All authentication is handled automatically via Azure Key Vault.

Quick Start:
    # Get a database client
    from rclco.databases import get_database
    
    db = get_database("rclco_db")
    df = db.query("SELECT * FROM users")
    db.close()

    # Get an API client
    from rclco.apis import get_api
    
    api = get_api("rclco_api")
    data = api.get("endpoint")

    # Get a storage client
    from rclco.storage import get_storage
    
    storage = get_storage("data_lake")
    df = storage.download_dataframe("data.parquet")

    # Get SharePoint client
    from rclco.sharepoint import get_sharepoint
    
    sp = get_sharepoint()
    files = sp.list_files("Shared Documents")

Prerequisites:
    - Azure CLI authentication: run `az login`
    - Or use Managed Identity in Azure environments
"""

from rclco._version import __version__

# Core exceptions for error handling
from rclco.core.exceptions import (
    RCLCOError,
    ConfigurationError,
    ConnectionError,
    QueryError,
    AuthenticationError,
    APIError,
    StorageError,
)

# Logging configuration
from rclco.core.logging import configure_logging

# Factory functions (primary API)
from rclco.databases import get_database, list_databases
from rclco.apis import get_api, list_apis
from rclco.storage import get_storage, list_storage
from rclco.sharepoint import get_sharepoint

__all__ = [
    # Version
    "__version__",
    # Factory functions
    "get_database",
    "get_api",
    "get_storage",
    "get_sharepoint",
    # List functions
    "list_databases",
    "list_apis",
    "list_storage",
    # Exceptions
    "RCLCOError",
    "ConfigurationError",
    "ConnectionError",
    "QueryError",
    "AuthenticationError",
    "APIError",
    "StorageError",
    # Logging
    "configure_logging",
]
