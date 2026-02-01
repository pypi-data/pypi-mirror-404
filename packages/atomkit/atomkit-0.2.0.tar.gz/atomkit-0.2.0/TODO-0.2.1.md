# TODO for v0.2.1 - Cumsum API Improvements

Tracked from code review on 2026-02-01.

## Goal

Simplify the cumsum-based O(1) query API. Current implementation has the primitives but the user-facing API is verbose.

---

## High Priority

### 1. Add `.project()` method to `ReductionAccessor`

**Current (verbose):**
```python
from atomkit.spatial_grid import project_2d_fast
data_2d = project_2d_fast(grid.cells._counts_cumsum.astype(np.float64), ("x", "y"))
```

**Proposed:**
```python
data_2d = grid.cells.counts.project(keep=("x", "y"))
# or for fields:
data_2d = grid.cells["stress"].sum.project(keep=("x", "y"))
```

- Wraps `project_2d_fast` internally
- Handles dtype conversion
- Returns extent tuple as second return value (optional)

### 2. Add batched index lookup

For arbitrary cell lookups without iterating:

```python
# Query multiple boxes at once
indices = [(t, x, y, z) for ...]  # list of cell indices
values = grid.cells["stress"].sum.batch_lookup(indices)

# Or box ranges
boxes = [(t0, t1, x0, x1, y0, y1, z0, z1), ...]
sums = grid.cells["stress"].sum.batch_box_sum(boxes)
```

Useful for sampling paths, Monte Carlo, etc.

---

## Medium Priority

### 3. Deprecate `get_field_data_4d` helper

Currently in `atomkit/viz.py`:
```python
def get_field_data_4d(grid, field, agg="mean"):
    if field == "counts":
        return grid.counts.astype(np.float64)
    return getattr(grid.cells[field], agg).np
```

This is just a thin wrapper. Users should use direct access:
```python
grid.cells["stress"].mean.np  # instead of get_field_data_4d(grid, "stress", "mean")
grid.counts                   # instead of get_field_data_4d(grid, "counts", ...)
```

Action: Add deprecation warning, remove in v0.3.0.

### 4. Simplify `reduce_4d_to_2d`

Current function handles too many cases. Split into:
- `project_2d()` - sum projection (uses cumsum, O(n*m))
- `slice_2d()` - slice at index (direct indexing)
- Keep `reduce_4d_to_2d` only for mixed-mode reductions (rare)

---

## Low Priority / Future

### 5. Add `grid.cells.counts` accessor

Currently counts are accessed via `grid.counts` or `grid.cells._counts_cumsum`.
Consider adding `grid.cells.counts` as a `ReductionAccessor` for consistency:

```python
grid.cells.counts.project(keep=("x", "y"))  # instead of special-casing
```

### 6. Consider 1D projections

```python
data_1d = grid.cells["stress"].sum.project(keep="x")  # reduce t, y, z
```

---

## Files to modify

- `atomkit/spatial_grid.py` - `ReductionAccessor` class (~line 519)
- `atomkit/viz.py` - deprecate helpers, simplify
- `atomkit/marimo/widgets.py` - update to use new API
- `examples/notch_explorer.py` - simplify with new API

---

## Notes

- All cumsum-based operations are O(1) per cell query (16-corner inclusion-exclusion)
- `project_2d_fast` is O(n*m) where n,m are output dimensions
- Numba-accelerated versions exist for common projections (xy, xz, yz, tx, ty, tz)
