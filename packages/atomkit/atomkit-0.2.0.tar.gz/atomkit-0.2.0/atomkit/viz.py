"""
Fast visualization for SpatialGrid.

Core utilities for extracting 2D planes from 4D grid data, used by
marimo widgets and notebooks. Also provides interactive marimo widgets.

Usage in marimo notebook:
    from atomkit import SpatialGrid
    from atomkit.viz import grid_explorer

    grid = SpatialGrid.load("data.h5")
    grid_explorer(grid)  # Returns interactive UI
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from atomkit.spatial_grid import SpatialGrid

try:
    import marimo as mo
    MARIMO_AVAILABLE = True
except ImportError:
    MARIMO_AVAILABLE = False
    mo = None

try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None


def _check_deps():
    if not MARIMO_AVAILABLE:
        raise ImportError("marimo required: pip install marimo")
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required: pip install matplotlib")


# Axis index mapping (4D: t, x, y, z)
DIM_MAP_4D = {"t": 0, "x": 1, "y": 2, "z": 3}
DIM_NAMES_4D = ("t", "x", "y", "z")

# Axis index mapping (3D spatial only)
_AXIS_MAP = {"x": 0, "y": 1, "z": 2}


# =============================================================================
# Core utilities for 4D -> 2D reduction (shared by widgets and notebooks)
# =============================================================================

def get_field_data_4d(
    grid: "SpatialGrid",
    field: str,
    agg: Literal["mean", "sum", "min", "max"] = "mean",
) -> "NDArray[np.float64]":
    """
    Get 4D field data from a grid.

    Parameters
    ----------
    grid : SpatialGrid
        The grid to extract data from.
    field : str
        Field name. Use "counts" for atom counts.
    agg : {"mean", "sum", "min", "max"}
        Aggregation type for non-count fields.

    Returns
    -------
    data : ndarray, shape (n_timesteps, nx, ny, nz)
        4D field data.
    """
    if field == "counts":
        return grid.counts.astype(np.float64)

    field_agg = grid.cells[field]
    if agg == "sum":
        return field_agg.sum.np
    elif agg == "min":
        return field_agg.min.np
    elif agg == "max":
        return field_agg.max.np
    else:  # mean
        return field_agg.mean.np


def get_axis_extent(
    grid: "SpatialGrid",
    axis: str,
) -> tuple[float, float, int, str]:
    """
    Get extent information for an axis.

    Parameters
    ----------
    grid : SpatialGrid
        The grid.
    axis : str
        Axis name: "t", "x", "y", or "z".

    Returns
    -------
    lo : float
        Lower bound.
    hi : float
        Upper bound.
    n : int
        Number of cells along this axis.
    label : str
        Axis label for plotting.
    """
    if axis == "t":
        return 0.0, float(grid.n_timesteps), grid.n_timesteps, "timestep"

    i = {"x": 0, "y": 1, "z": 2}[axis]
    lo = grid.box_bounds[i * 2]
    hi = grid.box_bounds[i * 2 + 1]
    n = grid.grid_shape[i]
    return lo, hi, n, axis


def coord_to_index(
    value: float,
    lo: float,
    hi: float,
    n: int,
) -> int:
    """
    Convert a coordinate value to a cell index.

    Parameters
    ----------
    value : float
        Coordinate value.
    lo, hi : float
        Axis bounds.
    n : int
        Number of cells.

    Returns
    -------
    idx : int
        Cell index (clamped to valid range).
    """
    if n <= 0 or hi <= lo:
        return 0
    idx = int((value - lo) / ((hi - lo) / n))
    return max(0, min(idx, n - 1))


def reduce_4d_to_2d(
    data: "NDArray",
    grid: "SpatialGrid",
    plot_x: str,
    plot_y: str,
    reductions: dict[str, tuple[str, float | None]],
    cumsum: "NDArray | None" = None,
) -> tuple["NDArray", tuple[float, float, float, float]]:
    """
    Reduce 4D data to 2D for visualization.

    Parameters
    ----------
    data : ndarray, shape (t, nx, ny, nz)
        4D input data.
    grid : SpatialGrid
        Grid for bounds/shape info.
    plot_x : str
        Axis to plot on X ("t", "x", "y", or "z").
    plot_y : str
        Axis to plot on Y.
    reductions : dict
        For each non-plotted axis, a tuple of (mode, value) where:
        - mode is "slice", "sum", "mean", or "max"
        - value is the slice coordinate (for "slice" mode) or None
    cumsum : ndarray, optional
        Precomputed cumsum for O(1) sum projections. If provided and both
        reduced axes use "sum" mode, uses fast O(n*m) cumsum projection.

    Returns
    -------
    data_2d : ndarray
        2D array oriented for imshow.
    extent : tuple
        (x_lo, x_hi, y_lo, y_hi) for imshow extent parameter.

    Raises
    ------
    ValueError
        If plot_x == plot_y.
    """
    if plot_x == plot_y:
        raise ValueError("plot_x and plot_y must be different")

    # Determine which axes to reduce
    all_axes = ["t", "x", "y", "z"]
    reduce_axes = [a for a in all_axes if a not in {plot_x, plot_y}]

    # Check if we can use fast cumsum projection
    # (both reduced axes must be "sum" mode with full range)
    modes = {axis: reductions.get(axis, ("slice", None))[0] for axis in reduce_axes}
    can_use_cumsum = (
        cumsum is not None
        and all(m == "sum" for m in modes.values())
    )

    if can_use_cumsum:
        # Use O(n*m) cumsum-based projection
        from atomkit.spatial_grid import project_2d_fast

        # Build reduce_ranges (full range for sum)
        reduce_ranges = {}
        for axis in reduce_axes:
            _, _, n, _ = get_axis_extent(grid, axis)
            reduce_ranges[axis] = (0, n - 1)

        result = project_2d_fast(cumsum, (plot_x, plot_y), reduce_ranges)

        # Transpose if needed
        if DIM_MAP_4D[plot_x] > DIM_MAP_4D[plot_y]:
            result = result.T

        x_lo, x_hi, _, _ = get_axis_extent(grid, plot_x)
        y_lo, y_hi, _, _ = get_axis_extent(grid, plot_y)
        return result, (x_lo, x_hi, y_lo, y_hi)

    # Fallback: standard numpy reduction
    reduction_list = []
    for axis in reduce_axes:
        mode, value = reductions.get(axis, ("slice", None))
        lo, hi, n, _ = get_axis_extent(grid, axis)
        reduction_list.append({
            "axis": axis,
            "dim": DIM_MAP_4D[axis],
            "mode": mode,
            "value": value,
            "lo": lo,
            "hi": hi,
            "n": n,
        })

    # Sort by dimension descending (reduce from back to front)
    reduction_list.sort(key=lambda x: x["dim"], reverse=True)

    # Apply reductions
    result = data
    current_dim_map = DIM_MAP_4D.copy()

    for r in reduction_list:
        dim = current_dim_map[r["axis"]]

        if r["mode"] == "slice":
            # Convert coordinate to index
            if r["axis"] == "t":
                idx = int(r["value"]) if r["value"] is not None else 0
            else:
                val = r["value"] if r["value"] is not None else (r["lo"] + r["hi"]) / 2
                idx = coord_to_index(val, r["lo"], r["hi"], r["n"])
            idx = max(0, min(idx, result.shape[dim] - 1))
            result = np.take(result, idx, axis=dim)
        else:
            # Reduction operation
            fn = {"sum": np.sum, "mean": np.mean, "max": np.max, "min": np.min}[r["mode"]]
            result = fn(result, axis=dim)

        # Update dimension map after removing an axis
        removed_dim = current_dim_map[r["axis"]]
        current_dim_map = {
            k: (v if v < removed_dim else v - 1)
            for k, v in current_dim_map.items()
            if k != r["axis"]
        }

    # Transpose if needed for correct orientation
    if DIM_MAP_4D[plot_x] > DIM_MAP_4D[plot_y]:
        result = result.T

    # Compute extent
    x_lo, x_hi, _, _ = get_axis_extent(grid, plot_x)
    y_lo, y_hi, _, _ = get_axis_extent(grid, plot_y)

    return result, (x_lo, x_hi, y_lo, y_hi)


def plot_2d_field(
    data: "NDArray",
    extent: tuple[float, float, float, float],
    xlabel: str = "x",
    ylabel: str = "y",
    title: str = "",
    cmap: str = "viridis",
    aspect: str = "auto",
    colorbar_label: str = "",
    figsize: tuple[float, float] = (10, 6),
    ax=None,
):
    """
    Plot a 2D field with imshow.

    Parameters
    ----------
    data : ndarray
        2D data to plot.
    extent : tuple
        (x_lo, x_hi, y_lo, y_hi) for imshow.
    xlabel, ylabel : str
        Axis labels.
    title : str
        Plot title.
    cmap : str
        Colormap name.
    aspect : str
        Aspect ratio ("auto" or "equal").
    colorbar_label : str
        Label for colorbar.
    figsize : tuple
        Figure size.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. If None, creates new figure.

    Returns
    -------
    fig : matplotlib.figure.Figure or None
        The figure (None if ax was provided).
    ax : matplotlib.axes.Axes
        The axes.
    im : matplotlib.image.AxesImage
        The image object.
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required: pip install matplotlib")

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = None

    im = ax.imshow(
        data,
        extent=extent,
        origin="lower",
        aspect=aspect,
        cmap=cmap,
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)

    if fig is not None:
        fig.colorbar(im, ax=ax, label=colorbar_label, shrink=0.8)
        plt.tight_layout()

    return fig, ax, im


