"""
Map visualization functions.

Provides choropleth map creation using folium (interactive) or matplotlib (static).
"""

from typing import Any, Literal, Union

from rclco.viz._colors import classify, get_color_palette, ClassificationScheme


def choropleth(
    gdf,
    column: str,
    interactive: bool = True,
    cmap: str = "Blues",
    scheme: ClassificationScheme = "quantiles",
    k: int = 5,
    legend: bool = True,
    title: str | None = None,
    tooltip_columns: list[str] | None = None,
    figsize: tuple[int, int] = (12, 8),
    tiles: str = "cartodbpositron",
    style_kwds: dict[str, Any] | None = None,
    **kwargs,
) -> Any:
    """Create a choropleth map from a GeoDataFrame.

    Args:
        gdf: GeoDataFrame with geometry and data columns
        column: Column name to visualize
        interactive: If True, return folium map; if False, return matplotlib figure
        cmap: Color palette name (matplotlib colormap)
        scheme: Classification scheme for binning values
        k: Number of classes/bins
        legend: Whether to show legend
        title: Map title
        tooltip_columns: Columns to show on hover (folium only). If None, shows
            column value and geometry name if available.
        figsize: Figure size for matplotlib (width, height in inches)
        tiles: Tile layer for folium ("cartodbpositron", "openstreetmap", etc.)
        style_kwds: Additional style keywords passed to plotting function
        **kwargs: Additional arguments passed to the underlying plot function

    Returns:
        folium.Map if interactive=True, matplotlib.Figure if interactive=False

    Example:
        from rclco.viz import choropleth

        # Interactive map (folium)
        m = choropleth(gdf, "totpop_cy", title="Population by Tract")
        m  # displays in notebook

        # Static map (matplotlib)
        fig = choropleth(gdf, "medhinc_cy", interactive=False, cmap="Greens")
        fig.savefig("income_map.png")

        # Custom classification
        m = choropleth(gdf, "medhinc_cy", scheme="natural_breaks", k=7)
    """
    # Validate inputs
    if column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found in GeoDataFrame")

    if gdf.geometry.isna().all():
        raise ValueError("GeoDataFrame has no valid geometries")

    if interactive:
        return _choropleth_folium(
            gdf=gdf,
            column=column,
            cmap=cmap,
            scheme=scheme,
            k=k,
            legend=legend,
            title=title,
            tooltip_columns=tooltip_columns,
            tiles=tiles,
            style_kwds=style_kwds,
            **kwargs,
        )
    else:
        return _choropleth_matplotlib(
            gdf=gdf,
            column=column,
            cmap=cmap,
            scheme=scheme,
            k=k,
            legend=legend,
            title=title,
            figsize=figsize,
            style_kwds=style_kwds,
            **kwargs,
        )


def _choropleth_folium(
    gdf,
    column: str,
    cmap: str,
    scheme: ClassificationScheme,
    k: int,
    legend: bool,
    title: str | None,
    tooltip_columns: list[str] | None,
    tiles: str,
    style_kwds: dict[str, Any] | None,
    **kwargs,
):
    """Create interactive choropleth using folium."""
    try:
        import folium
        from branca.colormap import LinearColormap
    except ImportError as e:
        raise ImportError(
            "folium is required for interactive maps. Run: pip install folium"
        ) from e

    import json

    # Get classification bins and colors
    values = gdf[column].values
    bin_indices, bin_edges = classify(values, scheme=scheme, k=k)
    colors = get_color_palette(cmap, k)

    # Create color mapping function
    def get_color(value):
        if value is None or (isinstance(value, float) and value != value):  # NaN check
            return "#cccccc"
        for i, edge in enumerate(bin_edges[1:]):
            if value <= edge:
                return colors[min(i, len(colors) - 1)]
        return colors[-1]

    # Calculate map center from bounds
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    # Create base map
    m = folium.Map(location=center, tiles=tiles, **kwargs)

    # Fit bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Prepare tooltip fields
    if tooltip_columns is None:
        tooltip_columns = [column]
        if "name" in gdf.columns:
            tooltip_columns = ["name"] + tooltip_columns
        elif "geoid" in gdf.columns:
            tooltip_columns = ["geoid"] + tooltip_columns

    # Style function
    default_style = {
        "fillOpacity": 0.7,
        "weight": 1,
        "color": "#333333",
    }
    if style_kwds:
        default_style.update(style_kwds)

    def style_function(feature):
        value = feature["properties"].get(column)
        return {
            **default_style,
            "fillColor": get_color(value),
        }

    # Convert to GeoJSON and add to map
    # Need to ensure CRS is WGS84 for folium
    gdf_wgs84 = gdf.to_crs(epsg=4326) if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf

    geojson = folium.GeoJson(
        gdf_wgs84.__geo_interface__,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_columns,
            aliases=[c.replace("_", " ").title() for c in tooltip_columns],
            sticky=True,
        ),
    )
    geojson.add_to(m)

    # Add legend
    if legend:
        colormap = LinearColormap(
            colors=colors,
            vmin=bin_edges[0],
            vmax=bin_edges[-1],
            caption=title or column.replace("_", " ").title(),
        )
        colormap.add_to(m)

    # Add title if provided (as a custom HTML element)
    if title:
        title_html = f'''
        <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;
                    background-color: white; padding: 10px; border-radius: 5px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
            <h4 style="margin: 0;">{title}</h4>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

    return m


def _choropleth_matplotlib(
    gdf,
    column: str,
    cmap: str,
    scheme: ClassificationScheme,
    k: int,
    legend: bool,
    title: str | None,
    figsize: tuple[int, int],
    style_kwds: dict[str, Any] | None,
    **kwargs,
):
    """Create static choropleth using matplotlib/geopandas."""
    try:
        import matplotlib.pyplot as plt
        import mapclassify
    except ImportError as e:
        raise ImportError(
            "matplotlib and mapclassify are required for static maps. "
            "Run: pip install matplotlib mapclassify"
        ) from e

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Default style
    plot_kwds = {
        "edgecolor": "#333333",
        "linewidth": 0.5,
    }
    if style_kwds:
        plot_kwds.update(style_kwds)

    # Plot with classification
    gdf.plot(
        column=column,
        ax=ax,
        cmap=cmap,
        scheme=scheme,
        k=k,
        legend=legend,
        legend_kwds={"loc": "lower right", "title": column.replace("_", " ").title()},
        **plot_kwds,
        **kwargs,
    )

    # Set title
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold")

    # Clean up axes
    ax.set_axis_off()

    plt.tight_layout()

    return fig
