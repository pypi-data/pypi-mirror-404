"""Tests for cell aggregates and slicing via the new cells API."""

import numpy as np
import pytest

from atomkit import SpatialGrid


@pytest.fixture
def simple_grid():
    """Create a simple 10x10x10 grid with known distribution."""
    np.random.seed(42)
    n_atoms = 1000
    coords = np.random.uniform(0, 100, (n_atoms, 3)).astype(np.float32)
    stress = np.random.randn(n_atoms).astype(np.float32)

    return SpatialGrid.from_arrays(
        coords=coords,
        cell_size=10.0,
        box_bounds=(0, 100, 0, 100, 0, 100),
        stress=stress,
    )


@pytest.fixture
def multi_ts_grid():
    """Multi-timestep grid."""
    np.random.seed(42)
    n_atoms = 500
    coords = [np.random.uniform(0, 100, (n_atoms, 3)).astype(np.float32) for _ in range(3)]
    stress = [np.random.randn(n_atoms).astype(np.float32) for _ in range(3)]

    return SpatialGrid.from_arrays(
        coords=coords,
        cell_size=10.0,
        box_bounds=(0, 100, 0, 100, 0, 100),
        timestep_values=[0, 100, 200],
        stress=stress,
    )


class TestCellsSlicing:
    """Test slicing via cells aggregates (replaces slice_2d tests)."""

    def test_slice_z_via_cells(self, simple_grid):
        """Slice along z axis using cells aggregates."""
        # Get mean at z_idx=5 (cell containing z=50)
        z_idx = 5
        mean_slice = simple_grid.cells["stress"].mean[0, :, :, z_idx]

        nx, ny, nz = simple_grid.grid_shape
        assert mean_slice.shape == (nx, ny)

    def test_slice_x_via_cells(self, simple_grid):
        """Slice along x axis."""
        x_idx = 5
        mean_slice = simple_grid.cells["stress"].mean[0, x_idx, :, :]

        nx, ny, nz = simple_grid.grid_shape
        assert mean_slice.shape == (ny, nz)

    def test_slice_y_via_cells(self, simple_grid):
        """Slice along y axis."""
        y_idx = 5
        mean_slice = simple_grid.cells["stress"].mean[0, :, y_idx, :]

        nx, ny, nz = simple_grid.grid_shape
        assert mean_slice.shape == (nx, nz)

    def test_slice_counts_via_property(self, simple_grid):
        """Counts slicing via counts property."""
        z_idx = 5
        count_slice = simple_grid.counts[0, :, :, z_idx]

        nx, ny, nz = simple_grid.grid_shape
        assert count_slice.shape == (nx, ny)

    def test_multi_timestep_slice(self, multi_ts_grid):
        """Slice specific timestep from multi-timestep grid."""
        # Access timestep 1 (index 1)
        mean_t1 = multi_ts_grid.cells["stress"].mean[1, :, :, 5]

        nx, ny, nz = multi_ts_grid.grid_shape
        assert mean_t1.shape == (nx, ny)


class TestCellsProjection:
    """Test projection via cells aggregates (replaces project_2d tests)."""

    def test_project_z_sum(self, simple_grid):
        """Project counts along z with sum."""
        # Sum along z axis
        count_projection = simple_grid.counts[0].sum(axis=2)

        nx, ny, nz = simple_grid.grid_shape
        assert count_projection.shape == (nx, ny)

    def test_project_sum_equals_total(self, simple_grid):
        """Sum projection should equal total atoms."""
        count_projection = simple_grid.counts[0].sum(axis=2)
        assert count_projection.sum() == simple_grid.n_atoms

    def test_project_all_axes(self, simple_grid):
        """Projection works for all axes."""
        counts = simple_grid.counts[0]

        # Sum along each axis
        proj_x = counts.sum(axis=0)  # Sum over x
        proj_y = counts.sum(axis=1)  # Sum over y
        proj_z = counts.sum(axis=2)  # Sum over z

        # All should sum to total atoms
        assert proj_x.sum() == simple_grid.n_atoms
        assert proj_y.sum() == simple_grid.n_atoms
        assert proj_z.sum() == simple_grid.n_atoms

    def test_project_mean_via_cells(self, simple_grid):
        """Mean projection via cells aggregates."""
        mean_3d = simple_grid.cells["stress"].mean[0]
        mean_proj_z = mean_3d.mean(axis=2)

        nx, ny, nz = simple_grid.grid_shape
        assert mean_proj_z.shape == (nx, ny)


class TestCellAggregates:
    """Test cell-level aggregation via cells accessor."""

    def test_sum_matches_field_total(self, simple_grid):
        """Sum aggregation matches total field sum."""
        stress = simple_grid["stress"][:]
        cell_sums = simple_grid.cells["stress"].sum[0]

        np.testing.assert_allclose(cell_sums.sum(), stress.sum(), rtol=1e-5)

    def test_mean_zero_for_empty_cells(self, simple_grid):
        """Mean should be 0 where counts == 0."""
        cell_means = simple_grid.cells["stress"].mean[0]
        counts = simple_grid.counts[0]

        assert np.all(cell_means[counts == 0] == 0)

    def test_min_max_bounds(self, simple_grid):
        """Min <= max for non-empty cells."""
        mins = simple_grid.cells["stress"].min[0]
        maxs = simple_grid.cells["stress"].max[0]
        counts = simple_grid.counts[0]

        non_empty = counts > 0
        assert np.all(mins[non_empty] <= maxs[non_empty])


class TestDirectCountsAccess:
    """Verify direct counts access matches cells accessor."""

    def test_counts_match(self, simple_grid):
        """grid.counts matches grid.cells.counts."""
        np.testing.assert_array_equal(simple_grid.counts, simple_grid.cells.counts)

    def test_slice_via_counts_vs_cells(self, simple_grid):
        """Direct counts slicing matches cells.counts slicing."""
        z_idx = 5
        direct = simple_grid.counts[0, :, :, z_idx]
        via_cells = simple_grid.cells.counts[0, :, :, z_idx]

        np.testing.assert_array_equal(direct, via_cells)