# =============================================================================
# Legacy utilities (kept for backwards compatibility)
# =============================================================================


def _get_slice_data(
    grid: "SpatialGrid",
    axis: Literal["x", "y", "z"],
    cell_idx: int,
    field: str,
    t_idx: int,
    cell_agg: Literal["sum", "mean", "max", "min"],
) -> tuple[NDArray[np.float64], dict]:
    """
    Extract a 2D slice from the grid at a given cell index.

    Returns (data_2d, info) where data_2d is transposed for imshow (row=y, col=x).
    """
    ax_idx = _AXIS_MAP[axis]

    # Get 3D data for this timestep
    if field == "counts":
        data_3d = grid.cells.counts[t_idx]
    else:
        agg = grid.cells[field]
        accessor = getattr(agg, cell_agg)
        data_3d = accessor[t_idx]

    # Slice along the specified axis
    if ax_idx == 0:  # x slice -> (ny, nz)
        data_2d = data_3d[cell_idx, :, :]
        extent = (grid.box_bounds[2], grid.box_bounds[3],  # y
                  grid.box_bounds[4], grid.box_bounds[5])  # z
        xlabel, ylabel = "y", "z"
    elif ax_idx == 1:  # y slice -> (nx, nz)
        data_2d = data_3d[:, cell_idx, :]
        extent = (grid.box_bounds[0], grid.box_bounds[1],  # x
                  grid.box_bounds[4], grid.box_bounds[5])  # z
        xlabel, ylabel = "x", "z"
    else:  # z slice -> (nx, ny)
        data_2d = data_3d[:, :, cell_idx]
        extent = (grid.box_bounds[0], grid.box_bounds[1],  # x
                  grid.box_bounds[2], grid.box_bounds[3])  # y
        xlabel, ylabel = "x", "y"

    info = {
        "extent": extent,
        "xlabel": xlabel,
        "ylabel": ylabel,
        "axis": axis,
        "cell_index": cell_idx,
        "field": field,
    }

    return np.asarray(data_2d).T, info


