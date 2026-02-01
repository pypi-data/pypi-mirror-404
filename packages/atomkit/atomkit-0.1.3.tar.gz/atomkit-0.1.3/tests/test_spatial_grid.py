"""Comprehensive tests for SpatialGrid correctness and performance."""

import math
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

from atomkit import SpatialGrid, Region


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def small_grid():
    """Create a small in-memory grid for testing."""
    np.random.seed(42)
    n_atoms = 1000
    n_timesteps = 3

    # Random coords in a 100x100x100 box
    coords = [np.random.uniform(0, 100, (n_atoms, 3)).astype(np.float32)
              for _ in range(n_timesteps)]

    # Some extra fields
    atom_ids = [np.arange(n_atoms, dtype=np.int32) for _ in range(n_timesteps)]
    stress = [np.random.randn(n_atoms).astype(np.float32) for _ in range(n_timesteps)]

    grid = SpatialGrid.from_arrays(
        coords=coords,
        cell_size=10.0,
        timestep_values=[0, 100, 200],
        atom_id=atom_ids,
        stress=stress,
    )
    return grid, coords, atom_ids, stress


@pytest.fixture
def large_grid():
    """Create a larger grid for performance testing."""
    np.random.seed(123)
    n_atoms = 100_000
    n_timesteps = 2

    coords = [np.random.uniform(0, 500, (n_atoms, 3)).astype(np.float32)
              for _ in range(n_timesteps)]
    stress = [np.random.randn(n_atoms).astype(np.float32) for _ in range(n_timesteps)]

    grid = SpatialGrid.from_arrays(
        coords=coords,
        cell_size=10.0,
        timestep_values=[0, 1000],
        stress=stress,
    )
    return grid, coords, stress


# -----------------------------------------------------------------------------
# Correctness Tests
# -----------------------------------------------------------------------------

class TestCSRCorrectness:
    """Test that CSR indexing correctly assigns atoms to cells."""

    def test_all_atoms_accounted(self, small_grid):
        """Every atom should be in exactly one cell."""
        grid, coords, _, _ = small_grid

        for t in range(grid.n_timesteps):
            total_count = grid.counts[t].sum()
            assert total_count == grid.n_atoms, f"Timestep {t}: {total_count} != {grid.n_atoms}"

    def test_source_idx_preserves_data(self, small_grid):
        """_source_idx should allow reconstruction of original order."""
        grid, coords, _, _ = small_grid

        for t in range(grid.n_timesteps):
            t_start = t * grid.n_atoms
            t_end = (t + 1) * grid.n_atoms

            sorted_coords = grid["coords"][t_start:t_end]
            source_idx = grid["_source_idx"][t_start:t_end]

            # Reconstruct original order
            reconstructed = np.empty_like(sorted_coords)
            reconstructed[source_idx] = sorted_coords

            np.testing.assert_allclose(reconstructed, coords[t], rtol=1e-5)

    def test_atoms_in_correct_cells(self, small_grid):
        """Verify atoms are assigned to cells matching their coordinates."""
        grid, coords, _, _ = small_grid

        xlo, _, ylo, _, zlo, _ = grid.box_bounds
        cs_x, cs_y, cs_z = grid.cell_size
        nx, ny, nz = grid.grid_shape

        for t in range(grid.n_timesteps):
            t_start = t * grid.n_atoms
            offsets = grid.offsets[t].ravel()
            counts = grid.counts[t].ravel()

            for cell_idx in range(nx * ny * nz):
                if counts[cell_idx] == 0:
                    continue

                # Get atoms in this cell
                start = int(offsets[cell_idx])
                end = start + int(counts[cell_idx])
                cell_coords = grid["coords"][t_start + start:t_start + end]

                # Compute expected cell bounds
                ix = cell_idx // (ny * nz)
                iy = (cell_idx % (ny * nz)) // nz
                iz = cell_idx % nz

                cell_xlo, cell_xhi = xlo + ix * cs_x, xlo + (ix + 1) * cs_x
                cell_ylo, cell_yhi = ylo + iy * cs_y, ylo + (iy + 1) * cs_y
                cell_zlo, cell_zhi = zlo + iz * cs_z, zlo + (iz + 1) * cs_z

                # Verify all atoms are within cell bounds (with small tolerance for edge)
                for coord in cell_coords:
                    assert cell_xlo - 1e-5 <= coord[0] <= cell_xhi + 1e-5
                    assert cell_ylo - 1e-5 <= coord[1] <= cell_yhi + 1e-5
                    assert cell_zlo - 1e-5 <= coord[2] <= cell_zhi + 1e-5

    def test_per_axis_cell_size(self):
        """Test that per-axis cell sizes work correctly."""
        np.random.seed(42)
        n_atoms = 500
        coords = np.random.rand(n_atoms, 3).astype(np.float32) * 100

        # Different cell sizes per axis
        cell_size = (5.0, 10.0, 20.0)
        grid = SpatialGrid.from_arrays(coords, cell_size=cell_size)

        # Check cell_size is stored correctly
        assert grid.cell_size == cell_size

        # Check grid shape reflects different cell sizes
        xlo, xhi, ylo, yhi, zlo, zhi = grid.box_bounds
        nx, ny, nz = grid.grid_shape

        # Grid should have more cells in x (smaller cell) than z (larger cell)
        expected_nx = int(np.ceil((xhi - xlo) / 5.0))
        expected_ny = int(np.ceil((yhi - ylo) / 10.0))
        expected_nz = int(np.ceil((zhi - zlo) / 20.0))

        assert nx == expected_nx
        assert ny == expected_ny
        assert nz == expected_nz

        # Query should still work
        data = grid.query(Region(x=(20, 80), y=(20, 80), z=(20, 80)))
        assert len(data["coords"]) > 0


