"""
Fast LAMMPS trajectory parser using mmap + polars.

Uses memory-mapped file access and polars' optimized CSV parser
for ~20x faster parsing compared to line-by-line Python parsing.
"""

from __future__ import annotations

import io
import logging
import mmap
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl
from tqdm import tqdm

if TYPE_CHECKING:
    from numpy.typing import NDArray

from atomkit._constants import TQDM_ATOM_THRESHOLD, POLARS_N_THREADS

# Coordinate column names by type (in preference order for "auto")
COORD_COLUMNS = {
    "unwrapped": ["xu", "yu", "zu"],
    "wrapped": ["x", "y", "z"],
    "scaled": ["xs", "ys", "zs"],
}
# Auto mode: try each type in order of preference
COORD_PREFERENCE = ["unwrapped", "wrapped", "scaled"]
CoordType = Literal["unwrapped", "wrapped", "scaled", "auto"]


def _get_coord_candidates(coord_type: CoordType) -> tuple[list[str], list[str], list[str]]:
    """Get (x_candidates, y_candidates, z_candidates) for a coordinate type."""
    if coord_type == "auto":
        # Stack all types in preference order
        x_cands = [COORD_COLUMNS[t][0] for t in COORD_PREFERENCE]
        y_cands = [COORD_COLUMNS[t][1] for t in COORD_PREFERENCE]
        z_cands = [COORD_COLUMNS[t][2] for t in COORD_PREFERENCE]
        return x_cands, y_cands, z_cands
    cols = COORD_COLUMNS[coord_type]
    return [cols[0]], [cols[1]], [cols[2]]

logger = logging.getLogger(__name__)


