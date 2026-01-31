"""
Chart visualization functions.

Provides bar charts, histograms, and scatter plots using matplotlib or plotly.
"""

from typing import Any, Literal, Union

import numpy as np

# Backend type
Backend = Literal["matplotlib", "plotly"]


def bar_chart(
    df,
    x: str,
    y: str,
    backend: Backend = "matplotlib",
    horizontal: bool = False,
    top_n: int | None = None,
    sort: bool = True,
    ascending: bool = False,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    color: str | None = None,
    figsize: tuple[int, int] = (10, 6),
    **kwargs,
) -> Any:
    """Create a bar chart from a DataFrame.

    Args:
        df: DataFrame (pandas or polars)
        x: Column name for x-axis (categories)
        y: Column name for y-axis (values)
        backend: "matplotlib" or "plotly"
        horizontal: If True, create horizontal bar chart
        top_n: If set, limit to top N values (after sorting)
        sort: If True, sort bars by value
        ascending: Sort order (False = descending, largest first)
        title: Chart title
        xlabel: X-axis label (defaults to column name)
        ylabel: Y-axis label (defaults to column name)
        color: Bar color (hex or named color)
        figsize: Figure size for matplotlib (width, height in inches)
        **kwargs: Additional arguments passed to the plotting function

    Returns:
        matplotlib.Figure if backend="matplotlib", plotly.Figure if backend="plotly"

    Example:
        from rclco.viz import bar_chart

        # Top 10 tracts by population
        bar_chart(gdf, x="name", y="totpop_cy", top_n=10, title="Top 10 Tracts")

        # Horizontal bar chart with plotly
        bar_chart(gdf, x="name", y="medhinc_cy", horizontal=True, backend="plotly")
    """
    # Convert polars to pandas if needed
    pdf = _to_pandas(df)

    # Validate columns
    if x not in pdf.columns:
        raise ValueError(f"Column '{x}' not found in DataFrame")
    if y not in pdf.columns:
        raise ValueError(f"Column '{y}' not found in DataFrame")

    # Prepare data
    plot_df = pdf[[x, y]].dropna()

    if sort:
        plot_df = plot_df.sort_values(y, ascending=ascending)

    if top_n is not None:
        if ascending:
            plot_df = plot_df.head(top_n)
        else:
            plot_df = plot_df.head(top_n)

    if backend == "matplotlib":
        return _bar_chart_matplotlib(
            plot_df, x, y, horizontal, title, xlabel, ylabel, color, figsize, **kwargs
        )
    elif backend == "plotly":
        return _bar_chart_plotly(
            plot_df, x, y, horizontal, title, xlabel, ylabel, color, **kwargs
        )
    else:
        raise ValueError(f"Unknown backend: '{backend}'. Use 'matplotlib' or 'plotly'")


def histogram(
    df,
    column: str,
    bins: int = 20,
    backend: Backend = "matplotlib",
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = "Count",
    color: str | None = None,
    figsize: tuple[int, int] = (10, 6),
    kde: bool = False,
    **kwargs,
) -> Any:
    """Create a histogram from a DataFrame column.

    Args:
        df: DataFrame (pandas or polars)
        column: Column name to plot
        bins: Number of bins
        backend: "matplotlib" or "plotly"
        title: Chart title
        xlabel: X-axis label (defaults to column name)
        ylabel: Y-axis label
        color: Bar color
        figsize: Figure size for matplotlib
        kde: If True, overlay kernel density estimate (matplotlib only)
        **kwargs: Additional arguments passed to the plotting function

    Returns:
        matplotlib.Figure if backend="matplotlib", plotly.Figure if backend="plotly"

    Example:
        from rclco.viz import histogram

        histogram(gdf, "medhinc_cy", bins=30, title="Income Distribution")
    """
    # Convert polars to pandas if needed
    pdf = _to_pandas(df)

    if column not in pdf.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")

    values = pdf[column].dropna()

    if backend == "matplotlib":
        return _histogram_matplotlib(
            values, column, bins, title, xlabel, ylabel, color, figsize, kde, **kwargs
        )
    elif backend == "plotly":
        return _histogram_plotly(
            values, column, bins, title, xlabel, ylabel, color, **kwargs
        )
    else:
        raise ValueError(f"Unknown backend: '{backend}'. Use 'matplotlib' or 'plotly'")