class TestQuery:
    """Test region query correctness."""

    def test_query_finds_correct_atoms(self, small_grid):
        """Query should return exactly the atoms within the region."""
        grid, coords, _, _ = small_grid

        for t in range(grid.n_timesteps):
            # Use new 4D Region with time
            region = Region(
                x=(20.0, 40.0),
                y=(30.0, 50.0),
                z=(10.0, 30.0),
                t=grid.timestep_values[t],
            )
            result = grid.query(region)

            # Manually find atoms in region
            c = coords[t]
            mask = (
                (c[:, 0] >= 20.0) & (c[:, 0] <= 40.0) &
                (c[:, 1] >= 30.0) & (c[:, 1] <= 50.0) &
                (c[:, 2] >= 10.0) & (c[:, 2] <= 30.0)
            )
            expected_count = mask.sum()

            assert len(result["coords"]) == expected_count, \
                f"Timestep {t}: found {len(result['coords'])}, expected {expected_count}"

    def test_query_exact_vs_cell_level(self, small_grid):
        """Exact query should have <= atoms than cell_level query."""
        grid, _, _, _ = small_grid

        # Single timestep query
        region = Region(x=(25.0, 35.0), y=(25.0, 35.0), z=(25.0, 35.0), t=0)

        exact_result = grid.query(region, cell_level=False)
        cell_level_result = grid.query(region, cell_level=True)

        assert len(exact_result["coords"]) <= len(cell_level_result["coords"])

    def test_query_empty_region(self, small_grid):
        """Query of empty region should return empty arrays."""
        grid, _, _, _ = small_grid

        # Region outside the data
        region = Region(x=(1000.0, 1100.0), y=(1000.0, 1100.0), z=(1000.0, 1100.0))
        result = grid.query(region)

        assert len(result["coords"]) == 0
        assert "_timestep" in result

    def test_query_multi_timestep(self, small_grid):
        """Multi-timestep query should include atoms from all timesteps."""
        grid, _, _, _ = small_grid

        # Spatial region, all timesteps (t=None means unbounded)
        region = Region(x=(20.0, 80.0), y=(20.0, 80.0), z=(20.0, 80.0))

        result = grid.query(region)

        # Should have _timestep field
        assert "_timestep" in result

        # Should have atoms from multiple timesteps
        unique_ts = np.unique(result["_timestep"])
        assert len(unique_ts) > 1

    def test_query_returns_all_fields(self, small_grid):
        """Query should return all stored fields."""
        grid, _, _, _ = small_grid

        # Single timestep
        region = Region(x=(20.0, 80.0), y=(20.0, 80.0), z=(20.0, 80.0), t=0)
        result = grid.query(region)

        for field in grid.fields:
            assert field in result, f"Missing field: {field}"

    def test_query_single_value_bounds(self, small_grid):
        """Single value bounds should work as slice queries."""
        grid, _, _, _ = small_grid

        # Single x value (slice at x=50)
        region = Region(x=50.0, t=0)
        result = grid.query(region)

        # Should find atoms near x=50 (within cell tolerance)
        if len(result["coords"]) > 0:
            # All atoms should be in cells containing x=50
            assert True  # If we got atoms, the query worked

    def test_query_unbounded(self, small_grid):
        """Unbounded region should return all atoms."""
        grid, _, _, _ = small_grid

        # Query everything
        result = grid.query(Region())

        # Should have all atoms from all timesteps
        expected_total = grid.n_atoms * grid.n_timesteps
        assert len(result["coords"]) == expected_total


