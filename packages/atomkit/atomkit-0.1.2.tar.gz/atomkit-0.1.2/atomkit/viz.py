"""
Fast visualization for SpatialGrid using marimo.

Provides interactive heatmap exploration with sliders for time and space.
Uses the fast slice_2d/project_2d methods on SpatialGrid.

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
        axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
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
        timestep = grid.timestep_values[ts_slider.value] if ts_slider is not None else None

        fig, ax = plt.subplots(figsize=figsize)

        try:
            if mode == "slice":
                data, info = grid.slice_2d(
                    axis=axis,
                    position=pos_slider.value,
                    field=field,
                    timestep=timestep,
                    cell_aggregator=cell_agg,
                )
                title = f"{field} slice at {axis}={pos_slider.value:.1f}"
            else:
                data, info = grid.project_2d(
                    axis=axis,
                    field=field,
                    timestep=timestep,
                    cell_aggregator=cell_agg,
                    projection=proj_agg,
                )
                title = f"{field} {proj_agg} along {axis}"

            if timestep is not None:
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
    cell_aggregator: str = "mean",
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

    # Collect 1D slices across time
    lines = []
    for ts in grid.timestep_values:
        data_2d, info = grid.slice_2d(
            axis=axis,
            position=position,
            field=field,
            timestep=ts,
            cell_aggregator=cell_aggregator,
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


__all__ = ["grid_explorer", "time_evolution", "MARIMO_AVAILABLE", "MATPLOTLIB_AVAILABLE"]
