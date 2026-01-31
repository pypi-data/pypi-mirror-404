# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "atomkit>=0.1.2",
#     "hdf5plugin",
#     "marimo",
#     "matplotlib==3.10.8",
#     "numpy==2.3.5",
# ]
# ///
"""
SpatialGrid Explorer - Interactive visualization for atomkit grids.

Run: marimo run examples/grid_explorer.py
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from pathlib import Path
    from atomkit import SpatialGrid
    return Path, SpatialGrid, mo, np, plt


@app.cell
def _(mo):
    mo.md("# SpatialGrid Explorer\n*Interactive visualization for molecular dynamics grids*")
    return


@app.cell
def _(Path, mo):
    # File selection - scan for .h5 and .lammpstrj files
    _h5_files = sorted(Path(".").glob("*.h5"))
    _traj_files = sorted(Path(".").glob("*.lammpstrj"))
    _all_files = [str(f) for f in _h5_files + _traj_files]

    if not _all_files:
        mo.stop(True, mo.md("⚠️ No `.h5` or `.lammpstrj` files found in current directory"))

    file_select = mo.ui.dropdown(_all_files, value=_all_files[0], label="File")
    cell_size_input = mo.ui.number(value=5.0, start=1.0, stop=20.0, step=0.5, label="Cell size (Å)")
    coord_type_select = mo.ui.dropdown(
        ["auto", "unwrapped", "wrapped", "scaled"],
        value="auto",
        label="Coords"
    )
    rebuild_btn = mo.ui.run_button(label="Rebuild")

    mo.hstack([file_select, cell_size_input, coord_type_select, rebuild_btn], justify="start")
    return cell_size_input, coord_type_select, file_select, rebuild_btn


@app.cell
def _(mo):
    # State to track current grid for cleanup - returns (getter, setter)
    get_prev_grid, set_prev_grid = mo.state(None)
    return get_prev_grid, set_prev_grid


@app.cell
def _(Path, SpatialGrid, cell_size_input, coord_type_select, file_select, get_prev_grid, mo, rebuild_btn, set_prev_grid):
    # Close previous grid to free memory/file handles
    _prev = get_prev_grid()
    if _prev is not None:
        _prev.close()

    _path = Path(file_select.value)
    _cell_size = cell_size_input.value
    _coord_type = coord_type_select.value

    # Cache filename includes cell size and coord type
    _coord_suffix = "" if _coord_type == "auto" else f"_{_coord_type[:2]}"
    _cache_name = _path.stem + f"_cs{_cell_size:.1f}{_coord_suffix}.h5"
    _cache_path = _path.parent / _cache_name

    if _path.suffix == ".h5" and not rebuild_btn.value:
        grid = SpatialGrid.load(_path)
        _status = f"Loaded: `{_path.name}`"
    elif _cache_path.exists() and not rebuild_btn.value:
        grid = SpatialGrid.load(_cache_path)
        _status = f"Loaded cache: `{_cache_name}`"
    else:
        if _path.suffix == ".h5":
            mo.stop(True, mo.md("⚠️ Select a `.lammpstrj` file to rebuild with different cell size"))
        with mo.status.spinner("Building grid..."):
            grid = SpatialGrid.from_lammps(_path, cell_size=_cell_size, coord_type=_coord_type)
            grid.save(_cache_path, compression=3)
        _status = f"Built: `{_cache_name}`"

    # Track grid for cleanup on next load
    set_prev_grid(grid)

    available_fields = ["counts"] + [f for f in grid.fields if f not in ("coords", "_source_idx")]

    mo.md(f"**{_status}** | shape=`{grid.grid_shape}` | atoms=`{grid.n_atoms:,}` | timesteps=`{grid.n_timesteps}` | fields=`{available_fields}`")
    return available_fields, grid


@app.cell
def _(available_fields, mo):
    # Plot axes and field selection
    plot_x = mo.ui.dropdown(["x", "y", "z", "t"], value="x", label="Plot X")
    plot_y = mo.ui.dropdown(["x", "y", "z", "t"], value="y", label="Plot Y")
    field_select = mo.ui.dropdown(available_fields, value="counts", label="Field")
    cell_agg = mo.ui.dropdown(["mean", "sum", "max", "min"], value="mean", label="Cell Agg")
    cmap = mo.ui.dropdown(["viridis", "plasma", "inferno", "hot", "coolwarm", "gray"], value="viridis", label="Cmap")
    aspect = mo.ui.dropdown(["auto", "equal"], value="auto", label="Aspect")
    mo.hstack([plot_x, plot_y, field_select, cell_agg, cmap, aspect], justify="start")
    return aspect, cell_agg, cmap, field_select, plot_x, plot_y


@app.cell
def _(grid, mo, plot_x, plot_y):
    # Remaining axes controls
    if plot_x.value == plot_y.value:
        mo.stop(True, mo.md("⚠️ Select different axes for X and Y"))

    _all = ["x", "y", "z", "t"]
    _remaining = [a for a in _all if a not in {plot_x.value, plot_y.value}]

    # First remaining axis
    r1_name = _remaining[0]
    r1_mode = mo.ui.dropdown(["slice", "sum", "mean", "max"], value="slice", label=f"{r1_name.upper()}")
    if r1_name == "t":
        r1_slider = mo.ui.slider(0, grid.n_timesteps - 1, value=0, step=1, label=r1_name, show_value=False)
        r1_range = (0, grid.n_timesteps - 1, grid.n_timesteps)
    else:
        _i = {"x": 0, "y": 1, "z": 2}[r1_name]
        _lo, _hi = grid.box_bounds[_i*2], grid.box_bounds[_i*2+1]
        _n = grid.grid_shape[_i]
        r1_slider = mo.ui.slider(_lo, _hi, value=(_lo+_hi)/2, step=(_hi-_lo)/_n, label=r1_name, show_value=False)
        r1_range = (_lo, _hi, _n)

    # Second remaining axis
    r2_name = _remaining[1]
    r2_mode = mo.ui.dropdown(["slice", "sum", "mean", "max"], value="slice", label=f"{r2_name.upper()}")
    if r2_name == "t":
        r2_slider = mo.ui.slider(0, grid.n_timesteps - 1, value=0, step=1, label=r2_name, show_value=False)
        r2_range = (0, grid.n_timesteps - 1, grid.n_timesteps)
    else:
        _i = {"x": 0, "y": 1, "z": 2}[r2_name]
        _lo, _hi = grid.box_bounds[_i*2], grid.box_bounds[_i*2+1]
        _n = grid.grid_shape[_i]
        r2_slider = mo.ui.slider(_lo, _hi, value=(_lo+_hi)/2, step=(_hi-_lo)/_n, label=r2_name, show_value=False)
        r2_range = (_lo, _hi, _n)

    return r1_mode, r1_name, r1_range, r1_slider, r2_mode, r2_name, r2_range, r2_slider


@app.cell
def _(mo, r1_mode, r1_name, r1_slider, r2_mode, r2_name, r2_slider):
    # Display remaining axis controls - slider only when slice mode
    # Format value display (scientific for large/small, otherwise short float)
    def _fmt(name, val):
        if name == "t":
            return f"t={int(val)}"
        if abs(val) > 1000 or (abs(val) < 0.01 and val != 0):
            return f"{val:.2e}"
        return f"{val:.1f}"

    if r1_mode.value == "slice":
        _r1_ui = mo.hstack([r1_mode, r1_slider, mo.md(f"**{_fmt(r1_name, r1_slider.value)}**")])
    else:
        _r1_ui = r1_mode

    if r2_mode.value == "slice":
        _r2_ui = mo.hstack([r2_mode, r2_slider, mo.md(f"**{_fmt(r2_name, r2_slider.value)}**")])
    else:
        _r2_ui = r2_mode

    mo.vstack([_r1_ui, _r2_ui])
    return


@app.cell
def _(
    aspect, cell_agg, cmap, field_select, grid, np, plt, plot_x, plot_y,
    r1_mode, r1_name, r1_range, r1_slider,
    r2_mode, r2_name, r2_range, r2_slider,
):
    # Build 4D data: counts or aggregated field
    if field_select.value == "counts":
        _data_4d = grid.counts.astype(np.float64)
    else:
        _cell_data = []
        for _t in range(grid.n_timesteps):
            _cell_data.append(grid._cell_field_3d(field_select.value, _t, cell_agg.value))
        _data_4d = np.stack(_cell_data, axis=0)

    _axis_to_dim = {"t": 0, "x": 1, "y": 2, "z": 3}

    def _reduce(data, axis_name, mode_val, slider_val, rng, axis_map):
        dim = axis_map[axis_name]
        if mode_val == "slice":
            lo, hi, n = rng
            idx = int(slider_val) if axis_name == "t" else min(int((slider_val - lo) / ((hi - lo) / n)), n - 1)
            idx = max(0, min(idx, data.shape[dim] - 1))
            return np.take(data, idx, axis=dim)
        fn = {"sum": np.sum, "mean": np.mean, "max": np.max}[mode_val]
        return fn(data, axis=dim)

    # Reduce from highest dim to lowest
    _reductions = [
        (r1_name, r1_mode.value, r1_slider.value, r1_range),
        (r2_name, r2_mode.value, r2_slider.value, r2_range),
    ]
    _reductions.sort(key=lambda x: _axis_to_dim[x[0]], reverse=True)

    _data = _data_4d
    for _name, _mode, _sval, _rng in _reductions:
        _data = _reduce(_data, _name, _mode, _sval, _rng, _axis_to_dim)
        _rdim = _axis_to_dim[_name]
        _axis_to_dim = {k: (v if v < _rdim else v - 1) for k, v in _axis_to_dim.items() if k != _name}

    # Extents
    def _extent(ax):
        if ax == "t":
            return 0, grid.n_timesteps, "timestep"
        i = {"x": 0, "y": 1, "z": 2}[ax]
        return grid.box_bounds[i*2], grid.box_bounds[i*2+1], ax

    _x_lo, _x_hi, _x_lbl = _extent(plot_x.value)
    _y_lo, _y_hi, _y_lbl = _extent(plot_y.value)

    # Transpose for correct orientation
    if {"t": 0, "x": 1, "y": 2, "z": 3}[plot_x.value] < {"t": 0, "x": 1, "y": 2, "z": 3}[plot_y.value]:
        _data = _data.T

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    _im = ax.imshow(_data, extent=(_x_lo, _x_hi, _y_lo, _y_hi), origin="lower",
                    aspect=aspect.value, cmap=cmap.value)
    ax.set_xlabel(_x_lbl)
    ax.set_ylabel(_y_lbl)

    # Title
    _parts = []
    for _n, _m, _s, _ in [(r1_name, r1_mode.value, r1_slider.value, None),
                          (r2_name, r2_mode.value, r2_slider.value, None)]:
        _parts.append(f"{_n}={_s:.1f}" if _m == "slice" and _n != "t" else
                      f"t={int(_s)}" if _m == "slice" else f"{_n}:{_m}")
    ax.set_title(f"{field_select.value} | " + " | ".join(_parts))

    fig.colorbar(_im, ax=ax, label=field_select.value, shrink=0.8)
    plt.tight_layout()
    fig
    return ax, fig


if __name__ == "__main__":
    app.run()