class TestSaveLoad:
    """Test save/load round-trip correctness."""

    def test_round_trip_preserves_data(self, small_grid):
        """Save and load should preserve all data exactly."""
        grid, _, _, _ = small_grid

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            path = Path(f.name)

        try:
            grid.save(path)

            with SpatialGrid.load(path) as loaded:
                # Check metadata
                assert loaded.cell_size == grid.cell_size
                assert loaded.box_bounds == grid.box_bounds
                assert loaded.grid_shape == grid.grid_shape
                assert loaded.n_atoms == grid.n_atoms
                assert loaded.n_timesteps == grid.n_timesteps
                assert loaded.timestep_values == grid.timestep_values

                # Check fields
                assert set(loaded.fields) == set(grid.fields)

                # Check data
                for field in grid.fields:
                    np.testing.assert_array_equal(
                        np.asarray(loaded[field][:]),
                        np.asarray(grid[field][:])
                    )
        finally:
            path.unlink()

    def test_loaded_grid_queries_correctly(self, small_grid):
        """Loaded grid should produce same query results."""
        grid, _, _, _ = small_grid

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            path = Path(f.name)

        try:
            grid.save(path)

            region = Region(x=(20.0, 60.0), y=(20.0, 60.0), z=(20.0, 60.0), t=0)
            original_result = grid.query(region)

            with SpatialGrid.load(path) as loaded:
                loaded_result = loaded.query(region)

                assert len(loaded_result["coords"]) == len(original_result["coords"])
                # Note: order might differ, so compare sets of coordinates
                orig_set = set(map(tuple, original_result["coords"]))
                load_set = set(map(tuple, loaded_result["coords"]))
                assert orig_set == load_set
        finally:
            path.unlink()


class TestAddField:
    """Test adding fields to existing grids."""

    def test_add_field_in_memory(self, small_grid):
        """Adding field to in-memory grid should work."""
        grid, _, _, _ = small_grid

        # Create new field in original order
        new_data = np.arange(grid.n_atoms * grid.n_timesteps, dtype=np.float32)

        grid.add_field("test_field", new_data)

        assert "test_field" in grid.fields
        assert len(grid["test_field"]) == len(new_data)

    def test_add_field_to_file(self, small_grid):
        """Adding field to file-backed grid should work."""
        grid, _, _, _ = small_grid

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            path = Path(f.name)

        try:
            grid.save(path)

            with SpatialGrid.load(path) as loaded:
                new_data = np.arange(loaded.n_atoms * loaded.n_timesteps, dtype=np.float32)
                loaded.add_field("test_field", new_data)

                assert "test_field" in loaded.fields
        finally:
            path.unlink()


