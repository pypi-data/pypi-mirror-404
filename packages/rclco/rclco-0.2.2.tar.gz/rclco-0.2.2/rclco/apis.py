"""
API access module.

Provides simple factory function to get configured REST API clients.

Usage:
    from rclco.apis import get_api

    api = get_api("rclco_api")
    data = api.get("endpoint", params={"page": 1})
    result = api.post("submit", json={"name": "test"})

Prerequisites:
    - User must be authenticated to Azure (run `az login` or use Managed Identity)
    - API must be registered in rclco/config/settings.py
    - API credentials (if required) must exist in Azure Key Vault
"""

from rclco.config.settings import API_REGISTRY
from rclco.config.vault import credentials
from rclco.connectors.api import RESTClient
from rclco.core.exceptions import ConfigurationError


def get_api(name: str) -> RESTClient:
    """Get a configured API client by name.

    Args:
        name: Name of the API from API_REGISTRY (e.g., "rclco_api")

    Returns:
        A REST client with get(), post(), put(), delete() methods

    Raises:
        ConfigurationError: If the API is not registered

    Example:
        api = get_api("rclco_api")
        data = api.get("users", params={"page": 1})
        result = api.post("users", json={"name": "John"})
    """
    if name not in API_REGISTRY:
        available = ", ".join(API_REGISTRY.keys()) or "(none configured)"
        raise ConfigurationError(
            f"Unknown API: '{name}'. Available: {available}"
        )

    config = API_REGISTRY[name]

    # Get base URL (from hardcoded value or Key Vault)
    base_url = credentials.get_api_base_url(name)

    # Get API key if required
    api_key = None
    if config.api_key_secret:
        api_key = credentials.get_api_key(name)

    return RESTClient(base_url=base_url, api_key=api_key)


def list_apis() -> list[str]:
    """List all available API names.

    Returns:
        List of registered API names
    """
    return list(API_REGISTRY.keys())


def get_api_info(name: str) -> dict[str, str | bool | None]:
    """Get information about a registered API.

    Args:
        name: Name of the API

    Returns:
        Dictionary with API information

    Raises:
        ConfigurationError: If the API is not registered
    """
    if name not in API_REGISTRY:
        available = ", ".join(API_REGISTRY.keys()) or "(none)"
        raise ConfigurationError(
            f"Unknown API: '{name}'. Available: {available}"
        )

    config = API_REGISTRY[name]
    return {
        "name": name,
        "base_url": config.base_url,
        "url_from_keyvault": config.base_url_secret is not None,
        "requires_auth": config.api_key_secret is not None,
        "description": config.description,
    }


__all__ = ["get_api", "list_apis", "get_api_info"]
