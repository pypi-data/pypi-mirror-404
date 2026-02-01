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
Notch Explorer - Find notches, measure dimensions, and sample stress between them.

Run: marimo run examples/notch_explorer.py
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from atomkit import SpatialGrid, SourceBox
    from atomkit.marimo import GridLoader
    from atomkit.viz import get_field_data_4d, reduce_4d_to_2d, get_axis_extent, coord_to_index
    from atomkit.spatial_grid import project_2d_fast, _box_sum_4d
    return GridLoader, Rectangle, SourceBox, SpatialGrid, _box_sum_4d, coord_to_index, get_axis_extent, get_field_data_4d, mo, np, plt, project_2d_fast, reduce_4d_to_2d


@app.cell
def _(mo):
    mo.md("# Notch Explorer\n*Detect notches, measure dimensions, sample stress between notch tips*")
    return


# =============================================================================
# SECTION 1: Load Grid
# =============================================================================

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
        mo.stop(True, mo.md("Select a grid file and click **Load**"))
    grid = loader.value

    _info = f"**Loaded:** shape=`{grid.grid_shape}` | atoms=`{grid.n_atoms:,}` | timesteps=`{grid.n_timesteps}`"
    _info += f"\n**Cell aggregates:** {grid.cells.fields}"

    # Show source box if available
    if grid.source_box.is_valid:
        _b = grid.source_box.bounds
        _info += f"\n**Source box:** x=[{_b[0]:.1f}, {_b[1]:.1f}] y=[{_b[2]:.1f}, {_b[3]:.1f}] z=[{_b[4]:.1f}, {_b[5]:.1f}]"
        if grid.source_box.is_triclinic:
            _info += f" *(triclinic: tilt={grid.source_box.tilt})*"

    mo.md(_info)
    return (grid,)


# =============================================================================
# SECTION 2: View Selection (which 2D plane to analyze)
# =============================================================================

@app.cell
def _(mo):
    mo.md("## Step 1: Select View Plane")
    return


@app.cell
def _(grid, mo):
    plot_x = mo.ui.dropdown(["x", "y", "z"], value="x", label="Plot X")
    plot_y = mo.ui.dropdown(["x", "y", "z"], value="z", label="Plot Y")
    # Toggle for source box constraint (only shown if available)
    use_source_box = mo.ui.checkbox(value=True, label="Constrain to source box") if grid.source_box.is_valid else None
    # Toggle for density calculation method
    density_non_empty = mo.ui.checkbox(value=True, label="Density: non-empty cells only")
    _widgets = [plot_x, plot_y]
    if use_source_box:
        _widgets.append(use_source_box)
    _widgets.append(density_non_empty)
    mo.hstack(_widgets, justify="start")
    return density_non_empty, plot_x, plot_y, use_source_box


@app.cell
def _(get_axis_extent, get_field_data_4d, grid, mo, np, plot_x, plot_y, project_2d_fast, reduce_4d_to_2d, use_source_box):
    if plot_x.value == plot_y.value:
        mo.stop(True, mo.md("⚠️ Select different axes"))

    _px, _py = plot_x.value, plot_y.value
    _all_spatial = ["x", "y", "z"]
    sum_axis_name = [a for a in _all_spatial if a not in {_px, _py}][0]

    # Use O(1) cumsum projection for counts (sum over t and sum_axis)
    # This is O(nx * ny) instead of O(t * nx * ny * nz)
    _counts_cumsum = grid.cells._counts_cumsum
    if _counts_cumsum is not None:
        _data = project_2d_fast(
            _counts_cumsum.astype(np.float64),
            (_px, _py),
            reduce_ranges=None,  # Full range
        )
    else:
        # Fallback to numpy
        _counts_4d = get_field_data_4d(grid, "counts", "sum")
        _reductions = {"t": ("sum", None), sum_axis_name: ("sum", None)}
        _data, _ = reduce_4d_to_2d(_counts_4d, grid, _px, _py, _reductions)

    # Get extents
    x_lo_full, x_hi_full, n_x, _ = get_axis_extent(grid, _px)
    y_lo_full, y_hi_full, n_y, _ = get_axis_extent(grid, _py)
    cell_w_x = (x_hi_full - x_lo_full) / n_x
    cell_w_y = (y_hi_full - y_lo_full) / n_y

    # Apply source box constraint if enabled
    _use_constraint = use_source_box is not None and use_source_box.value and grid.source_box.is_valid
    if _use_constraint:
        _sb = grid.source_box.bounds
        _src_bounds = {"x": (_sb[0], _sb[1]), "y": (_sb[2], _sb[3]), "z": (_sb[4], _sb[5])}

        x_lo = max(_src_bounds[_px][0], x_lo_full)
        x_hi = min(_src_bounds[_px][1], x_hi_full)
        y_lo = max(_src_bounds[_py][0], y_lo_full)
        y_hi = min(_src_bounds[_py][1], y_hi_full)

        _x_i0 = max(0, int((x_lo - x_lo_full) / cell_w_x))
        _x_i1 = min(n_x, int(np.ceil((x_hi - x_lo_full) / cell_w_x)))
        _y_i0 = max(0, int((y_lo - y_lo_full) / cell_w_y))
        _y_i1 = min(n_y, int(np.ceil((y_hi - y_lo_full) / cell_w_y)))

        data_2d = _data[_x_i0:_x_i1, _y_i0:_y_i1]
        n_x = _x_i1 - _x_i0
        n_y = _y_i1 - _y_i0

        x_lo = x_lo_full + _x_i0 * cell_w_x
        x_hi = x_lo_full + _x_i1 * cell_w_x
        y_lo = y_lo_full + _y_i0 * cell_w_y
        y_hi = y_lo_full + _y_i1 * cell_w_y
    else:
        data_2d = _data
        x_lo, x_hi = x_lo_full, x_hi_full
        y_lo, y_hi = y_lo_full, y_hi_full

    # Cell width for summed axis
    _sum_lo, _sum_hi, _, _ = get_axis_extent(grid, sum_axis_name)
    _sum_n = grid.grid_shape[{"x": 0, "y": 1, "z": 2}[sum_axis_name]]
    cell_w_sum = (_sum_hi - _sum_lo) / _sum_n

    _constraint_info = " **(constrained to source box)**" if _use_constraint else ""
    mo.md(f"**View:** {_px} vs {_py} (summed over {sum_axis_name}, t) | shape: ({n_x}, {n_y}){_constraint_info}")
    return cell_w_sum, cell_w_x, cell_w_y, data_2d, n_x, n_y, sum_axis_name, x_hi, x_lo, y_hi, y_lo


