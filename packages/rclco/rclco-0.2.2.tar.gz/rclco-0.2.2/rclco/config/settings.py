"""
RCLCO Library Settings and Service Registries.

This file contains the hardcoded configuration for all services.
Library maintainers update this file when adding new databases, APIs, or storage accounts.

To add a new database:
1. Add the connection string to Azure Key Vault
2. Add an entry to DATABASE_REGISTRY below
3. Update rclco/databases.py to export the new query function
4. Release a new version of the library
"""

from rclco.core.types import DatabaseConfig, APIConfig, BlobConfig, SharePointConfig

# =============================================================================
# Azure Key Vault Configuration
# =============================================================================
# This is NOT a secret - it's just the endpoint URL for the Key Vault.
# Users must be authenticated via Azure CLI (az login), Managed Identity,
# or other DefaultAzureCredential-supported methods.

AZURE_KEYVAULT_URL = "https://rclcoai-key-vault.vault.azure.net"

# =============================================================================
# Database Registry
# =============================================================================
# Maps friendly database names to their Key Vault secret names.
# The secret in Key Vault should contain the full connection string.

DATABASE_REGISTRY: dict[str, DatabaseConfig] = {
    "rclco_db": DatabaseConfig(
        secret_name="ETL-TOOLBOX-DATABASE-CONNECTION-STRING",
        db_type="postgres",
        description="RCLCO Database (ETL Toolbox)",
    )
    # Example Azure SQL database
    # "analytics": DatabaseConfig(
    #     secret_name="analytics-connection-string",
    #     db_type="azure_sql",
    #     description="Main analytics Azure SQL database",
    # ),
    #
    # Example PostgreSQL database
    # "reporting": DatabaseConfig(
    #     secret_name="reporting-pg-connection-string",
    #     db_type="postgres",
    #     description="PostgreSQL reporting database",
    # ),
}

# =============================================================================
# API Registry
# =============================================================================
# Maps friendly API names to their configuration.
# 
# URL can be specified two ways:
#   - base_url: Hardcoded URL (for public APIs or static URLs)
#   - base_url_secret: Key Vault secret name containing the URL
#
# At least one of base_url or base_url_secret must be provided.

API_REGISTRY: dict[str, APIConfig] = {
    "rclco_api": APIConfig(
        base_url_secret="ETL-TOOLBOX-API-BASE-URL",
        api_key_secret="ETL-TOOLBOX-API-KEY",
        description="RCLCO Data API (ETL Toolbox)",
    ),
    # Example: Internal API with URL and key both from Key Vault
    # "internal_api": APIConfig(
    #     base_url_secret="internal-api-url",
    #     api_key_secret="internal-api-key",
    #     description="Internal data API",
    # ),
    #
    # Example: API with hardcoded URL but key from Key Vault
    # "partner_api": APIConfig(
    #     base_url="https://api.partner.com/v1",
    #     api_key_secret="partner-api-key",
    #     description="Partner API",
    # ),
    #
    # Example: Public API (no auth, hardcoded URL)
    # "census": APIConfig(
    #     base_url="https://api.census.gov/data",
    #     description="US Census Bureau API",
    # ),
}

# =============================================================================
# Blob Storage Registry
# =============================================================================
# Maps friendly storage names to their Azure Blob Storage configuration.

BLOB_REGISTRY: dict[str, BlobConfig] = {
    # Example blob storage
    # "data_lake": BlobConfig(
    #     account_url="https://rclcodata.blob.core.windows.net",
    #     container="analytics",
    #     secret_name="data-lake-sas-token",
    #     description="Main data lake storage",
    # ),
}

# =============================================================================
# SharePoint Configuration
# =============================================================================
# SharePoint site configuration for file operations.
# Set to None if SharePoint integration is not needed.

SHAREPOINT_CONFIG: SharePointConfig | None = None

# Example SharePoint configuration:
# SHAREPOINT_CONFIG = SharePointConfig(
#     site_url="https://rclco.sharepoint.com/sites/Data",
#     client_id="your-azure-ad-app-client-id",
#     tenant_id="your-azure-ad-tenant-id",
#     client_secret_name="sharepoint-client-secret",
#     description="RCLCO Data SharePoint site",
# )
