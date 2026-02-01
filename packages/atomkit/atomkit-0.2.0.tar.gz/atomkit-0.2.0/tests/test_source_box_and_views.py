"""Tests for SourceBox, GridView, and related APIs."""

import numpy as np
import pytest

from atomkit import SpatialGrid, SourceBox, GridView


@pytest.fixture
def simple_grid():
    """Create a simple grid for testing."""
    np.random.seed(42)
    n_atoms = 500
    coords = np.random.uniform(0, 100, (n_atoms, 3)).astype(np.float32)
    stress = np.random.randn(n_atoms).astype(np.float32)

    return SpatialGrid.from_arrays(
        coords=coords,
        cell_size=10.0,
        box_bounds=(0, 100, 0, 100, 0, 100),
        stress=stress,
    )


class TestSourceBox:
    """Tests for SourceBox dataclass."""

    def test_default_source_box(self):
        """Default SourceBox has no bounds."""
        box = SourceBox()
        assert box.bounds is None
        assert box.tilt is None
        assert box.boundary == ""
        assert not box.is_valid
        assert not box.is_triclinic

    def test_orthogonal_box(self):
        """Orthogonal box with valid bounds."""
        box = SourceBox(
            bounds=(0, 10, 0, 20, 0, 30),
            boundary="pp pp pp",
        )
        assert box.is_valid
        assert not box.is_triclinic
        assert box.bounds == (0, 10, 0, 20, 0, 30)

    def test_triclinic_box(self):
        """Triclinic box with tilt factors."""
        box = SourceBox(
            bounds=(0, 10, 0, 20, 0, 30),
            tilt=(1.0, 0.5, 0.2),
            boundary="pp pp pp",
        )
        assert box.is_valid
        assert box.is_triclinic

    def test_zero_tilt_not_triclinic(self):
        """Zero tilt factors are not triclinic."""
        box = SourceBox(
            bounds=(0, 10, 0, 20, 0, 30),
            tilt=(0.0, 0.0, 0.0),
        )
        assert not box.is_triclinic

    def test_contains_orthogonal(self):
        """contains() for orthogonal box."""
        box = SourceBox(bounds=(0, 10, 0, 10, 0, 10))
        assert box.contains(5, 5, 5)
        assert box.contains(0, 0, 0)
        assert box.contains(10, 10, 10)
        assert not box.contains(11, 5, 5)
        assert not box.contains(-1, 5, 5)

    def test_contains_invalid_box(self):
        """contains() returns True for invalid box (no bounds)."""
        box = SourceBox()
        assert box.contains(999, 999, 999)


class TestGridView:
    """Tests for GridView class."""

    def test_view_returns_gridview(self, simple_grid):
        """view() returns a GridView instance."""
        view = simple_grid.view(x=(20, 80))
        assert isinstance(view, GridView)
        assert view.parent is simple_grid

    def test_view_full_extent(self, simple_grid):
        """view() with no args returns full grid."""
        view = simple_grid.view()
        assert view.grid_shape == simple_grid.grid_shape
        assert view.n_timesteps == simple_grid.n_timesteps

    def test_view_x_slice(self, simple_grid):
        """view() with x bounds reduces x dimension."""
        view = simple_grid.view(x=(20, 60))
        nx, ny, nz = view.grid_shape
        orig_nx, orig_ny, orig_nz = simple_grid.grid_shape

        # x should be reduced, y and z unchanged
        assert nx < orig_nx
        assert ny == orig_ny
        assert nz == orig_nz

    def test_view_counts_shape(self, simple_grid):
        """View counts have correct shape."""
        view = simple_grid.view(x=(20, 80), y=(30, 70))
        counts = view.counts
        assert counts.shape == (simple_grid.n_timesteps,) + view.grid_shape

    def test_view_box_bounds(self, simple_grid):
        """View box_bounds are computed correctly."""
        view = simple_grid.view(x=(20, 60), y=(30, 70), z=(10, 90))
        xlo, xhi, ylo, yhi, zlo, zhi = view.box_bounds

        # Bounds should be within original and close to specified
        assert xlo >= 20
        assert xhi <= 60
        assert ylo >= 30
        assert yhi <= 70
        assert zlo >= 10
        assert zhi <= 90

    def test_view_cell_size_preserved(self, simple_grid):
        """View preserves cell size."""
        view = simple_grid.view(x=(20, 80))
        assert view.cell_size == simple_grid.cell_size

    def test_view_repr(self, simple_grid):
        """View has meaningful repr."""
        view = simple_grid.view(x=(20, 80))
        r = repr(view)
        assert "GridView" in r
        assert "shape" in r


