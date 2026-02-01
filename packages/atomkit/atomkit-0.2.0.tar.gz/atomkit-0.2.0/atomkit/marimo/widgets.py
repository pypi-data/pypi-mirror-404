"""
Marimo widgets for atomkit.

Requires marimo to be installed: pip install marimo
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from atomkit import SpatialGrid

# Lazy import marimo to avoid import errors when not installed
_mo = None


def _get_marimo():
    """Lazy import marimo."""
    global _mo
    if _mo is None:
        try:
            import marimo as mo

            _mo = mo
        except ImportError:
            raise ImportError(
                "marimo is required for atomkit.marimo widgets. "
                "Install with: pip install marimo"
            )
    return _mo


class GridLoader:
    """
    Interactive grid loader widget for marimo notebooks.

    Displays a file selector with load button. The `.value` property returns
    the loaded SpatialGrid (or None if not yet loaded).

    Usage
    -----
    ```python
    # Cell 1: Create and display the loader
    from atomkit.marimo import GridLoader
    loader = GridLoader()
    loader  # displays the UI

    # Cell 2: Use the grid (reactive to loader)
    grid = loader.value
    if grid is not None:
        mo.md(f"Loaded {grid.n_atoms:,} atoms")
    ```

    Parameters
    ----------
    directory : str or Path, optional
        Directory to scan for files. Defaults to current directory.
    patterns : list[str], optional
        Glob patterns for file types. Defaults to ["*.h5", "*.lammpstrj"].
    default_cell_size : float, optional
        Default cell size in Angstroms for LAMMPS conversion. Defaults to 5.0.
    default_coord_type : str, optional
        Default coordinate type for LAMMPS. Defaults to "auto".
    """

    def __init__(
        self,
        directory: str | Path = ".",
        patterns: list[str] | None = None,
        default_cell_size: float = 5.0,
        default_coord_type: str = "auto",
    ):
        self._directory = Path(directory)
        self._patterns = patterns or ["*.h5", "*.lammpstrj"]
        self._default_cell_size = default_cell_size
        self._default_coord_type = default_coord_type

        self._cached_grid: SpatialGrid | None = None
        self._cached_key: tuple | None = None
        self._file_path: Path | None = None

        self._build_ui()

    def _build_ui(self):
        """Build marimo UI components."""
        mo = _get_marimo()

        # Scan for files
        files = []
        for pattern in self._patterns:
            files.extend(self._directory.glob(pattern))
        files = sorted(files)

        if not files:
            self._file_select = None
            self._no_files_msg = mo.md(
                f"⚠️ No files matching `{self._patterns}` found in `{self._directory}`"
            )
            return

        file_options = [str(f) for f in files]

        # Simple UI elements
        self._file_select = mo.ui.dropdown(
            file_options, value=file_options[0], label="File"
        )
        self._cell_size = mo.ui.number(
            value=self._default_cell_size,
            start=1.0,
            stop=50.0,
            step=0.5,
            label="Cell size Å",
        )
        self._coord_type = mo.ui.dropdown(
            ["auto", "unwrapped", "wrapped", "scaled"],
            value=self._default_coord_type,
            label="Coords",
        )
        self._load_btn = mo.ui.run_button(label="Load")

    @property
    def value(self) -> "SpatialGrid | None":
        """
        The loaded SpatialGrid, or None if Load not clicked.

        Access this from a DIFFERENT cell than where the loader is displayed.
        """
        if self._file_select is None:
            return None

        # Only load when button is clicked
        if not self._load_btn.value:
            return None

        # Get current selections
        file_path = self._file_select.value
        cell_size = self._cell_size.value
        coord_type = self._coord_type.value

        # Cache key - only reload if parameters changed
        cache_key = (file_path, cell_size, coord_type)
        if cache_key == self._cached_key:
            return self._cached_grid

        # Close previous grid
        if self._cached_grid is not None:
            self._cached_grid.close()

        # Load the grid
        self._cached_grid, self._file_path = self._load_grid(
            file_path, cell_size, coord_type
        )
        self._cached_key = cache_key
        return self._cached_grid

    @property
    def file_path(self) -> Path | None:
        """Path to the currently loaded file (H5 file, possibly cached)."""
        return self._file_path

    @property
    def button(self):
        """The load button - use this for marimo reactivity tracking."""
        return self._load_btn

    def _load_grid(
        self, file_path: str, cell_size: float, coord_type: str
    ) -> tuple["SpatialGrid", Path]:
        """Load grid from file, converting LAMMPS if needed."""
        from atomkit import SpatialGrid

        path = Path(file_path)

        if path.suffix == ".h5":
            return SpatialGrid.load(path), path

        # LAMMPS file - check for cached H5
        coord_suffix = "" if coord_type == "auto" else f"_{coord_type[:2]}"
        cache_name = f"{path.stem}_cs{cell_size:.1f}{coord_suffix}.h5"
        cache_path = path.parent / cache_name

        if cache_path.exists():
            return SpatialGrid.load(cache_path), cache_path

        # Convert LAMMPS to H5 (shows tqdm progress for large files)
        grid = SpatialGrid.from_lammps(path, cell_size=cell_size, coord_type=coord_type)
        grid.save(cache_path, compression=3)
        return SpatialGrid.load(cache_path), cache_path  # Reload for mmap

    def close(self):
        """Close the currently loaded grid and free resources."""
        if self._cached_grid is not None:
            self._cached_grid.close()
            self._cached_grid = None
            self._cached_key = None

    def _display_(self):
        """Marimo display integration."""
        mo = _get_marimo()

        if self._file_select is None:
            return self._no_files_msg

        # Simple hstack layout like the original
        return mo.hstack(
            [self._file_select, self._cell_size, self._coord_type, self._load_btn],
            justify="start",
        )

    def __repr__(self) -> str:
        if self._cached_grid is not None:
            return f"GridLoader(loaded={self._file_path})"
        return f"GridLoader(directory={self._directory})"


class GridViewer:
    """
    Interactive 2D slice viewer for SpatialGrid data.

    Displays controls for selecting which 2D plane to view from the 4D data
    (t, x, y, z), with options for slicing or reducing the remaining axes.

    Usage
    -----
    ```python
    # Cell 1: Create viewer (after loading grid)
    from atomkit.marimo import GridViewer
    viewer = GridViewer(grid)
    viewer
    return viewer, viewer.controls

    # Cell 2: Display the plot (reactive to controls)
    viewer.plot()
    ```

    Parameters
    ----------
    grid : SpatialGrid
        The grid to visualize.
    default_field : str, optional
        Default field to display. Defaults to "counts".
    default_cmap : str, optional
        Default colormap. Defaults to "viridis".
    """

    def __init__(
        self,
        grid: "SpatialGrid",
        default_field: str = "counts",
        default_cmap: str = "viridis",
    ):
        self._grid = grid
        self._default_field = default_field
        self._default_cmap = default_cmap
        self._build_ui()

    def _build_ui(self):
        """Build marimo UI components."""
        mo = _get_marimo()
        grid = self._grid

        # Available fields
        fields = ["counts"] + grid.cells.fields
        default_field = self._default_field if self._default_field in fields else fields[0]

        # Main controls
        self._plot_x = mo.ui.dropdown(["x", "y", "z", "t"], value="x", label="X")
        self._plot_y = mo.ui.dropdown(["x", "y", "z", "t"], value="y", label="Y")
        self._field = mo.ui.dropdown(fields, value=default_field, label="Field")
        self._agg = mo.ui.dropdown(["mean", "sum", "max", "min"], value="mean", label="Agg")
        self._cmap = mo.ui.dropdown(
            ["viridis", "plasma", "inferno", "hot", "coolwarm", "gray"],
            value=self._default_cmap,
            label="Cmap",
        )
        self._aspect = mo.ui.dropdown(["auto", "equal"], value="auto", label="Aspect")

        # Axis reduction controls (for the 2 non-plotted axes)
        # We'll create sliders for all axes; visibility controlled in _display_
        self._axis_modes = {}
        self._axis_sliders = {}

        for axis in ["t", "x", "y", "z"]:
            self._axis_modes[axis] = mo.ui.dropdown(
                ["slice", "sum", "mean", "max"], value="slice", label=axis.upper()
            )
            if axis == "t":
                self._axis_sliders[axis] = mo.ui.slider(
                    0, max(0, grid.n_timesteps - 1), value=0, step=1, label=axis
                )
            else:
                i = {"x": 0, "y": 1, "z": 2}[axis]
                lo, hi = grid.box_bounds[i * 2], grid.box_bounds[i * 2 + 1]
                n = grid.grid_shape[i]
                step = (hi - lo) / n if n > 0 else 1
                self._axis_sliders[axis] = mo.ui.slider(
                    lo, hi, value=(lo + hi) / 2, step=step, label=axis
                )

    @property
    def controls(self):
        """All UI controls - return this for marimo reactivity."""
        mo = _get_marimo()
        return mo.ui.dictionary({
            "plot_x": self._plot_x,
            "plot_y": self._plot_y,
            "field": self._field,
            "agg": self._agg,
            "cmap": self._cmap,
            "aspect": self._aspect,
            **{f"mode_{k}": v for k, v in self._axis_modes.items()},
            **{f"slider_{k}": v for k, v in self._axis_sliders.items()},
        })

    def _get_remaining_axes(self) -> list[str]:
        """Get the two axes not being plotted."""
        all_axes = ["t", "x", "y", "z"]
        return [a for a in all_axes if a not in {self._plot_x.value, self._plot_y.value}]

    def get_data_2d(self):
        """
        Get the 2D data array based on current UI selections.

        Uses shared viz utilities for efficient 4D -> 2D reduction.
        When both reduced axes use "sum" mode, uses O(n*m) cumsum projection.

        Returns
        -------
        data : ndarray, shape (n_x, n_y)
            2D array for plotting.
        extent : tuple
            (x_lo, x_hi, y_lo, y_hi) for imshow.
        """
        from atomkit.viz import get_field_data_4d, reduce_4d_to_2d

        grid = self._grid
        field = self._field.value
        agg = self._agg.value
        plot_x, plot_y = self._plot_x.value, self._plot_y.value

        if plot_x == plot_y:
            raise ValueError("X and Y axes must be different")

        # Get 4D data using shared utility
        data_4d = get_field_data_4d(grid, field, agg)

        # Build reductions dict for non-plotted axes
        remaining = self._get_remaining_axes()
        reductions = {}
        for axis in remaining:
            mode = self._axis_modes[axis].value
            slider_val = self._axis_sliders[axis].value
            reductions[axis] = (mode, slider_val)

        # Try to get cumsum for fast projection (only for sum aggregation)
        cumsum = None
        if agg == "sum" and field != "counts":
            try:
                cumsum = grid.cells[field]._cumsum
            except (AttributeError, KeyError):
                pass
        elif field == "counts":
            try:
                cumsum = grid.cells._counts_cumsum
                if cumsum is not None:
                    cumsum = cumsum.astype(float)
            except AttributeError:
                pass

        # Use shared utility for 4D -> 2D reduction
        return reduce_4d_to_2d(data_4d, grid, plot_x, plot_y, reductions, cumsum)

    def plot(self, figsize=(10, 6)):
        """
        Create and return the matplotlib figure.

        Parameters
        ----------
        figsize : tuple, optional
            Figure size. Defaults to (10, 6).

        Returns
        -------
        fig : matplotlib.figure.Figure
            The plot figure.
        """
        import matplotlib.pyplot as plt

        data, (x_lo, x_hi, y_lo, y_hi) = self.get_data_2d()

        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(
            data,
            extent=(x_lo, x_hi, y_lo, y_hi),
            origin="lower",
            aspect=self._aspect.value,
            cmap=self._cmap.value,
        )

        # Labels
        plot_x, plot_y = self._plot_x.value, self._plot_y.value
        ax.set_xlabel("timestep" if plot_x == "t" else plot_x)
        ax.set_ylabel("timestep" if plot_y == "t" else plot_y)

        # Title showing reduction info
        remaining = self._get_remaining_axes()
        parts = []
        for axis in remaining:
            mode = self._axis_modes[axis].value
            if mode == "slice":
                val = self._axis_sliders[axis].value
                if axis == "t":
                    parts.append(f"t={int(val)}")
                else:
                    parts.append(f"{axis}={val:.1f}")
            else:
                parts.append(f"{axis}:{mode}")

        title = f"{self._field.value}"
        if self._field.value != "counts":
            title += f" ({self._agg.value})"
        title += " | " + " | ".join(parts)
        ax.set_title(title)

        fig.colorbar(im, ax=ax, label=self._field.value, shrink=0.8)
        plt.tight_layout()
        return fig

    def _display_(self):
        """Marimo display integration - shows the main controls."""
        mo = _get_marimo()

        # Main row: plot axes, field, agg, cmap, aspect
        main_row = mo.hstack(
            [self._plot_x, self._plot_y, self._field, self._agg, self._cmap, self._aspect],
            justify="start",
        )

        # Remaining axes controls (only show for non-plotted axes)
        remaining = self._get_remaining_axes()
        axis_rows = []
        for axis in remaining:
            mode = self._axis_modes[axis]
            slider = self._axis_sliders[axis]
            # Show slider only in slice mode
            axis_rows.append(mo.hstack([mode, slider], justify="start"))

        return mo.vstack([main_row, *axis_rows])

    def __repr__(self) -> str:
        return f"GridViewer(grid={self._grid!r})"
