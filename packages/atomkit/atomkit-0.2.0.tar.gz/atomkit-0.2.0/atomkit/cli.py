"""
Command-line interface for atomkit.

Usage:
    atomkit convert input.lammpstrj output.h5 [--cell-size 4.0] [--timesteps 0:100]
    atomkit info file.h5
"""

import argparse
import logging
import sys
from pathlib import Path

from atomkit._constants import DEFAULT_CELL_SIZE, DEFAULT_COMPRESSION_LEVEL


def parse_timesteps(value: str) -> list[int] | slice | None:
    """
    Parse timesteps argument.

    Formats:
        "all" or None -> None (all timesteps)
        "5" -> [5] (single timestep)
        "0,10,20" -> [0, 10, 20] (specific timesteps)
        "0:100" -> slice(0, 100) (range)
        "0:100:10" -> slice(0, 100, 10) (range with step)
    """
    if value is None or value.lower() == "all":
        return None

    if ":" in value:
        parts = value.split(":")
        if len(parts) == 2:
            return slice(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return slice(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            raise ValueError(f"Invalid timestep range: {value}")

    if "," in value:
        return [int(x.strip()) for x in value.split(",")]

    return [int(value)]


def cmd_convert(args):
    """Convert LAMMPS trajectory to HDF5 spatial grid."""
    from atomkit.spatial_grid import SpatialGrid

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".h5")

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    if args.cell_size <= 0:
        print(f"Error: Cell size must be positive, got {args.cell_size}", file=sys.stderr)
        return 1

    try:
        timesteps = parse_timesteps(args.timesteps)
    except ValueError as e:
        print(f"Error: Invalid timesteps format: {e}", file=sys.stderr)
        return 1

    print(f"Converting: {input_path}")
    print(f"  Cell size: {args.cell_size} Å")
    print(f"  Coordinates: {args.coords}")
    if timesteps is None:
        print("  Timesteps: all")
    elif isinstance(timesteps, slice):
        print(f"  Timesteps: {timesteps.start}:{timesteps.stop}" +
              (f":{timesteps.step}" if timesteps.step else ""))
    else:
        print(f"  Timesteps: {timesteps}")

    try:
        grid = SpatialGrid.from_lammps(
            input_path,
            cell_size=args.cell_size,
            timesteps=timesteps,
            coord_type=args.coords,
        )
    except ValueError as e:
        print(f"Error: Failed to parse trajectory: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Unexpected error during parsing: {e}", file=sys.stderr)
        return 1

    try:
        grid.save(output_path, compression=args.compression)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Failed to save HDF5 file: {e}", file=sys.stderr)
        return 1

    print(f"  Grid shape: {grid.grid_shape}")
    print(f"  Atoms per timestep: {grid.n_atoms:,}")
    print(f"  Timesteps: {grid.n_timesteps}")
    if grid.n_timesteps <= 10:
        print(f"  Timestep values: {list(grid.timestep_values)}")
    else:
        print(f"  Timestep values: {list(grid.timestep_values[:5])} ... {list(grid.timestep_values[-5:])}")
    print(f"  Fields: {grid.fields}")
    print(f"Output: {output_path}")

    return 0


def cmd_info(args):
    """Show information about an HDF5 spatial grid file."""
    from atomkit.spatial_grid import SpatialGrid

    path = Path(args.file)

    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        return 1

    with SpatialGrid.load(path) as grid:
        print(f"File: {path}")
        print(f"  Cell size: {grid.cell_size} Å")
        print(f"  Box bounds: {grid.box_bounds}")
        print(f"  Grid shape: {grid.grid_shape}")
        print(f"  Atoms per timestep: {grid.n_atoms:,}")
        print(f"  Timesteps: {grid.n_timesteps}")
        if grid.n_timesteps <= 10:
            print(f"  Timestep values: {list(grid.timestep_values)}")
        else:
            print(f"  Timestep values: {list(grid.timestep_values[:5])} ... {list(grid.timestep_values[-5:])}")
        print(f"  Total atoms: {grid.n_atoms * grid.n_timesteps:,}")
        print(f"  Fields: {grid.fields}")

        # Show file size
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  File size: {size_mb:.2f} MB")

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="atomkit",
        description="Atom-level analysis toolkit for MD trajectories",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # convert command
    p_convert = subparsers.add_parser(
        "convert",
        help="Convert LAMMPS trajectory to HDF5 spatial grid",
    )
    p_convert.add_argument("input", help="Input .lammpstrj file")
    p_convert.add_argument("output", nargs="?", help="Output .h5 file (default: same name)")
    p_convert.add_argument(
        "-c", "--cell-size",
        type=float,
        default=DEFAULT_CELL_SIZE,
        help=f"Grid cell size in Angstroms (default: {DEFAULT_CELL_SIZE})",
    )
    p_convert.add_argument(
        "-t", "--timesteps",
        type=str,
        default=None,
        help="Timesteps to extract: 'all', single (5), list (0,10,20), or range (0:100 or 0:100:10)",
    )
    p_convert.add_argument(
        "-z", "--compression",
        type=int,
        default=DEFAULT_COMPRESSION_LEVEL,
        help=f"Zstd compression level 1-22 (default: {DEFAULT_COMPRESSION_LEVEL})",
    )
    p_convert.add_argument(
        "--coords",
        type=str,
        choices=["auto", "unwrapped", "wrapped", "scaled"],
        default="auto",
        help="Coordinate type: unwrapped (xu,yu,zu), wrapped (x,y,z), scaled (xs,ys,zs), or auto (default: auto)",
    )
    p_convert.set_defaults(func=cmd_convert)

    # info command
    p_info = subparsers.add_parser(
        "info",
        help="Show information about an HDF5 spatial grid file",
    )
    p_info.add_argument("file", help="HDF5 file to inspect")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args(argv)

    # Configure logging based on verbosity
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(name)s: %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format="%(message)s",
        )

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
