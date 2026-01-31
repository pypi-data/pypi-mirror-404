"""
Spatial Grid Preprocessing Module for LAMMPS Trajectory Analysis.

Preprocesses large atom data into a 4D CSR-indexed spatial grid (time + space)
for fast region queries across timesteps. Stores as single HDF5 file with
zstd compression and lazy loading.

Usage:
    # Create from LAMMPS trajectory (all timesteps)
    grid = SpatialGrid.from_lammps('traj.lammpstrj', cell_size=4.0).save('data.h5')

    # Load and query (lazy mmap)
    with SpatialGrid.load('data.h5') as grid:
        # 4D region queries
        data = grid.query(Region(x=(0, 10), y=(0, 10), z=(0, 10), t=100))

        # Single timestep, all space
        data = grid.query(Region(t=100))

        # Spatial region, all timesteps
        data = grid.query(Region(x=(0, 10), y=(0, 10), z=(0, 10)))

        # Time range
        data = grid.query(Region(t=(0, 1000)))

Thread Safety
-------------
HDF5 has complex threading rules. By default, h5py is NOT thread-safe for
concurrent reads/writes to the same file. If you need multi-threaded access:
- Use separate SpatialGrid instances per thread (each opens its own file handle)
- Or serialize access with a lock
- h5py can be built with thread-safe HDF5, but this is not guaranteed

For parallel processing, prefer multiprocessing over threading.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import h5py
import numpy as np
from tqdm import tqdm

from atomkit.region import Region, RegionTuple, ensure_region, INF, NEG_INF

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Optional dependency: hdf5plugin (for zstd compression)
try:
    import hdf5plugin
    HDF5PLUGIN_AVAILABLE = True
except ImportError:
    HDF5PLUGIN_AVAILABLE = False
    warnings.warn(
        "hdf5plugin not available. HDF5 files will use gzip compression instead of zstd. "
        "Install hdf5plugin for better compression: pip install hdf5plugin",
        ImportWarning,
        stacklevel=2,
    )

# Optional dependency: numba (for fast kernels)
try:
    import numba
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    warnings.warn(
        "numba not available, using slower pure-numpy fallback for CSR grid building. "
        "Install numba for 10-100x faster grid construction: pip install numba",
        ImportWarning,
        stacklevel=2,
    )

from atomkit._constants import (
    TQDM_ATOM_THRESHOLD,
    DEFAULT_CELL_SIZE,
    BOX_PADDING_FACTOR,
)

# HDF5 group names
_CSR_GROUP = "_csr"
_FIELDS_GROUP = "fields"



# Type for cell_size: single float (uniform) or per-axis tuple
CellSize = float | tuple[float, float, float]


def _normalize_cell_size(cell_size: CellSize) -> tuple[float, float, float]:
    """Normalize cell_size to (cs_x, cs_y, cs_z) tuple."""
    if isinstance(cell_size, (int, float)):
        cs = float(cell_size)
        return (cs, cs, cs)
    if isinstance(cell_size, tuple) and len(cell_size) == 3:
        return (float(cell_size[0]), float(cell_size[1]), float(cell_size[2]))
    raise ValueError(
        f"cell_size must be a float or (cs_x, cs_y, cs_z) tuple, got {cell_size!r}"
    )


# -----------------------------------------------------------------------------
# CSR Grid Kernels (with numba acceleration if available)
# -----------------------------------------------------------------------------


def _compute_cell_indices_numpy(
    coords: NDArray[np.float32],
    box_lo: NDArray[np.float64],
    inv_cell_sizes: NDArray[np.float64],
    grid_shape: NDArray[np.int64],
) -> NDArray[np.int64]:
    """Compute flat cell index for each atom (pure numpy)."""
    nx, ny, nz = grid_shape

    # Vectorized cell coordinate computation
    cell_coords = ((coords - box_lo) * inv_cell_sizes).astype(np.int64)

    # Clamp to valid range
    cell_coords[:, 0] = np.clip(cell_coords[:, 0], 0, nx - 1)
    cell_coords[:, 1] = np.clip(cell_coords[:, 1], 0, ny - 1)
    cell_coords[:, 2] = np.clip(cell_coords[:, 2], 0, nz - 1)

    # Flat index (row-major: z varies fastest)
    return cell_coords[:, 0] * (ny * nz) + cell_coords[:, 1] * nz + cell_coords[:, 2]


def _count_per_cell_numpy(cell_indices: NDArray[np.int64], n_cells: int) -> NDArray[np.uint32]:
    """Count atoms per cell (pure numpy)."""
    return np.bincount(cell_indices, minlength=n_cells).astype(np.uint32)


def _compute_offsets_numpy(counts_flat: NDArray[np.uint32]) -> NDArray[np.uint64]:
    """Compute CSR offsets from flat counts (pure numpy)."""
    offsets = np.empty(len(counts_flat), dtype=np.uint64)
    offsets[0] = 0
    np.cumsum(counts_flat[:-1], out=offsets[1:])
    return offsets


def _build_sort_indices_numpy(
    cell_indices: NDArray[np.int64],
    offsets_flat: NDArray[np.uint64],
    counts_flat: NDArray[np.uint32],
) -> NDArray[np.uint32]:
    """Build sorted indices array where atoms are grouped by cell (pure numpy)."""
    # Use argsort to group by cell - stable sort preserves order within cells
    return np.argsort(cell_indices, kind='stable').astype(np.uint32)


# Numba-accelerated versions (if available)
if NUMBA_AVAILABLE:
    @numba.njit(parallel=True, cache=True)
    def _compute_cell_indices_numba(
        coords: NDArray[np.float32],
        box_lo: NDArray[np.float64],
        inv_cell_sizes: NDArray[np.float64],
        grid_shape: NDArray[np.int64],
    ) -> NDArray[np.int64]:
        """Compute flat cell index for each atom (numba accelerated)."""
        n_atoms = coords.shape[0]
        nx, ny, nz = grid_shape[0], grid_shape[1], grid_shape[2]
        cell_indices = np.empty(n_atoms, dtype=np.int64)

        for i in numba.prange(n_atoms):
            ix = int((coords[i, 0] - box_lo[0]) * inv_cell_sizes[0])
            iy = int((coords[i, 1] - box_lo[1]) * inv_cell_sizes[1])
            iz = int((coords[i, 2] - box_lo[2]) * inv_cell_sizes[2])

            ix = max(0, min(ix, nx - 1))
            iy = max(0, min(iy, ny - 1))
            iz = max(0, min(iz, nz - 1))

            cell_indices[i] = ix * (ny * nz) + iy * nz + iz

        return cell_indices

    @numba.njit(cache=True)
    def _count_per_cell_numba(cell_indices: NDArray[np.int64], n_cells: int) -> NDArray[np.uint32]:
        """Count atoms per cell (numba accelerated)."""
        counts = np.zeros(n_cells, dtype=np.uint32)
        for idx in cell_indices:
            counts[idx] += 1
        return counts

    @numba.njit(cache=True)
    def _compute_offsets_numba(counts_flat: NDArray[np.uint32]) -> NDArray[np.uint64]:
        """Compute CSR offsets from flat counts (numba accelerated)."""
        n_cells = counts_flat.shape[0]
        offsets = np.empty(n_cells, dtype=np.uint64)
        total = np.uint64(0)
        for i in range(n_cells):
            offsets[i] = total
            total += counts_flat[i]
        return offsets

    @numba.njit(parallel=True, cache=True)
    def _build_sort_indices_numba(
        cell_indices: NDArray[np.int64],
        offsets_flat: NDArray[np.uint64],
        counts_flat: NDArray[np.uint32],
    ) -> NDArray[np.uint32]:
        """Build sorted indices array where atoms are grouped by cell (numba accelerated)."""
        n_atoms = cell_indices.shape[0]
        n_cells = offsets_flat.shape[0]

        positions = np.empty(n_cells, dtype=np.uint64)
        for i in numba.prange(n_cells):
            positions[i] = offsets_flat[i]

        sort_indices = np.empty(n_atoms, dtype=np.uint32)
        for atom_idx in range(n_atoms):
            cell_idx = cell_indices[atom_idx]
            pos = positions[cell_idx]
            sort_indices[pos] = atom_idx
            positions[cell_idx] += 1

        return sort_indices

    # Use numba versions
    _compute_cell_indices = _compute_cell_indices_numba
    _count_per_cell = _count_per_cell_numba
    _compute_offsets = _compute_offsets_numba
    _build_sort_indices = _build_sort_indices_numba
else:
    # Fall back to numpy versions
    _compute_cell_indices = _compute_cell_indices_numpy
    _count_per_cell = _count_per_cell_numpy
    _compute_offsets = _compute_offsets_numpy
    _build_sort_indices = _build_sort_indices_numpy


def _merge_slices(slices: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge adjacent/overlapping (start, end) slices into contiguous ranges."""
    if not slices:
        return []
    slices = sorted(slices)
    merged = []
    start, end = slices[0]
    for s, e in slices[1:]:
        if s <= end:
            end = max(end, e)
        else:
            merged.append((start, end))
            start, end = s, e
    merged.append((start, end))
    return merged