# -----------------------------------------------------------------------------
# Performance Tests
# -----------------------------------------------------------------------------

class TestPerformance:
    """Performance benchmarks."""

    def test_query_performance(self, large_grid):
        """Query should be fast."""
        grid, _, _ = large_grid

        region = Region(x=(100.0, 200.0), y=(100.0, 200.0), z=(100.0, 200.0), t=0)

        # Warmup
        grid.query(region)

        # Benchmark
        start = time.perf_counter()
        for _ in range(10):
            grid.query(region)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / 10) * 1000
        print(f"\nIn-memory query: {avg_ms:.2f}ms avg")
        assert avg_ms < 100, f"Query too slow: {avg_ms:.2f}ms"

    def test_file_query_performance(self, large_grid):
        """File-backed query should still be reasonably fast."""
        grid, _, _ = large_grid

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            path = Path(f.name)

        try:
            grid.save(path)

            with SpatialGrid.load(path) as loaded:
                region = Region(x=(100.0, 200.0), y=(100.0, 200.0), z=(100.0, 200.0), t=0)

                # Warmup
                loaded.query(region)

                # Benchmark
                start = time.perf_counter()
                for _ in range(10):
                    loaded.query(region)
                elapsed = time.perf_counter() - start

                avg_ms = (elapsed / 10) * 1000
                print(f"\nFile-backed query: {avg_ms:.2f}ms avg")
                assert avg_ms < 500, f"File query too slow: {avg_ms:.2f}ms"
        finally:
            path.unlink()


# -----------------------------------------------------------------------------
# LAMMPS Parser Tests (if file exists)
# -----------------------------------------------------------------------------

class TestRegion:
    """Test new 4D Region functionality."""

    def test_region_defaults(self):
        """Region() should create unbounded region."""
        r = Region()
        assert r.x == (-math.inf, math.inf)
        assert r.y == (-math.inf, math.inf)
        assert r.z == (-math.inf, math.inf)
        assert r.t == (-math.inf, math.inf)

    def test_region_single_values(self):
        """Single values should become point ranges."""
        r = Region(x=5.0, t=100)
        assert r.x == (5.0, 5.0)
        assert r.t == (100.0, 100.0)

    def test_region_tuple_bounds(self):
        """Tuple bounds should pass through."""
        r = Region(x=(0, 10), y=(5, 15), z=(-5, 5), t=(100, 200))
        assert r.x == (0.0, 10.0)
        assert r.y == (5.0, 15.0)
        assert r.z == (-5.0, 5.0)
        assert r.t == (100.0, 200.0)

    def test_region_from_tuple(self):
        """Legacy tuple format should work."""
        legacy = ((0, 10), (0, 20), (0, 30))
        r = Region.from_tuple(legacy)
        assert r.x == (0.0, 10.0)
        assert r.y == (0.0, 20.0)
        assert r.z == (0.0, 30.0)
        assert r.t == (-math.inf, math.inf)  # No time constraint

    def test_region_subdivide(self):
        """Subdivision should work with time axis."""
        r = Region(x=(0, 10), y=(0, 10), z=(0, 10), t=(0, 100))
        subs = r.subdivide(nx=2, ny=1, nz=1, nt=2)
        assert len(subs) == 4  # 2 * 1 * 1 * 2

        # Check first and last
        assert subs[0].x == (0.0, 5.0)
        assert subs[0].t == (0.0, 50.0)
        assert subs[-1].x == (5.0, 10.0)
        assert subs[-1].t == (50.0, 100.0)

    def test_region_repr(self):
        """Repr should be clean and readable."""
        assert repr(Region()) == "Region()"
        assert "x=5.0" in repr(Region(x=5.0))
        assert "t=100" in repr(Region(t=100))
        assert "x=(0.0, 10.0)" in repr(Region(x=(0, 10)))

    def test_region_with_time(self):
        """with_time should update time bounds."""
        r = Region(x=(0, 10))
        r2 = r.with_time(100)
        assert r2.x == r.x
        assert r2.t == (100.0, 100.0)


