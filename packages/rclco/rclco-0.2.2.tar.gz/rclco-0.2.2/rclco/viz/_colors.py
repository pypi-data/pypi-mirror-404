"""
Color utilities for visualization.

Provides color palette retrieval and data classification for choropleth maps.
"""

from typing import Literal, Sequence
import numpy as np

# Classification scheme types
ClassificationScheme = Literal[
    "quantiles",
    "equal_interval",
    "natural_breaks",
    "std_mean",
    "percentiles",
]

# Built-in color palettes (matplotlib compatible names)
SEQUENTIAL_PALETTES = [
    "Blues", "Greens", "Reds", "Oranges", "Purples", "Greys",
    "YlOrRd", "YlOrBr", "YlGnBu", "YlGn", "BuGn", "BuPu",
    "GnBu", "OrRd", "PuBu", "PuBuGn", "PuRd", "RdPu",
    "viridis", "plasma", "inferno", "magma", "cividis",
]

DIVERGING_PALETTES = [
    "RdYlGn", "RdYlBu", "RdBu", "RdGy", "PiYG", "PRGn",
    "BrBG", "PuOr", "coolwarm", "bwr", "seismic",
]

QUALITATIVE_PALETTES = [
    "Set1", "Set2", "Set3", "Pastel1", "Pastel2",
    "Paired", "Accent", "Dark2", "tab10", "tab20",
]


def get_color_palette(
    name: str = "Blues",
    n: int = 5,
    reverse: bool = False,
) -> list[str]:
    """Get a list of n colors from a named palette.

    Args:
        name: Palette name (matplotlib colormap name)
        n: Number of colors to return
        reverse: Whether to reverse the palette order

    Returns:
        List of hex color strings

    Example:
        colors = get_color_palette("Blues", 5)
        # ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#084594']
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
    except ImportError as e:
        raise ImportError(
            "matplotlib is required for color palettes. Run: pip install matplotlib"
        ) from e

    # Handle reversed palette names (e.g., "Blues_r")
    if name.endswith("_r"):
        name = name[:-2]
        reverse = not reverse

    try:
        cmap = plt.get_cmap(name)
    except ValueError:
        raise ValueError(
            f"Unknown palette: '{name}'. Try one of: {SEQUENTIAL_PALETTES[:5]}"
        )

    # Sample colors evenly across the colormap
    if n == 1:
        positions = [0.5]
    else:
        positions = np.linspace(0.1, 0.9, n)

    if reverse:
        positions = positions[::-1]

    colors = [mcolors.to_hex(cmap(p)) for p in positions]
    return colors


def classify(
    values: Sequence[float],
    scheme: ClassificationScheme = "quantiles",
    k: int = 5,
) -> tuple[np.ndarray, list[float]]:
    """Classify values into bins using a classification scheme.

    Args:
        values: Sequence of numeric values to classify
        scheme: Classification scheme:
            - "quantiles": Equal number of observations per bin
            - "equal_interval": Equal-width bins
            - "natural_breaks": Jenks natural breaks
            - "std_mean": Standard deviation from mean
            - "percentiles": Custom percentile breaks
        k: Number of classes/bins

    Returns:
        Tuple of (bin_indices, bin_edges) where:
            - bin_indices: Array of bin index for each value (0 to k-1)
            - bin_edges: List of bin edge values (k+1 values)

    Example:
        bins, edges = classify([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "quantiles", 5)
    """
    try:
        import mapclassify
    except ImportError as e:
        raise ImportError(
            "mapclassify is required for classification. Run: pip install mapclassify"
        ) from e

    # Convert to numpy array and handle NaN
    arr = np.asarray(values, dtype=float)
    valid_mask = ~np.isnan(arr)
    valid_values = arr[valid_mask]

    if len(valid_values) == 0:
        raise ValueError("No valid (non-NaN) values to classify")

    # Apply classification scheme
    if scheme == "quantiles":
        classifier = mapclassify.Quantiles(valid_values, k=k)
    elif scheme == "equal_interval":
        classifier = mapclassify.EqualInterval(valid_values, k=k)
    elif scheme == "natural_breaks":
        classifier = mapclassify.NaturalBreaks(valid_values, k=k)
    elif scheme == "std_mean":
        classifier = mapclassify.StdMean(valid_values)
    elif scheme == "percentiles":
        classifier = mapclassify.Percentiles(valid_values, pct=[20, 40, 60, 80, 100])
    else:
        raise ValueError(
            f"Unknown scheme: '{scheme}'. Use: quantiles, equal_interval, "
            "natural_breaks, std_mean, or percentiles"
        )

    # Build full result array (with NaN handling)
    bin_indices = np.full(len(arr), -1, dtype=int)
    bin_indices[valid_mask] = classifier.yb

    # Get bin edges
    bin_edges = list(classifier.bins)
    # Prepend the minimum value
    bin_edges = [float(valid_values.min())] + bin_edges

    return bin_indices, bin_edges


def list_palettes(palette_type: Literal["sequential", "diverging", "qualitative", "all"] = "all") -> list[str]:
    """List available color palette names.

    Args:
        palette_type: Type of palettes to list

    Returns:
        List of palette names
    """
    if palette_type == "sequential":
        return SEQUENTIAL_PALETTES.copy()
    elif palette_type == "diverging":
        return DIVERGING_PALETTES.copy()
    elif palette_type == "qualitative":
        return QUALITATIVE_PALETTES.copy()
    else:
        return SEQUENTIAL_PALETTES + DIVERGING_PALETTES + QUALITATIVE_PALETTES