def _normalize_coords(
    coords: "NDArray[np.floating] | list[NDArray[np.floating]]",
) -> tuple[list["NDArray[np.float32]"], int, int]:
    """Normalize coords to list of float32 arrays. Returns (coords_list, n_timesteps, n_atoms)."""
    if isinstance(coords, list):
        coords_list = [np.asarray(c, dtype=np.float32) for c in coords]
    else:
        coords = np.asarray(coords, dtype=np.float32)
        coords_list = [coords] if coords.ndim == 2 else [coords[t] for t in range(coords.shape[0])]
    return coords_list, len(coords_list), coords_list[0].shape[0]


def _normalize_fields(
    fields: dict[str, "NDArray | list[NDArray]"],
    n_timesteps: int,
    n_atoms: int,
) -> dict[str, list["NDArray"]]:
    """Normalize fields to dict of list of arrays, with validation."""
    fields_list: dict[str, list[NDArray]] = {}
    for name, data in fields.items():
        if isinstance(data, list):
            fields_list[name] = [np.asarray(d) for d in data]
        else:
            data = np.asarray(data)
            if data.ndim == 1 or (data.ndim == 2 and data.shape[0] == n_atoms):
                fields_list[name] = [data] * n_timesteps
            else:
                fields_list[name] = [data[t] for t in range(data.shape[0])]

    # Validate
    for name, data_list in fields_list.items():
        if len(data_list) != n_timesteps:
            raise ValueError(f"Field '{name}' has {len(data_list)} timesteps, expected {n_timesteps}")
        for t, arr in enumerate(data_list):
            if arr.shape[0] != n_atoms:
                raise ValueError(f"Field '{name}' at timestep {t} has {arr.shape[0]} atoms, expected {n_atoms}")
    return fields_list


def _compute_bounds(
    coords_list: list["NDArray[np.float32]"],
    cell_sizes: tuple[float, float, float],
) -> tuple[float, float, float, float, float, float]:
    """Compute box bounds from coordinate data with padding."""
    cs_x, cs_y, cs_z = cell_sizes
    all_coords = np.concatenate(coords_list, axis=0)
    pad_x, pad_y, pad_z = cs_x * BOX_PADDING_FACTOR, cs_y * BOX_PADDING_FACTOR, cs_z * BOX_PADDING_FACTOR
    return (
        float(all_coords[:, 0].min() - pad_x), float(all_coords[:, 0].max() + pad_x),
        float(all_coords[:, 1].min() - pad_y), float(all_coords[:, 1].max() + pad_y),
        float(all_coords[:, 2].min() - pad_z), float(all_coords[:, 2].max() + pad_z),
    )


# -----------------------------------------------------------------------------
# SpatialGrid Class
# -----------------------------------------------------------------------------