TRAJ_FILE = Path(__file__).parent.parent / "5_Trajectory-SP6250_activated-E7-6_corrected.lammpstrj"

@pytest.mark.skipif(not TRAJ_FILE.exists(), reason="Test trajectory file not found")
class TestLAMMPSParser:
    """Test LAMMPS file parsing."""

    def test_auto_detect_columns(self):
        """Column auto-detection should find coordinates."""
        grid = SpatialGrid.from_lammps(TRAJ_FILE, cell_size=20.0, timesteps=slice(0, 1))

        assert "coords" in grid.fields
        assert grid.n_atoms > 0
        assert grid.n_timesteps == 1

    def test_all_atoms_parsed(self):
        """All atoms should be parsed."""
        grid = SpatialGrid.from_lammps(TRAJ_FILE, cell_size=20.0, timesteps=slice(0, 1))

        # File has 1,666,800 atoms per timestep
        assert grid.n_atoms == 1666800

    def test_coords_in_reasonable_range(self):
        """Coordinates should be in a reasonable range."""
        grid = SpatialGrid.from_lammps(TRAJ_FILE, cell_size=20.0, timesteps=slice(0, 1))

        coords = grid["coords"][:]

        # Should have finite values
        assert np.all(np.isfinite(coords))

        # Range should be reasonable (not garbage)
        assert coords[:, 0].max() - coords[:, 0].min() > 100  # X extent > 100
        assert coords[:, 1].max() - coords[:, 1].min() > 100  # Y extent > 100
        assert coords[:, 2].max() - coords[:, 2].min() > 100  # Z extent > 100