@app.cell
def _(cell_w_sum, cell_w_x, cell_w_y, data_2d, density_non_empty, grid, mo, np):
    # =========================
    # Global atom density calculation
    # =========================
    # Cell volume in Å³
    _cell_volume = cell_w_x * cell_w_y * cell_w_sum

    # Mean counts over timesteps (data_2d is already summed over time and sum_axis)
    # Need to get per-timestep data for proper averaging
    _total_atoms_per_t = []
    _non_empty_cells_per_t = []
    _total_cells = np.prod(grid.grid_shape)

    for _t in range(grid.n_timesteps):
        _counts_t = grid.counts[_t]
        _total_atoms_per_t.append(_counts_t.sum())
        _non_empty_cells_per_t.append((_counts_t > 0).sum())

    # Time-averaged values
    mean_total_atoms = np.mean(_total_atoms_per_t)
    mean_non_empty_cells = np.mean(_non_empty_cells_per_t)

    # Volume calculation
    if density_non_empty.value:
        effective_volume = mean_non_empty_cells * _cell_volume  # Å³
        volume_method = "non-empty cells"
    else:
        effective_volume = _total_cells * _cell_volume  # Å³
        volume_method = "all cells"

    # Density in atoms/Å³
    global_density = mean_total_atoms / effective_volume if effective_volume > 0 else 0.0

    mo.md(f"""
**Global density:** `{global_density:.6f}` atoms/Å³ ({volume_method})
- Mean atoms: `{mean_total_atoms:,.0f}` | Volume: `{effective_volume:,.0f}` Å³
- Non-empty cells: `{mean_non_empty_cells:,.0f}` / `{_total_cells:,}` ({100*mean_non_empty_cells/_total_cells:.1f}%)
"""
    )
    return global_density, mean_non_empty_cells, mean_total_atoms


# =============================================================================
# SECTION 3: Notch Detection
# =============================================================================

@app.cell
def _(mo):
    mo.md("## Step 2: Detect Notches")
    return


