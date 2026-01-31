"""Tests for SpatialGrid.slice_2d and project_2d methods."""

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

    return SpatialGrid.from_arrays(
        coords=coords,
        cell_size=10.0,
        box_bounds=(0, 100, 0, 100, 0, 100),
        timestep_values=[0, 100, 200],
    )


class TestSlice2D:
    """Test slice_2d method."""

    def test_slice_z_counts(self, simple_grid):
        """Slice counts along z axis."""
        data, info = simple_grid.slice_2d("z", 50.0, field="counts")

        # Shape should be (ny, nx) for z-slice with transpose
        nx, ny, nz = simple_grid.grid_shape
        assert data.shape == (ny, nx)
        assert info["axis"] == "z"
        assert info["xlabel"] == "x"
        assert info["ylabel"] == "y"

    def test_slice_x_counts(self, simple_grid):
        """Slice counts along x axis."""
        data, info = simple_grid.slice_2d("x", 50.0, field="counts")

        nx, ny, nz = simple_grid.grid_shape
        assert data.shape == (nz, ny)  # (nz, ny) after transpose
        assert info["xlabel"] == "y"
        assert info["ylabel"] == "z"

    def test_slice_y_counts(self, simple_grid):
        """Slice counts along y axis."""
        data, info = simple_grid.slice_2d("y", 50.0, field="counts")

        nx, ny, nz = simple_grid.grid_shape
        assert data.shape == (nz, nx)
        assert info["xlabel"] == "x"
        assert info["ylabel"] == "z"

    def test_slice_field_mean(self, simple_grid):
        """Slice stress field with mean aggregation."""
        data, info = simple_grid.slice_2d("z", 50.0, field="stress", cell_aggregator="mean")

        assert data.dtype == np.float64
        assert info["field"] == "stress"

    def test_slice_field_sum(self, simple_grid):
        """Slice stress field with sum aggregation."""
        data, info = simple_grid.slice_2d("z", 50.0, field="stress", cell_aggregator="sum")

        assert data.dtype == np.float64

    def test_slice_position_out_of_bounds(self, simple_grid):
        """Position outside grid raises ValueError."""
        with pytest.raises(ValueError, match="outside bounds"):
            simple_grid.slice_2d("z", 150.0)

    def test_slice_multi_timestep_requires_timestep(self, multi_ts_grid):
        """Multi-timestep grid requires timestep parameter."""
        with pytest.raises(ValueError, match="timestep required"):
            multi_ts_grid.slice_2d("z", 50.0)

    def test_slice_with_timestep(self, multi_ts_grid):
        """Slice with explicit timestep."""
        data, info = multi_ts_grid.slice_2d("z", 50.0, timestep=100)

        assert info["timestep"] == 100


class TestProject2D:
    """Test project_2d method."""

    def test_project_z_sum(self, simple_grid):
        """Project counts along z with sum."""
        data, info = simple_grid.project_2d("z", field="counts", projection="sum")

        nx, ny, nz = simple_grid.grid_shape
        assert data.shape == (ny, nx)
        assert info["projection"] == "sum"

    def test_project_sum_equals_total(self, simple_grid):
        """Sum projection should equal total atoms."""
        data, info = simple_grid.project_2d("z", field="counts", projection="sum")

        # Total of projection should equal total atoms
        assert data.sum() == simple_grid.n_atoms

    def test_project_all_axes(self, simple_grid):
        """Projection works for all axes."""
        for axis in ["x", "y", "z"]:
            data, info = simple_grid.project_2d(axis, field="counts")
            assert data.sum() == simple_grid.n_atoms

    def test_project_mean(self, simple_grid):
        """Mean projection."""
        data_sum, _ = simple_grid.project_2d("z", projection="sum")
        data_mean, _ = simple_grid.project_2d("z", projection="mean")

        nz = simple_grid.grid_shape[2]
        np.testing.assert_allclose(data_mean * nz, data_sum)


class TestCellFieldAggregation:
    """Test _cell_field_3d internal method."""

    def test_sum_aggregation(self, simple_grid):
        """Sum aggregation should match total field sum per cell."""
        # Get raw data
        stress = np.asarray(simple_grid["stress"][:])
        counts = simple_grid.counts[0]

        # Aggregate via method
        cell_sums = simple_grid._cell_field_3d("stress", 0, "sum")

        # Total should match
        np.testing.assert_allclose(cell_sums.sum(), stress.sum(), rtol=1e-5)

    def test_mean_aggregation_nonzero(self, simple_grid):
        """Mean should be non-zero where counts > 0."""
        cell_means = simple_grid._cell_field_3d("stress", 0, "mean")
        counts = simple_grid.counts[0]

        # Where counts > 0, mean can be anything (including 0 by chance)
        # Where counts == 0, mean should be 0
        assert np.all(cell_means[counts == 0] == 0)


class TestSliceMatchesCounts:
    """Verify slice_2d matches direct array access."""

    def test_counts_slice_matches_array(self, simple_grid):
        """slice_2d counts should match direct array indexing."""
        # Get slice via method
        data, info = simple_grid.slice_2d("z", 50.0, field="counts")

        # Get same slice directly
        cell_idx = info["cell_index"]
        direct = simple_grid.counts[0, :, :, cell_idx].T

        np.testing.assert_array_equal(data, direct)