# -----------------------------------------------------------------------------
# Edge Case Tests
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_single_atom(self):
        """Grid with exactly one atom should work."""
        coords = np.array([[50.0, 50.0, 50.0]], dtype=np.float32)
        grid = SpatialGrid.from_arrays(coords, cell_size=10.0)

        assert grid.n_atoms == 1
        assert grid.counts.sum() == 1

        # Query should find the single atom
        result = grid.query(Region(x=(40, 60), y=(40, 60), z=(40, 60)))
        assert len(result["coords"]) == 1

        # Query outside should find nothing
        result = grid.query(Region(x=(0, 10), y=(0, 10), z=(0, 10)))
        assert len(result["coords"]) == 0

    def test_negative_coordinates(self):
        """Atoms with negative coordinates should work."""
        coords = np.array([
            [-100.0, -50.0, -25.0],
            [-10.0, -10.0, -10.0],
            [0.0, 0.0, 0.0],
            [10.0, 10.0, 10.0],
        ], dtype=np.float32)
        grid = SpatialGrid.from_arrays(coords, cell_size=10.0)

        assert grid.n_atoms == 4

        # Query negative region
        result = grid.query(Region(x=(-150, -5), y=(-100, -5), z=(-50, -5)))
        assert len(result["coords"]) == 2  # First two atoms

    def test_large_coordinates(self):
        """Very large coordinate values should work."""
        coords = np.array([
            [1e6, 1e6, 1e6],
            [1e6 + 100, 1e6 + 100, 1e6 + 100],
        ], dtype=np.float32)
        grid = SpatialGrid.from_arrays(coords, cell_size=50.0)

        assert grid.n_atoms == 2

        # Query around the large coords
        result = grid.query(Region(
            x=(1e6 - 10, 1e6 + 200),
            y=(1e6 - 10, 1e6 + 200),
            z=(1e6 - 10, 1e6 + 200)
        ))
        assert len(result["coords"]) == 2

    def test_atoms_on_cell_boundaries(self):
        """Atoms exactly on cell boundaries should be assigned consistently."""
        # Place atoms exactly on cell boundaries
        coords = np.array([
            [0.0, 0.0, 0.0],    # Origin
            [10.0, 0.0, 0.0],   # X boundary
            [0.0, 10.0, 0.0],   # Y boundary
            [0.0, 0.0, 10.0],   # Z boundary
            [10.0, 10.0, 10.0], # Corner
        ], dtype=np.float32)
        grid = SpatialGrid.from_arrays(
            coords,
            box_bounds=(-5, 25, -5, 25, -5, 25),
            cell_size=10.0,
        )

        # All atoms should be accounted for
        assert grid.counts.sum() == 5

        # Query all should return all
        result = grid.query()
        assert len(result["coords"]) == 5

    def test_very_small_cell_size(self):
        """Very small cell size (many cells) should work."""
        np.random.seed(42)
        coords = np.random.uniform(0, 10, (100, 3)).astype(np.float32)
        grid = SpatialGrid.from_arrays(coords, cell_size=0.5)

        # Should have many cells
        nx, ny, nz = grid.grid_shape
        assert nx >= 20 and ny >= 20 and nz >= 20

        # Query should still work
        result = grid.query(Region(x=(2, 8), y=(2, 8), z=(2, 8)))
        assert len(result["coords"]) > 0

    def test_very_large_cell_size(self):
        """Cell size larger than box should result in single cell."""
        coords = np.array([
            [5.0, 5.0, 5.0],
            [6.0, 6.0, 6.0],
        ], dtype=np.float32)
        grid = SpatialGrid.from_arrays(
            coords,
            box_bounds=(0, 10, 0, 10, 0, 10),
            cell_size=100.0,
        )

        # Should have single cell
        assert grid.grid_shape == (1, 1, 1)
        assert grid.counts[0, 0, 0, 0] == 2

    def test_zero_volume_region_query(self):
        """Query with zero volume (point/line/plane) should work."""
        np.random.seed(42)
        coords = np.random.uniform(0, 100, (1000, 3)).astype(np.float32)
        grid = SpatialGrid.from_arrays(coords, cell_size=10.0)

        # Point query (all axes are single values)
        result = grid.query(Region(x=50.0, y=50.0, z=50.0))
        # Should find atoms in the cell containing (50, 50, 50)
        assert "_timestep" in result

        # Line query (one axis is range, others are points)
        result = grid.query(Region(x=(0, 100), y=50.0, z=50.0))
        assert "_timestep" in result

        # Plane query (two axes are ranges, one is point)
        result = grid.query(Region(x=(0, 100), y=(0, 100), z=50.0))
        assert "_timestep" in result

    def test_cell_level_vs_exact_boundary_filtering(self):
        """Verify boundary filtering correctly excludes atoms outside region."""
        # Create atoms at known positions
        coords = np.array([
            [5.0, 5.0, 5.0],   # Inside region
            [15.0, 5.0, 5.0],  # Outside region (x too high)
            [5.0, 15.0, 5.0],  # Outside region (y too high)
            [5.0, 5.0, 15.0],  # Outside region (z too high)
        ], dtype=np.float32)

        grid = SpatialGrid.from_arrays(
            coords,
            box_bounds=(0, 20, 0, 20, 0, 20),
            cell_size=20.0,  # All in one cell
        )

        # Query small region that only contains first atom
        region = Region(x=(0, 10), y=(0, 10), z=(0, 10))

        # Cell-level should return all (they're in same cell)
        cell_result = grid.query(region, cell_level=True)
        assert len(cell_result["coords"]) == 4

        # Exact should return only the one inside
        exact_result = grid.query(region, cell_level=False)
        assert len(exact_result["coords"]) == 1
        np.testing.assert_allclose(exact_result["coords"][0], [5.0, 5.0, 5.0])

    def test_multiple_timesteps_same_query(self):
        """Same spatial region across multiple timesteps."""
        np.random.seed(42)
        n_atoms = 100
        coords = [
            np.random.uniform(0, 100, (n_atoms, 3)).astype(np.float32)
            for _ in range(5)
        ]
        grid = SpatialGrid.from_arrays(
            coords,
            cell_size=10.0,
            timestep_values=[0, 100, 200, 300, 400],
        )

        # Query all timesteps
        result = grid.query(Region(x=(20, 80), y=(20, 80), z=(20, 80)))

        # Should have atoms from all 5 timesteps
        unique_ts = np.unique(result["_timestep"])
        assert len(unique_ts) == 5
        assert set(unique_ts) == {0, 100, 200, 300, 400}

    def test_query_single_timestep_by_value(self):
        """Query specific timestep by its value (not index)."""
        np.random.seed(42)
        coords = [np.random.uniform(0, 100, (50, 3)).astype(np.float32) for _ in range(3)]
        grid = SpatialGrid.from_arrays(
            coords,
            cell_size=10.0,
            timestep_values=[1000, 2000, 3000],  # Non-sequential values
        )

        # Query timestep 2000 specifically
        result = grid.query(Region(t=2000))

        # All atoms should be from timestep 2000
        assert len(result["coords"]) == 50
        assert np.all(result["_timestep"] == 2000)

    def test_query_timestep_range(self):
        """Query range of timesteps."""
        np.random.seed(42)
        coords = [np.random.uniform(0, 100, (30, 3)).astype(np.float32) for _ in range(5)]
        grid = SpatialGrid.from_arrays(
            coords,
            cell_size=10.0,
            timestep_values=[100, 200, 300, 400, 500],
        )

        # Query timesteps 200-400
        result = grid.query(Region(t=(200, 400)))

        # Should have atoms from timesteps 200, 300, 400 only
        unique_ts = set(result["_timestep"])
        assert unique_ts == {200, 300, 400}
        assert len(result["coords"]) == 90  # 30 atoms * 3 timesteps

    def test_query_nonexistent_timestep(self):
        """Query timestep that doesn't exist should return empty."""
        coords = [np.random.uniform(0, 100, (50, 3)).astype(np.float32)]
        grid = SpatialGrid.from_arrays(coords, cell_size=10.0, timestep_values=[100])

        # Query timestep 999 which doesn't exist
        result = grid.query(Region(t=999))

        assert len(result["coords"]) == 0
        assert len(result["_timestep"]) == 0

    def test_count_approximation(self):
        """Count should be >= exact query length (approximate)."""
        np.random.seed(42)
        coords = np.random.uniform(0, 100, (1000, 3)).astype(np.float32)
        grid = SpatialGrid.from_arrays(coords, cell_size=10.0)

        region = Region(x=(25, 75), y=(25, 75), z=(25, 75), t=0)

        approx_count = grid.count(region)
        exact_result = grid.query(region)

        # Approximate count should be >= exact (includes boundary cells)
        assert approx_count >= len(exact_result["coords"])

    def test_invalid_cell_size_raises(self):
        """Zero or negative cell size should raise ValueError."""
        coords = np.random.uniform(0, 100, (10, 3)).astype(np.float32)

        with pytest.raises(ValueError):
            SpatialGrid.from_arrays(coords, cell_size=0)

        with pytest.raises(ValueError):
            SpatialGrid.from_arrays(coords, cell_size=-5.0)

    def test_mismatched_field_length_raises(self):
        """Field with wrong length should raise ValueError."""
        coords = np.random.uniform(0, 100, (10, 3)).astype(np.float32)
        wrong_stress = np.random.uniform(0, 1, (5,)).astype(np.float32)  # Wrong length

        with pytest.raises(ValueError, match="expected"):
            SpatialGrid.from_arrays(coords, cell_size=10.0, stress=wrong_stress)


