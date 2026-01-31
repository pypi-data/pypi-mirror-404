"""
Database access module.

Provides simple factory function to get configured database clients.

Usage:
    from rclco.databases import get_database

    db = get_database("rclco_db")
    df = db.query("SELECT * FROM users WHERE active = :active", {"active": True})
    db.execute("INSERT INTO logs (msg) VALUES (:msg)", {"msg": "test"})

Prerequisites:
    - User must be authenticated to Azure (run `az login` or use Managed Identity)
    - Database must be registered in rclco/config/settings.py
    - Connection string must exist in Azure Key Vault
"""

from rclco.config.settings import DATABASE_REGISTRY
from rclco.config.vault import credentials
from rclco.connectors.database import AzureSQLConnector, PostgresConnector
from rclco.connectors.database.base import BaseDatabaseConnector
from rclco.core.exceptions import ConfigurationError


def get_database(name: str) -> BaseDatabaseConnector:
    """Get a configured database client by name.

    Args:
        name: Name of the database from DATABASE_REGISTRY (e.g., "rclco_db")

    Returns:
        A database connector with query() and execute() methods

    Raises:
        ConfigurationError: If the database is not registered

    Example:
        db = get_database("rclco_db")
        df = db.query("SELECT * FROM users")
        db.execute("INSERT INTO logs (msg) VALUES (:msg)", {"msg": "hello"})
    """
    if name not in DATABASE_REGISTRY:
        available = ", ".join(DATABASE_REGISTRY.keys()) or "(none configured)"
        raise ConfigurationError(
            f"Unknown database: '{name}'. Available: {available}"
        )

    config = DATABASE_REGISTRY[name]
    connection_string = credentials.get_connection_string(name)

    if config.db_type == "postgres":
        connector = PostgresConnector(connection_string)
    elif config.db_type == "azure_sql":
        connector = AzureSQLConnector(connection_string)
    else:
        raise ConfigurationError(f"Unknown database type: {config.db_type}")

    # Connect immediately so the client is ready to use
    connector.connect()
    return connector


def list_databases() -> list[str]:
    """List all available database names.

    Returns:
        List of registered database names
    """
    return list(DATABASE_REGISTRY.keys())


def get_database_info(name: str) -> dict[str, str]:
    """Get information about a registered database.

    Args:
        name: Name of the database

    Returns:
        Dictionary with database information

    Raises:
        ConfigurationError: If the database is not registered
    """
    if name not in DATABASE_REGISTRY:
        available = ", ".join(DATABASE_REGISTRY.keys()) or "(none)"
        raise ConfigurationError(
            f"Unknown database: '{name}'. Available: {available}"
        )

    config = DATABASE_REGISTRY[name]
    return {
        "name": name,
        "type": config.db_type,
        "description": config.description,
    }


__all__ = ["get_database", "list_databases", "get_database_info"]
