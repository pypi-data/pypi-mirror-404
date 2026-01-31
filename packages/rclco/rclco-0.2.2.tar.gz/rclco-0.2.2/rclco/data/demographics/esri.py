"""
Esri Demographics data access.

Provides easy access to Esri demographic datasets with spatial query support.

Usage:
    from rclco.data.demographics import Esri

    esri = Esri()

    # Get demographics by point location
    df = esri.get_by_point("demographics", lat=35.83, lon=-81.55, geo_unit="tract", year=2024)

    # Get income by age for specific geoids
    df = esri.get_by_geoids("income_by_age_cy", geoids=["37001000100"], year=2024)

    # Get all tracts in a state with geometry
    gdf = esri.get_by_state("demographics", state="NC", geo_unit="tract", year=2024, include_geometry=True)

    # Shorthand methods
    df = esri.demographics(lat=35.83, lon=-81.55, geo_unit="tract", year=2024)
    df = esri.income_by_age_cy(geoids=["37001000100"], year=2024)
"""

from typing import Any, Literal, Union

import polars as pl

from rclco.databases import get_database
from rclco.core.exceptions import ConfigurationError

# Type aliases
ReturnType = Literal["polars", "pandas", "geopandas"]
GeoUnit = Literal["tr", "bg", "cy", "st", "zp", "pl", 'cb', 'md']

# Dataset registry - maps dataset names to table names
_ESRI_DATASETS = {
    "demographics": "esri_demographics",
    "income_by_age_cy": "esri_income_by_age_cy",
    "income_by_age_fy": "esri_income_by_age_fy",
}

# Common columns across all Esri datasets (for joining/filtering)
_COMMON_COLUMNS = [
    "geoid",
    "geo_unit",
    "name",
    "st_abbrev",
    "current_year",
    "future_year",
    "census_shape_wide_id",
]