def scatter(
    df,
    x: str,
    y: str,
    backend: Backend = "matplotlib",
    color_by: str | None = None,
    size_by: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    cmap: str = "viridis",
    figsize: tuple[int, int] = (10, 8),
    alpha: float = 0.7,
    **kwargs,
) -> Any:
    """Create a scatter plot from a DataFrame.

    Args:
        df: DataFrame (pandas or polars)
        x: Column name for x-axis
        y: Column name for y-axis
        backend: "matplotlib" or "plotly"
        color_by: Column name to color points by (continuous or categorical)
        size_by: Column name to size points by
        title: Chart title
        xlabel: X-axis label (defaults to column name)
        ylabel: Y-axis label (defaults to column name)
        cmap: Colormap for color_by (matplotlib name)
        figsize: Figure size for matplotlib
        alpha: Point transparency (0-1)
        **kwargs: Additional arguments passed to the plotting function

    Returns:
        matplotlib.Figure if backend="matplotlib", plotly.Figure if backend="plotly"

    Example:
        from rclco.viz import scatter

        # Basic scatter
        scatter(gdf, x="totpop_cy", y="medhinc_cy")

        # Colored by another variable
        scatter(gdf, x="totpop_cy", y="medhinc_cy", color_by="divindx_cy")

        # Sized by population
        scatter(gdf, x="totpop_cy", y="medhinc_cy", size_by="tothh_cy")
    """
    # Convert polars to pandas if needed
    pdf = _to_pandas(df)

    # Validate columns
    for col in [x, y]:
        if col not in pdf.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")

    if color_by and color_by not in pdf.columns:
        raise ValueError(f"Column '{color_by}' not found in DataFrame")

    if size_by and size_by not in pdf.columns:
        raise ValueError(f"Column '{size_by}' not found in DataFrame")

    # Prepare data
    cols = [x, y]
    if color_by:
        cols.append(color_by)
    if size_by:
        cols.append(size_by)
    plot_df = pdf[cols].dropna()

    if backend == "matplotlib":
        return _scatter_matplotlib(
            plot_df, x, y, color_by, size_by, title, xlabel, ylabel, cmap, figsize, alpha, **kwargs
        )
    elif backend == "plotly":
        return _scatter_plotly(
            plot_df, x, y, color_by, size_by, title, xlabel, ylabel, cmap, alpha, **kwargs
        )
    else:
        raise ValueError(f"Unknown backend: '{backend}'. Use 'matplotlib' or 'plotly'")


# =============================================================================
# Helper functions
# =============================================================================

def _to_pandas(df):
    """Convert DataFrame to pandas if it's polars."""
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df


# =============================================================================
# Matplotlib implementations
# =============================================================================

def _bar_chart_matplotlib(
    df, x, y, horizontal, title, xlabel, ylabel, color, figsize, **kwargs
):
    """Create bar chart using matplotlib."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError("matplotlib is required. Run: pip install matplotlib") from e

    fig, ax = plt.subplots(figsize=figsize)

    bar_color = color or "#4C78A8"

    if horizontal:
        ax.barh(df[x], df[y], color=bar_color, **kwargs)
        ax.set_xlabel(ylabel or y.replace("_", " ").title())
        ax.set_ylabel(xlabel or x.replace("_", " ").title())
    else:
        ax.bar(df[x], df[y], color=bar_color, **kwargs)
        ax.set_xlabel(xlabel or x.replace("_", " ").title())
        ax.set_ylabel(ylabel or y.replace("_", " ").title())
        # Rotate x labels if many categories
        if len(df) > 5:
            plt.xticks(rotation=45, ha="right")

    if title:
        ax.set_title(title, fontsize=14, fontweight="bold")

    plt.tight_layout()
    return fig


def _histogram_matplotlib(
    values, column, bins, title, xlabel, ylabel, color, figsize, kde, **kwargs
):
    """Create histogram using matplotlib."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError("matplotlib is required. Run: pip install matplotlib") from e

    fig, ax = plt.subplots(figsize=figsize)

    bar_color = color or "#4C78A8"

    n, bins_out, patches = ax.hist(values, bins=bins, color=bar_color, edgecolor="white", **kwargs)

    if kde:
        try:
            from scipy import stats
            kde_x = np.linspace(values.min(), values.max(), 200)
            kde_y = stats.gaussian_kde(values)(kde_x)
            # Scale KDE to match histogram
            kde_y = kde_y * len(values) * (bins_out[1] - bins_out[0])
            ax.plot(kde_x, kde_y, color="darkred", linewidth=2, label="KDE")
            ax.legend()
        except ImportError:
            pass  # scipy not available, skip KDE

    ax.set_xlabel(xlabel or column.replace("_", " ").title())
    ax.set_ylabel(ylabel or "Count")

    if title:
        ax.set_title(title, fontsize=14, fontweight="bold")

    plt.tight_layout()
    return fig


