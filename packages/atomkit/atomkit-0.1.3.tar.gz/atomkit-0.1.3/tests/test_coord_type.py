"""Tests for coord_type parameter in LAMMPS parsing."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from atomkit import SpatialGrid
from atomkit.io.lammps import parse_lammps, CoordType


# -----------------------------------------------------------------------------
# Test fixtures - inline LAMMPS trajectory data
# -----------------------------------------------------------------------------

def make_lammpstrj(columns: list[str], atoms: list[list[float]]) -> str:
    """Create a minimal LAMMPS trajectory string.

    Parameters
    ----------
    columns : list[str]
        Column names for ITEM: ATOMS header (e.g., ["id", "x", "y", "z"])
    atoms : list[list[float]]
        Atom data rows, each row matches columns
    """
    header = f"""ITEM: TIMESTEP
0
ITEM: NUMBER OF ATOMS
{len(atoms)}
ITEM: BOX BOUNDS pp pp pp
0 100
0 100
0 100
ITEM: ATOMS {" ".join(columns)}
"""
    atom_lines = "\n".join(" ".join(str(v) for v in row) for row in atoms)
    return header + atom_lines + "\n"


@pytest.fixture
def traj_wrapped_only(tmp_path):
    """Trajectory with only wrapped coordinates (x, y, z)."""
    content = make_lammpstrj(
        ["id", "x", "y", "z", "vx", "vy", "vz"],
        [
            [1, 10.0, 20.0, 30.0, 0.1, 0.2, 0.3],
            [2, 40.0, 50.0, 60.0, 0.4, 0.5, 0.6],
        ]
    )
    path = tmp_path / "wrapped.lammpstrj"
    path.write_text(content)
    return path


@pytest.fixture
def traj_unwrapped_only(tmp_path):
    """Trajectory with only unwrapped coordinates (xu, yu, zu)."""
    content = make_lammpstrj(
        ["id", "xu", "yu", "zu"],
        [
            [1, 110.0, 120.0, 130.0],  # Outside box (unwrapped)
            [2, 140.0, 150.0, 160.0],
        ]
    )
    path = tmp_path / "unwrapped.lammpstrj"
    path.write_text(content)
    return path


@pytest.fixture
def traj_scaled_only(tmp_path):
    """Trajectory with only scaled coordinates (xs, ys, zs)."""
    content = make_lammpstrj(
        ["id", "xs", "ys", "zs"],
        [
            [1, 0.1, 0.2, 0.3],  # Fractional coordinates
            [2, 0.4, 0.5, 0.6],
        ]
    )
    path = tmp_path / "scaled.lammpstrj"
    path.write_text(content)
    return path


@pytest.fixture
def traj_all_types(tmp_path):
    """Trajectory with all coordinate types - tests preference order."""
    # Wrapped: 10, 20, 30
    # Unwrapped: 110, 120, 130  (should be preferred in auto mode)
    # Scaled: 0.1, 0.2, 0.3
    content = make_lammpstrj(
        ["id", "x", "y", "z", "xu", "yu", "zu", "xs", "ys", "zs"],
        [
            [1, 10.0, 20.0, 30.0, 110.0, 120.0, 130.0, 0.1, 0.2, 0.3],
            [2, 40.0, 50.0, 60.0, 140.0, 150.0, 160.0, 0.4, 0.5, 0.6],
        ]
    )
    path = tmp_path / "all_types.lammpstrj"
    path.write_text(content)
    return path


@pytest.fixture
def traj_wrapped_and_scaled(tmp_path):
    """Trajectory with wrapped and scaled (no unwrapped) - tests fallback."""
    content = make_lammpstrj(
        ["id", "x", "y", "z", "xs", "ys", "zs"],
        [
            [1, 10.0, 20.0, 30.0, 0.1, 0.2, 0.3],
            [2, 40.0, 50.0, 60.0, 0.4, 0.5, 0.6],
        ]
    )
    path = tmp_path / "wrapped_scaled.lammpstrj"
    path.write_text(content)
    return path


# -----------------------------------------------------------------------------
# Tests for explicit coord_type selection
# -----------------------------------------------------------------------------

class TestExplicitCoordType:
    """Test explicit coordinate type selection."""

    def test_explicit_wrapped(self, traj_all_types):
        """coord_type='wrapped' should use x, y, z columns."""
        coords, _, _, _ = parse_lammps(traj_all_types, coord_type="wrapped")

        # Should get wrapped coords: 10, 20, 30 for atom 1
        np.testing.assert_allclose(coords[0][0], [10.0, 20.0, 30.0])
        np.testing.assert_allclose(coords[0][1], [40.0, 50.0, 60.0])

    def test_explicit_unwrapped(self, traj_all_types):
        """coord_type='unwrapped' should use xu, yu, zu columns."""
        coords, _, _, _ = parse_lammps(traj_all_types, coord_type="unwrapped")

        # Should get unwrapped coords: 110, 120, 130 for atom 1
        np.testing.assert_allclose(coords[0][0], [110.0, 120.0, 130.0])
        np.testing.assert_allclose(coords[0][1], [140.0, 150.0, 160.0])

    def test_explicit_scaled(self, traj_all_types):
        """coord_type='scaled' should use xs, ys, zs columns."""
        coords, _, _, _ = parse_lammps(traj_all_types, coord_type="scaled")

        # Should get scaled coords: 0.1, 0.2, 0.3 for atom 1
        np.testing.assert_allclose(coords[0][0], [0.1, 0.2, 0.3])
        np.testing.assert_allclose(coords[0][1], [0.4, 0.5, 0.6])


# -----------------------------------------------------------------------------
# Tests for auto mode preference order
# -----------------------------------------------------------------------------

class TestAutoPreference:
    """Test that auto mode prefers unwrapped > wrapped > scaled."""

    def test_auto_prefers_unwrapped(self, traj_all_types):
        """Auto mode should prefer unwrapped when all types available."""
        coords, _, _, _ = parse_lammps(traj_all_types, coord_type="auto")

        # Should get unwrapped coords (preferred)
        np.testing.assert_allclose(coords[0][0], [110.0, 120.0, 130.0])

    def test_auto_falls_back_to_wrapped(self, traj_wrapped_and_scaled):
        """Auto mode should fall back to wrapped when no unwrapped."""
        coords, _, _, _ = parse_lammps(traj_wrapped_and_scaled, coord_type="auto")

        # Should get wrapped coords (unwrapped not available)
        np.testing.assert_allclose(coords[0][0], [10.0, 20.0, 30.0])

    def test_auto_uses_scaled_as_last_resort(self, traj_scaled_only):
        """Auto mode should use scaled when no other types available."""
        coords, _, _, _ = parse_lammps(traj_scaled_only, coord_type="auto")

        # Should get scaled coords
        np.testing.assert_allclose(coords[0][0], [0.1, 0.2, 0.3])

    def test_auto_uses_only_available_type(self, traj_wrapped_only):
        """Auto mode should work with only wrapped coordinates."""
        coords, _, _, _ = parse_lammps(traj_wrapped_only, coord_type="auto")

        np.testing.assert_allclose(coords[0][0], [10.0, 20.0, 30.0])


# -----------------------------------------------------------------------------
# Tests for error handling
# -----------------------------------------------------------------------------

class TestCoordTypeErrors:
    """Test error handling for missing coordinate types."""

    def test_missing_unwrapped_raises(self, traj_wrapped_only):
        """Requesting unwrapped when not available should raise."""
        with pytest.raises(ValueError, match="Could not find unwrapped coordinates"):
            parse_lammps(traj_wrapped_only, coord_type="unwrapped")

    def test_missing_scaled_raises(self, traj_wrapped_only):
        """Requesting scaled when not available should raise."""
        with pytest.raises(ValueError, match="Could not find scaled coordinates"):
            parse_lammps(traj_wrapped_only, coord_type="scaled")

    def test_error_message_shows_available(self, traj_wrapped_only):
        """Error message should list available coordinate columns."""
        with pytest.raises(ValueError, match="Available coord columns:.*x.*y.*z"):
            parse_lammps(traj_wrapped_only, coord_type="unwrapped")


# -----------------------------------------------------------------------------
# Integration tests with SpatialGrid
# -----------------------------------------------------------------------------

class TestSpatialGridCoordType:
    """Test coord_type parameter through SpatialGrid.from_lammps()."""

    def test_from_lammps_passes_coord_type(self, traj_all_types):
        """SpatialGrid.from_lammps should pass coord_type to parser."""
        grid = SpatialGrid.from_lammps(
            traj_all_types,
            cell_size=50.0,
            coord_type="wrapped"
        )

        # Wrapped coords are in 0-100 range, should fit in ~2 cells per axis
        assert grid.n_atoms == 2
        coords = grid["coords"][:]
        # First atom should be near (10, 20, 30)
        assert np.all(coords[:, 0] < 100)  # All x coords in box

    def test_from_lammps_unwrapped_extends_box(self, traj_all_types):
        """Unwrapped coords can extend beyond original box bounds."""
        grid = SpatialGrid.from_lammps(
            traj_all_types,
            cell_size=50.0,
            coord_type="unwrapped"
        )

        # Unwrapped coords are 110-160, should extend beyond 0-100 box
        coords = grid["coords"][:]
        assert np.any(coords[:, 0] > 100)  # Some x coords outside original box