class Esri:
    """Access Esri demographic datasets with spatial query support.

    This class provides methods to query Esri demographic data by:
    - Point location (lat/lon)
    - Polygon geometry
    - GeoIDs
    - State
    - Spatial join to a GeoDataFrame of sites

    Available datasets:
    - demographics: Population, households, income, housing stats
    - income_by_age_cy: Income by age brackets (current year)
    - income_by_age_fy: Income by age brackets (future year)

    Example:
        esri = Esri()

        # Query by point
        df = esri.get_by_point("demographics", lat=35.83, lon=-81.55, geo_unit="tract", year=2024)

        # Query by geoids
        df = esri.get_by_geoids("demographics", geoids=["37001000100", "37001000200"], year=2024)

        # Get with geometry for mapping
        gdf = esri.get_by_state("demographics", state="NC", geo_unit="tract", year=2024, include_geometry=True)

        # Shorthand
        df = esri.demographics(lat=35.83, lon=-81.55, geo_unit="tract", year=2024)
    """

    def __init__(self, database: str = "rclco_db"):
        """Initialize Esri data accessor.

        Args:
            database: Name of the database in DATABASE_REGISTRY (default: "rclco_db")
        """
        self._database_name = database
        self._db = None

    def _get_db(self):
        """Get or create database connection."""
        if self._db is None:
            self._db = get_database(self._database_name)
        return self._db

    def _get_table_name(self, dataset: str) -> str:
        """Get table name for a dataset."""
        if dataset not in _ESRI_DATASETS:
            available = ", ".join(_ESRI_DATASETS.keys())
            raise ConfigurationError(
                f"Unknown Esri dataset: '{dataset}'. Available: {available}"
            )
        return _ESRI_DATASETS[dataset]

    def list_datasets(self) -> list[str]:
        """List available Esri datasets.

        Returns:
            List of dataset names
        """
        return list(_ESRI_DATASETS.keys())

    def list_geo_units(self) -> list[str]:
        """List available geographic unit types.

        Returns:
            List of geo_unit values
        """
        return ["tract", "block_group", "county", "state", "zip", "place"]

    def get_years(self, dataset: str = "demographics") -> list[int]:
        """Get available years for a dataset.

        Args:
            dataset: Dataset name

        Returns:
            List of available years
        """
        table = self._get_table_name(dataset)
        db = self._get_db()
        df = db.query(f"SELECT DISTINCT current_year FROM {table} ORDER BY current_year")
        return df["current_year"].to_list()

    def get_columns(self, dataset: str = "demographics") -> list[str]:
        """Get available columns for a dataset.

        Args:
            dataset: Dataset name

        Returns:
            List of column names
        """
        table = self._get_table_name(dataset)
        db = self._get_db()
        df = db.query(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """)
        return df["column_name"].to_list()

    def get_by_point(
        self,
        dataset: str,
        lat: float,
        lon: float,
        geo_unit: str = "tract",
        year: int | None = None,
        columns: list[str] | None = None,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, Any]:
        """Get ESRI data for the geography containing a point.

        Args:
            dataset: Dataset name ("demographics", "income_by_age_cy", etc.)
            lat: Latitude
            lon: Longitude
            geo_unit: Geographic unit type (default: "tract")
            year: Current year filter (default: latest available)
            columns: Specific columns to return (default: all)
            return_type: "polars", "pandas", or "geopandas"

        Returns:
            DataFrame with Esri data for the geography containing the point

        Example:
            df = esri.get_by_point("demographics", lat=35.83, lon=-81.55, geo_unit="tract", year=2024)
        """
        table = self._get_table_name(dataset)
        db = self._get_db()

        # Build column selection
        col_select = "*" if columns is None else ", ".join(["e." + c for c in columns])

        # Build year filter
        year_filter = ""
        if year is not None:
            year_filter = f"AND e.current_year = {year}"

        sql = f"""
            SELECT {col_select}
            FROM {table} e
            JOIN census_shapes_wide csw ON e.census_shape_wide_id = csw.id
            WHERE e.geo_unit = :geo_unit
            {year_filter}
            AND ST_Contains(csw.geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        """

        params = {"geo_unit": geo_unit, "lon": lon, "lat": lat}

        if return_type == "geopandas":
            # Need to include geometry
            sql = f"""
                SELECT e.*, csw.geometry
                FROM {table} e
                JOIN census_shapes_wide csw ON e.census_shape_wide_id = csw.id
                WHERE e.geo_unit = :geo_unit
                {year_filter}
                AND ST_Contains(csw.geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            """
            return db.query_spatial(sql, params, geometry_column="geometry")

        return db.query(sql, params, return_type=return_type)

    def get_by_geoids(
        self,
        dataset: str,
        geoids: list[str],
        year: int | None = None,
        columns: list[str] | None = None,
        include_geometry: bool = False,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, Any]:
        """Get ESRI data for specific GeoIDs.

        Args:
            dataset: Dataset name
            geoids: List of GeoID values
            year: Current year filter (default: latest available)
            columns: Specific columns to return (default: all)
            include_geometry: Whether to include geometry column
            return_type: "polars", "pandas", or "geopandas"

        Returns:
            DataFrame with Esri data for the specified geoids

        Example:
            df = esri.get_by_geoids("demographics", geoids=["37001000100", "37001000200"], year=2024)
        """
        table = self._get_table_name(dataset)
        db = self._get_db()

        # Build column selection
        col_select = "e.*" if columns is None else ", ".join(["e." + c for c in columns])

        # Build year filter
        year_filter = ""
        if year is not None:
            year_filter = f"AND e.current_year = {year}"

        # Build geoid list for SQL
        geoid_list = ", ".join([f"'{g}'" for g in geoids])

        if include_geometry or return_type == "geopandas":
            sql = f"""
                SELECT {col_select}, csw.geometry
                FROM {table} e
                JOIN census_shapes_wide csw ON e.census_shape_wide_id = csw.id
                WHERE e.geoid IN ({geoid_list})
                {year_filter}
            """
            if return_type == "geopandas":
                return db.query_spatial(sql, geometry_column="geometry")
            return db.query(sql, return_type=return_type)
        else:
            sql = f"""
                SELECT {col_select}
                FROM {table} e
                WHERE e.geoid IN ({geoid_list})
                {year_filter}
            """
            return db.query(sql, return_type=return_type)

    def get_by_state(
        self,
        dataset: str,
        state: str,
        geo_unit: str = "tract",
        year: int | None = None,
        columns: list[str] | None = None,
        include_geometry: bool = False,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, Any]:
        """Get ESRI data for all geographies in a state.

        Args:
            dataset: Dataset name
            state: State abbreviation (e.g., "NC", "CA")
            geo_unit: Geographic unit type (default: "tract")
            year: Current year filter (default: latest available)
            columns: Specific columns to return (default: all)
            include_geometry: Whether to include geometry column
            return_type: "polars", "pandas", or "geopandas"

        Returns:
            DataFrame with Esri data for all geographies in the state

        Example:
            gdf = esri.get_by_state("demographics", state="NC", geo_unit="tract", year=2024, include_geometry=True)
        """
        table = self._get_table_name(dataset)
        db = self._get_db()

        # Build column selection
        col_select = "e.*" if columns is None else ", ".join(["e." + c for c in columns])

        # Build year filter
        year_filter = ""
        if year is not None:
            year_filter = f"AND e.current_year = {year}"

        if include_geometry or return_type == "geopandas":
            sql = f"""
                SELECT {col_select}, csw.geometry
                FROM {table} e
                JOIN census_shapes_wide csw ON e.census_shape_wide_id = csw.id
                WHERE e.st_abbrev = :state
                AND e.geo_unit = :geo_unit
                {year_filter}
            """
            params = {"state": state.upper(), "geo_unit": geo_unit}
            if return_type == "geopandas":
                return db.query_spatial(sql, params, geometry_column="geometry")
            return db.query(sql, params, return_type=return_type)
        else:
            sql = f"""
                SELECT {col_select}
                FROM {table} e
                WHERE e.st_abbrev = :state
                AND e.geo_unit = :geo_unit
                {year_filter}
            """
            params = {"state": state.upper(), "geo_unit": geo_unit}
            return db.query(sql, params, return_type=return_type)

    def get_by_polygon(
        self,
        dataset: str,
        geometry,  # Shapely geometry or WKT string
        geo_unit: str = "tract",
        year: int | None = None,
        columns: list[str] | None = None,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, Any]:
        """Get ESRI data for geographies intersecting a polygon.

        Args:
            dataset: Dataset name
            geometry: Shapely geometry object or WKT string
            geo_unit: Geographic unit type (default: "tract")
            year: Current year filter (default: latest available)
            columns: Specific columns to return (default: all)
            return_type: "polars", "pandas", or "geopandas"

        Returns:
            DataFrame with Esri data for geographies intersecting the polygon

        Example:
            from shapely.geometry import box
            bbox = box(-82, 35, -81, 36)
            gdf = esri.get_by_polygon("demographics", geometry=bbox, geo_unit="tract", year=2024, return_type="geopandas")
        """
        table = self._get_table_name(dataset)
        db = self._get_db()

        # Convert geometry to WKT if needed
        if hasattr(geometry, "wkt"):
            wkt = geometry.wkt
        else:
            wkt = str(geometry)

        # Build column selection
        col_select = "e.*" if columns is None else ", ".join(["e." + c for c in columns])

        # Build year filter
        year_filter = ""
        if year is not None:
            year_filter = f"AND e.current_year = {year}"

        sql = f"""
            SELECT {col_select}, csw.geometry
            FROM {table} e
            JOIN census_shapes_wide csw ON e.census_shape_wide_id = csw.id
            WHERE e.geo_unit = :geo_unit
            {year_filter}
            AND ST_Intersects(csw.geometry, ST_GeomFromText(:wkt, 4326))
        """

        params = {"geo_unit": geo_unit, "wkt": wkt}

        if return_type == "geopandas":
            return db.query_spatial(sql, params, geometry_column="geometry")
        return db.query(sql, params, return_type=return_type)

    def join_to_sites(
        self,
        sites_gdf,  # GeoDataFrame with site locations
        dataset: str,
        geo_unit: str = "tract",
        year: int | None = None,
        columns: list[str] | None = None,
    ):
        """Join Esri data to a GeoDataFrame of site locations.

        Each site will get the Esri data for the geography it falls within.

        Args:
            sites_gdf: GeoDataFrame with site point geometries
            dataset: Dataset name
            geo_unit: Geographic unit type (default: "tract")
            year: Current year filter (default: latest available)
            columns: Specific Esri columns to include (default: all)

        Returns:
            GeoDataFrame with original sites plus Esri columns

        Example:
            import geopandas as gpd
            sites = gpd.GeoDataFrame({"name": ["Site A", "Site B"]}, geometry=[Point(-81.5, 35.8), Point(-80.8, 35.2)])
            gdf = esri.join_to_sites(sites, "demographics", geo_unit="tract", year=2024)
        """
        try:
            import geopandas as gpd
            from shapely.geometry import mapping
        except ImportError as e:
            raise ConfigurationError(
                "geopandas is required for join_to_sites. Run: pip install geopandas"
            ) from e

        results = []
        for idx, row in sites_gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue

            # Get centroid for points, or use as-is
            if geom.geom_type == "Point":
                lat, lon = geom.y, geom.x
            else:
                centroid = geom.centroid
                lat, lon = centroid.y, centroid.x

            try:
                esri_data = self.get_by_point(
                    dataset=dataset,
                    lat=lat,
                    lon=lon,
                    geo_unit=geo_unit,
                    year=year,
                    columns=columns,
                    return_type="pandas",
                )
                if len(esri_data) > 0:
                    esri_row = esri_data.iloc[0].to_dict()
                    results.append({"_site_idx": idx, **esri_row})
            except Exception:
                # Site doesn't fall within any geography
                pass

        if not results:
            return sites_gdf.copy()

        # Merge results back to sites
        esri_df = gpd.pd.DataFrame(results).set_index("_site_idx")
        
        # Drop overlapping columns from Esri data (except the ones we want)
        drop_cols = [c for c in esri_df.columns if c in sites_gdf.columns and c != "geometry"]
        esri_df = esri_df.drop(columns=drop_cols, errors="ignore")

        return sites_gdf.join(esri_df)

    def close(self):
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None

    # =========================================================================
    # Shorthand methods for common datasets
    # =========================================================================

    def demographics(
        self,
        lat: float | None = None,
        lon: float | None = None,
        geoids: list[str] | None = None,
        state: str | None = None,
        geo_unit: str = "tract",
        year: int | None = None,
        columns: list[str] | None = None,
        include_geometry: bool = False,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, Any]:
        """Shorthand for querying demographics dataset.

        Provide ONE of: (lat, lon), geoids, or state.

        Example:
            df = esri.demographics(lat=35.83, lon=-81.55, geo_unit="tract", year=2024)
            df = esri.demographics(geoids=["37001000100"], year=2024)
            gdf = esri.demographics(state="NC", geo_unit="tract", year=2024, include_geometry=True)
        """
        return self._shorthand_query(
            "demographics", lat, lon, geoids, state, geo_unit, year, columns, include_geometry, return_type
        )

    def income_by_age_cy(
        self,
        lat: float | None = None,
        lon: float | None = None,
        geoids: list[str] | None = None,
        state: str | None = None,
        geo_unit: str = "tract",
        year: int | None = None,
        columns: list[str] | None = None,
        include_geometry: bool = False,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, Any]:
        """Shorthand for querying income_by_age_cy dataset.

        Provide ONE of: (lat, lon), geoids, or state.
        """
        return self._shorthand_query(
            "income_by_age_cy", lat, lon, geoids, state, geo_unit, year, columns, include_geometry, return_type
        )

    def income_by_age_fy(
        self,
        lat: float | None = None,
        lon: float | None = None,
        geoids: list[str] | None = None,
        state: str | None = None,
        geo_unit: str = "tract",
        year: int | None = None,
        columns: list[str] | None = None,
        include_geometry: bool = False,
        return_type: ReturnType = "polars",
    ) -> Union[pl.DataFrame, Any]:
        """Shorthand for querying income_by_age_fy dataset.

        Provide ONE of: (lat, lon), geoids, or state.
        """
        return self._shorthand_query(
            "income_by_age_fy", lat, lon, geoids, state, geo_unit, year, columns, include_geometry, return_type
        )

    def _shorthand_query(
        self,
        dataset: str,
        lat: float | None,
        lon: float | None,
        geoids: list[str] | None,
        state: str | None,
        geo_unit: str,
        year: int | None,
        columns: list[str] | None,
        include_geometry: bool,
        return_type: ReturnType,
    ) -> Union[pl.DataFrame, Any]:
        """Internal helper for shorthand methods."""
        if lat is not None and lon is not None:
            return self.get_by_point(dataset, lat, lon, geo_unit, year, columns, return_type)
        elif geoids is not None:
            return self.get_by_geoids(dataset, geoids, year, columns, include_geometry, return_type)
        elif state is not None:
            return self.get_by_state(dataset, state, geo_unit, year, columns, include_geometry, return_type)
        else:
            raise ConfigurationError(
                "Must provide one of: (lat, lon), geoids, or state"
            )


# Convenience function
def get_esri(database: str = "rclco_db") -> Esri:
    """Get an Esri data accessor.

    Args:
        database: Name of the database (default: "rclco_db")

    Returns:
        Esri instance

    Example:
        esri = get_esri()
        df = esri.demographics(state="NC", geo_unit="tract", year=2024)
    """
    return Esri(database=database)
