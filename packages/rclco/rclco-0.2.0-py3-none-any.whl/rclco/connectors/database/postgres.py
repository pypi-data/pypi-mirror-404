"""PostgreSQL database connector."""

from typing import Any

import polars as pl

from rclco.connectors.database.base import BaseDatabaseConnector
from rclco.core.exceptions import ConnectionError, QueryError, ConfigurationError
from rclco.core.logging import get_logger

logger = get_logger("connectors.database.postgres")


class PostgresConnector(BaseDatabaseConnector):
    """Connector for PostgreSQL databases.

    Uses psycopg (psycopg3) for database connectivity. The connection string
    should be a valid PostgreSQL connection string.

    Example connection string formats:
        # Standard format
        "postgresql://user:password@host:5432/database"

        # With SSL
        "postgresql://user:password@host:5432/database?sslmode=require"

        # Key-value format
        "host=localhost port=5432 dbname=mydb user=user password=secret"

    Example:
        with PostgresConnector(connection_string="postgresql://...") as db:
            df = db.fetch("SELECT * FROM users")
    """

    def __init__(self, connection_string: str):
        """Initialize the PostgreSQL connector.

        Args:
            connection_string: PostgreSQL connection string (URI or key-value format)
        """
        self._connection_string = connection_string
        self._connection = None

    def connect(self) -> None:
        """Establish connection to the PostgreSQL database."""
        try:
            import psycopg
        except ImportError as e:
            raise ConfigurationError(
                "psycopg not installed. Run: pip install 'psycopg[binary]'"
            ) from e

        try:
            logger.debug("Connecting to PostgreSQL database")
            self._connection = psycopg.connect(self._connection_string)
            logger.debug("Successfully connected to PostgreSQL database")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL database: {e}") from e

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            try:
                self._connection.close()
                logger.debug("Disconnected from PostgreSQL database")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._connection = None

    def _ensure_connected(self) -> None:
        """Ensure we have an active connection."""
        if self._connection is None:
            raise ConnectionError("Not connected to database. Use 'with' statement or call connect() first.")

    def _convert_params(self, query: str, params: dict[str, Any] | None) -> tuple[str, dict[str, Any] | None]:
        """Convert :param_name style to %(param_name)s for psycopg.

        Args:
            query: SQL query with :param_name placeholders
            params: Dictionary of parameter values

        Returns:
            Tuple of (converted query, params dict)
        """
        if params is None:
            return query, None

        import re

        # Convert :param_name to %(param_name)s
        def replace_param(match):
            param_name = match.group(1)
            if param_name not in params:
                raise QueryError(f"Missing parameter: {param_name}")
            return f"%({param_name})s"

        param_pattern = re.compile(r":(\w+)")
        converted_query = param_pattern.sub(replace_param, query)

        return converted_query, params

    def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        """Execute a SQL query without returning results."""
        self._ensure_connected()

        converted_query, converted_params = self._convert_params(query, params)

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(converted_query, converted_params)
            self._connection.commit()
            logger.debug(f"Executed query: {query[:100]}...")
        except Exception as e:
            self._connection.rollback()
            raise QueryError(f"Query execution failed: {e}") from e

    def fetch(self, query: str, params: dict[str, Any] | None = None) -> pl.DataFrame:
        """Execute a SQL query and return results as a Polars DataFrame."""
        self._ensure_connected()

        converted_query, converted_params = self._convert_params(query, params)

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(converted_query, converted_params)

                # Get column names from cursor description
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                # Fetch all rows
                rows = cursor.fetchall()

                if not rows:
                    # Return empty DataFrame with correct columns
                    return pl.DataFrame({col: [] for col in columns})

                # Convert to list of dicts for Polars
                data = [dict(zip(columns, row)) for row in rows]

                logger.debug(f"Fetched {len(rows)} rows")
                return pl.DataFrame(data)

        except Exception as e:
            self._connection.rollback()
            raise QueryError(f"Query execution failed: {e}") from e

    def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Execute a SQL query and return the first row as a dictionary."""
        self._ensure_connected()

        converted_query, converted_params = self._convert_params(query, params)

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(converted_query, converted_params)

                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                row = cursor.fetchone()

                if row is None:
                    return None

                return dict(zip(columns, row))

        except Exception as e:
            self._connection.rollback()
            raise QueryError(f"Query execution failed: {e}") from e

    def fetch_scalar(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a SQL query and return a single scalar value."""
        self._ensure_connected()

        converted_query, converted_params = self._convert_params(query, params)

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(converted_query, converted_params)

                row = cursor.fetchone()

                if row is None or len(row) == 0:
                    return None

                return row[0]

        except Exception as e:
            self._connection.rollback()
            raise QueryError(f"Query execution failed: {e}") from e
