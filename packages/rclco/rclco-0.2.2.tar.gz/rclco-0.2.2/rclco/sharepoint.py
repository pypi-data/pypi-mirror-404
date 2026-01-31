"""
SharePoint access module.

Provides simple factory function to get configured SharePoint client.

Usage:
    from rclco.sharepoint import get_sharepoint

    sp = get_sharepoint()
    
    # List files
    files = sp.list_files("Shared Documents/Reports")
    
    # Download/upload files
    content = sp.download_file("Shared Documents/report.xlsx")
    sp.upload_file("Shared Documents/Outputs", "result.csv", csv_bytes)

Prerequisites:
    - User must be authenticated to Azure (run `az login` or use Managed Identity)
    - SharePoint must be configured in rclco/config/settings.py
    - SharePoint client secret must exist in Azure Key Vault
"""

from rclco.config.settings import SHAREPOINT_CONFIG
from rclco.config.vault import credentials
from rclco.connectors.microsoft import SharePointConnector
from rclco.core.exceptions import ConfigurationError


def get_sharepoint() -> SharePointConnector:
    """Get a configured SharePoint client.

    Returns:
        A SharePoint connector with file operation methods

    Raises:
        ConfigurationError: If SharePoint is not configured

    Example:
        sp = get_sharepoint()
        files = sp.list_files("Shared Documents/Reports")
        content = sp.download_file("Shared Documents/report.xlsx")
    """
    if SHAREPOINT_CONFIG is None:
        raise ConfigurationError(
            "SharePoint is not configured. "
            "Update SHAREPOINT_CONFIG in rclco/config/settings.py"
        )

    client_secret = credentials.get_sharepoint_secret()

    return SharePointConnector(
        site_url=SHAREPOINT_CONFIG.site_url,
        client_id=SHAREPOINT_CONFIG.client_id,
        client_secret=client_secret,
        tenant_id=SHAREPOINT_CONFIG.tenant_id,
    )


def get_sharepoint_info() -> dict[str, str] | None:
    """Get information about the configured SharePoint site.

    Returns:
        Dictionary with SharePoint information, or None if not configured
    """
    if SHAREPOINT_CONFIG is None:
        return None

    return {
        "site_url": SHAREPOINT_CONFIG.site_url,
        "description": SHAREPOINT_CONFIG.description,
    }


__all__ = ["get_sharepoint", "get_sharepoint_info"]
