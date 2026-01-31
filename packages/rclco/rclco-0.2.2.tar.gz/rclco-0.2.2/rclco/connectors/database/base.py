"""Base class for database connectors."""

from abc import abstractmethod
from typing import Any, Literal, Union

import polars as pl

from rclco.connectors.base import BaseConnector
from rclco.core.exceptions import ConfigurationError

# Type alias for return type parameter
ReturnType = Literal["polars", "pandas"]
SpatialReturnType = Literal["geopandas"]

# Import pandas/geopandas types for type hints (optional at runtime)
try:
    import pandas as pd
    PandasDataFrame = pd.DataFrame
except ImportError:
    PandasDataFrame = Any  # type: ignore

try:
    import geopandas as gpd
    GeoDataFrame = gpd.GeoDataFrame
except ImportError:
    GeoDataFrame = Any  # type: ignore


class BaseDatabaseConnector(BaseConnector[pl.DataFrame]):
    """Abstract base class for SQL database connectors.

    This class defines the common interface for all database connectors,
    providing methods for executing queries and fetching results.

    Results can be returned as Polars DataFrames (default) or pandas DataFrames.

    Example:
        db = get_database("my_db")
        
        # Query data - returns Polars DataFrame by default
        df = db.query("SELECT * FROM users WHERE active = :active", {"active": True})

        # Query data - return pandas DataFrame
        pdf = db.query("SELECT * FROM users", return_type="pandas")

        # Query spatial data - returns GeoDataFrame
        gdf = db.query_spatial("SELECT * FROM shapes", geometry_column="geometry")

        # Execute a command (INSERT, UPDATE, DELETE)
        db.execute("UPDATE users SET last_login = NOW() WHERE id = :id", {"id": 123})

        # Don't forget to close when done (or use context manager)
        db.close()
    """

    def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, PandasDataFrame]:
        """Execute a SQL query and return results as a DataFrame.

        Args:
            sql: SQL query string. Use :param_name for parameter placeholders.
            params: Optional dictionary of parameter values.
            return_type: Type of DataFrame to return - "polars" (default) or "pandas"

        Returns:
            Polars DataFrame or pandas DataFrame depending on return_type

        Example:
            # Polars (default)
            df = db.query("SELECT * FROM users")

            # pandas (for GeoPandas compatibility, etc.)
            pdf = db.query("SELECT * FROM users", return_type="pandas")

            # With parameters
            df = db.query("SELECT * FROM users WHERE id = :id", {"id": 123})
        """
        df = self.fetch(sql, params)

        if return_type == "pandas":
            return df.to_pandas()
        return df

    def query_spatial(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        geometry_column: str | None = None,
        geometry_columns: list[str] | None = None,
        return_type: SpatialReturnType = "geopandas",
    ) -> GeoDataFrame:
        """Execute a SQL query and return results as a GeoDataFrame.

        Converts WKB (Well-Known Binary) geometry columns to Shapely geometry objects
        and returns a GeoPandas GeoDataFrame.

        Args:
            sql: SQL query string. Use :param_name for parameter placeholders.
            params: Optional dictionary of parameter values.
            geometry_column: Name of the geometry column (for single geometry).
            geometry_columns: List of geometry column names (for multiple geometries).
                             The first column becomes the active geometry.
            return_type: Return type - currently only "geopandas" is supported.

        Returns:
            GeoPandas GeoDataFrame with geometry column(s) converted from WKB.

        Raises:
            ConfigurationError: If geopandas/shapely not installed or no geometry column specified.

        Example:
            # Single geometry column
            gdf = db.query_spatial(
                "SELECT * FROM census_shapes WHERE state = 'NC'",
                geometry_column="geometry"
            )

            # Multiple geometry columns
            gdf = db.query_spatial(
                "SELECT * FROM census_shapes",
                geometry_columns=["geometry", "geometry_point"]
            )

            # With parameters
            gdf = db.query_spatial(
                "SELECT * FROM shapes WHERE type = :type",
                params={"type": "polygon"},
                geometry_column="geom"
            )
        """
        # Validate inputs
        if geometry_column is None and geometry_columns is None:
            raise ConfigurationError(
                "Must specify either 'geometry_column' or 'geometry_columns'"
            )

        # Normalize to list
        geom_cols: list[str] = []
        if geometry_column is not None:
            geom_cols = [geometry_column]
        if geometry_columns is not None:
            geom_cols = geometry_columns

        if not geom_cols:
            raise ConfigurationError("No geometry columns specified")

        # Check for required libraries
        try:
            import geopandas as gpd
            from shapely import wkb
        except ImportError as e:
            raise ConfigurationError(
                "geopandas and shapely are required for spatial queries. "
                "Run: pip install geopandas shapely"
            ) from e

        # Execute query and get pandas DataFrame
        pdf = self.query(sql, params, return_type="pandas")

        # Convert WKB columns to geometry
        def wkb_to_geometry(value):
            """Convert WKB hex string to Shapely geometry."""
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            if isinstance(value, str):
                # WKB as hex string
                return wkb.loads(bytes.fromhex(value))
            elif isinstance(value, bytes):
                # WKB as bytes
                return wkb.loads(value)
            elif isinstance(value, memoryview):
                # WKB as memoryview
                return wkb.loads(bytes(value))
            else:
                # Already a geometry or unknown type
                return value

        for col in geom_cols:
            if col not in pdf.columns:
                raise ConfigurationError(
                    f"Geometry column '{col}' not found in query results. "
                    f"Available columns: {list(pdf.columns)}"
                )
            pdf[col] = pdf[col].apply(wkb_to_geometry)

        # Create GeoDataFrame with first geometry column as active
        gdf = gpd.GeoDataFrame(pdf, geometry=geom_cols[0])

        return gdf

    def close(self) -> None:
        """Close the database connection.

        This is an alias for disconnect() with a more intuitive name.
        """
        self.disconnect()

    @abstractmethod
    def execute(self, sql: str, params: dict[str, Any] | None = None) -> None:
        """Execute a SQL command without returning results.

        Use this for INSERT, UPDATE, DELETE, or DDL statements.

        Args:
            sql: SQL command string. Use :param_name for parameter placeholders.
            params: Optional dictionary of parameter values.

        Raises:
            QueryError: If the execution fails
            ConnectionError: If not connected to the database
        """
        ...

    @abstractmethod
    def fetch(self, sql: str, params: dict[str, Any] | None = None) -> pl.DataFrame:
        """Execute a SQL query and return results as a Polars DataFrame.

        Args:
            sql: SQL query string. Use :param_name for parameter placeholders.
            params: Optional dictionary of parameter values.

        Returns:
            Polars DataFrame containing the query results

        Raises:
            QueryError: If the query execution fails
            ConnectionError: If not connected to the database
        """
        ...

    @abstractmethod
    def fetch_one(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Execute a SQL query and return the first row as a dictionary.

        Args:
            sql: SQL query string. Use :param_name for parameter placeholders.
            params: Optional dictionary of parameter values.

        Returns:
            Dictionary containing the first row, or None if no results

        Raises:
            QueryError: If the query execution fails
            ConnectionError: If not connected to the database
        """
        ...

    @abstractmethod
    def fetch_scalar(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a SQL query and return a single scalar value.

        Args:
            sql: SQL query string that returns a single value.
            params: Optional dictionary of parameter values.

        Returns:
            The scalar value from the first column of the first row,
            or None if no results

        Raises:
            QueryError: If the query execution fails
            ConnectionError: If not connected to the database
        """
        ...