@app.cell
def _(mo, n_x):
    # Threshold: how many empty cells along perpendicular axis to consider "notch"
    threshold = mo.ui.slider(1, max(10, n_x // 4), value=5, step=1, label="Min empty")
    width_threshold = mo.ui.slider(1, max(100, n_x // 2), value=max(30, n_x // 3), step=1, label="Max empty")
    mo.vstack([
        mo.hstack([threshold, mo.md("*(min empty - lower bound for notch/tip detection)*")]),
        mo.hstack([width_threshold, mo.md("*(max empty - upper bound, exclude edge artifacts)*")]),
    ])
    return threshold, width_threshold


@app.cell
def _(data_2d, mo, np, plot_x, plot_y, threshold, width_threshold, x_hi, x_lo, y_hi, y_lo, n_x, n_y, cell_w_x, cell_w_y, plt):
    # Count empty cells along x-axis for each y position
    empty_per_y = (data_2d == 0).sum(axis=0)  # shape (n_y,)
    notch_mask = empty_per_y >= threshold.value

    # Convert to coordinates
    y_centers = y_lo + (np.arange(n_y) + 0.5) * cell_w_y

    # Minimum empty cells to consider for width measurement
    width_min_empty = width_threshold.value

    notches = []

    # BOTTOM NOTCH: scan from bottom edge (idx=0) upward until we find NO notch
    # Tip = last index (highest y) that still has >= threshold empty cells
    bottom_tip_idx = None
    for i in range(n_y):
        if notch_mask[i]:
            bottom_tip_idx = i  # keep updating until we hit a non-notch position
        else:
            if bottom_tip_idx is not None:
                break  # found the end of the bottom notch

    # TOP NOTCH: scan from top edge (idx=n_y-1) downward until we find NO notch
    # Tip = last index (lowest y) that still has >= threshold empty cells
    top_tip_idx = None
    for i in range(n_y - 1, -1, -1):
        if notch_mask[i]:
            top_tip_idx = i  # keep updating until we hit a non-notch position
        else:
            if top_tip_idx is not None:
                break  # found the end of the top notch

    # Helper to find center_x at tip (median of empty cells)
    def find_center_at_tip(tip_idx):
        empty_at_tip = data_2d[:, tip_idx] == 0
        if empty_at_tip.any():
            empty_x_indices = np.nonzero(empty_at_tip)[0]
            # Use median for center
            median_idx = int(np.median(empty_x_indices))
            center_x = x_lo + (median_idx + 0.5) * cell_w_x
            return center_x, median_idx
        return (x_lo + x_hi) / 2, n_x // 2

    # Helper to measure width: find contiguous empty region containing center
    def measure_width_from_center(y_idx, center_x_idx):
        empty_at_y = data_2d[:, y_idx] == 0

        if not empty_at_y[center_x_idx]:
            # Center is not empty at this y, return 0
            return 0

        # Expand left from center
        left_idx = center_x_idx
        while left_idx > 0 and empty_at_y[left_idx - 1]:
            left_idx -= 1

        # Expand right from center
        right_idx = center_x_idx
        while right_idx < n_x - 1 and empty_at_y[right_idx + 1]:
            right_idx += 1

        width = (right_idx - left_idx + 1) * cell_w_x
        return width

    # Helper to find best width in notch region
    # Only measure at positions with fewer than width_threshold empties
    # (to avoid edge artifacts where whole rows are empty)
    def find_notch_width(start_idx, end_idx, center_x_idx):
        best_width = 0
        for y_idx in range(start_idx, end_idx + 1):
            if threshold.value <= empty_per_y[y_idx] < width_min_empty:
                w = measure_width_from_center(y_idx, center_x_idx)
                if w > best_width:
                    best_width = w
        return best_width

    # Build bottom notch info
    if bottom_tip_idx is not None and bottom_tip_idx > 0:
        edge_idx = 0  # bottom edge
        tip_y = y_centers[bottom_tip_idx]
        edge_y = y_centers[edge_idx]
        depth = abs(tip_y - edge_y)
        center_x, center_x_idx = find_center_at_tip(bottom_tip_idx)
        width = find_notch_width(edge_idx, bottom_tip_idx, center_x_idx)
        notches.append({
            "id": 0,
            "direction": "bottom",
            "tip_y": tip_y,
            "tip_y_idx": bottom_tip_idx,
            "edge_y": edge_y,
            "depth": depth,
            "width": width,
            "center_x": center_x,
            "max_empty": int(empty_per_y[:bottom_tip_idx+1].max()),
        })

    # Build top notch info
    if top_tip_idx is not None and top_tip_idx < n_y - 1:
        edge_idx = n_y - 1  # top edge
        tip_y = y_centers[top_tip_idx]
        edge_y = y_centers[edge_idx]
        depth = abs(tip_y - edge_y)
        center_x, center_x_idx = find_center_at_tip(top_tip_idx)
        width = find_notch_width(top_tip_idx, edge_idx, center_x_idx)
        notches.append({
            "id": 1,
            "direction": "top",
            "tip_y": tip_y,
            "tip_y_idx": top_tip_idx,
            "edge_y": edge_y,
            "depth": depth,
            "width": width,
            "center_x": center_x,
            "max_empty": int(empty_per_y[top_tip_idx:].max()),
        })

    mo.md(f"**Found {len(notches)} notch(es)** with threshold={threshold.value}")
    return empty_per_y, notch_mask, notches, y_centers


@app.cell
def _(cell_w_y, empty_per_y, mo, notches, np, plt, threshold, width_threshold, y_centers, y_hi, y_lo, n_x):
    # Plot empty count profile with notch markers
    fig1, ax1 = plt.subplots(figsize=(12, 4))

    ax1.fill_between(y_centers, 0, empty_per_y, alpha=0.3, label="Empty count")
    ax1.plot(y_centers, empty_per_y, "b-", linewidth=1)

    # Threshold lines
    # Lower bound: minimum empty cells to be considered "notch"
    ax1.axhline(threshold.value, color="orange", linestyle="--",
                label=f"Min empty ({threshold.value}) - notch lower bound")

    # Upper bound: exclude edge artifacts
    ax1.axhline(width_threshold.value, color="green", linestyle=":",
                label=f"Max empty ({width_threshold.value}) - exclude artifacts")

    # Shade the valid measurement zone between thresholds
    ax1.axhspan(threshold.value, width_threshold.value, alpha=0.1, color="yellow",
                label="Width measurement zone")

    # Mark notch tips
    for notch in notches:
        ax1.axvline(notch["tip_y"], color="red", linestyle="-", linewidth=2, alpha=0.7)
        ax1.annotate(f"Notch {notch['id']+1}\n{notch['direction']}\ndepth={notch['depth']:.1f}",
                    xy=(notch["tip_y"], notch["max_empty"]),
                    xytext=(10, 10), textcoords="offset points",
                    fontsize=8, bbox=dict(boxstyle="round", fc="white", alpha=0.8))

    ax1.set_xlabel("z (Å)")
    ax1.set_ylabel(f"# empty cells (along x)")
    ax1.set_title("Empty Cell Profile - Notch Detection")
    ax1.set_xlim(y_lo, y_hi)
    ax1.legend(loc="upper right")
    plt.tight_layout()
    fig1
    return ax1, fig1


@app.cell
def _(mo, notches, plot_x, plot_y):
    # Display notch info table
    if not notches:
        mo.stop(True, mo.md("⚠️ No notches detected. Try lowering the threshold."))

    _rows = []
    for n in notches:
        _rows.append(f"| {n['id']+1} | {n['direction']} | {n['tip_y']:.1f} | {n['depth']:.1f} | {n['width']:.1f} | {n['center_x']:.1f} |")

    mo.md(f"""
### Detected Notches

| # | Direction | Tip {plot_y.value} | Depth | Width | Center {plot_x.value} |
|---|-----------|---------|-------|-------|---------|
{chr(10).join(_rows)}
""")
    return


# =============================================================================
# SECTION 4: Visualize Selection on Grid
# =============================================================================

@app.cell
def _(mo):
    mo.md("## Step 3: Region Between Notches")
    return


@app.cell
def _(cell_w_x, mo, notches, np, x_hi, x_lo):
    if len(notches) < 2:
        mo.stop(True, mo.md("⚠️ Need at least 2 notches to define a region between them"))

    # Sort notches by tip_y to get bottom and top
    _sorted = sorted(notches, key=lambda n: n["tip_y"])
    notch_bottom = _sorted[0]
    notch_top = _sorted[-1]

    # Region between notch tips
    region_y_lo = notch_bottom["tip_y"]
    region_y_hi = notch_top["tip_y"]

    # Width: use the narrower notch width, centered
    region_width = min(notch_bottom["width"], notch_top["width"])
    region_center_x = (notch_bottom["center_x"] + notch_top["center_x"]) / 2

    region_x_lo = region_center_x - region_width / 2
    region_x_hi = region_center_x + region_width / 2

    # Clamp to grid bounds
    region_x_lo = max(region_x_lo, x_lo)
    region_x_hi = min(region_x_hi, x_hi)

    mo.md(f"""
**Region between notches:**
- {notch_bottom['direction']} tip → {notch_top['direction']} tip
- Y range: [{region_y_lo:.1f}, {region_y_hi:.1f}] (height: {region_y_hi - region_y_lo:.1f} Å)
- X range: [{region_x_lo:.1f}, {region_x_hi:.1f}] (width: {region_x_hi - region_x_lo:.1f} Å)
""")
    return notch_bottom, notch_top, region_center_x, region_width, region_x_hi, region_x_lo, region_y_hi, region_y_lo


@app.cell
def _(
    Rectangle, data_2d, mo, notch_bottom, notch_top, np, plt,
    region_x_hi, region_x_lo, region_y_hi, region_y_lo,
    x_hi, x_lo, y_hi, y_lo, plot_x, plot_y
):
    # Plot 2D grid with notch tips and region highlighted
    fig2, ax2 = plt.subplots(figsize=(10, 8))

    im = ax2.imshow(data_2d.T, extent=(x_lo, x_hi, y_lo, y_hi), origin="lower",
                    aspect="auto", cmap="viridis")

    # Draw region rectangle
    rect = Rectangle((region_x_lo, region_y_lo),
                     region_x_hi - region_x_lo,
                     region_y_hi - region_y_lo,
                     linewidth=2, edgecolor="red", facecolor="none", linestyle="--",
                     label="Analysis region")
    ax2.add_patch(rect)

    # Mark notch tips
    ax2.scatter([notch_bottom["center_x"]], [notch_bottom["tip_y"]],
               c="red", s=100, marker="^", zorder=5, label="Bottom notch tip")
    ax2.scatter([notch_top["center_x"]], [notch_top["tip_y"]],
               c="orange", s=100, marker="v", zorder=5, label="Top notch tip")

    # Draw line between notch tips (sampling path)
    ax2.plot([notch_bottom["center_x"], notch_top["center_x"]],
            [notch_bottom["tip_y"], notch_top["tip_y"]],
            "r-", linewidth=2, alpha=0.7, label="Sampling path")

    ax2.set_xlabel(plot_x.value)
    ax2.set_ylabel(plot_y.value)
    ax2.set_title("Grid View with Notch Detection")
    ax2.legend(loc="upper right")
    fig2.colorbar(im, ax=ax2, label="count", shrink=0.8)
    plt.tight_layout()
    fig2
    return ax2, fig2, im, rect


# =============================================================================
# SECTION 5: Stress Sampling Along Path
# =============================================================================

@app.cell
def _(mo):
    mo.md("## Step 4: Sample Stress Along Path")
    return


@app.cell
def _(grid, mo):
    # Find stress-like fields
    _stress_fields = [f for f in grid.fields if "stress" in f.lower() or "pressure" in f.lower()]
    _all_fields = [f for f in grid.fields if not f.startswith("_") and f != "coords"]

    if not _all_fields:
        mo.stop(True, mo.md("⚠️ No fields available for sampling"))

    _options = _stress_fields + [f for f in _all_fields if f not in _stress_fields]

    field_select = mo.ui.dropdown(_options, value=_options[0] if _options else None, label="Field")
    n_samples = mo.ui.slider(5, 50, value=20, step=1, label="# samples")
    mo.hstack([field_select, n_samples])
    return field_select, n_samples


@app.cell
def _(
    field_select, grid, mo, n_samples, notch_bottom, notch_top, np,
    region_x_hi, region_x_lo, region_y_hi, region_y_lo, sum_axis_name
):
    # Create rectangular slices across the analysis region
    _n = n_samples.value

    # Region bounds
    y_start, y_end = region_y_lo, region_y_hi
    x_start, x_end = region_x_lo, region_x_hi

    # Sample y-positions (center of each slice)
    slice_height = (y_end - y_start) / _n
    sample_y = np.linspace(y_start + slice_height/2, y_end - slice_height/2, _n)

    # Distance along path (z direction)
    path_length = y_end - y_start
    sample_dist = np.linspace(0, path_length, _n)

    mo.md(f"**Sampling {_n} rectangular slices** | region: x=[{x_start:.1f}, {x_end:.1f}], z=[{y_start:.1f}, {y_end:.1f}] | slice height: {slice_height:.1f} Å")
    return path_length, sample_dist, sample_y, slice_height, x_end, x_start, y_end, y_start


@app.cell
def _(
    cell_w_x, cell_w_y, coord_to_index, field_select, get_axis_extent, get_field_data_4d, grid, mo, np,
    plot_x, plot_y, reduce_4d_to_2d, sample_dist, sample_y, slice_height,
    sum_axis_name, x_lo, x_hi, y_lo, n_x, n_y,
    x_start, x_end
):
    # Sample rectangular slices across the analysis region
    _field_name = field_select.value
    _px, _py = plot_x.value, plot_y.value

    # Get field and counts data using new API
    # For mean: get sum and counts, compute mean = sum / counts
    _field_sum_4d = get_field_data_4d(grid, _field_name, "sum")
    _counts_4d = get_field_data_4d(grid, "counts", "sum")

    # Reduce to 2D: mean over t and sum_axis
    # For field: use sum, then divide by counts for weighted mean
    # For counts: use sum
    _reductions = {"t": ("sum", None), sum_axis_name: ("sum", None)}

    # Try to use cumsum for O(1) projection
    _field_cumsum = grid.cells[_field_name]._cumsum if hasattr(grid.cells[_field_name], '_cumsum') else None
    _counts_cumsum = grid.cells._counts_cumsum.astype(np.float64) if grid.cells._counts_cumsum is not None else None

    _field_sum_2d, _ = reduce_4d_to_2d(_field_sum_4d, grid, _px, _py, _reductions, _field_cumsum)
    counts_2d, _ = reduce_4d_to_2d(_counts_4d, grid, _px, _py, _reductions, _counts_cumsum)

    # Compute mean = sum / counts (with safe division)
    with np.errstate(invalid='ignore', divide='ignore'):
        field_2d = _field_sum_2d / counts_2d
        field_2d[~np.isfinite(field_2d)] = 0

    # Convert region bounds to indices
    x_idx_lo = max(0, int((x_start - x_lo) / cell_w_x))
    x_idx_hi = min(n_x - 1, int((x_end - x_lo) / cell_w_x))

    # Sample each rectangular slice
    sampled_values = []
    sampled_counts = []
    slice_bounds = []

    for y_center in sample_y:
        y_slice_lo = y_center - slice_height / 2
        y_slice_hi = y_center + slice_height / 2
        slice_bounds.append((y_slice_lo, y_slice_hi))

        y_idx_lo = max(0, int((y_slice_lo - y_lo) / cell_w_y))
        y_idx_hi = min(n_y - 1, int((y_slice_hi - y_lo) / cell_w_y))

        region_field = field_2d[x_idx_lo:x_idx_hi+1, y_idx_lo:y_idx_hi+1]
        region_counts = counts_2d[x_idx_lo:x_idx_hi+1, y_idx_lo:y_idx_hi+1]

        if region_counts.sum() > 0:
            sampled_values.append(np.average(region_field, weights=region_counts))
        else:
            sampled_values.append(np.mean(region_field))
        sampled_counts.append(region_counts.sum())

    sampled_values = np.array(sampled_values)
    sampled_counts = np.array(sampled_counts)

    mo.md(f"Sampled `{_field_name}` from {len(sampled_values)} rectangular slices (x: [{x_idx_lo}:{x_idx_hi}])")
    return counts_2d, field_2d, sampled_counts, sampled_values, slice_bounds, x_idx_hi, x_idx_lo


@app.cell
def _(field_select, np, plt, sample_dist, sample_y, sampled_counts, sampled_values, slice_height):
    # Plot stress vs distance along path
    fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    # Top: field value (bar chart to show slice regions)
    ax3a.bar(sample_dist, sampled_values, width=slice_height * 0.9, alpha=0.7, label=field_select.value)
    ax3a.plot(sample_dist, sampled_values, "r-", linewidth=1, alpha=0.7)
    ax3a.set_ylabel(field_select.value)
    ax3a.set_title(f"{field_select.value} across rectangular slices (notch to notch)")
    ax3a.axhline(0, color="gray", linestyle="--", alpha=0.5)
    ax3a.legend()
    ax3a.grid(True, alpha=0.3)

    # Mark notch positions
    ax3a.axvline(0, color="red", linestyle=":", alpha=0.7)
    ax3a.axvline(sample_dist[-1], color="red", linestyle=":", alpha=0.7)

    # Bottom: atom count (sanity check)
    ax3b.bar(sample_dist, sampled_counts, width=slice_height * 0.9, alpha=0.3, color="green")
    ax3b.plot(sample_dist, sampled_counts, "g-", linewidth=1)
    ax3b.set_xlabel("Distance from bottom tip (Å)")
    ax3b.set_ylabel("Atom count in slice")
    ax3b.set_title("Atom count per slice (sanity check)")
    ax3b.grid(True, alpha=0.3)

    plt.tight_layout()
    fig3
    return ax3a, ax3b, fig3


@app.cell
def _(
    Rectangle, data_2d, field_2d, mo, notch_bottom, notch_top, np, plt,
    region_x_hi, region_x_lo, region_y_hi, region_y_lo,
    sample_y, slice_bounds, x_hi, x_lo, y_hi, y_lo, plot_x, plot_y, field_select
):
    # Final visualization: field heatmap with sampling slices
    fig4, (ax4a, ax4b) = plt.subplots(1, 2, figsize=(14, 6))

    # Left: counts with sample slices
    im1 = ax4a.imshow(data_2d.T, extent=(x_lo, x_hi, y_lo, y_hi), origin="lower",
                      aspect="auto", cmap="viridis")
    ax4a.set_xlabel(plot_x.value)
    ax4a.set_ylabel(plot_y.value)
    ax4a.set_title("Atom counts with sample slices")
    fig4.colorbar(im1, ax=ax4a, label="count", shrink=0.8)

    # Right: field values with sample slices
    im2 = ax4b.imshow(field_2d.T, extent=(x_lo, x_hi, y_lo, y_hi), origin="lower",
                      aspect="auto", cmap="coolwarm")
    ax4b.set_xlabel(plot_x.value)
    ax4b.set_ylabel(plot_y.value)
    ax4b.set_title(f"{field_select.value} with sample slices")
    fig4.colorbar(im2, ax=ax4b, label=field_select.value, shrink=0.8)

    # Draw sample slices on both plots
    for _i, (_y_lo, _y_hi) in enumerate(slice_bounds):
        for _ax, _color in [(ax4a, "red"), (ax4b, "black")]:
            _rect = Rectangle((region_x_lo, _y_lo),
                              region_x_hi - region_x_lo,
                              _y_hi - _y_lo,
                              linewidth=1, edgecolor=_color, facecolor=_color, alpha=0.15)
            _ax.add_patch(_rect)

    # Draw outer region boundary
    for _ax in [ax4a, ax4b]:
        _rect = Rectangle((region_x_lo, region_y_lo),
                          region_x_hi - region_x_lo,
                          region_y_hi - region_y_lo,
                          linewidth=2, edgecolor="yellow", facecolor="none", linestyle="--")
        _ax.add_patch(_rect)

    plt.tight_layout()
    fig4
    return ax4a, ax4b, fig4, im1, im2


@app.cell
def _(
    _box_sum_4d, coord_to_index, get_axis_extent,
    field_select, global_density, loader, mo, notch_bottom, notch_top, np,
    path_length, region_x_lo, region_x_hi, sample_dist, sample_y,
    sampled_values, slice_height, grid, cell_w_x, cell_w_y, cell_w_sum,
    x_lo, n_x, y_lo, n_y, plot_x, plot_y, sum_axis_name,
    mean_total_atoms, mean_non_empty_cells, density_non_empty
):
    # =========================
    # Averaged notch geometry
    # =========================
    mean_depth = (notch_bottom["depth"] + notch_top["depth"]) / 2
    mean_radius = (notch_bottom["width"] + notch_top["width"]) / 4
    tip_radius_sigma = mean_radius**2 / mean_depth

    # =========================
    # Aligned notch tips (averaged center)
    # =========================
    center_mean = (notch_bottom["center_x"] + notch_top["center_x"]) / 2
    tip_lo = notch_bottom["tip_y"]  # lower tip position (plot_y axis)
    tip_hi = notch_top["tip_y"]     # upper tip position (plot_y axis)

    # =========================
    # Boxes around notch tips
    # =========================
    _px, _py = plot_x.value, plot_y.value

    # Upper notch box: extends inward (negative plot_y direction)
    upper_box = {
        f"{_px}_lo": center_mean - 1.5 * tip_radius_sigma,
        f"{_px}_hi": center_mean + 1.5 * tip_radius_sigma,
        f"{_py}_lo": tip_hi - 3.0 * tip_radius_sigma,
        f"{_py}_hi": tip_hi,
    }
    # Lower notch box: extends inward (positive plot_y direction)
    lower_box = {
        f"{_px}_lo": center_mean - 1.5 * tip_radius_sigma,
        f"{_px}_hi": center_mean + 1.5 * tip_radius_sigma,
        f"{_py}_lo": tip_lo,
        f"{_py}_hi": tip_lo + 3.0 * tip_radius_sigma,
    }

    # =========================
    # Mean stress in box using O(1) cumsum queries
    # =========================
    # For box mean = sum(field) / sum(counts), we use cumsum for both
    _field_cumsum = grid.cells[field_select.value]._cumsum
    _counts_cumsum = grid.cells._counts_cumsum.astype(np.float64)

    # Map plot axes to 4D indices: t=0, x=1, y=2, z=3
    _dim_map = {"t": 0, "x": 1, "y": 2, "z": 3}

    def _mean_stress_in_box_fast(box):
        """Compute mean stress in a 3D box (plot_x, plot_y, summed over sum_axis and t)."""
        # Convert coordinate bounds to indices
        _px_lo, _px_hi, _px_n, _ = get_axis_extent(grid, _px)
        _py_lo, _py_hi, _py_n, _ = get_axis_extent(grid, _py)
        _ps_lo, _ps_hi, _ps_n, _ = get_axis_extent(grid, sum_axis_name)

        _x_i0 = coord_to_index(box[f"{_px}_lo"], _px_lo, _px_hi, _px_n)
        _x_i1 = coord_to_index(box[f"{_px}_hi"], _px_lo, _px_hi, _px_n)
        _y_i0 = coord_to_index(box[f"{_py}_lo"], _py_lo, _py_hi, _py_n)
        _y_i1 = coord_to_index(box[f"{_py}_hi"], _py_lo, _py_hi, _py_n)

        # Build 4D box indices: [t0, t1, x0, x1, y0, y1, z0, z1]
        _box_4d = [0, grid.n_timesteps - 1, 0, 0, 0, 0, 0, 0]  # Initialize

        # Set indices based on which axis is which
        _axis_indices = {
            _px: (_x_i0, _x_i1),
            _py: (_y_i0, _y_i1),
            sum_axis_name: (0, _ps_n - 1),  # Full range for summed axis
        }

        for _axis, (_lo, _hi) in _axis_indices.items():
            _dim = _dim_map[_axis]
            _box_4d[_dim * 2] = _lo
            _box_4d[_dim * 2 + 1] = _hi

        # O(1) box sum queries
        _field_sum = _box_sum_4d(_field_cumsum, *_box_4d)
        _counts_sum = _box_sum_4d(_counts_cumsum, *_box_4d)

        if _counts_sum > 0:
            return _field_sum / _counts_sum
        return np.nan

    # =========================
    # Compute box stress values
    # =========================
    stress_upper = _mean_stress_in_box_fast(upper_box)
    stress_lower = _mean_stress_in_box_fast(lower_box)

    # =========================
    # Unit conversion with pint
    # =========================
    # LAMMPS per-atom stress is stress*volume (atm·Å³), not stress directly.
    # Use pint for clean unit handling.
    from atomkit import ureg, Q_

    _volume_per_atom = Q_(1.0 / global_density if global_density > 0 else 1.0, "angstrom**3")
    _stress_upper_raw = Q_(stress_upper, "atm * angstrom**3")
    _stress_lower_raw = Q_(stress_lower, "atm * angstrom**3")

    _stress_upper_pa = (_stress_upper_raw / _volume_per_atom).to("Pa")
    _stress_lower_pa = (_stress_lower_raw / _volume_per_atom).to("Pa")

    # =========================
    # Build YAML export
    # =========================
    _cell_volume = cell_w_x * cell_w_y * cell_w_sum
    _total_cells = np.prod(grid.grid_shape)
    _effective_volume = mean_non_empty_cells * _cell_volume if density_non_empty.value else _total_cells * _cell_volume

    _yaml = f"""# Notch Explorer Analysis Results
# Source: {loader.file_path.name}
# Field: {field_select.value}

metadata:
  source_file: "{loader.file_path.name}"
  field_analyzed: "{field_select.value}"
  view_plane: "{_px} vs {_py}"
  summed_axis: "{sum_axis_name}"
  n_timesteps: {grid.n_timesteps}

global_properties:
  density:
    value: {global_density:.6e}
    unit: "atoms/A^3"
    method: "{'non-empty cells' if density_non_empty.value else 'all cells'}"
  mean_atom_count: {mean_total_atoms:.0f}
  effective_volume:
    value: {_effective_volume:.2f}
    unit: "A^3"
  cell_volume:
    value: {_cell_volume:.4f}
    unit: "A^3"

analysis_region:
  {_px}_range: [{region_x_lo:.2f}, {region_x_hi:.2f}]  # A
  {_py}_range: [{sample_y[0] - slice_height/2:.2f}, {sample_y[-1] + slice_height/2:.2f}]  # A
  path_length: {path_length:.2f}  # A
  slice_height: {slice_height:.2f}  # A
  n_slices: {len(sample_y)}

notch_geometry:
  mean_depth: {mean_depth:.4f}  # A
  mean_radius: {mean_radius:.4f}  # A
  tip_radius_sigma: {tip_radius_sigma:.4f}  # A (r^2/d)
  center_{_px}: {center_mean:.4f}  # A

notch_tips:
  lower:
    position: [{center_mean:.4f}, {tip_lo:.4f}]  # ({_px}, {_py}) in A
    depth: {notch_bottom['depth']:.4f}
    width: {notch_bottom['width']:.4f}
  upper:
    position: [{center_mean:.4f}, {tip_hi:.4f}]  # ({_px}, {_py}) in A
    depth: {notch_top['depth']:.4f}
    width: {notch_top['width']:.4f}

stress_boxes:
  # Boxes extend 1.5*sigma perpendicular and 3*sigma along notch direction
  # Raw values are stress*volume (atm·Å³); converted using volume_per_atom={_volume_per_atom.magnitude:.4f} Å³
  lower:
    bounds:
      {_px}: [{lower_box[f'{_px}_lo']:.4f}, {lower_box[f'{_px}_hi']:.4f}]
      {_py}: [{lower_box[f'{_py}_lo']:.4f}, {lower_box[f'{_py}_hi']:.4f}]
    mean_stress:
      raw: {stress_lower:.6e}  # atm·Å³
      pa: {_stress_lower_pa.magnitude:.4f}
  upper:
    bounds:
      {_px}: [{upper_box[f'{_px}_lo']:.4f}, {upper_box[f'{_px}_hi']:.4f}]
      {_py}: [{upper_box[f'{_py}_lo']:.4f}, {upper_box[f'{_py}_hi']:.4f}]
    mean_stress:
      raw: {stress_upper:.6e}  # atm·Å³
      pa: {_stress_upper_pa.magnitude:.4f}

sampled_slices:
  distance_from_lower_tip: {[round(d, 2) for d in sample_dist.tolist()]}
  {_py}_centers: {[round(y, 2) for y in sample_y.tolist()]}
  values: {[round(v, 4) for v in sampled_values.tolist()]}
"""

    # Create download button
    _filename = loader.file_path.name.replace(".h5", f"_{field_select.value}_analysis.yaml")
    _download = mo.download(
        data=_yaml.encode("utf-8"),
        filename=_filename,
        label="Download YAML",
    )

    mo.vstack([
        mo.md("## Export Data"),
        _download,
        mo.md(f"```yaml\n{_yaml}```"),
    ])
    return


if __name__ == "__main__":
    app.run()