class TestViewSourceBox:
    """Tests for view_source_box() method."""

    def test_no_source_box_returns_none(self, simple_grid):
        """view_source_box() returns None if no source box."""
        # simple_grid was created from arrays, not from_lammps, so no source_box
        result = simple_grid.view_source_box()
        assert result is None

    def test_with_source_box(self):
        """view_source_box() constrains to source box bounds."""
        np.random.seed(42)
        # Create grid with wider bounds than source box
        coords = np.random.uniform(-10, 110, (200, 3)).astype(np.float32)
        grid = SpatialGrid.from_arrays(
            coords=coords,
            cell_size=10.0,
            box_bounds=(-20, 120, -20, 120, -20, 120),  # padded
        )
        # Manually set source_box
        grid.source_box = SourceBox(bounds=(0, 100, 0, 100, 0, 100))

        view = grid.view_source_box()
        assert view is not None
        xlo, xhi, ylo, yhi, zlo, zhi = view.box_bounds
        # View should be constrained to source box
        assert xlo >= 0
        assert xhi <= 100


class TestCellsAccessor:
    """Tests for cells accessor and precomputed aggregates."""

    def test_cells_counts(self, simple_grid):
        """cells.counts matches grid counts."""
        np.testing.assert_array_equal(simple_grid.cells.counts, simple_grid.counts)

    def test_cells_fields(self, simple_grid):
        """cells.fields lists available aggregates."""
        fields = simple_grid.cells.fields
        assert "stress" in fields

    def test_cells_aggregates_shape(self, simple_grid):
        """Cell aggregates have correct shape."""
        agg = simple_grid.cells["stress"]
        expected_shape = (simple_grid.n_timesteps,) + simple_grid.grid_shape

        assert agg.sum.shape == expected_shape
        assert agg.min.shape == expected_shape
        assert agg.max.shape == expected_shape
        assert agg.mean.shape == expected_shape

    def test_cells_sum_matches_field_total(self, simple_grid):
        """Cell sum aggregates match total field sum."""
        stress = simple_grid["stress"][:]
        # New API: .sum() returns total, or .sum.np.sum() for numpy
        cell_sum_total = simple_grid.cells["stress"].sum()
        np.testing.assert_allclose(cell_sum_total, stress.sum(), rtol=1e-5)

    def test_cells_min_max_bounds(self, simple_grid):
        """Cell min/max are within field bounds."""
        stress = simple_grid["stress"][:]
        agg = simple_grid.cells["stress"]

        # Non-zero cells should have min <= max
        counts = simple_grid.counts
        non_empty = counts > 0
        assert np.all(agg.min[non_empty] <= agg.max[non_empty])

    def test_cells_mean_empty_cells(self, simple_grid):
        """Mean is 0 for empty cells."""
        mean = simple_grid.cells["stress"].mean
        counts = simple_grid.counts
        assert np.all(mean[counts == 0] == 0)

    def test_cells_contains(self, simple_grid):
        """__contains__ works for cells accessor."""
        assert "stress" in simple_grid.cells
        assert "nonexistent" not in simple_grid.cells

    def test_cells_missing_field_raises(self, simple_grid):
        """Accessing missing field raises KeyError."""
        with pytest.raises(KeyError):
            simple_grid.cells["nonexistent"]
