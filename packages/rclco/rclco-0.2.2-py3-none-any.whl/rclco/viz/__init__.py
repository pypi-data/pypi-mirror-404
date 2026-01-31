"""
Visualization module for RCLCO.

Provides functions for creating charts and maps from DataFrames and GeoDataFrames.

Charts (matplotlib/plotly):
    - bar_chart: Bar charts for categorical comparisons
    - histogram: Distribution histograms
    - scatter: Scatter plots with optional color/size encoding

Maps (folium/matplotlib):
    - choropleth: Choropleth maps for spatial data

Example:
    from rclco.data.demographics import Esri
    from rclco.viz import choropleth, bar_chart

    esri = Esri()
    gdf = esri.get_by_state("demographics", state="NC", geo_unit="tract", year=2024, return_type="geopandas")

    # Interactive choropleth map
    m = choropleth(gdf, "totpop_cy", title="Population by Tract")

    # Bar chart of top 10 tracts
    bar_chart(gdf, x="name", y="totpop_cy", top_n=10)
"""

from rclco.viz._maps import choropleth
from rclco.viz._charts import bar_chart, histogram, scatter
from rclco.viz._colors import get_color_palette, classify, list_palettes

__all__ = [
    "choropleth",
    "bar_chart",
    "histogram",
    "scatter",
    "get_color_palette",
    "classify",
    "list_palettes",
]
