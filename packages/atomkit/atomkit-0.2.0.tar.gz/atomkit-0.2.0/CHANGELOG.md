# Changelog

All notable changes to atomkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased

### Added
- **Pint unit system integration**: Optional unit-aware quantities via `use_units=True`
  - `grid.query(region, use_units=True)` returns pint Quantities
  - Field units inferred from names (e.g., "stress" → bar, "energy" → eV)
  - Custom units via `grid.set_field_unit(field, unit_str)`
- **Marimo widgets**: Interactive grid exploration in notebooks
  - `GridLoader`: File picker with cell size and coordinate type controls
  - `grid_explorer()`: Interactive 2D slice/projection viewer
  - `time_evolution()`: Kymograph visualization
- **Visualization utilities** in `atomkit.viz`:
  - `get_field_data_4d()`: Extract 4D field arrays
  - `reduce_4d_to_2d()`: Flexible 4D→2D reduction with slice/sum/mean/max
  - `plot_2d_field()`: Quick matplotlib plotting

### Changed
- `viz.py` rewritten to use cell aggregates accessor pattern (faster)
- Examples updated to use new accessor APIs

### Removed (Breaking Changes)
- **Deprecated properties** (use `source_box.*` instead):
  - `grid.source_box_bounds` → `grid.source_box.bounds`
  - `grid.source_box_tilt` → `grid.source_box.tilt`
  - `grid.source_box_boundary` → `grid.source_box.boundary`
- **Deprecated methods** (use cell aggregates instead):
  - `grid._cell_field_3d()` → `grid.cells[field].sum/mean/min/max[t_idx]`
  - `grid.slice_2d()` → `grid.cells[field].mean[t, :, :, z_idx]`
  - `grid.project_2d()` → `grid.cells[field].mean[t].sum(axis=0)`

## [0.1.3] - 2026-01-15

### Added
- `SourceBox` dataclass for consolidated simulation box metadata
- `CellsAccessor` with precomputed per-cell aggregates (sum/min/max/mean)
- `GridView` for zero-copy views into grid subregions
- `ReductionAccessor` with O(1) region queries via 4D cumulative sums
- `MeanAccessor` and `DensityAccessor` for derived quantities
- Backwards compatibility for loading old HDF5 files (auto-migration)
- Progress bars for large file operations
- Pre-allocated arrays for faster grid building

### Deprecated
- `source_box_bounds`, `source_box_tilt`, `source_box_boundary` properties
- `_cell_field_3d()`, `slice_2d()`, `project_2d()` methods

## [0.1.2] - 2026-01-10

### Added
- `coord_type` parameter for LAMMPS coordinate selection
  - `"unwrapped"` (xu, yu, zu): actual positions
  - `"wrapped"` (x, y, z): positions in simulation box
  - `"scaled"` (xs, ys, zs): fractional coordinates
  - `"auto"` (default): prefers unwrapped → wrapped → scaled
- Lagrangian grid mode for tracking atom trajectories

## [0.1.1] - 2026-01-05

### Added
- `atomkit.viz` module with marimo grid explorer
- Interactive heatmap exploration with sliders

## [0.1.0] - 2026-01-01

### Added
- Initial release
- `SpatialGrid`: 4D CSR-indexed spatial grid for LAMMPS trajectories
- `Region`: 4D axis-aligned bounding box for queries
- HDF5 storage with zstd compression
- CLI: `atomkit convert` and `atomkit info`
- Optional Numba JIT acceleration
- Per-axis cell sizes
