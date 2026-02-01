# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "atomkit>=0.1.3",
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
    from atomkit.marimo import GridLoader, GridViewer
    return GridLoader, GridViewer, mo


@app.cell
def _(mo):
    mo.md("# SpatialGrid Explorer\n*Interactive visualization for molecular dynamics grids*")
    return


@app.cell
def _(GridLoader):
    # Grid loader widget - select file and click Load
    loader = GridLoader(default_cell_size=5.0, default_coord_type="auto")
    button = loader.button
    loader
    return loader, button


@app.cell
def _(loader, button, mo):
    # Reactive: re-runs when button is clicked
    if not button.value:
        mo.stop(True, mo.md("Select a file and click **Load** to start"))
    grid = loader.value

    _info = f"**Loaded:** shape=`{grid.grid_shape}` | atoms=`{grid.n_atoms:,}` | timesteps=`{grid.n_timesteps}`"
    _info += f"\n**Fields:** {grid.cells.fields}"
    if grid.source_box.is_valid:
        _b = grid.source_box.bounds
        _info += f"\n**Source box:** [{_b[0]:.0f}, {_b[1]:.0f}] x [{_b[2]:.0f}, {_b[3]:.0f}] x [{_b[4]:.0f}, {_b[5]:.0f}]"
    mo.md(_info)
    return (grid,)


@app.cell
def _(GridViewer, grid):
    # Grid viewer widget - all controls in one
    viewer = GridViewer(grid)
    controls = viewer.controls
    viewer
    return viewer, controls


@app.cell
def _(viewer, controls):
    # Reactive plot - re-runs when any control changes
    _ = controls  # Depend on controls for reactivity
    viewer.plot()
    return


if __name__ == "__main__":
    app.run()