def _get_projection_data(
    grid: "SpatialGrid",
    axis: Literal["x", "y", "z"],
    field: str,
    t_idx: int,
    cell_agg: Literal["sum", "mean", "max", "min"],
    projection: Literal["sum", "mean", "max", "min"],
) -> tuple[NDArray[np.float64], dict]:
    """
    Project grid data along an axis (reduce 3D -> 2D).

    Returns (data_2d, info) where data_2d is transposed for imshow (row=y, col=x).
    """
    ax_idx = _AXIS_MAP[axis]

    # Get 3D data for this timestep
    if field == "counts":
        data_3d = grid.cells.counts[t_idx]
    else:
        agg = grid.cells[field]
        accessor = getattr(agg, cell_agg)
        data_3d = accessor[t_idx]

    # Project along the specified axis
    proj_func = {"sum": np.sum, "mean": np.mean, "max": np.max, "min": np.min}[projection]
    data_2d = proj_func(data_3d, axis=ax_idx)

    if ax_idx == 0:  # project x -> (ny, nz)
        extent = (grid.box_bounds[2], grid.box_bounds[3],
                  grid.box_bounds[4], grid.box_bounds[5])
        xlabel, ylabel = "y", "z"
    elif ax_idx == 1:  # project y -> (nx, nz)
        extent = (grid.box_bounds[0], grid.box_bounds[1],
                  grid.box_bounds[4], grid.box_bounds[5])
        xlabel, ylabel = "x", "z"
    else:  # project z -> (nx, ny)
        extent = (grid.box_bounds[0], grid.box_bounds[1],
                  grid.box_bounds[2], grid.box_bounds[3])
        xlabel, ylabel = "x", "y"

    info = {
        "extent": extent,
        "xlabel": xlabel,
        "ylabel": ylabel,
        "axis": axis,
        "projection": projection,
        "field": field,
    }

    return np.asarray(data_2d).T, info