def _scatter_matplotlib(
    df, x, y, color_by, size_by, title, xlabel, ylabel, cmap, figsize, alpha, **kwargs
):
    """Create scatter plot using matplotlib."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError("matplotlib is required. Run: pip install matplotlib") from e

    fig, ax = plt.subplots(figsize=figsize)

    # Prepare color and size
    c = df[color_by] if color_by else "#4C78A8"
    s = df[size_by] if size_by else 50

    # Normalize size if provided
    if size_by:
        s_min, s_max = df[size_by].min(), df[size_by].max()
        s = 20 + 200 * (df[size_by] - s_min) / (s_max - s_min + 1e-10)

    scatter = ax.scatter(df[x], df[y], c=c, s=s, cmap=cmap, alpha=alpha, **kwargs)

    if color_by:
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(color_by.replace("_", " ").title())

    ax.set_xlabel(xlabel or x.replace("_", " ").title())
    ax.set_ylabel(ylabel or y.replace("_", " ").title())

    if title:
        ax.set_title(title, fontsize=14, fontweight="bold")

    plt.tight_layout()
    return fig


# =============================================================================
# Plotly implementations
# =============================================================================

def _bar_chart_plotly(df, x, y, horizontal, title, xlabel, ylabel, color, **kwargs):
    """Create bar chart using plotly."""
    try:
        import plotly.express as px
    except ImportError as e:
        raise ImportError("plotly is required. Run: pip install plotly") from e

    bar_color = color or "#4C78A8"

    if horizontal:
        fig = px.bar(
            df,
            x=y,
            y=x,
            orientation="h",
            color_discrete_sequence=[bar_color],
            **kwargs,
        )
        fig.update_layout(
            xaxis_title=ylabel or y.replace("_", " ").title(),
            yaxis_title=xlabel or x.replace("_", " ").title(),
        )
    else:
        fig = px.bar(
            df,
            x=x,
            y=y,
            color_discrete_sequence=[bar_color],
            **kwargs,
        )
        fig.update_layout(
            xaxis_title=xlabel or x.replace("_", " ").title(),
            yaxis_title=ylabel or y.replace("_", " ").title(),
        )

    if title:
        fig.update_layout(title=title)

    return fig


def _histogram_plotly(values, column, bins, title, xlabel, ylabel, color, **kwargs):
    """Create histogram using plotly."""
    try:
        import plotly.express as px
        import pandas as pd
    except ImportError as e:
        raise ImportError("plotly is required. Run: pip install plotly") from e

    bar_color = color or "#4C78A8"

    # Convert to DataFrame for plotly
    temp_df = pd.DataFrame({column: values})

    fig = px.histogram(
        temp_df,
        x=column,
        nbins=bins,
        color_discrete_sequence=[bar_color],
        **kwargs,
    )

    fig.update_layout(
        xaxis_title=xlabel or column.replace("_", " ").title(),
        yaxis_title=ylabel or "Count",
    )

    if title:
        fig.update_layout(title=title)

    return fig


def _scatter_plotly(
    df, x, y, color_by, size_by, title, xlabel, ylabel, cmap, alpha, **kwargs
):
    """Create scatter plot using plotly."""
    try:
        import plotly.express as px
    except ImportError as e:
        raise ImportError("plotly is required. Run: pip install plotly") from e

    # Map matplotlib colormap names to plotly
    plotly_cmap = cmap
    cmap_mapping = {
        "viridis": "Viridis",
        "plasma": "Plasma",
        "inferno": "Inferno",
        "magma": "Magma",
        "Blues": "Blues",
        "Greens": "Greens",
        "Reds": "Reds",
        "RdYlGn": "RdYlGn",
        "RdYlBu": "RdYlBu",
    }
    plotly_cmap = cmap_mapping.get(cmap, cmap)

    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color_by,
        size=size_by,
        color_continuous_scale=plotly_cmap if color_by else None,
        opacity=alpha,
        **kwargs,
    )

    fig.update_layout(
        xaxis_title=xlabel or x.replace("_", " ").title(),
        yaxis_title=ylabel or y.replace("_", " ").title(),
    )

    if title:
        fig.update_layout(title=title)

    return fig
