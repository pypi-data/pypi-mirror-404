"""Azure SQL (SQL Server) database connector."""

from typing import Any

import polars as pl

from rclco.connectors.database.base import BaseDatabaseConnector
from rclco.core.exceptions import ConnectionError, QueryError, ConfigurationError
from rclco.core.logging import get_logger

logger = get_logger("connectors.database.azure_sql")


class AzureSQLConnector(BaseDatabaseConnector):
    """Connector for Azure SQL and SQL Server databases.

    Uses pyodbc for database connectivity. The connection string should be
    a valid ODBC connection string for SQL Server.

    Example connection string formats:
        # Azure SQL with Azure AD auth
        "Driver={ODBC Driver 18 for SQL Server};Server=server.database.windows.net;Database=mydb;Authentication=ActiveDirectoryDefault"

        # SQL Server with SQL auth
        "Driver={ODBC Driver 18 for SQL Server};Server=server;Database=mydb;UID=user;PWD=password"

    Example:
        with AzureSQLConnector(connection_string="...") as db:
            df = db.fetch("SELECT * FROM users")
    """

    def __init__(self, connection_string: str):
        """Initialize the Azure SQL connector.

        Args:
            connection_string: ODBC connection string for the database
        """
        self._connection_string = connection_string
        self._connection = None

    def connect(self) -> None:
        """Establish connection to the Azure SQL database."""
        try:
            import pyodbc
        except ImportError as e:
            raise ConfigurationError(
                "pyodbc not installed. Run: pip install pyodbc"
            ) from e

        try:
            logger.debug("Connecting to Azure SQL database")
            self._connection = pyodbc.connect(self._connection_string)
            logger.debug("Successfully connected to Azure SQL database")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Azure SQL database: {e}") from e

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            try:
                self._connection.close()
                logger.debug("Disconnected from Azure SQL database")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._connection = None

    def _ensure_connected(self) -> None:
        """Ensure we have an active connection."""
        if self._connection is None:
            raise ConnectionError("Not connected to database. Use 'with' statement or call connect() first.")

    def _convert_params(self, query: str, params: dict[str, Any] | None) -> tuple[str, list[Any]]:
        """Convert named parameters to positional parameters for pyodbc.

        pyodbc uses ? for parameter placeholders, so we need to convert
        :param_name style to ? and build a positional parameter list.

        Args:
            query: SQL query with :param_name placeholders
            params: Dictionary of parameter values

        Returns:
            Tuple of (converted query, positional parameter list)
        """
        if params is None:
            return query, []

        # Simple conversion: replace :name with ? and track order
        import re

        positional_params = []
        param_pattern = re.compile(r":(\w+)")

        def replace_param(match):
            param_name = match.group(1)
            if param_name not in params:
                raise QueryError(f"Missing parameter: {param_name}")
            positional_params.append(params[param_name])
            return "?"

        converted_query = param_pattern.sub(replace_param, query)
        return converted_query, positional_params

    def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        """Execute a SQL query without returning results."""
        self._ensure_connected()

        converted_query, positional_params = self._convert_params(query, params)

        try:
            cursor = self._connection.cursor()
            cursor.execute(converted_query, positional_params)
            self._connection.commit()
            cursor.close()
            logger.debug(f"Executed query: {query[:100]}...")
        except Exception as e:
            raise QueryError(f"Query execution failed: {e}") from e

    def fetch(self, query: str, params: dict[str, Any] | None = None) -> pl.DataFrame:
        """Execute a SQL query and return results as a Polars DataFrame."""
        self._ensure_connected()

        converted_query, positional_params = self._convert_params(query, params)

        try:
            cursor = self._connection.cursor()
            cursor.execute(converted_query, positional_params)

            # Get column names from cursor description
            columns = [column[0] for column in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                # Return empty DataFrame with correct columns
                return pl.DataFrame({col: [] for col in columns})

            # Convert to list of dicts for Polars
            data = [dict(zip(columns, row)) for row in rows]

            logger.debug(f"Fetched {len(rows)} rows")
            return pl.DataFrame(data)

        except Exception as e:
            raise QueryError(f"Query execution failed: {e}") from e

    def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Execute a SQL query and return the first row as a dictionary."""
        self._ensure_connected()

        converted_query, positional_params = self._convert_params(query, params)

        try:
            cursor = self._connection.cursor()
            cursor.execute(converted_query, positional_params)

            columns = [column[0] for column in cursor.description] if cursor.description else []
            row = cursor.fetchone()
            cursor.close()

            if row is None:
                return None

            return dict(zip(columns, row))

        except Exception as e:
            raise QueryError(f"Query execution failed: {e}") from e

    def fetch_scalar(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a SQL query and return a single scalar value."""
        self._ensure_connected()

        converted_query, positional_params = self._convert_params(query, params)

        try:
            cursor = self._connection.cursor()
            cursor.execute(converted_query, positional_params)

            row = cursor.fetchone()
            cursor.close()

            if row is None or len(row) == 0:
                return None

            return row[0]

        except Exception as e:
            raise QueryError(f"Query execution failed: {e}") from e
