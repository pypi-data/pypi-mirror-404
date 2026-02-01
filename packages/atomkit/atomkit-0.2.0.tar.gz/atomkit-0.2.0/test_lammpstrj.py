#!/usr/bin/env python3
"""Test script for parsing the real lammpstrj file."""

import sys
import time
from pathlib import Path

# Add atomkit to path
sys.path.insert(0, str(Path(__file__).parent))

from atomkit import SpatialGrid

TRAJ_FILE = Path(__file__).parent / "5_Trajectory-SP6250_activated-E7-6_corrected.lammpstrj"

# No manual column mapping needed - auto-detected from ITEM: ATOMS header!


def test_parse_single_timestep():
    """Test parsing just the first timestep."""
    print("=" * 60)
    print("TEST: Parse single timestep (auto-detect columns)")
    print("=" * 60)

    start = time.time()

    # Load only first timestep - columns auto-detected from header!
    grid = SpatialGrid.from_lammps(
        TRAJ_FILE,
        cell_size=10.0,  # Larger cells for faster indexing
        timesteps=slice(0, 1),  # Just first timestep
    )

    elapsed = time.time() - start
    print(f"Parsing took: {elapsed:.2f}s")
    print(f"Grid shape: {grid.grid_shape}")
    print(f"Box bounds: {grid.box_bounds}")
    print(f"N atoms: {grid.n_atoms:,}")
    print(f"N timesteps: {grid.n_timesteps}")
    print(f"Timestep values: {grid.timestep_values}")
    print(f"Fields: {grid.fields}")

    # Check coords
    coords = grid["coords"]
    print(f"\nCoords shape: {coords.shape}")
    print(f"Coords dtype: {coords.dtype}")
    print(f"X range: [{coords[:, 0].min():.2f}, {coords[:, 0].max():.2f}]")
    print(f"Y range: [{coords[:, 1].min():.2f}, {coords[:, 1].max():.2f}]")
    print(f"Z range: [{coords[:, 2].min():.2f}, {coords[:, 2].max():.2f}]")

    # Verify box_bounds now matches actual data (with padding)
    xlo, xhi, ylo, yhi, zlo, zhi = grid.box_bounds
    print(f"\nBox bounds (computed from data):")
    print(f"  X: [{xlo:.2f}, {xhi:.2f}]")
    print(f"  Y: [{ylo:.2f}, {yhi:.2f}]")
    print(f"  Z: [{zlo:.2f}, {zhi:.2f}]")

    return grid


def test_query(grid):
    """Test region query."""
    print("\n" + "=" * 60)
    print("TEST: Region query")
    print("=" * 60)

    # Get box center for query
    xlo, xhi, ylo, yhi, zlo, zhi = grid.box_bounds
    x_mid = (xlo + xhi) / 2
    y_mid = (ylo + yhi) / 2
    z_mid = (zlo + zhi) / 2

    # Query a 50A cube around center
    size = 50.0
    region = (
        (x_mid - size, x_mid + size),
        (y_mid - size, y_mid + size),
        (z_mid - size, z_mid + size),
    )

    print(f"Query region: {region}")

    start = time.time()
    result = grid.query(region)
    elapsed = time.time() - start

    print(f"Query took: {elapsed:.4f}s")
    print(f"Atoms found: {len(result['coords']):,}")
    print(f"Result keys: {list(result.keys())}")

    if len(result["coords"]) > 0:
        print(f"\nSample atom coords:")
        for i in range(min(5, len(result["coords"]))):
            x, y, z = result["coords"][i]
            print(f"  [{i}] ({x:.2f}, {y:.2f}, {z:.2f})")

    return result


def test_save_load(grid):
    """Test save and load."""
    print("\n" + "=" * 60)
    print("TEST: Save and load")
    print("=" * 60)

    h5_path = TRAJ_FILE.parent / "test_output.h5"

    # Save
    start = time.time()
    grid.save(h5_path)
    elapsed = time.time() - start
    print(f"Save took: {elapsed:.2f}s")
    print(f"File size: {h5_path.stat().st_size / 1024 / 1024:.2f} MB")

    # Load
    start = time.time()
    with SpatialGrid.load(h5_path) as loaded:
        elapsed = time.time() - start
        print(f"Load took: {elapsed:.4f}s")

        print(f"\nLoaded grid:")
        print(f"  N atoms: {loaded.n_atoms:,}")
        print(f"  N timesteps: {loaded.n_timesteps}")
        print(f"  Fields: {loaded.fields}")

        # Test query on loaded grid
        xlo, xhi, ylo, yhi, zlo, zhi = loaded.box_bounds
        region = (
            ((xlo + xhi) / 2 - 25, (xlo + xhi) / 2 + 25),
            ((ylo + yhi) / 2 - 25, (ylo + yhi) / 2 + 25),
            ((zlo + zhi) / 2 - 25, (zlo + zhi) / 2 + 25),
        )

        result = loaded.query(region)
        print(f"  Query result: {len(result['coords']):,} atoms")

    # Cleanup
    h5_path.unlink()
    print("Cleaned up test file")


def test_all_timesteps():
    """Test parsing all timesteps."""
    print("\n" + "=" * 60)
    print("TEST: Parse all timesteps (auto-detect)")
    print("=" * 60)

    start = time.time()

    grid = SpatialGrid.from_lammps(
        TRAJ_FILE,
        cell_size=10.0,
        timesteps=None,  # All timesteps
    )

    elapsed = time.time() - start
    print(f"Parsing took: {elapsed:.2f}s")
    print(f"N timesteps: {grid.n_timesteps}")
    print(f"Timestep values: {grid.timestep_values}")
    print(f"Total atoms (all timesteps): {grid.n_atoms * grid.n_timesteps:,}")

    # Test multi-timestep query
    xlo, xhi, ylo, yhi, zlo, zhi = grid.box_bounds
    region = (
        ((xlo + xhi) / 2 - 25, (xlo + xhi) / 2 + 25),
        ((ylo + yhi) / 2 - 25, (ylo + yhi) / 2 + 25),
        ((zlo + zhi) / 2 - 25, (zlo + zhi) / 2 + 25),
    )

    print(f"\nMulti-timestep query:")
    result = grid.query(region, timesteps=None)  # All timesteps
    print(f"  Total atoms across all timesteps: {len(result['coords']):,}")

    # Count per timestep
    for ts in grid.timestep_values:
        mask = result["_timestep"] == ts
        print(f"  Timestep {ts}: {mask.sum():,} atoms")

    return grid


if __name__ == "__main__":
    print("Testing atomkit with real lammpstrj file")
    print(f"File: {TRAJ_FILE}")
    print(f"File size: {TRAJ_FILE.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    # Run tests
    grid = test_parse_single_timestep()
    test_query(grid)
    test_save_load(grid)

    # This takes longer, run it last
    test_all_timesteps()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