@dataclass
class SpatialGrid:
    """
    4D CSR-indexed spatial grid for fast region queries on atom trajectory data.

    Supports queries across both space and time dimensions.

    Attributes
    ----------
    cell_size : tuple[float, float, float]
        Size of each grid cell per axis (cs_x, cs_y, cs_z) in Angstroms.
    box_bounds : tuple[float, ...]
        Box boundaries (xlo, xhi, ylo, yhi, zlo, zhi).
    grid_shape : tuple[int, int, int]
        Number of cells in each spatial dimension (nx, ny, nz).
    n_atoms : int
        Number of atoms per timestep.
    n_timesteps : int
        Number of timesteps in the trajectory.
    timestep_values : tuple[int, ...]
        Actual timestep values from the trajectory file.
    """

    cell_size: tuple[float, float, float]
    box_bounds: tuple[float, ...]
    grid_shape: tuple[int, int, int]
    n_atoms: int
    n_timesteps: int = 1
    timestep_values: tuple[int, ...] = (0,)
    _file: h5py.File | None = field(default=None, repr=False)
    _offsets: NDArray[np.uint64] | None = field(default=None, repr=False)
    _counts: NDArray[np.uint32] | None = field(default=None, repr=False)
    _fields_cache: dict[str, NDArray] = field(default_factory=dict, repr=False)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def offsets(self) -> NDArray[np.uint64]:
        """CSR offsets array (n_timesteps, nx, ny, nz), lazy loaded from HDF5."""
        if self._offsets is None:
            if self._file is not None:
                self._offsets = self._file[f"{_CSR_GROUP}/offsets"][:]
            else:
                raise ValueError("No offsets available (grid not loaded or built)")
        return self._offsets

    @property
    def counts(self) -> NDArray[np.uint32]:
        """Atom counts per cell (n_timesteps, nx, ny, nz), lazy loaded from HDF5."""
        if self._counts is None:
            if self._file is not None:
                self._counts = self._file[f"{_CSR_GROUP}/counts"][:]
            else:
                raise ValueError("No counts available (grid not loaded or built)")
        return self._counts

    @property
    def fields(self) -> list[str]:
        """List of available field names."""
        if self._file is not None:
            return list(self._file[_FIELDS_GROUP].keys())
        return list(self._fields_cache.keys())

    # -------------------------------------------------------------------------
    # Field Access
    # -------------------------------------------------------------------------

    def __getitem__(self, key: str) -> NDArray | h5py.Dataset:
        """
        Access a field by name.

        Returns h5py.Dataset (lazy) if loaded from file, or numpy array if in memory.
        """
        if self._file is not None:
            return self._file[f"{_FIELDS_GROUP}/{key}"]
        if key in self._fields_cache:
            return self._fields_cache[key]
        raise KeyError(f"Field '{key}' not found")

    def __contains__(self, key: str) -> bool:
        """Check if a field exists."""
        if self._file is not None:
            return key in self._file[_FIELDS_GROUP]
        return key in self._fields_cache

    def __len__(self) -> int:
        """Return number of timesteps."""
        return self.n_timesteps

    def __repr__(self) -> str:
        file_info = f", file='{self._file.filename}'" if self._file else ""
        return (
            f"SpatialGrid(shape={self.grid_shape}, cell_size={self.cell_size}, "
            f"atoms={self.n_atoms}, timesteps={self.n_timesteps}{file_info})"
        )

    # -------------------------------------------------------------------------
    # Timestep Utilities
    # -------------------------------------------------------------------------

    def _timesteps_from_region(
        self, region: Region
    ) -> tuple[list[int], list[int]]:
        """
        Get timestep indices and values that fall within the region's time bounds.

        The region's t bounds are interpreted as timestep VALUES (not indices).
        - t=(100, 500) → all timesteps with values in [100, 500]
        - t=100 (single value) → timestep with value 100
        - t=(-inf, inf) → all timesteps

        Returns
        -------
        indices : list[int]
            Indices into the timestep dimension (0-based).
        values : list[int]
            Actual timestep values.
        """
        t_min, t_max = region.t

        # Handle unbounded (all timesteps)
        if t_min == NEG_INF and t_max == INF:
            return list(range(self.n_timesteps)), list(self.timestep_values)

        # Find timesteps whose values fall within [t_min, t_max]
        indices = []
        values = []
        for i, t_val in enumerate(self.timestep_values):
            if t_min <= t_val <= t_max:
                indices.append(i)
                values.append(t_val)

        return indices, values

    # -------------------------------------------------------------------------
    # Region Queries
    # -------------------------------------------------------------------------

    def _cells_in_region(
        self, region: Region
    ) -> tuple[list[int], list[int]]:
        """
        Get cell indices for cells that overlap with the region.

        Separates interior cells (fully contained, no filtering needed) from
        boundary cells (partially overlapping, need coordinate filtering).

        Handles unbounded regions by clamping to grid bounds.

        Parameters
        ----------
        region : Region
            Query region with x, y, z spatial bounds.

        Returns
        -------
        interior_cells : list[int]
            Flat indices of cells fully contained in region.
        boundary_cells : list[int]
            Flat indices of cells that straddle the region boundary.
        """
        xlo, xhi, ylo, yhi, zlo, zhi = self.box_bounds
        nx, ny, nz = self.grid_shape
        cs_x, cs_y, cs_z = self.cell_size

        # Clamp region bounds to grid bounds (handles -inf/inf)
        xmin = max(region.x[0], xlo)
        xmax = min(region.x[1], xhi)
        ymin = max(region.y[0], ylo)
        ymax = min(region.y[1], yhi)
        zmin = max(region.z[0], zlo)
        zmax = min(region.z[1], zhi)

        # Check for non-overlapping region
        if xmin > xmax or ymin > ymax or zmin > zmax:
            return [], []

        # Cell index bounds (inclusive)
        ix_min = max(0, int((xmin - xlo) / cs_x))
        ix_max = min(nx - 1, int((xmax - xlo) / cs_x))
        iy_min = max(0, int((ymin - ylo) / cs_y))
        iy_max = min(ny - 1, int((ymax - ylo) / cs_y))
        iz_min = max(0, int((zmin - zlo) / cs_z))
        iz_max = min(nz - 1, int((zmax - zlo) / cs_z))

        # Check if region is unbounded (covers entire grid on this axis)
        x_unbounded = region.x[0] == NEG_INF and region.x[1] == INF
        y_unbounded = region.y[0] == NEG_INF and region.y[1] == INF
        z_unbounded = region.z[0] == NEG_INF and region.z[1] == INF

        # Interior cell bounds: cells where entire cell is within region
        # Cell [i] spans [xlo + i*cs, xlo + (i+1)*cs]
        # Interior if: xlo + i*cs >= xmin AND xlo + (i+1)*cs <= xmax
        # For unbounded axis, all cells are interior on that axis
        if x_unbounded:
            ix_int_min, ix_int_max = 0, nx - 1
        else:
            ix_int_min = max(ix_min, int(np.ceil((xmin - xlo) / cs_x)))
            ix_int_max = min(ix_max, int(np.floor((xmax - xlo) / cs_x)) - 1)

        if y_unbounded:
            iy_int_min, iy_int_max = 0, ny - 1
        else:
            iy_int_min = max(iy_min, int(np.ceil((ymin - ylo) / cs_y)))
            iy_int_max = min(iy_max, int(np.floor((ymax - ylo) / cs_y)) - 1)

        if z_unbounded:
            iz_int_min, iz_int_max = 0, nz - 1
        else:
            iz_int_min = max(iz_min, int(np.ceil((zmin - zlo) / cs_z)))
            iz_int_max = min(iz_max, int(np.floor((zmax - zlo) / cs_z)) - 1)

        interior_cells = []
        boundary_cells = []

        for ix in range(ix_min, ix_max + 1):
            for iy in range(iy_min, iy_max + 1):
                for iz in range(iz_min, iz_max + 1):
                    cell_idx = ix * (ny * nz) + iy * nz + iz
                    is_interior = (
                        ix_int_min <= ix <= ix_int_max
                        and iy_int_min <= iy <= iy_int_max
                        and iz_int_min <= iz <= iz_int_max
                    )
                    if is_interior:
                        interior_cells.append(cell_idx)
                    else:
                        boundary_cells.append(cell_idx)

        return interior_cells, boundary_cells

    def _get_slices_for_timestep(
        self, t_idx: int, interior_cells: list[int], boundary_cells: list[int]
    ) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        """
        Get contiguous slices for atoms within cells at a specific timestep.

        Returns merged, sorted slices for efficient HDF5 reads (no fancy indexing).

        Parameters
        ----------
        t_idx : int
            Timestep index (0-based).
        interior_cells : list[int]
            Cell indices fully contained in region.
        boundary_cells : list[int]
            Cell indices straddling region boundary.

        Returns
        -------
        interior_slices : list of (start, end) tuples
            Contiguous slices for atoms in interior cells (global indices).
        boundary_slices : list of (start, end) tuples
            Contiguous slices for atoms in boundary cells (global indices).
        """
        # Load only this timestep's offsets/counts (lazy per-timestep)
        if self._file is not None:
            offsets_t = self._file[f"{_CSR_GROUP}/offsets"][t_idx].ravel()
            counts_t = self._file[f"{_CSR_GROUP}/counts"][t_idx].ravel()
        else:
            offsets_t = self._offsets[t_idx].ravel()
            counts_t = self._counts[t_idx].ravel()

        t_offset = t_idx * self.n_atoms

        def cell_slices(cell_list: list[int]) -> list[tuple[int, int]]:
            slices = []
            for cell_idx in cell_list:
                start = int(offsets_t[cell_idx])
                count = int(counts_t[cell_idx])
                if count > 0:
                    slices.append((start + t_offset, start + count + t_offset))
            return _merge_slices(slices)

        return cell_slices(interior_cells), cell_slices(boundary_cells)

    @staticmethod
    def _filter_by_bounds(
        region: Region,
        coords: NDArray[np.float32],
    ) -> NDArray[np.bool_]:
        """Create boolean mask for atoms within region's spatial bounds."""
        x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
        mask = np.ones(len(coords), dtype=np.bool_)

        # Only filter bounded axes
        if region.x[0] != NEG_INF:
            mask &= x >= region.x[0]
        if region.x[1] != INF:
            mask &= x <= region.x[1]
        if region.y[0] != NEG_INF:
            mask &= y >= region.y[0]
        if region.y[1] != INF:
            mask &= y <= region.y[1]
        if region.z[0] != NEG_INF:
            mask &= z >= region.z[0]
        if region.z[1] != INF:
            mask &= z <= region.z[1]

        return mask

    def _read_slices(self, name: str, slices: list[tuple[int, int]]) -> NDArray:
        """
        Read field data using contiguous slice reads (fast for HDF5).

        This avoids fancy indexing which is slow for h5py.Dataset.
        """
        if not slices:
            return np.array([], dtype=self[name].dtype)

        data = self[name]
        chunks = []

        for start, end in slices:
            chunk = data[start:end]
            if isinstance(chunk, np.ndarray):
                chunks.append(chunk)
            else:
                # h5py returns array-like, ensure numpy
                chunks.append(np.asarray(chunk))

        if len(chunks) == 1:
            return chunks[0]
        return np.concatenate(chunks)

    def query(
        self,
        region: Region | RegionTuple | None = None,
        fields: list[str] | None = None,
        cell_level: bool = False,
    ) -> dict[str, NDArray]:
        """
        Query atoms within a 4D region (space + time).

        Parameters
        ----------
        region : Region, optional
            4D query region with x, y, z spatial bounds and t time bounds.
            If None, returns all atoms across all timesteps.

            Bounds can be specified as:
            - (min, max) tuple: explicit range
            - Single value: slice at that point (e.g., t=100 for single timestep)
            - None/omitted: unbounded (all values)

            Time bounds are interpreted as timestep VALUES (not indices).

        fields : list[str], optional
            Fields to return. If None, returns all fields.
        cell_level : bool, default False
            Controls the granularity of the query.

            - False (default): Filter boundary cell atoms to exact region bounds.
              Returns only atoms whose coordinates fall within the region.
            - True: Return all atoms in any cell that overlaps the region.
              This is faster but may include atoms OUTSIDE the region bounds
              (up to cell_size distance beyond each boundary).

            Interior cells (fully contained in region) are always included
            without filtering regardless of this setting.

        Returns
        -------
        dict[str, ndarray]
            Dictionary mapping field names to arrays for atoms in region.
            Includes '_timestep' field indicating which timestep each atom belongs to.
            All arrays are read-only views.

        Examples
        --------
        >>> grid.query(Region(x=(0, 10), y=(0, 10), z=(0, 10)))  # All timesteps
        >>> grid.query(Region(t=100))  # Single timestep, all space
        >>> grid.query(Region(x=(0, 10), t=(0, 1000)))  # 4D query
        >>> grid.query()  # Everything
        """
        # Handle None or legacy tuple input
        if region is None:
            region = Region()  # Everything
        else:
            region = ensure_region(region)

        t_indices, t_values = self._timesteps_from_region(region)

        if fields is None:
            fields = self.fields

        # Classify cells once (same for all timesteps since grid is fixed)
        interior_cells, boundary_cells = self._cells_in_region(region)

        # Collect slices from all timesteps (not indices - slices are fast for HDF5)
        all_interior_slices: list[tuple[int, int]] = []
        all_boundary_slices: list[tuple[int, int]] = []
        interior_ts_counts: list[tuple[int, int]] = []  # (timestep_value, atom_count)
        boundary_ts_counts: list[tuple[int, int]] = []

        for t_idx, t_val in zip(t_indices, t_values):
            int_slices, bnd_slices = self._get_slices_for_timestep(
                t_idx, interior_cells, boundary_cells
            )
            if int_slices:
                count = sum(e - s for s, e in int_slices)
                all_interior_slices.extend(int_slices)
                interior_ts_counts.append((t_val, count))
            if bnd_slices:
                count = sum(e - s for s, e in bnd_slices)
                all_boundary_slices.extend(bnd_slices)
                boundary_ts_counts.append((t_val, count))

        # Handle empty result
        if not all_interior_slices and not all_boundary_slices:
            result = {name: np.array([], dtype=self[name].dtype) for name in fields}
            result["_timestep"] = np.array([], dtype=np.int64)
            return result

        # Build timestep arrays from counts
        def build_timestep_array(ts_counts: list[tuple[int, int]]) -> NDArray[np.int64]:
            if not ts_counts:
                return np.array([], dtype=np.int64)
            parts = [np.full(count, ts_val, dtype=np.int64) for ts_val, count in ts_counts]
            return np.concatenate(parts) if len(parts) > 1 else parts[0]

        # Read interior data using slice reads (fast!)
        interior_data: dict[str, NDArray] = {}
        if all_interior_slices:
            for name in fields:
                interior_data[name] = self._read_slices(name, all_interior_slices)
            interior_data["_timestep"] = build_timestep_array(interior_ts_counts)

        # Read boundary data
        boundary_data: dict[str, NDArray] = {}
        if all_boundary_slices:
            for name in fields:
                boundary_data[name] = self._read_slices(name, all_boundary_slices)
            boundary_data["_timestep"] = build_timestep_array(boundary_ts_counts)

            if not cell_level and "coords" in boundary_data:
                # Filter boundary atoms to exact region
                mask = self._filter_by_bounds(region, boundary_data["coords"])
                for name in list(fields) + ["_timestep"]:
                    boundary_data[name] = boundary_data[name][mask]

        # Combine interior and boundary results
        result = {}
        for name in list(fields) + ["_timestep"]:
            parts = []
            if name in interior_data and len(interior_data[name]) > 0:
                parts.append(interior_data[name])
            if name in boundary_data and len(boundary_data[name]) > 0:
                parts.append(boundary_data[name])

            if parts:
                combined = np.concatenate(parts) if len(parts) > 1 else parts[0].copy()
                combined.flags.writeable = False
                result[name] = combined
            else:
                dtype = self[name].dtype if name in fields else np.int64
                result[name] = np.array([], dtype=dtype)

        return result

    def count(
        self,
        region: Region | RegionTuple | None = None,
    ) -> int | NDArray[np.int64]:
        """
        Count atoms in a region (fast, reads only cell counts, no field data).

        Note: This is an APPROXIMATE count based on overlapping cells.
        For boundary cells (cells that partially overlap the region), all
        atoms in the cell are counted even if they fall outside the region.
        The overcount can be up to cell_size distance beyond each boundary.

        For exact count, use `len(grid.query(region)["coords"])`.

        Parameters
        ----------
        region : Region, optional
            4D query region. If None, counts all atoms.

        Returns
        -------
        int or ndarray
            If single timestep: number of atoms in region.
            If multiple timesteps: array of counts per timestep.
        """
        if region is None:
            region = Region()
        else:
            region = ensure_region(region)

        t_indices, _ = self._timesteps_from_region(region)
        single = len(t_indices) == 1

        interior_cells, boundary_cells = self._cells_in_region(region)
        all_cells = interior_cells + boundary_cells

        result = []
        for t_idx in t_indices:
            # Load only this timestep's counts (lazy per-timestep)
            if self._file is not None:
                counts_t = self._file[f"{_CSR_GROUP}/counts"][t_idx].ravel()
            else:
                counts_t = self._counts[t_idx].ravel()

            total = sum(int(counts_t[cell_idx]) for cell_idx in all_cells)
            result.append(total)

        if single:
            return result[0]
        arr = np.array(result, dtype=np.int64)
        arr.flags.writeable = False
        return arr

    # -------------------------------------------------------------------------
    # Fast Slice & Projection Operations
    # -------------------------------------------------------------------------

    def _resolve_timestep(self, timestep: int | None) -> tuple[int, int]:
        """Resolve timestep to (t_idx, t_val). Raises if ambiguous."""
        if timestep is None:
            if self.n_timesteps == 1:
                return 0, self.timestep_values[0]
            raise ValueError("timestep required for multi-timestep grids")
        if timestep not in self.timestep_values:
            raise ValueError(f"timestep {timestep} not found")
        return self.timestep_values.index(timestep), timestep

    def _position_to_index(self, axis: Literal["x", "y", "z"], position: float) -> int:
        """Convert real position to cell index."""
        axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
        lo = self.box_bounds[axis_idx * 2]
        hi = self.box_bounds[axis_idx * 2 + 1]
        cs = self.cell_size[axis_idx]
        n = self.grid_shape[axis_idx]

        if position < lo or position > hi:
            raise ValueError(f"Position {position} outside bounds [{lo}, {hi}]")

        idx = int((position - lo) / cs)
        return min(idx, n - 1)  # clamp to valid range

    def _cell_field_3d(
        self,
        field: str,
        t_idx: int,
        aggregator: Literal["sum", "mean", "max", "min"] = "mean",
    ) -> NDArray[np.float64]:
        """
        Aggregate per-atom field to cell level. Returns (nx, ny, nz) array.

        Uses vectorized cumsum for sum, loop for others (numba-acceleratable).
        """
        nx, ny, nz = self.grid_shape
        n_cells = nx * ny * nz

        # Get data for this timestep
        t_start = t_idx * self.n_atoms
        t_end = (t_idx + 1) * self.n_atoms

        field_data = self[field][t_start:t_end]
        if not isinstance(field_data, np.ndarray):
            field_data = np.asarray(field_data)
        field_data = field_data.astype(np.float64, copy=False)

        counts_flat = self.counts[t_idx].ravel().astype(np.int64)
        offsets_flat = self.offsets[t_idx].ravel().astype(np.int64)

        result = np.zeros(n_cells, dtype=np.float64)

        if aggregator == "sum":
            # Fast path: cumsum trick
            cumsum = np.zeros(len(field_data) + 1, dtype=np.float64)
            cumsum[1:] = np.cumsum(field_data)
            end_indices = offsets_flat + counts_flat
            result = cumsum[end_indices] - cumsum[offsets_flat]

        elif aggregator == "mean":
            # Sum then divide by count
            cumsum = np.zeros(len(field_data) + 1, dtype=np.float64)
            cumsum[1:] = np.cumsum(field_data)
            end_indices = offsets_flat + counts_flat
            sums = cumsum[end_indices] - cumsum[offsets_flat]
            mask = counts_flat > 0
            result[mask] = sums[mask] / counts_flat[mask]

        else:
            # max/min - need loop (could be numba-ified)
            agg_func = {"max": np.max, "min": np.min}[aggregator]
            for i in range(n_cells):
                if counts_flat[i] > 0:
                    start = offsets_flat[i]
                    end = start + counts_flat[i]
                    result[i] = agg_func(field_data[start:end])

        return result.reshape(nx, ny, nz)

    def slice_2d(
        self,
        axis: Literal["x", "y", "z"],
        position: float,
        field: str = "counts",
        timestep: int | None = None,
        cell_aggregator: Literal["sum", "mean", "max", "min"] = "mean",
    ) -> tuple[NDArray[np.float64], dict]:
        """
        Extract a 2D slice from the grid at a given position.

        Fast operation: O(ny*nz) for counts, O(n_atoms) for fields (first time).

        Parameters
        ----------
        axis : 'x', 'y', or 'z'
            Axis perpendicular to the slice plane.
        position : float
            Position along the axis (in real coordinates).
        field : str, default 'counts'
            Field to slice. 'counts' uses pre-computed cell counts (fastest).
        timestep : int, optional
            Timestep value. Required for multi-timestep grids.
        cell_aggregator : str, default 'mean'
            For non-counts fields, how to aggregate atoms within cells.

        Returns
        -------
        data : ndarray, shape depends on axis
            2D array of values. Axes are (axis1, axis2) where axis1, axis2
            are the two axes perpendicular to the slice axis.
        info : dict
            Metadata: 'extent' (xmin, xmax, ymin, ymax), 'xlabel', 'ylabel',
            'axis', 'position', 'timestep'.
        """
        t_idx, t_val = self._resolve_timestep(timestep)
        cell_idx = self._position_to_index(axis, position)

        # Get 3D data
        if field == "counts":
            data_3d = self.counts[t_idx].astype(np.float64)
        else:
            data_3d = self._cell_field_3d(field, t_idx, cell_aggregator)

        # Slice
        axis_map = {"x": 0, "y": 1, "z": 2}
        ax_idx = axis_map[axis]

        if ax_idx == 0:  # x slice -> (ny, nz)
            data_2d = data_3d[cell_idx, :, :]
            extent = (self.box_bounds[2], self.box_bounds[3],  # y
                      self.box_bounds[4], self.box_bounds[5])  # z
            xlabel, ylabel = "y", "z"
        elif ax_idx == 1:  # y slice -> (nx, nz)
            data_2d = data_3d[:, cell_idx, :]
            extent = (self.box_bounds[0], self.box_bounds[1],  # x
                      self.box_bounds[4], self.box_bounds[5])  # z
            xlabel, ylabel = "x", "z"
        else:  # z slice -> (nx, ny)
            data_2d = data_3d[:, :, cell_idx]
            extent = (self.box_bounds[0], self.box_bounds[1],  # x
                      self.box_bounds[2], self.box_bounds[3])  # y
            xlabel, ylabel = "x", "y"

        info = {
            "extent": extent,
            "xlabel": xlabel,
            "ylabel": ylabel,
            "axis": axis,
            "position": position,
            "cell_index": cell_idx,
            "timestep": t_val,
            "field": field,
        }

        return data_2d.T, info  # transpose for imshow (row=y, col=x)

    def project_2d(
        self,
        axis: Literal["x", "y", "z"],
        field: str = "counts",
        timestep: int | None = None,
        cell_aggregator: Literal["sum", "mean", "max", "min"] = "mean",
        projection: Literal["sum", "mean", "max", "min"] = "sum",
    ) -> tuple[NDArray[np.float64], dict]:
        """
        Project grid data along an axis (reduce 3D -> 2D).

        Parameters
        ----------
        axis : 'x', 'y', or 'z'
            Axis to project along (reduce out).
        field : str, default 'counts'
            Field to project.
        timestep : int, optional
            Timestep value.
        cell_aggregator : str, default 'mean'
            For non-counts fields, how to aggregate atoms within cells.
        projection : str, default 'sum'
            How to aggregate cells along the projection axis.

        Returns
        -------
        data : ndarray
            2D projected data.
        info : dict
            Metadata about the projection.
        """
        t_idx, t_val = self._resolve_timestep(timestep)

        # Get 3D data
        if field == "counts":
            data_3d = self.counts[t_idx].astype(np.float64)
        else:
            data_3d = self._cell_field_3d(field, t_idx, cell_aggregator)

        # Project
        axis_map = {"x": 0, "y": 1, "z": 2}
        ax_idx = axis_map[axis]
        proj_func = {"sum": np.sum, "mean": np.mean, "max": np.max, "min": np.min}[projection]

        data_2d = proj_func(data_3d, axis=ax_idx)

        if ax_idx == 0:  # project x -> (ny, nz)
            extent = (self.box_bounds[2], self.box_bounds[3],
                      self.box_bounds[4], self.box_bounds[5])
            xlabel, ylabel = "y", "z"
        elif ax_idx == 1:  # project y -> (nx, nz)
            extent = (self.box_bounds[0], self.box_bounds[1],
                      self.box_bounds[4], self.box_bounds[5])
            xlabel, ylabel = "x", "z"
        else:  # project z -> (nx, ny)
            extent = (self.box_bounds[0], self.box_bounds[1],
                      self.box_bounds[2], self.box_bounds[3])
            xlabel, ylabel = "x", "y"

        info = {
            "extent": extent,
            "xlabel": xlabel,
            "ylabel": ylabel,
            "axis": axis,
            "projection": projection,
            "timestep": t_val,
            "field": field,
        }

        return data_2d.T, info

    # -------------------------------------------------------------------------
    # Constructors
    # -------------------------------------------------------------------------

    @classmethod
    def from_arrays(
        cls,
        coords: NDArray[np.floating] | list[NDArray[np.floating]],
        box_bounds: tuple[float, float, float, float, float, float] | None = None,
        cell_size: CellSize = DEFAULT_CELL_SIZE,
        timestep_values: list[int] | None = None,
        **fields: NDArray | list[NDArray],
    ) -> SpatialGrid:
        """
        Create a SpatialGrid from coordinate and field arrays.

        Parameters
        ----------
        coords : (n_timesteps, n_atoms, 3) array or list of (n_atoms, 3) arrays
            Atom coordinates for each timestep.
        box_bounds : tuple, optional
            Box boundaries (xlo, xhi, ylo, yhi, zlo, zhi).
            If None, computed from actual coordinate ranges with padding.
        cell_size : float or tuple[float, float, float], default 4.0
            Grid cell size in Angstroms. Either a single value (uniform) or
            per-axis sizes (cs_x, cs_y, cs_z).
        timestep_values : list[int], optional
            Actual timestep values. If None, uses 0, 1, 2, ...
        **fields : ndarray or list of ndarray
            Additional fields (e.g., stress=stress_array, atom_id=id_array).
            Should have shape (n_timesteps, n_atoms, ...) or be list of arrays.

        Returns
        -------
        SpatialGrid
            In-memory grid ready for queries or saving.

        Raises
        ------
        ValueError
            If cell_size is not positive.
        """
        # Validate and normalize inputs
        cell_sizes = _normalize_cell_size(cell_size)
        cs_x, cs_y, cs_z = cell_sizes
        if cs_x <= 0 or cs_y <= 0 or cs_z <= 0:
            raise ValueError(f"cell_size must be positive, got {cell_size}")

        coords_list, n_timesteps, n_atoms = _normalize_coords(coords)
        timestep_values = timestep_values or list(range(n_timesteps))
        fields_list = _normalize_fields(fields, n_timesteps, n_atoms)

        # Compute bounds from data if not provided
        if box_bounds is None:
            box_bounds = _compute_bounds(coords_list, cell_sizes)
        xlo, xhi, ylo, yhi, zlo, zhi = box_bounds
        box_lo = np.array([xlo, ylo, zlo], dtype=np.float64)

        # Compute grid shape (per-axis cell sizes)
        nx = max(1, int(np.ceil((xhi - xlo) / cs_x)))
        ny = max(1, int(np.ceil((yhi - ylo) / cs_y)))
        nz = max(1, int(np.ceil((zhi - zlo) / cs_z)))
        grid_shape = (nx, ny, nz)
        n_cells = nx * ny * nz

        # Build CSR for each timestep
        all_offsets = []
        all_counts = []
        all_sorted_coords = []
        all_sorted_source_idx = []
        all_sorted_fields: dict[str, list[NDArray]] = {name: [] for name in fields_list}

        total_atoms = n_timesteps * n_atoms
        logger.info("Building spatial grid for %d timesteps, %d atoms each (%d total)", n_timesteps, n_atoms, total_atoms)

        show_progress = total_atoms >= TQDM_ATOM_THRESHOLD
        pbar = tqdm(
            total=total_atoms,
            desc="Building CSR grid",
            unit="Atoms",
            unit_scale=True,
            disable=not show_progress,
        )

        # Pre-compute inverse cell sizes for numba kernel
        inv_cell_sizes = np.array([1.0 / cs_x, 1.0 / cs_y, 1.0 / cs_z], dtype=np.float64)
        grid_shape_arr = np.array(grid_shape, dtype=np.int64)

        for t in range(n_timesteps):
            coords_t = coords_list[t]

            # Compute cell indices for each atom
            cell_indices = _compute_cell_indices(
                coords_t,
                box_lo,
                inv_cell_sizes,
                grid_shape_arr,
            )

            # Build CSR structure
            counts_flat = _count_per_cell(cell_indices, n_cells)
            offsets_flat = _compute_offsets(counts_flat)
            sort_indices = _build_sort_indices(cell_indices, offsets_flat, counts_flat)

            # Reshape to 3D
            all_offsets.append(offsets_flat.reshape(grid_shape))
            all_counts.append(counts_flat.reshape(grid_shape))

            # Sort data
            all_sorted_source_idx.append(np.arange(n_atoms, dtype=np.uint32)[sort_indices])
            all_sorted_coords.append(coords_t[sort_indices])

            for name, data_list in fields_list.items():
                all_sorted_fields[name].append(data_list[t][sort_indices])

            pbar.update(n_atoms)

        pbar.close()

        # Stack into 4D arrays
        offsets = np.stack(all_offsets, axis=0)
        counts = np.stack(all_counts, axis=0)

        # Concatenate field data: [t0_atoms, t1_atoms, ...]
        fields_cache = {
            "_source_idx": np.concatenate(all_sorted_source_idx),
            "coords": np.concatenate(all_sorted_coords),
        }
        for name, sorted_list in all_sorted_fields.items():
            fields_cache[name] = np.concatenate(sorted_list)

        return cls(
            cell_size=cell_sizes,
            box_bounds=box_bounds,
            grid_shape=grid_shape,
            n_atoms=n_atoms,
            n_timesteps=n_timesteps,
            timestep_values=tuple(timestep_values),
            _offsets=offsets,
            _counts=counts,
            _fields_cache=fields_cache,
        )

    @classmethod
    def from_lammps(
        cls,
        path: str | Path,
        cell_size: CellSize = DEFAULT_CELL_SIZE,
        timesteps: list[int] | slice | None = None,
        columns: dict[str, int] | None = None,
        coord_type: Literal["auto", "unwrapped", "wrapped", "scaled"] = "auto",
    ) -> SpatialGrid:
        """
        Create a SpatialGrid from a LAMMPS trajectory file.

        Parameters
        ----------
        path : str or Path
            Path to the .lammpstrj file.
        cell_size : float or tuple[float, float, float], default 4.0
            Grid cell size in Angstroms. Either uniform or per-axis (cs_x, cs_y, cs_z).
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
        SpatialGrid
            Grid built from the LAMMPS data.
        """
        from atomkit.io.lammps import parse_lammps

        coords_list, fields_list, selected_timesteps = parse_lammps(
            path, timesteps=timesteps, columns=columns, coord_type=coord_type
        )

        # box_bounds=None -> computed from actual coordinate data
        return cls.from_arrays(
            coords=coords_list,
            box_bounds=None,
            cell_size=cell_size,
            timestep_values=selected_timesteps,
            **fields_list,
        )

    @classmethod
    def load(cls, path: str | Path) -> SpatialGrid:
        """
        Load a SpatialGrid from an HDF5 file.

        The file is opened in read mode with lazy loading (data read on demand).

        Parameters
        ----------
        path : str or Path
            Path to the HDF5 file.

        Returns
        -------
        SpatialGrid
            Grid with lazy-loaded data.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        KeyError
            If required attributes are missing from the file.
        """
        path = Path(path)
        f = h5py.File(path, "r")

        try:
            # Read attributes
            attrs = f.attrs
            cell_size = tuple(float(x) for x in attrs["cell_size"])
            box_bounds = tuple(attrs["box_bounds"])
            grid_shape = tuple(attrs["grid_shape"])
            n_atoms = int(attrs["n_atoms"])
            n_timesteps = int(attrs.get("n_timesteps", 1))
            timestep_values = tuple(attrs.get("timestep_values", [0]))
        except Exception:
            f.close()
            raise

        logger.debug("Loaded grid from %s: %d timesteps, %d atoms", path, n_timesteps, n_atoms)

        return cls(
            cell_size=cell_size,
            box_bounds=box_bounds,
            grid_shape=grid_shape,
            n_atoms=n_atoms,
            n_timesteps=n_timesteps,
            timestep_values=timestep_values,
            _file=f,
        )

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def save(self, path: str | Path, compression: int = 0) -> SpatialGrid:
        """
        Save the grid to an HDF5 file.

        Parameters
        ----------
        path : str or Path
            Output file path.
        compression : int, default 0
            Zstd compression level. 0 = no compression (fastest),
            1-22 = zstd level (higher = smaller but slower, 3 is good default).
        """
        path = Path(path)
        if compression > 0:
            if not HDF5PLUGIN_AVAILABLE:
                raise ImportError(
                    "hdf5plugin is required for zstd compression. "
                    "Install with: pip install 'atomkit[compression]'"
                )
            compression_opts = dict(hdf5plugin.Zstd(clevel=compression))
        else:
            compression_opts = {}

        with h5py.File(path, "w") as f:
            # Store metadata as attributes
            f.attrs["cell_size"] = np.array(self.cell_size)
            f.attrs["box_bounds"] = np.array(self.box_bounds)
            f.attrs["grid_shape"] = np.array(self.grid_shape)
            f.attrs["n_atoms"] = self.n_atoms
            f.attrs["n_timesteps"] = self.n_timesteps
            f.attrs["timestep_values"] = np.array(self.timestep_values)

            # CSR structure (4D: n_timesteps, nx, ny, nz)
            csr = f.create_group(_CSR_GROUP)
            csr.create_dataset("offsets", data=self.offsets, **compression_opts)
            csr.create_dataset("counts", data=self.counts, **compression_opts)

            # Fields (concatenated: [t0_atoms, t1_atoms, ...])
            fields_grp = f.create_group(_FIELDS_GROUP)
            for name in self._fields_cache:
                data = self._fields_cache[name]
                fields_grp.create_dataset(name, data=data, **compression_opts)

        return self

    def add_field(self, name: str, data: NDArray, compression: int = 0) -> None:
        """
        Add a field to the grid (in-memory or to HDF5 file).

        Data is reordered to match grid cell ordering using _source_idx.

        Parameters
        ----------
        name : str
            Field name.
        data : ndarray
            Data in original order. Shape: (n_timesteps, n_atoms, ...) or flat.
        compression : int, default 0
            Zstd compression level for file-backed grids. 0 = none, 1-22 = zstd.
        """
        total_atoms = self.n_timesteps * self.n_atoms

        if self._file is None:
            # In-memory grid
            data = np.asarray(data)
            if data.shape[0] == self.n_timesteps:
                # Shape is (n_timesteps, n_atoms, ...)
                data = data.reshape((total_atoms,) + data.shape[2:])

            if data.shape[0] != total_atoms:
                raise ValueError(
                    f"Data has {data.shape[0]} elements, expected {total_atoms}"
                )

            # Reorder each timestep: original order -> grid order using _source_idx
            source_idx = self._fields_cache["_source_idx"]
            sorted_data = []
            for t in range(self.n_timesteps):
                t_start = t * self.n_atoms
                t_end = (t + 1) * self.n_atoms
                t_source_idx = source_idx[t_start:t_end]
                t_data = data[t_start:t_end]
                # t_source_idx maps grid position -> original position
                # So t_data[t_source_idx] reorders from original to grid order
                sorted_data.append(t_data[t_source_idx])

            self._fields_cache[name] = np.concatenate(sorted_data)
            return

        # File-backed grid - validate and prepare data before closing file
        file_path = Path(self._file.filename)

        # Read source_idx while file is still open
        source_idx = self._file[f"{_FIELDS_GROUP}/_source_idx"][:]

        # Validate and reshape data
        data = np.asarray(data)
        if data.shape[0] == self.n_timesteps:
            data = data.reshape((total_atoms,) + data.shape[2:])

        if data.shape[0] != total_atoms:
            raise ValueError(
                f"Data has {data.shape[0]} elements, expected {total_atoms}"
            )

        # Check compression availability before modifying file
        if compression > 0 and not HDF5PLUGIN_AVAILABLE:
            raise ImportError(
                "hdf5plugin is required for zstd compression. "
                "Install with: pip install 'atomkit[compression]'"
            )

        # Reorder each timestep
        sorted_chunks = []
        for t in range(self.n_timesteps):
            t_start = t * self.n_atoms
            t_end = (t + 1) * self.n_atoms
            t_source_idx = source_idx[t_start:t_end]
            t_data = data[t_start:t_end]
            sorted_chunks.append(t_data[t_source_idx])
        sorted_data = np.concatenate(sorted_chunks)

        # Now close and reopen for writing (with guaranteed reopen)
        self._file.close()
        self._file = None
        try:
            compression_opts = dict(hdf5plugin.Zstd(clevel=compression)) if compression > 0 else {}
            with h5py.File(file_path, "a") as f:
                if name in f[_FIELDS_GROUP]:
                    del f[f"{_FIELDS_GROUP}/{name}"]
                f[_FIELDS_GROUP].create_dataset(name, data=sorted_data, **compression_opts)
        finally:
            self._file = h5py.File(file_path, "r")

    def remove_field(self, name: str) -> None:
        """
        Remove a field from the grid.

        Parameters
        ----------
        name : str
            Field name to remove.
        """
        if name == "_source_idx":
            raise ValueError("Cannot remove _source_idx field")
        if name == "coords":
            raise ValueError("Cannot remove coords field")

        if self._file is None:
            if name in self._fields_cache:
                del self._fields_cache[name]
            return

        file_path = Path(self._file.filename)
        self._file.close()
        self._file = None
        try:
            with h5py.File(file_path, "a") as f:
                if name in f[_FIELDS_GROUP]:
                    del f[f"{_FIELDS_GROUP}/{name}"]
        finally:
            self._file = h5py.File(file_path, "r")

    # -------------------------------------------------------------------------
    # Context Manager
    # -------------------------------------------------------------------------

    def __enter__(self) -> SpatialGrid:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Literal[False]:
        self.close()
        return False

    def close(self) -> None:
        """Close the underlying HDF5 file if open."""
        if self._file is not None:
            self._file.close()
            self._file = None


# -----------------------------------------------------------------------------
# Convenience Functions
# -----------------------------------------------------------------------------


def preprocess_lammps(
    input_path: str | Path,
    output_path: str | Path,
    cell_size: CellSize = DEFAULT_CELL_SIZE,
    timesteps: list[int] | slice | None = None,
    compression: int = 0,
) -> SpatialGrid:
    """
    One-liner to preprocess a LAMMPS file to HDF5.

    Parameters
    ----------
    input_path : str or Path
        Input .lammpstrj file.
    output_path : str or Path
        Output .h5 file.
    cell_size : float or (cs_x, cs_y, cs_z), default 4.0
        Grid cell size in Angstroms.
    timesteps : list[int] | slice, optional
        Timesteps to extract. If None, extracts all.
    compression : int, default 0
        Zstd compression level. 0 = none, 1-22 = zstd.
    """
    grid = SpatialGrid.from_lammps(input_path, cell_size=cell_size, timesteps=timesteps)
    grid.save(output_path, compression=compression)
    return grid
