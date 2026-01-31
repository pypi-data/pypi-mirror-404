# Future Ideas

## Surface Extraction for Visualization

**Status:** Pinned for later consideration

### Problem
Rendering 1.67M atoms directly is too slow for interactive visualization.
Need a way to extract and render surfaces/boundaries efficiently.

### Idea: Cell-Based Surface Extraction (Alternative to Marching Cubes)

Instead of marching cubes (fixed primitive lookup table), store actual
surface data per boundary cell:

```
Standard marching cubes:         Proposed approach:
┌───┬───┬───┐                    ┌───┬───┬───┐
│   │ ▄▄│███│                    │   │  ╱│███│
│   │▄██│███│  Fixed primitives  │   │ ╱ │███│  Actual plane per cell
│   │███│███│  from lookup table │   │╱  │███│  stored as edge intersections
└───┴───┴───┘                    └───┴───┴───┘
     ↑ blocky                         ↑ smooth, data-driven
```

### Data Structure

For each boundary cell (cell adjacent to empty cell):

```python
{
    'cell': (ix, iy, iz),
    'edge_points': [
        # Points where surface crosses cell edges
        # Shared with neighbors at that edge
        # Parameter t ∈ [0,1] along edge
        ((ix, iy, iz), 'x+', t),
        ((ix, iy, iz), 'z+', t),
        ...
    ],
    'normal': (nx, ny, nz),  # Surface orientation
}
```

### Advantages
- Edge points shared between cells → watertight mesh
- Smooth surfaces (not blocky like marching cubes)
- Data-driven: surface position from actual atom distribution
- Works for iso-surfaces too (stress contours, density, etc.)

### Rendering Options
1. **2D projection**: Project to x-z plane, draw as line segments
2. **Per-cell polygons**: Connect edge points to form quads/triangles
3. **Contour lines**: For scalar fields (stress levels)

### Open Questions
- How to compute edge intersection points? Options:
  - Binary: surface at cell face (empty vs non-empty)
  - Interpolated: based on atom count ratio
  - Fitted: plane fit to atoms in boundary cells

- How to handle contour lines for interior fields (stress)?
  - Need iso-surface extraction within occupied region
  - Similar approach but with scalar threshold instead of empty/non-empty

### Related Work
- Dual contouring
- Surface nets
- Marching cubes (for comparison)