def _position_to_cell_index(grid: "SpatialGrid", axis: str, position: float) -> int:
    """Convert a spatial position to a cell index."""
    axis_idx = _AXIS_MAP[axis]
    lo = grid.box_bounds[axis_idx * 2]
    cs = grid.cell_size[axis_idx]
    n = grid.grid_shape[axis_idx]
    idx = int((position - lo) / cs)
    return max(0, min(idx, n - 1))


def _resolve_timestep(grid: "SpatialGrid", timestep: int | None) -> int:
    """Resolve a timestep value to an index."""
    if timestep is None:
        return 0
    for i, t_val in enumerate(grid.timestep_values):
        if t_val == timestep:
            return i
    raise ValueError(f"Timestep {timestep} not found in grid")


def grid_explorer(
    grid: "SpatialGrid",
    initial_field: str = "counts",
    initial_axis: Literal["x", "y", "z"] = "z",
    cmap: str = "viridis",
    figsize: tuple[float, float] = (8, 6),
):
    """
    Create an interactive marimo widget for exploring a SpatialGrid.

    Features:
    - Slice or project along any axis
    - Slider for position (slice mode) or projection aggregation
    - Timestep slider for multi-timestep grids
    - Field selector for available fields
    - Colormap options

    Parameters
    ----------
    grid : SpatialGrid
        The grid to explore.
    initial_field : str, default 'counts'
        Initial field to display.
    initial_axis : 'x', 'y', or 'z', default 'z'
        Initial slice/projection axis.
    cmap : str, default 'viridis'
        Matplotlib colormap.
    figsize : tuple, default (8, 6)
        Figure size.

    Returns
    -------
    marimo UI element
        Interactive widget for display in marimo notebook.
    """
    _check_deps()

    # Field options
    field_options = ["counts"] + [f for f in grid.fields if f not in ("coords", "_source_idx")]

    # UI elements
    mode_select = mo.ui.dropdown(
        options=["slice", "project"],
        value="slice",
        label="Mode",
    )

    axis_select = mo.ui.dropdown(
        options=["x", "y", "z"],
        value=initial_axis,
        label="Axis",
    )

    field_select = mo.ui.dropdown(
        options=field_options,
        value=initial_field if initial_field in field_options else "counts",
        label="Field",
    )

    # Cell aggregator (for non-counts fields)
    cell_agg_select = mo.ui.dropdown(
        options=["mean", "sum", "max", "min"],
        value="mean",
        label="Cell Agg",
    )

    # Projection aggregator
    proj_agg_select = mo.ui.dropdown(
        options=["sum", "mean", "max", "min"],
        value="sum",
        label="Proj Agg",
    )

    cmap_select = mo.ui.dropdown(
        options=["viridis", "plasma", "inferno", "magma", "cividis", "gray", "hot", "coolwarm"],
        value=cmap,
        label="Colormap",
    )

    aspect_select = mo.ui.dropdown(
        options=["auto", "equal"],
        value="auto",
        label="Aspect",
    )

    # Build the reactive UI
    def build_ui():
        # Get axis bounds for position slider
        axis = axis_select.value
        axis_idx = _AXIS_MAP[axis]
        lo = grid.box_bounds[axis_idx * 2]
        hi = grid.box_bounds[axis_idx * 2 + 1]

        pos_slider = mo.ui.slider(
            start=lo,
            stop=hi,
            value=(lo + hi) / 2,
            step=(hi - lo) / max(grid.grid_shape[axis_idx], 1),
            label=f"{axis} position",
            show_value=True,
        )

        # Timestep slider
        if grid.n_timesteps > 1:
            ts_slider = mo.ui.slider(
                start=0,
                stop=grid.n_timesteps - 1,
                value=0,
                step=1,
                label="Timestep",
                show_value=True,
            )
        else:
            ts_slider = None

        return pos_slider, ts_slider

    # This will be called reactively
    def render_plot(mode, axis, field, cell_agg, proj_agg, colormap, aspect, pos_slider, ts_slider):
        t_idx = ts_slider.value if ts_slider is not None else 0
        timestep = grid.timestep_values[t_idx]

        fig, ax = plt.subplots(figsize=figsize)

        try:
            if mode == "slice":
                cell_idx = _position_to_cell_index(grid, axis, pos_slider.value)
                data, info = _get_slice_data(
                    grid, axis, cell_idx, field, t_idx, cell_agg
                )
                title = f"{field} slice at {axis}={pos_slider.value:.1f}"
            else:
                data, info = _get_projection_data(
                    grid, axis, field, t_idx, cell_agg, proj_agg
                )
                title = f"{field} {proj_agg} along {axis}"

            if grid.n_timesteps > 1:
                title += f" (t={timestep})"

            im = ax.imshow(
                data,
                extent=info["extent"],
                origin="lower",
                aspect=aspect,
                cmap=colormap,
            )
            ax.set_xlabel(info["xlabel"])
            ax.set_ylabel(info["ylabel"])
            ax.set_title(title)
            fig.colorbar(im, ax=ax, label=field)

        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {e}", ha="center", va="center", transform=ax.transAxes)

        plt.tight_layout()
        return fig

    # Combine into reactive UI
    def make_explorer():
        pos_slider, ts_slider = build_ui()

        # Control rows
        row1 = mo.hstack([mode_select, axis_select, field_select], justify="start", gap=1)
        row2 = mo.hstack([cell_agg_select, proj_agg_select, cmap_select, aspect_select], justify="start", gap=1)
        row3 = mo.hstack([pos_slider], justify="start") if mode_select.value == "slice" else None
        row4 = mo.hstack([ts_slider], justify="start") if ts_slider is not None else None

        # Render
        fig = render_plot(
            mode_select.value,
            axis_select.value,
            field_select.value,
            cell_agg_select.value,
            proj_agg_select.value,
            cmap_select.value,
            aspect_select.value,
            pos_slider,
            ts_slider,
        )

        # Stack everything
        elements = [
            mo.md(f"**Grid:** {grid.grid_shape}, {grid.n_atoms:,} atoms, {grid.n_timesteps} timesteps"),
            row1,
            row2,
        ]
        if row3 is not None:
            elements.append(row3)
        if row4 is not None:
            elements.append(row4)
        elements.append(fig)

        return mo.vstack(elements, gap=0.5)

    return make_explorer()


