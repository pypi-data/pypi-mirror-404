"""Tests for HDF5 file migration (adding cell aggregates to old files)."""

import tempfile
from pathlib import Path

import h5py
import numpy as np
import pytest

from atomkit import SpatialGrid


def create_old_format_h5(path: Path) -> None:
    """Create an HDF5 file in old format (without _cells group)."""
    # Create a simple grid
    np.random.seed(42)
    n_atoms = 100
    coords = np.random.uniform(0, 50, (n_atoms, 3)).astype(np.float32)
    stress = np.random.randn(n_atoms).astype(np.float32)

    grid = SpatialGrid.from_arrays(
        coords=coords,
        cell_size=10.0,
        stress=stress,
    )

    # Save normally (will include _cells)
    grid.save(path)
    grid.close()

    # Remove the _cells group to simulate old format
    with h5py.File(path, "r+") as f:
        if "_cells" in f:
            del f["_cells"]


class TestMigration:
    """Test automatic migration of old HDF5 files."""

    def test_migration_adds_cell_aggregates(self, tmp_path):
        """Loading an old file should add _cells group."""
        path = tmp_path / "old_format.h5"
        create_old_format_h5(path)

        # Verify _cells was removed
        with h5py.File(path, "r") as f:
            assert "_cells" not in f

        # Load should trigger migration
        grid = SpatialGrid.load(path)

        # Verify _cells now exists
        with h5py.File(path, "r") as f:
            assert "_cells" in f
            assert "stress" in f["_cells"]

        # Verify aggregates work
        assert "stress" in grid.cells.fields
        agg = grid.cells["stress"]
        assert agg.sum.shape == (1,) + grid.grid_shape
        assert agg.mean is not None

        grid.close()

    def test_migration_preserves_data(self, tmp_path):
        """Migration should preserve all original data."""
        path = tmp_path / "old_format.h5"

        # Create grid with known values
        np.random.seed(123)
        n_atoms = 50
        coords = np.random.uniform(0, 30, (n_atoms, 3)).astype(np.float32)
        stress = np.arange(n_atoms, dtype=np.float32)

        grid = SpatialGrid.from_arrays(coords=coords, cell_size=10.0, stress=stress)
        grid.save(path)
        original_stress = grid["stress"][:]
        grid.close()

        # Remove _cells
        with h5py.File(path, "r+") as f:
            del f["_cells"]

        # Load and verify data preserved
        grid = SpatialGrid.load(path)
        np.testing.assert_array_equal(grid["stress"][:], original_stress)
        grid.close()

    def test_new_files_not_migrated(self, tmp_path):
        """Files with _cells should not be modified."""
        path = tmp_path / "new_format.h5"

        coords = np.random.uniform(0, 20, (30, 3)).astype(np.float32)
        stress = np.random.randn(30).astype(np.float32)
        grid = SpatialGrid.from_arrays(coords=coords, cell_size=5.0, stress=stress)
        grid.save(path)
        grid.close()

        # Verify _cells exists in new file
        with h5py.File(path, "r") as f:
            assert "_cells" in f

        # Get modification time
        mtime_before = path.stat().st_mtime

        # Load (should not migrate since _cells already exists)
        grid = SpatialGrid.load(path)
        grid.close()

        # File should not have been modified
        with h5py.File(path, "r") as f:
            assert "_cells" in f
            assert "stress" in f["_cells"]

    def test_migration_handles_multiple_fields(self, tmp_path):
        """Migration should aggregate all numeric fields."""
        path = tmp_path / "multi_field.h5"

        n_atoms = 40
        coords = np.random.uniform(0, 20, (n_atoms, 3)).astype(np.float32)
        field_a = np.random.randn(n_atoms).astype(np.float32)
        field_b = np.random.randn(n_atoms).astype(np.float32)

        grid = SpatialGrid.from_arrays(
            coords=coords,
            cell_size=5.0,
            field_a=field_a,
            field_b=field_b,
        )
        grid.save(path)
        grid.close()

        # Remove _cells
        with h5py.File(path, "r+") as f:
            del f["_cells"]

        # Load and verify both fields migrated
        grid = SpatialGrid.load(path)
        assert "field_a" in grid.cells.fields
        assert "field_b" in grid.cells.fields
        grid.close()