def parse_lammps(
    path: str | Path,
    timesteps: list[int] | slice | None = None,
    columns: dict[str, int] | None = None,
    coord_type: CoordType = "auto",
) -> tuple[
    list[NDArray[np.float32]],  # coords per timestep
    dict[str, list[NDArray]],   # fields per timestep
    list[int],                   # selected timestep values
]:
    """
    Parse a LAMMPS trajectory file.

    Uses mmap for zero-copy file access and polars for fast CSV parsing.

    Parameters
    ----------
    path : str or Path
        Path to the .lammpstrj file.
    timesteps : list[int] | slice, optional
        Specific timesteps to load. If None, loads all timesteps.
    columns : dict[str, int], optional
        Mapping of field names to column indices (0-based).
        If None, auto-detected from ITEM: ATOMS header.
        Coordinate columns (x/xu/xs, y/yu/ys, z/zu/zs) are mapped to x, y, z.
    coord_type : {"auto", "unwrapped", "wrapped", "scaled"}, default "auto"
        Which coordinate columns to use:
        - "unwrapped": xu, yu, zu (actual positions, can be outside box)
        - "wrapped": x, y, z (wrapped into simulation box)
        - "scaled": xs, ys, zs (fractional 0-1 coordinates)
        - "auto": prefer unwrapped > wrapped > scaled (first available)

    Returns
    -------
    coords_list : list of (n_atoms, 3) arrays
        Coordinates for each timestep.
    fields_dict : dict of field_name -> list of arrays
        Additional fields for each timestep.
    timestep_values : list of int
        The actual timestep values that were loaded.
    """
    path = Path(path)
    file_size = path.stat().st_size

    # Memory-map the file for fast access
    with open(path, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        # Phase 1: Scan for timestep structure (byte positions)
        # Format: (timestep_value, atoms_data_start, atoms_data_end, n_atoms)
        timestep_info: list[tuple[int, int, int, int]] = []
        header_cols: list[str] | None = None
        n_cols = 0

        pos = 0
        item_timestep = b"ITEM: TIMESTEP"
        item_atoms = b"ITEM: ATOMS"
        item_marker = b"ITEM:"

        while pos < file_size:
            # Find next ITEM: TIMESTEP
            ts_pos = mm.find(item_timestep, pos)
            if ts_pos == -1:
                break

            # Read timestep value (next line after ITEM: TIMESTEP)
            line_end = mm.find(b"\n", ts_pos)
            ts_line_start = line_end + 1
            ts_line_end = mm.find(b"\n", ts_line_start)
            ts_value = int(mm[ts_line_start:ts_line_end])

            # Find ITEM: NUMBER OF ATOMS
            num_atoms_pos = mm.find(b"ITEM: NUMBER OF ATOMS", ts_line_end)
            num_line_start = mm.find(b"\n", num_atoms_pos) + 1
            num_line_end = mm.find(b"\n", num_line_start)
            n_atoms = int(mm[num_line_start:num_line_end])

            # Find ITEM: ATOMS header
            atoms_header_pos = mm.find(item_atoms, num_line_end)
            atoms_header_end = mm.find(b"\n", atoms_header_pos)

            # Parse column names from header (first time only)
            if header_cols is None:
                header_line = mm[atoms_header_pos:atoms_header_end].decode("ascii")
                header_cols = header_line.split()[2:]  # Skip "ITEM:" and "ATOMS"
                n_cols = len(header_cols)

            # Atom data starts after the header line
            atoms_data_start = atoms_header_end + 1

            # Find end of atom data (next ITEM: or EOF)
            next_item = mm.find(item_marker, atoms_data_start)
            if next_item == -1:
                atoms_data_end = file_size
            else:
                # Back up to end of last atom line (before newline before ITEM:)
                atoms_data_end = next_item
                while atoms_data_end > atoms_data_start and mm[atoms_data_end - 1:atoms_data_end] in (b"\n", b"\r", b" "):
                    atoms_data_end -= 1

            timestep_info.append((ts_value, atoms_data_start, atoms_data_end, n_atoms))
            pos = atoms_data_end

        if not timestep_info:
            mm.close()
            raise ValueError(f"No timesteps found in {path}")

        # Select timesteps
        if timesteps is None:
            selected_indices = list(range(len(timestep_info)))
        elif isinstance(timesteps, slice):
            selected_indices = list(range(*timesteps.indices(len(timestep_info))))
        else:
            selected_indices = [i for i, t in enumerate(timestep_info) if t[0] in timesteps]

        if not selected_indices:
            mm.close()
            raise ValueError("No matching timesteps found")

        selected_timesteps = [timestep_info[i][0] for i in selected_indices]
        n_atoms = timestep_info[0][3]

        # Auto-detect columns from header if not provided
        if columns is None:
            if header_cols is None:
                mm.close()
                raise ValueError("Could not find ITEM: ATOMS header for column detection")

            columns = {}
            x_candidates, y_candidates, z_candidates = _get_coord_candidates(coord_type)
            all_coord_cols = {c for cols in COORD_COLUMNS.values() for c in cols} | {"id"}

            # Build lowercase -> index mapping
            header_lower = {col.lower(): i for i, col in enumerate(header_cols)}

            # Find coordinates in preference order (first candidate that exists wins)
            for candidate in x_candidates:
                if candidate in header_lower:
                    columns["x"] = header_lower[candidate]
                    break
            for candidate in y_candidates:
                if candidate in header_lower:
                    columns["y"] = header_lower[candidate]
                    break
            for candidate in z_candidates:
                if candidate in header_lower:
                    columns["z"] = header_lower[candidate]
                    break

            # Handle other columns
            for i, col_name in enumerate(header_cols):
                col_lower = col_name.lower()
                if col_lower == "id":
                    columns["atom_id"] = i
                elif col_lower not in all_coord_cols:
                    columns[col_name] = i

            if not all(k in columns for k in ("x", "y", "z")):
                mm.close()
                available = [c for c in header_cols if c.lower() in all_coord_cols]
                raise ValueError(
                    f"Could not find {coord_type} coordinates in header. "
                    f"Available coord columns: {available}. "
                    f"Try coord_type='auto' or specify the correct type."
                )

        # Identify column indices
        x_col = columns["x"]
        y_col = columns["y"]
        z_col = columns["z"]
        extra_cols = {k: v for k, v in columns.items() if k not in ("x", "y", "z")}

        # Phase 2: Parse atom data using polars (highly optimized CSV parser)
        coords_list = []
        fields_list: dict[str, list[NDArray]] = {name: [] for name in extra_cols}

        total_atoms = len(selected_indices) * n_atoms
        logger.info(
            "Parsing %d timesteps from %s (%d atoms each, %d total)",
            len(selected_indices), path.name, n_atoms, total_atoms
        )

        show_progress = total_atoms >= TQDM_ATOM_THRESHOLD
        pbar = tqdm(
            total=total_atoms,
            desc="Parsing LAMMPS",
            unit="Atoms",
            unit_scale=True,
            disable=not show_progress,
        )

        for t_in in selected_indices:
            ts_value, atoms_start, atoms_end, ts_n_atoms = timestep_info[t_in]

            # Extract atom block as bytes
            atom_bytes = mm[atoms_start:atoms_end]

            # Parse with polars - handles whitespace separation efficiently
            df = pl.read_csv(
                io.BytesIO(atom_bytes),
                separator=" ",
                has_header=False,
                new_columns=header_cols,
                ignore_errors=True,
                n_threads=POLARS_N_THREADS,
            )

            if len(df) != ts_n_atoms:
                mm.close()
                raise ValueError(
                    f"Timestep {ts_value}: expected {ts_n_atoms} atoms, got {len(df)}"
                )

            # Extract coordinates directly from polars
            coords = np.column_stack([
                df[header_cols[x_col]].to_numpy(),
                df[header_cols[y_col]].to_numpy(),
                df[header_cols[z_col]].to_numpy(),
            ]).astype(np.float32)
            coords_list.append(coords)

            # Extract extra fields
            for name, col_idx in extra_cols.items():
                col_data = df[header_cols[col_idx]].to_numpy()
                if name == "atom_id":
                    fields_list[name].append(col_data.astype(np.int32))
                else:
                    fields_list[name].append(col_data.astype(np.float32))

            pbar.update(ts_n_atoms)

        pbar.close()
        mm.close()

    return coords_list, fields_list, selected_timesteps