def time_evolution(
    grid: "SpatialGrid",
    axis: Literal["x", "y", "z"],
    position: float,
    field: str = "counts",
    cell_aggregator: Literal["sum", "mean", "max", "min"] = "mean",
    cmap: str = "viridis",
    figsize: tuple[float, float] = (10, 4),
):
    """
    Show how a 1D line evolves over time (kymograph).

    Slices the grid at `position` along `axis`, then extracts a 1D line
    at the midpoint of the remaining axes. Stacks across timesteps to
    show temporal evolution.

    Parameters
    ----------
    grid : SpatialGrid
        Multi-timestep grid.
    axis : 'x', 'y', or 'z'
        Axis to slice along.
    position : float
        Position for the slice.
    field : str, default 'counts'
        Field to visualize.
    cell_aggregator : str, default 'mean'
        Aggregation for non-counts fields.
    cmap : str, default 'viridis'
        Colormap.
    figsize : tuple
        Figure size.

    Returns
    -------
    fig : matplotlib Figure
        The kymograph figure.
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required")

    if grid.n_timesteps < 2:
        raise ValueError("Need multi-timestep grid for time evolution")

    cell_idx = _position_to_cell_index(grid, axis, position)

    # Collect 1D slices across time
    lines = []
    info = None
    for t_idx in range(grid.n_timesteps):
        data_2d, info = _get_slice_data(
            grid, axis, cell_idx, field, t_idx, cell_aggregator
        )
        # Take middle row
        mid_idx = data_2d.shape[0] // 2
        lines.append(data_2d[mid_idx, :])

    kymograph = np.array(lines)  # (n_timesteps, n_cells)

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(
        kymograph,
        aspect="auto",
        origin="lower",
        cmap=cmap,
        extent=(info["extent"][0], info["extent"][1], 0, grid.n_timesteps),
    )
    ax.set_xlabel(info["xlabel"])
    ax.set_ylabel("Timestep index")
    ax.set_title(f"{field} evolution along {info['xlabel']} at {axis}={position:.1f}")
    fig.colorbar(im, ax=ax, label=field)
    plt.tight_layout()

    return fig


__all__ = [
    # Core utilities
    "get_field_data_4d",
    "get_axis_extent",
    "coord_to_index",
    "reduce_4d_to_2d",
    "plot_2d_field",
    "DIM_MAP_4D",
    "DIM_NAMES_4D",
    # Marimo widgets
    "grid_explorer",
    "time_evolution",
    # Availability flags
    "MARIMO_AVAILABLE",
    "MATPLOTLIB_AVAILABLE",
]