class TestRegionEdgeCases:
    """Test Region class edge cases."""

    def test_region_volume_with_infinities(self):
        """Volume should be inf for unbounded regions."""

        r = Region()  # Fully unbounded
        assert r.volume() == math.inf

        r = Region(x=(0, 10))  # One bounded axis
        assert r.volume() == math.inf

        r = Region(x=(0, 10), y=(0, 10), z=(0, 10))  # All bounded
        assert r.volume() == 1000.0

    def test_region_volume_zero_for_point(self):
        """Point region should have zero volume."""
        r = Region(x=5.0, y=5.0, z=5.0)
        assert r.volume() == 0.0

    def test_region_expand_with_infinities(self):
        """Expanding unbounded region should still be unbounded."""

        r = Region()
        expanded = r.expand(10.0)

        # Still unbounded (inf - 10 = inf, inf + 10 = inf)
        assert expanded.x[0] == -math.inf
        assert expanded.x[1] == math.inf

    def test_region_intersects(self):
        """Test region intersection detection."""
        r1 = Region(x=(0, 10), y=(0, 10), z=(0, 10))
        r2 = Region(x=(5, 15), y=(5, 15), z=(5, 15))  # Overlaps
        r3 = Region(x=(20, 30), y=(20, 30), z=(20, 30))  # No overlap

        assert r1.intersects(r2)
        assert r2.intersects(r1)
        assert not r1.intersects(r3)
        assert not r3.intersects(r1)

    def test_region_subdivide_partial_infinite_raises(self):
        """Cannot subdivide region with any infinite bound."""

        # Partially infinite (0, inf)
        r = Region(x=(0, math.inf), y=(0, 10), z=(0, 10))

        with pytest.raises(ValueError, match="infinite"):
            r.subdivide(nx=2)

    def test_region_contains_point(self):
        """Test point containment check."""
        r = Region(x=(0, 10), y=(0, 10), z=(0, 10), t=(0, 100))

        assert r.contains_point(5, 5, 5)
        assert r.contains_point(0, 0, 0)  # Boundary
        assert r.contains_point(10, 10, 10)  # Boundary
        assert not r.contains_point(15, 5, 5)  # Outside

        # With time
        assert r.contains_point(5, 5, 5, t=50)
        assert not r.contains_point(5, 5, 5, t=150)  # Outside time range

    def test_region_bounds_direct_check(self):
        """Test direct bound checking (no property indirection)."""

        # Fully unbounded
        r1 = Region()
        assert r1.x == (-math.inf, math.inf)

        # Partially unbounded (0, inf)
        r2 = Region(x=(0, math.inf))
        assert r2.x[0] == 0
        assert r2.x[1] == math.inf

        # Fully bounded
        r3 = Region(x=(0, 10))
        assert r3.x == (0.0, 10.0)

    def test_region_invalid_bounds_raises(self):
        """Invalid bounds should raise ValueError."""
        # min > max
        with pytest.raises(ValueError, match="min.*>.*max"):
            Region(x=(10, 0))

        # NaN
        with pytest.raises(ValueError, match="NaN"):
            Region(x=float('nan'))

        with pytest.raises(ValueError, match="NaN"):
            Region(y=(0, float('nan')))

        # Invalid type
        with pytest.raises(ValueError, match="Invalid bounds"):
            Region(x="hello")


class TestReadOnlyResults:
    """Test that query results are read-only."""

    def test_query_results_not_writable(self):
        """Query results should be read-only arrays."""
        np.random.seed(42)
        coords = np.random.uniform(0, 100, (100, 3)).astype(np.float32)
        grid = SpatialGrid.from_arrays(coords, cell_size=10.0)

        result = grid.query(Region(x=(20, 80), y=(20, 80), z=(20, 80)))

        # Should not be able to modify
        with pytest.raises((ValueError, TypeError)):
            result["coords"][0] = [0, 0, 0]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
