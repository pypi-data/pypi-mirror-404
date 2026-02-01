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
from atomkit._units import ureg, Q_, get_unit, strip_units, Quantity

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from numpy.typing import NDArray

from atomkit.io.lammps import CoordType

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


# -----------------------------------------------------------------------------
# SourceBox: Consolidated box metadata from source files
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceBox:
    """
    Original simulation box information from source file (e.g., LAMMPS).

    Attributes
    ----------
    bounds : tuple[float, ...] | None
        Orthogonal box bounds (xlo, xhi, ylo, yhi, zlo, zhi) in Angstroms.
    tilt : tuple[float, float, float] | None
        Tilt factors (xy, xz, yz) for triclinic boxes. None for orthogonal.
    boundary : str
        Boundary conditions string (e.g., "pp pp pp").
    """
    bounds: tuple[float, ...] | None = None
    tilt: tuple[float, float, float] | None = None
    boundary: str = ""

    @property
    def is_triclinic(self) -> bool:
        """True if box has non-zero tilt factors (sheared)."""
        return self.tilt is not None and any(t != 0 for t in self.tilt)

    @property
    def is_valid(self) -> bool:
        """True if bounds are defined."""
        return self.bounds is not None and len(self.bounds) == 6

    def contains(self, x: float, y: float, z: float) -> bool:
        """
        Check if point is within box bounds.

        For triclinic boxes, this checks against the orthogonal bounding box
        (which is a superset of the actual triclinic box). This is conservative:
        atoms inside the triclinic box will always pass, but some atoms in the
        corners of the bounding box (outside the actual triclinic box) may also
        pass. This is acceptable for trim_to_source_box filtering.
        """
        if not self.is_valid:
            return True
        xlo, xhi, ylo, yhi, zlo, zhi = self.bounds
        # For both orthogonal and triclinic, check against bounding box.
        # The stored bounds are xlo_bound/xhi_bound for triclinic (from LAMMPS).
        return xlo <= x <= xhi and ylo <= y <= yhi and zlo <= z <= zhi


# -----------------------------------------------------------------------------
# CellsAccessor: Precomputed per-cell aggregates
# -----------------------------------------------------------------------------


# Dimension mapping for axis names
_DIM_MAP = {"t": 0, "x": 1, "y": 2, "z": 3}
_DIM_NAMES = ("t", "x", "y", "z")


def _build_cumsum_4d(
    data: NDArray,
    pbar: tqdm | None = None,
    label: str = "",
) -> NDArray[np.float64]:
    """
    Build a 4D cumulative sum array for O(1) region queries.

    Parameters
    ----------
    data : ndarray, shape (t, nx, ny, nz)
        Per-cell values (e.g., sum or counts).
    pbar : tqdm, optional
        External progress bar to update (4 steps per call).
    label : str, optional
        Label to show in pbar postfix.

    Returns
    -------
    cumsum : ndarray, shape (t, nx, ny, nz)
        Integral volume where cumsum[t,i,j,k] = sum of all cells in
        the 4D box [0:t+1, 0:i+1, 0:j+1, 0:k+1].
    """
    axis_names = ["t", "x", "y", "z"]
    cumsum = data.astype(np.float64)
    for axis, axis_name in enumerate(axis_names):
        if pbar is not None:
            pbar.set_postfix(field=label, axis=axis_name)
        np.cumsum(cumsum, axis=axis, out=cumsum)
        if pbar is not None:
            pbar.update(1)
    return cumsum


def _build_all_cumsums(
    counts: NDArray,
    agg_sum: dict[str, NDArray],
    numeric_fields: list[str],
) -> tuple[NDArray[np.uint64], dict[str, NDArray[np.float64]]]:
    """
    Build cumsum arrays for counts and all numeric fields with shared progress bar.

    Returns
    -------
    counts_cumsum : ndarray
        Cumsum for counts array.
    field_cumsums : dict
        Cumsum for each numeric field.
    """
    n_cells = np.prod(counts.shape)
    show_progress = n_cells >= TQDM_ATOM_THRESHOLD

    all_fields = ["counts"] + numeric_fields
    # 4 axis steps per field
    total_steps = len(all_fields) * 4
    pbar = tqdm(total=total_steps, desc="Building cumsums", disable=not show_progress)

    field_cumsums = {}
    counts_cumsum = _build_cumsum_4d(counts.astype(np.float64), pbar, "counts").astype(np.uint64)

    for name in numeric_fields:
        field_cumsums[name] = _build_cumsum_4d(agg_sum[name], pbar, name)

    pbar.close()
    return counts_cumsum, field_cumsums


def _box_sum_4d(
    cumsum: NDArray[np.float64],
    t0: int, t1: int,
    x0: int, x1: int,
    y0: int, y1: int,
    z0: int, z1: int,
) -> float:
    """
    Compute sum over a 4D box using inclusion-exclusion (O(1)).

    Parameters are inclusive indices: sum over [t0:t1+1, x0:x1+1, y0:y1+1, z0:z1+1].
    Uses 16-corner inclusion-exclusion formula.
    """
    def get(t: int, x: int, y: int, z: int) -> float:
        if t < 0 or x < 0 or y < 0 or z < 0:
            return 0.0
        return cumsum[t, x, y, z]

    # 16-term inclusion-exclusion formula for 4D
    return (
        get(t1, x1, y1, z1)
        - get(t0-1, x1, y1, z1) - get(t1, x0-1, y1, z1)
        - get(t1, x1, y0-1, z1) - get(t1, x1, y1, z0-1)
        + get(t0-1, x0-1, y1, z1) + get(t0-1, x1, y0-1, z1)
        + get(t0-1, x1, y1, z0-1) + get(t1, x0-1, y0-1, z1)
        + get(t1, x0-1, y1, z0-1) + get(t1, x1, y0-1, z0-1)
        - get(t0-1, x0-1, y0-1, z1) - get(t0-1, x0-1, y1, z0-1)
        - get(t0-1, x1, y0-1, z0-1) - get(t1, x0-1, y0-1, z0-1)
        + get(t0-1, x0-1, y0-1, z0-1)
    )


def _project_2d_cumsum(
    cumsum: NDArray[np.float64],
    keep_axes: tuple[int, int],
    reduce_ranges: dict[int, tuple[int, int]],
) -> NDArray[np.float64]:
    """
    Project 4D cumsum to 2D by summing over two axes using O(1) box queries.

    This is O(n1 * n2) where n1, n2 are the sizes of the kept axes,
    compared to O(n1 * n2 * n3 * n4) for naive summation.

    Parameters
    ----------
    cumsum : ndarray, shape (t, nx, ny, nz)
        4D cumulative sum array.
    keep_axes : tuple of 2 ints
        Which axes to keep (0=t, 1=x, 2=y, 3=z).
    reduce_ranges : dict
        For each reduced axis, (start_idx, end_idx) inclusive range.

    Returns
    -------
    result : ndarray, shape (n_keep0, n_keep1)
        2D projected array.
    """
    shape = cumsum.shape
    ax0, ax1 = keep_axes

    # Determine the other two axes to reduce
    all_axes = {0, 1, 2, 3}
    reduce_axes = sorted(all_axes - set(keep_axes))

    # Get ranges for reduced axes
    ranges = [None, None, None, None]  # [t, x, y, z] ranges
    for ax in reduce_axes:
        ranges[ax] = reduce_ranges.get(ax, (0, shape[ax] - 1))

    # Output shape
    n0, n1 = shape[ax0], shape[ax1]
    result = np.zeros((n0, n1), dtype=np.float64)

    # Helper to safely index cumsum (handles negative indices)
    def get(t, x, y, z):
        if t < 0 or x < 0 or y < 0 or z < 0:
            return 0.0
        return cumsum[t, x, y, z]

    # For each cell in the 2D output, compute box sum
    for i in range(n0):
        for j in range(n1):
            # Build the box bounds
            bounds = [None, None, None, None]  # [t0,t1], [x0,x1], [y0,y1], [z0,z1]

            for ax in range(4):
                if ax == ax0:
                    bounds[ax] = (i, i)
                elif ax == ax1:
                    bounds[ax] = (j, j)
                else:
                    bounds[ax] = ranges[ax]

            t0, t1 = bounds[0]
            x0, x1 = bounds[1]
            y0, y1 = bounds[2]
            z0, z1 = bounds[3]

            # 16-term inclusion-exclusion
            result[i, j] = (
                get(t1, x1, y1, z1)
                - get(t0-1, x1, y1, z1) - get(t1, x0-1, y1, z1)
                - get(t1, x1, y0-1, z1) - get(t1, x1, y1, z0-1)
                + get(t0-1, x0-1, y1, z1) + get(t0-1, x1, y0-1, z1)
                + get(t0-1, x1, y1, z0-1) + get(t1, x0-1, y0-1, z1)
                + get(t1, x0-1, y1, z0-1) + get(t1, x1, y0-1, z0-1)
                - get(t0-1, x0-1, y0-1, z1) - get(t0-1, x0-1, y1, z0-1)
                - get(t0-1, x1, y0-1, z0-1) - get(t1, x0-1, y0-1, z0-1)
                + get(t0-1, x0-1, y0-1, z0-1)
            )

    return result


# Try to use numba for faster 2D projection
try:
    from numba import njit, prange

    @njit(cache=True)
    def _cumsum_get(cumsum, t, x, y, z):
        """Safe cumsum indexing - returns 0 for negative indices."""
        if t < 0 or x < 0 or y < 0 or z < 0:
            return 0.0
        return cumsum[t, x, y, z]

    @njit(cache=True)
    def _box_sum_16(cumsum, t0, t1, x0, x1, y0, y1, z0, z1):
        """16-term inclusion-exclusion for 4D box sum."""
        return (
            _cumsum_get(cumsum, t1, x1, y1, z1)
            - _cumsum_get(cumsum, t0-1, x1, y1, z1)
            - _cumsum_get(cumsum, t1, x0-1, y1, z1)
            - _cumsum_get(cumsum, t1, x1, y0-1, z1)
            - _cumsum_get(cumsum, t1, x1, y1, z0-1)
            + _cumsum_get(cumsum, t0-1, x0-1, y1, z1)
            + _cumsum_get(cumsum, t0-1, x1, y0-1, z1)
            + _cumsum_get(cumsum, t0-1, x1, y1, z0-1)
            + _cumsum_get(cumsum, t1, x0-1, y0-1, z1)
            + _cumsum_get(cumsum, t1, x0-1, y1, z0-1)
            + _cumsum_get(cumsum, t1, x1, y0-1, z0-1)
            - _cumsum_get(cumsum, t0-1, x0-1, y0-1, z1)
            - _cumsum_get(cumsum, t0-1, x0-1, y1, z0-1)
            - _cumsum_get(cumsum, t0-1, x1, y0-1, z0-1)
            - _cumsum_get(cumsum, t1, x0-1, y0-1, z0-1)
            + _cumsum_get(cumsum, t0-1, x0-1, y0-1, z0-1)
        )

    @njit(parallel=True, cache=True)
    def _project_2d_xy(cumsum, t0, t1, z0, z1):
        """Project to (x, y) by summing over t and z."""
        _, nx, ny, _ = cumsum.shape
        result = np.zeros((nx, ny), dtype=np.float64)
        for i in prange(nx):
            for j in range(ny):
                result[i, j] = _box_sum_16(cumsum, t0, t1, i, i, j, j, z0, z1)
        return result

    @njit(parallel=True, cache=True)
    def _project_2d_xz(cumsum, t0, t1, y0, y1):
        """Project to (x, z) by summing over t and y."""
        _, nx, _, nz = cumsum.shape
        result = np.zeros((nx, nz), dtype=np.float64)
        for i in prange(nx):
            for k in range(nz):
                result[i, k] = _box_sum_16(cumsum, t0, t1, i, i, y0, y1, k, k)
        return result

    @njit(parallel=True, cache=True)
    def _project_2d_yz(cumsum, t0, t1, x0, x1):
        """Project to (y, z) by summing over t and x."""
        _, _, ny, nz = cumsum.shape
        result = np.zeros((ny, nz), dtype=np.float64)
        for j in prange(ny):
            for k in range(nz):
                result[j, k] = _box_sum_16(cumsum, t0, t1, x0, x1, j, j, k, k)
        return result

    @njit(parallel=True, cache=True)
    def _project_2d_tx(cumsum, y0, y1, z0, z1):
        """Project to (t, x) by summing over y and z."""
        nt, nx, _, _ = cumsum.shape
        result = np.zeros((nt, nx), dtype=np.float64)
        for t in prange(nt):
            for i in range(nx):
                result[t, i] = _box_sum_16(cumsum, t, t, i, i, y0, y1, z0, z1)
        return result

    @njit(parallel=True, cache=True)
    def _project_2d_ty(cumsum, x0, x1, z0, z1):
        """Project to (t, y) by summing over x and z."""
        nt, _, ny, _ = cumsum.shape
        result = np.zeros((nt, ny), dtype=np.float64)
        for t in prange(nt):
            for j in range(ny):
                result[t, j] = _box_sum_16(cumsum, t, t, x0, x1, j, j, z0, z1)
        return result

    @njit(parallel=True, cache=True)
    def _project_2d_tz(cumsum, x0, x1, y0, y1):
        """Project to (t, z) by summing over x and y."""
        nt, _, _, nz = cumsum.shape
        result = np.zeros((nt, nz), dtype=np.float64)
        for t in prange(nt):
            for k in range(nz):
                result[t, k] = _box_sum_16(cumsum, t, t, x0, x1, y0, y1, k, k)
        return result

    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False


def project_2d_fast(
    cumsum: NDArray[np.float64],
    keep_axes: tuple[str, str],
    reduce_ranges: dict[str, tuple[int, int]] | None = None,
) -> NDArray[np.float64]:
    """
    Fast 2D projection using cumsum O(1) box queries.

    Parameters
    ----------
    cumsum : ndarray, shape (t, nx, ny, nz)
        4D cumulative sum array.
    keep_axes : tuple of 2 str
        Axes to keep, e.g. ("x", "y").
    reduce_ranges : dict, optional
        For reduced axes, (start, end) inclusive index ranges.
        Defaults to full range.

    Returns
    -------
    result : ndarray
        2D projected sum array.
    """
    dim_map = {"t": 0, "x": 1, "y": 2, "z": 3}
    shape = cumsum.shape

    # Default to full ranges
    if reduce_ranges is None:
        reduce_ranges = {}

    # Get ranges for all axes
    t_range = reduce_ranges.get("t", (0, shape[0] - 1))
    x_range = reduce_ranges.get("x", (0, shape[1] - 1))
    y_range = reduce_ranges.get("y", (0, shape[2] - 1))
    z_range = reduce_ranges.get("z", (0, shape[3] - 1))

    ax0, ax1 = keep_axes

    if NUMBA_AVAILABLE:
        # Use optimized numba functions
        if (ax0, ax1) == ("x", "y"):
            return _project_2d_xy(cumsum, t_range[0], t_range[1], z_range[0], z_range[1])
        elif (ax0, ax1) == ("x", "z"):
            return _project_2d_xz(cumsum, t_range[0], t_range[1], y_range[0], y_range[1])
        elif (ax0, ax1) == ("y", "z"):
            return _project_2d_yz(cumsum, t_range[0], t_range[1], x_range[0], x_range[1])
        elif (ax0, ax1) == ("t", "x"):
            return _project_2d_tx(cumsum, y_range[0], y_range[1], z_range[0], z_range[1])
        elif (ax0, ax1) == ("t", "y"):
            return _project_2d_ty(cumsum, x_range[0], x_range[1], z_range[0], z_range[1])
        elif (ax0, ax1) == ("t", "z"):
            return _project_2d_tz(cumsum, x_range[0], x_range[1], y_range[0], y_range[1])
        # Handle reversed axes
        elif (ax1, ax0) == ("x", "y"):
            return _project_2d_xy(cumsum, t_range[0], t_range[1], z_range[0], z_range[1]).T
        elif (ax1, ax0) == ("x", "z"):
            return _project_2d_xz(cumsum, t_range[0], t_range[1], y_range[0], y_range[1]).T
        elif (ax1, ax0) == ("y", "z"):
            return _project_2d_yz(cumsum, t_range[0], t_range[1], x_range[0], x_range[1]).T
        elif (ax1, ax0) == ("t", "x"):
            return _project_2d_tx(cumsum, y_range[0], y_range[1], z_range[0], z_range[1]).T
        elif (ax1, ax0) == ("t", "y"):
            return _project_2d_ty(cumsum, x_range[0], x_range[1], z_range[0], z_range[1]).T
        elif (ax1, ax0) == ("t", "z"):
            return _project_2d_tz(cumsum, x_range[0], x_range[1], y_range[0], y_range[1]).T

    # Fallback to pure Python
    return _project_2d_cumsum(
        cumsum,
        (dim_map[ax0], dim_map[ax1]),
        {
            0: t_range,
            1: x_range,
            2: y_range,
            3: z_range,
        },
    )


class ReductionAccessor:
    """
    Accessor for cell aggregates with O(1) region queries via cumsum.

    Provides numpy array access and callable reduction operations.

    Usage
    -----
    >>> grid.cells["stress"].sum.np        # Raw numpy array (t, nx, ny, nz)
    >>> grid.cells["stress"].sum[0]        # Indexing
    >>> grid.cells["stress"].sum()         # Sum all (scalar)
    >>> grid.cells["stress"].sum(axis="z") # Reduce over z: (t, nx, ny)
    >>> grid.cells["stress"].sum(axis=["x", "y"])  # Reduce multiple: (t, nz)
    """

    def __init__(
        self,
        data: NDArray[np.float64],
        cumsum: NDArray[np.float64] | None,
        name: str,
    ):
        self._data = data
        self._cumsum = cumsum
        self._name = name

    @property
    def np(self) -> NDArray[np.float64]:
        """Raw numpy array: (t, nx, ny, nz)."""
        return self._data

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying array."""
        return self._data.shape

    def __getitem__(self, key):
        """Index into the underlying array."""
        return self._data[key]

    def __array__(self, dtype=None):
        """Support numpy array conversion."""
        if dtype is None:
            return self._data
        return self._data.astype(dtype)

    def __repr__(self) -> str:
        return f"ReductionAccessor({self._name}, shape={self._data.shape})"

    def __call__(
        self,
        axis: str | int | list[str | int] | None = None,
        **ranges,
    ) -> NDArray[np.float64] | float:
        """
        Reduce over specified axes, optionally with range constraints.

        Parameters
        ----------
        axis : str, int, or list thereof, optional
            Axis or axes to reduce over. Can be names ("t", "x", "y", "z")
            or indices (0, 1, 2, 3). If None, reduces over all axes (returns scalar).
        **ranges : tuple[int, int]
            Optional index ranges for each axis, e.g. t=(0, 5), z=(10, 50).
            Values are cell indices (not coordinates).

        Returns
        -------
        result : ndarray or float
            Reduced array, or scalar if all axes reduced.
        """
        # If no cumsum available, fall back to numpy
        if self._cumsum is None:
            return self._reduce_numpy(axis)

        # Parse axis argument
        if axis is None:
            # Reduce all: return scalar using cumsum
            shape = self._data.shape
            return _box_sum_4d(
                self._cumsum,
                0, shape[0] - 1,
                0, shape[1] - 1,
                0, shape[2] - 1,
                0, shape[3] - 1,
            )

        # Normalize axis to list of indices
        if isinstance(axis, (str, int)):
            axis = [axis]

        axis_indices = []
        for a in axis:
            if isinstance(a, str):
                if a not in _DIM_MAP:
                    raise ValueError(f"Unknown axis name: {a!r}")
                axis_indices.append(_DIM_MAP[a])
            else:
                axis_indices.append(int(a))

        axis_indices = sorted(set(axis_indices))

        # Use numpy sum for partial reductions (cumsum-based partial reduction
        # is complex; numpy is efficient for typical grid sizes)
        return self._reduce_numpy_axes(axis_indices)

    def _reduce_numpy(self, axis) -> NDArray[np.float64] | float:
        """Fallback numpy reduction."""
        if axis is None:
            return float(self._data.sum())

        if isinstance(axis, (str, int)):
            axis = [axis]

        axis_indices = []
        for a in axis:
            if isinstance(a, str):
                axis_indices.append(_DIM_MAP[a])
            else:
                axis_indices.append(int(a))

        return self._data.sum(axis=tuple(axis_indices))

    def _reduce_numpy_axes(self, axis_indices: list[int]) -> NDArray[np.float64] | float:
        """Reduce over specified axis indices using numpy."""
        result = self._data.sum(axis=tuple(axis_indices))
        if result.ndim == 0:
            return float(result)
        return result


def _box_sum_4d_int(
    cumsum: NDArray[np.uint64],
    t0: int, t1: int,
    x0: int, x1: int,
    y0: int, y1: int,
    z0: int, z1: int,
) -> int:
    """
    Compute sum over a 4D box using inclusion-exclusion (O(1)) for integer arrays.

    Same as _box_sum_4d but for uint64 arrays, returns int.
    """
    def get(t: int, x: int, y: int, z: int) -> int:
        if t < 0 or x < 0 or y < 0 or z < 0:
            return 0
        return int(cumsum[t, x, y, z])

    # 16-term inclusion-exclusion formula for 4D
    return (
        get(t1, x1, y1, z1)
        - get(t0-1, x1, y1, z1) - get(t1, x0-1, y1, z1)
        - get(t1, x1, y0-1, z1) - get(t1, x1, y1, z0-1)
        + get(t0-1, x0-1, y1, z1) + get(t0-1, x1, y0-1, z1)
        + get(t0-1, x1, y1, z0-1) + get(t1, x0-1, y0-1, z1)
        + get(t1, x0-1, y1, z0-1) + get(t1, x1, y0-1, z0-1)
        - get(t0-1, x0-1, y0-1, z1) - get(t0-1, x0-1, y1, z0-1)
        - get(t0-1, x1, y0-1, z0-1) - get(t1, x0-1, y0-1, z0-1)
        + get(t0-1, x0-1, y0-1, z0-1)
    )


def _normalize_axis(axis: str | int | list[str | int] | None) -> list[int] | None:
    """Normalize axis argument to list of integer indices, or None for all axes."""
    if axis is None:
        return None

    if isinstance(axis, (str, int)):
        axis = [axis]

    axis_indices = []
    for a in axis:
        if isinstance(a, str):
            if a not in _DIM_MAP:
                raise ValueError(f"Unknown axis name: {a!r}")
            axis_indices.append(_DIM_MAP[a])
        else:
            axis_indices.append(int(a))

    return sorted(set(axis_indices))


def _safe_divide(numerator: NDArray | float, denominator: NDArray | float) -> NDArray | float:
    """Divide with proper handling of zeros (returns 0 for 0/0)."""
    with np.errstate(invalid='ignore', divide='ignore'):
        result = numerator / denominator
        if isinstance(result, np.ndarray):
            result[~np.isfinite(result)] = 0
        elif not np.isfinite(result):
            result = 0.0
    return result


class MeanAccessor:
    """
    Accessor for mean values (sum / counts).

    Delegates to ReductionAccessor for sum and counts, then divides.
    Properly handles empty cells (returns 0 for 0/0).
    """

    def __init__(
        self,
        sum_accessor: ReductionAccessor,
        counts_accessor: ReductionAccessor,
    ):
        self._sum = sum_accessor
        self._counts = counts_accessor

    @property
    def np(self) -> NDArray[np.float64]:
        """Raw numpy array of mean values: (t, nx, ny, nz)."""
        return _safe_divide(self._sum.np, self._counts.np.astype(np.float64))

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying array."""
        return self._sum.shape

    def __getitem__(self, key):
        """Index into the mean array (computes on demand)."""
        return _safe_divide(self._sum[key], self._counts[key].astype(np.float64))

    def __array__(self, dtype=None):
        """Support numpy array conversion."""
        result = self.np
        if dtype is not None:
            result = result.astype(dtype)
        return result

    def __repr__(self) -> str:
        return f"MeanAccessor(shape={self._sum.shape})"

    def __call__(
        self,
        axis: str | int | list[str | int] | None = None,
    ) -> NDArray[np.float64] | float:
        """
        Compute mean reduced over specified axes.

        Parameters
        ----------
        axis : str, int, or list thereof, optional
            Axis or axes to reduce over. If None, returns global mean.

        Returns
        -------
        result : ndarray or float
            Reduced mean array, or scalar if all axes reduced.
        """
        total_sum = self._sum(axis)
        total_count = self._counts(axis)
        result = _safe_divide(total_sum, total_count)
        return float(result) if isinstance(result, np.ndarray) and result.ndim == 0 else result


class DensityAccessor:
    """
    Accessor for density values (sum / volume).

    Computes spatial density by dividing sum by the total volume of the region.
    Useful for continuum quantities like energy density or stress per unit volume.
    """

    def __init__(
        self,
        sum_accessor: ReductionAccessor,
        cell_volume: float,
    ):
        self._sum = sum_accessor
        self._cell_volume = cell_volume

    @property
    def np(self) -> NDArray[np.float64]:
        """Raw numpy array of density values: (t, nx, ny, nz)."""
        return self._sum.np / self._cell_volume

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying array."""
        return self._sum.shape

    def __getitem__(self, key):
        """Index into the density array."""
        return self._sum[key] / self._cell_volume

    def __array__(self, dtype=None):
        """Support numpy array conversion."""
        result = self.np
        if dtype is not None:
            result = result.astype(dtype)
        return result

    def __repr__(self) -> str:
        return f"DensityAccessor(shape={self._sum.shape}, cell_volume={self._cell_volume})"

    def __call__(
        self,
        axis: str | int | list[str | int] | None = None,
    ) -> NDArray[np.float64] | float:
        """
        Compute density reduced over specified axes.

        Parameters
        ----------
        axis : str, int, or list thereof, optional
            Axis or axes to reduce over. If None, returns global density
            (total sum / total volume).

        Returns
        -------
        result : ndarray or float
            Reduced density array, or scalar if all axes reduced.
        """
        axis_indices = _normalize_axis(axis)

        if axis_indices is None:
            # Full reduction: sum / total_volume
            total_sum = self._sum()
            n_cells = np.prod(self._sum.shape)
            return total_sum / (n_cells * self._cell_volume)

        # Partial reduction: need to compute volume of reduced dimensions
        # Volume = n_cells_in_reduced_dims * cell_volume
        shape = self._sum.shape
        n_cells_reduced = 1
        for idx in axis_indices:
            n_cells_reduced *= shape[idx]

        total_sum = self._sum(axis)
        return total_sum / (n_cells_reduced * self._cell_volume)


@dataclass
class FieldAggregates:
    """
    Precomputed aggregates for a field. Shape: (n_timesteps, nx, ny, nz).

    Provides ReductionAccessor for sum/min/max with O(1) region queries via cumsum,
    MeanAccessor for mean values (sum / counts), and DensityAccessor for density
    values (sum / volume).
    """
    _sum: NDArray[np.float64] = field(repr=False)
    _min: NDArray[np.float64] = field(repr=False)
    _max: NDArray[np.float64] = field(repr=False)
    _cumsum: NDArray[np.float64] | None = field(default=None, repr=False)
    _counts_ref: NDArray[np.uint32] | None = field(default=None, repr=False)
    _counts_cumsum: NDArray[np.uint64] | None = field(default=None, repr=False)
    _cell_volume: float | None = field(default=None, repr=False)

    @property
    def sum(self) -> ReductionAccessor:
        """Sum per cell with O(1) region queries."""
        return ReductionAccessor(self._sum, self._cumsum, "sum")

    @property
    def min(self) -> ReductionAccessor:
        """Min per cell."""
        return ReductionAccessor(self._min, None, "min")

    @property
    def max(self) -> ReductionAccessor:
        """Max per cell."""
        return ReductionAccessor(self._max, None, "max")

    @property
    def mean(self) -> MeanAccessor:
        """Mean per cell (sum / counts), with proper empty cell handling."""
        if self._counts_ref is None:
            raise ValueError("Counts reference not set")
        sum_accessor = ReductionAccessor(self._sum, self._cumsum, "sum")
        counts_accessor = ReductionAccessor(
            self._counts_ref.astype(np.float64),
            self._counts_cumsum.astype(np.float64) if self._counts_cumsum is not None else None,
            "counts",
        )
        return MeanAccessor(sum_accessor, counts_accessor)

    @property
    def density(self) -> DensityAccessor:
        """Density per cell (sum / volume)."""
        if self._cell_volume is None:
            raise ValueError("Cell volume not set")
        sum_accessor = ReductionAccessor(self._sum, self._cumsum, "sum")
        return DensityAccessor(sum_accessor, self._cell_volume)


class CellsAccessor:
    """
    Accessor for precomputed cell-level aggregates.

    Usage:
        grid.cells.counts              # ReductionAccessor for atom counts
        grid.cells.counts.np           # Raw numpy array (t, nx, ny, nz)
        grid.cells.counts()            # Scalar: total atom count
        grid.cells.counts(axis="z")    # Reduce over z: (t, nx, ny)
        grid.cells["stress"].sum       # ReductionAccessor for sum per cell
        grid.cells["stress"].sum.np    # Raw numpy array
        grid.cells["stress"].sum()     # Scalar: sum all
        grid.cells["stress"].sum(axis="z")  # Reduce over z: (t, nx, ny)
        grid.cells["stress"].min       # ReductionAccessor for min per cell
        grid.cells["stress"].max       # ReductionAccessor for max per cell
        grid.cells["stress"].mean      # MeanAccessor for mean per cell
        grid.cells["stress"].density   # DensityAccessor for density per cell
        grid.cells.fields              # list of fields with aggregates
    """

    def __init__(
        self,
        counts: NDArray[np.uint32],
        aggregates: dict[str, FieldAggregates] | None = None,
        file: h5py.File | None = None,
        counts_cumsum: NDArray[np.uint64] | None = None,
        cell_volume: float | None = None,
    ):
        self._counts = counts
        self._aggregates = aggregates or {}
        self._file = file
        self._counts_cumsum = counts_cumsum
        self._cell_volume = cell_volume

    @property
    def counts(self) -> ReductionAccessor:
        """Atom counts per cell as ReductionAccessor: (n_timesteps, nx, ny, nz)."""
        counts_cumsum = self._get_counts_cumsum()
        return ReductionAccessor(
            self._counts.astype(np.float64),
            counts_cumsum.astype(np.float64) if counts_cumsum is not None else None,
            "counts",
        )

    def _get_counts_cumsum(self) -> NDArray[np.uint64] | None:
        """Get counts_cumsum, loading from file if needed."""
        if self._counts_cumsum is None and self._file is not None:
            if "_counts_cumsum" in self._file[_CSR_GROUP]:
                self._counts_cumsum = self._file[f"{_CSR_GROUP}/_counts_cumsum"][:]
        return self._counts_cumsum

    @property
    def cell_volume(self) -> float | None:
        """Volume of a single cell (cs_x * cs_y * cs_z)."""
        return self._cell_volume

    @property
    def fields(self) -> list[str]:
        """List of fields with precomputed aggregates."""
        if self._file is not None and "_cells" in self._file:
            return list(self._file["_cells"].keys())
        return list(self._aggregates.keys())

    def __getitem__(self, field: str) -> FieldAggregates:
        """Get aggregates for a field."""
        if field in self._aggregates:
            return self._aggregates[field]
        # Lazy load from file
        if self._file is not None and "_cells" in self._file and field in self._file["_cells"]:
            grp = self._file[f"_cells/{field}"]

            # Load base arrays
            sum_data = grp["sum"][:]
            min_data = grp["min"][:]
            max_data = grp["max"][:]

            # Load cumsum if available
            cumsum = grp["cumsum"][:] if "cumsum" in grp else None

            agg = FieldAggregates(
                _sum=sum_data,
                _min=min_data,
                _max=max_data,
                _cumsum=cumsum,
                _counts_ref=self._counts,
                _counts_cumsum=self._get_counts_cumsum(),
                _cell_volume=self._cell_volume,
            )
            self._aggregates[field] = agg
            return agg
        raise KeyError(f"No aggregates for field '{field}'")

    def __contains__(self, field: str) -> bool:
        if field in self._aggregates:
            return True
        if self._file is not None and "_cells" in self._file:
            return field in self._file["_cells"]
        return False


# -----------------------------------------------------------------------------
# Boundary slices: non-overlapping hull between outer and inner regions
# -----------------------------------------------------------------------------


def boundary_slices(
    outer: tuple[slice, slice, slice],
    inner: tuple[slice, slice, slice],
) -> list[tuple[slice, slice, slice]]:
    """
    Generate non-overlapping slices covering outer - inner (the boundary hull).

    Given two nested boxes (outer containing inner), returns slices that cover
    exactly the boundary region (outer minus inner) with no overlap.

    Works by peeling off near/far slabs in each dimension, then shrinking
    inward to avoid overlap. If inner is empty/invalid, returns the entire outer.

    Parameters
    ----------
    outer : tuple[slice, slice, slice]
        Slices defining the outer box (x, y, z).
    inner : tuple[slice, slice, slice]
        Slices defining the inner box (subset of outer).

    Returns
    -------
    list[tuple[slice, slice, slice]]
        Non-overlapping slices covering outer - inner.
        Empty list if outer equals inner (no boundary).

    Examples
    --------
    >>> outer = (slice(0, 5), slice(0, 5), slice(0, 5))
    >>> inner = (slice(1, 4), slice(1, 4), slice(1, 4))
    >>> slices = boundary_slices(outer, inner)
    >>> len(slices)  # 6 slabs (2 per dimension)
    6
    """
    result = []
    outer_l = [slice(s.start, s.stop) for s in outer]
    inner_l = [slice(s.start, s.stop) for s in inner]

    # Clamp inner to be within outer
    inner_l = [
        slice(max(i.start, o.start), min(i.stop, o.stop))
        for i, o in zip(inner_l, outer_l)
    ]

    # Check if inner is valid (non-empty in all dims)
    inner_valid = all(i.stop > i.start for i in inner_l)

    if not inner_valid:
        # No interior cells, entire outer is boundary
        return [tuple(outer_l)]

    current = [slice(s.start, s.stop) for s in outer_l]

    for dim in range(3):
        o = current[dim]
        i = inner_l[dim]

        # Near slab: [outer_start, inner_start)
        if o.start < i.start:
            slab = current.copy()
            slab[dim] = slice(o.start, i.start)
            result.append(tuple(slab))

        # Far slab: [inner_stop, outer_stop)
        if i.stop < o.stop:
            slab = current.copy()
            slab[dim] = slice(i.stop, o.stop)
            result.append(tuple(slab))

        # Shrink current to inner extent for remaining dims
        current[dim] = i

    # After all dims, current == inner, which we exclude (it's interior)
    return result


def _compute_cell_aggregates(
    field_data: NDArray,
    counts: NDArray[np.uint32],
    offsets: NDArray[np.uint64],
    grid_shape: tuple[int, int, int],
    n_timesteps: int,
    n_atoms: int,
    counts_cumsum: NDArray[np.uint64] | None = None,
) -> FieldAggregates:
    """Compute sum/min/max/cumsum aggregates for a field across all cells and timesteps."""
    nx, ny, nz = grid_shape
    n_cells = nx * ny * nz

    sum_arr = np.zeros((n_timesteps, nx, ny, nz), dtype=np.float64)
    min_arr = np.zeros((n_timesteps, nx, ny, nz), dtype=np.float64)
    max_arr = np.zeros((n_timesteps, nx, ny, nz), dtype=np.float64)

    for t_idx in range(n_timesteps):
        t_start = t_idx * n_atoms
        t_end = (t_idx + 1) * n_atoms

        data_t = field_data[t_start:t_end].astype(np.float64, copy=False)
        counts_flat = counts[t_idx].ravel().astype(np.int64)
        offsets_flat = offsets[t_idx].ravel().astype(np.int64)

        # Sum via cumsum (vectorized)
        cumsum = np.zeros(len(data_t) + 1, dtype=np.float64)
        cumsum[1:] = np.cumsum(data_t)
        end_indices = offsets_flat + counts_flat
        sums = cumsum[end_indices] - cumsum[offsets_flat]
        sum_arr[t_idx] = sums.reshape(nx, ny, nz)

        # Min/max via reduceat (vectorized)
        # Only compute for non-empty cells
        non_empty = counts_flat > 0
        if non_empty.any():
            non_empty_offsets = offsets_flat[non_empty].astype(np.intp)
            mins_non_empty = np.minimum.reduceat(data_t, non_empty_offsets)
            maxs_non_empty = np.maximum.reduceat(data_t, non_empty_offsets)

            mins = np.zeros(n_cells, dtype=np.float64)
            maxs = np.zeros(n_cells, dtype=np.float64)
            mins[non_empty] = mins_non_empty
            maxs[non_empty] = maxs_non_empty
        else:
            mins = np.zeros(n_cells, dtype=np.float64)
            maxs = np.zeros(n_cells, dtype=np.float64)

        min_arr[t_idx] = mins.reshape(nx, ny, nz)
        max_arr[t_idx] = maxs.reshape(nx, ny, nz)

    # Build 4D cumsum for O(1) region queries
    cumsum_4d = _build_cumsum_4d(sum_arr)

    return FieldAggregates(
        _sum=sum_arr,
        _min=min_arr,
        _max=max_arr,
        _cumsum=cumsum_4d,
        _counts_ref=counts,
        _counts_cumsum=counts_cumsum,
    )


def _is_numeric_field(data: NDArray) -> bool:
    """Check if field data is numeric (int or float)."""
    return np.issubdtype(data.dtype, np.number)


# -----------------------------------------------------------------------------
# GridView: A view into a subset of a SpatialGrid
# -----------------------------------------------------------------------------


class GridView:
    """
    A view into a subset of a SpatialGrid (shares underlying data).

    Created via grid.view() method. Provides the same interface as SpatialGrid
    but constrained to a subregion of cells.

    Attributes
    ----------
    parent : SpatialGrid
        The original grid this view is derived from.
    slices : tuple[slice, slice, slice]
        Index slices for (x, y, z) dimensions.
    """

    def __init__(
        self,
        parent: "SpatialGrid",
        x_slice: slice,
        y_slice: slice,
        z_slice: slice,
    ):
        self._parent = parent
        self._x_slice = x_slice
        self._y_slice = y_slice
        self._z_slice = z_slice

        # Compute view properties
        nx_full, ny_full, nz_full = parent.grid_shape
        self._x_start = x_slice.start or 0
        self._x_stop = x_slice.stop or nx_full
        self._y_start = y_slice.start or 0
        self._y_stop = y_slice.stop or ny_full
        self._z_start = z_slice.start or 0
        self._z_stop = z_slice.stop or nz_full

    @property
    def parent(self) -> "SpatialGrid":
        return self._parent

    @property
    def grid_shape(self) -> tuple[int, int, int]:
        return (
            self._x_stop - self._x_start,
            self._y_stop - self._y_start,
            self._z_stop - self._z_start,
        )

    @property
    def box_bounds(self) -> tuple[float, float, float, float, float, float]:
        """Box bounds for this view."""
        p = self._parent
        cs_x, cs_y, cs_z = p.cell_size
        xlo, _, ylo, _, zlo, _ = p.box_bounds
        return (
            xlo + self._x_start * cs_x,
            xlo + self._x_stop * cs_x,
            ylo + self._y_start * cs_y,
            ylo + self._y_stop * cs_y,
            zlo + self._z_start * cs_z,
            zlo + self._z_stop * cs_z,
        )

    @property
    def counts(self) -> NDArray[np.uint32]:
        """Atom counts for cells in this view."""
        return self._parent.counts[
            :, self._x_slice, self._y_slice, self._z_slice
        ]

    @property
    def n_timesteps(self) -> int:
        return self._parent.n_timesteps

    @property
    def cell_size(self) -> tuple[float, float, float]:
        return self._parent.cell_size

    def __repr__(self) -> str:
        return (
            f"GridView(shape={self.grid_shape}, bounds={self.box_bounds}, "
            f"parent={self._parent!r})"
        )


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
    def _aggregate_field_numba(
        cell_indices: NDArray[np.int64],
        field_data: NDArray[np.float64],
        n_cells: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Compute sum/min/max per cell in single pass (numba accelerated)."""
        sums = np.zeros(n_cells, dtype=np.float64)
        mins = np.full(n_cells, np.inf, dtype=np.float64)
        maxs = np.full(n_cells, -np.inf, dtype=np.float64)

        for i in range(len(cell_indices)):
            cell = cell_indices[i]
            val = field_data[i]
            sums[cell] += val
            if val < mins[cell]:
                mins[cell] = val
            if val > maxs[cell]:
                maxs[cell] = val

        # Set min/max to 0 for empty cells (where min=inf, max=-inf)
        for i in range(n_cells):
            if mins[i] == np.inf:
                mins[i] = 0.0
                maxs[i] = 0.0

        return sums, mins, maxs

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
    _aggregate_field = _aggregate_field_numba
else:
    # Fall back to numpy versions
    _compute_cell_indices = _compute_cell_indices_numpy
    _count_per_cell = _count_per_cell_numpy
    _compute_offsets = _compute_offsets_numpy
    _build_sort_indices = _build_sort_indices_numpy

    def _aggregate_field_numpy(
        cell_indices: NDArray[np.int64],
        field_data: NDArray[np.float64],
        n_cells: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Compute sum/min/max per cell (numpy fallback)."""
        sums = np.bincount(cell_indices, weights=field_data, minlength=n_cells).astype(np.float64)
        mins = np.full(n_cells, np.inf, dtype=np.float64)
        maxs = np.full(n_cells, -np.inf, dtype=np.float64)
        for cell, val in zip(cell_indices, field_data):
            if val < mins[cell]:
                mins[cell] = val
            if val > maxs[cell]:
                maxs[cell] = val
        # Set empty cells to 0
        empty = mins == np.inf
        mins[empty] = 0.0
        maxs[empty] = 0.0
        return sums, mins, maxs

    _aggregate_field = _aggregate_field_numpy


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
        Box boundaries (xlo, xhi, ylo, yhi, zlo, zhi). Computed from data + padding.
    grid_shape : tuple[int, int, int]
        Number of cells in each spatial dimension (nx, ny, nz).
    n_atoms : int
        Number of atoms per timestep.
    n_timesteps : int
        Number of timesteps in the trajectory.
    timestep_values : tuple[int, ...]
        Actual timestep values from the trajectory file.
    source_box : SourceBox
        Original box info from source file (bounds, tilt, boundary conditions).
    cells : CellsAccessor
        Accessor for precomputed cell-level aggregates (sum/min/max/mean per cell).
    """

    cell_size: tuple[float, float, float]
    box_bounds: tuple[float, ...]
    grid_shape: tuple[int, int, int]
    n_atoms: int
    n_timesteps: int = 1
    timestep_values: tuple[int, ...] = (0,)
    source_box: SourceBox = field(default_factory=SourceBox)
    use_units: bool = False
    _file: h5py.File | None = field(default=None, repr=False)
    _offsets: NDArray[np.uint64] | None = field(default=None, repr=False)
    _counts: NDArray[np.uint32] | None = field(default=None, repr=False)
    _fields_cache: dict[str, NDArray] = field(default_factory=dict, repr=False)
    _cells: CellsAccessor | None = field(default=None, repr=False)
    _field_units: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def cells(self) -> CellsAccessor:
        """Accessor for precomputed cell-level aggregates."""
        if self._cells is None:
            # Use raw counts (without units) for CellsAccessor
            counts_raw = self._counts if self._counts is not None else self._file[f"{_CSR_GROUP}/counts"][:]
            cs_x, cs_y, cs_z = self.cell_size
            cell_volume = cs_x * cs_y * cs_z
            self._cells = CellsAccessor(counts_raw, {}, self._file, cell_volume=cell_volume)
        return self._cells

    @property
    def _grid_origin(self) -> tuple[float, float, float]:
        """Grid origin (xlo, ylo, zlo) for snapping regions."""
        xlo, _, ylo, _, zlo, _ = self.box_bounds
        return (xlo, ylo, zlo)

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
    def counts(self) -> NDArray[np.uint32] | Quantity:
        """Atom counts per cell (n_timesteps, nx, ny, nz), lazy loaded from HDF5."""
        if self._counts is None:
            if self._file is not None:
                self._counts = self._file[f"{_CSR_GROUP}/counts"][:]
            else:
                raise ValueError("No counts available (grid not loaded or built)")
        if self.use_units:
            return Q_(self._counts, ureg.dimensionless)
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

    def __getitem__(self, key: str) -> NDArray | h5py.Dataset | Quantity:
        """
        Access a field by name.

        Returns h5py.Dataset (lazy) if loaded from file, or numpy array if in memory.
        If use_units=True, wraps the result in a pint Quantity with appropriate units.
        """
        if self._file is not None:
            data = self._file[f"{_FIELDS_GROUP}/{key}"]
        elif key in self._fields_cache:
            data = self._fields_cache[key]
        else:
            raise KeyError(f"Field '{key}' not found")

        if self.use_units:
            # Get unit from stored metadata or infer from field name
            unit_str = self._field_units.get(key)
            unit = ureg.Unit(unit_str) if unit_str else get_unit(key)
            # For h5py.Dataset, we need to load it first to attach units
            if isinstance(data, h5py.Dataset):
                data = data[:]
            return Q_(data, unit)
        return data

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

    def _region_to_cell_slices(
        self, region: Region
    ) -> tuple[tuple[slice, slice, slice], tuple[slice, slice, slice]]:
        """
        Convert region to outer and inner cell index slices.

        Uses Region.snap_to_grid() for clean coordinate-to-index conversion.

        Parameters
        ----------
        region : Region
            Query region with x, y, z spatial bounds.

        Returns
        -------
        outer_slices : tuple[slice, slice, slice]
            Cell slices for all cells overlapping the region (snap outward).
        inner_slices : tuple[slice, slice, slice]
            Cell slices for cells fully interior to the region (snap inward).
            May be empty (stop <= start) if no interior cells exist.
        """
        outer = region.snap_to_grid(self.cell_size, self._grid_origin, "outward")
        inner = region.snap_to_grid(self.cell_size, self._grid_origin, "inward")

        outer_slices = outer.to_cell_slices(self.cell_size, self._grid_origin, self.grid_shape)
        inner_slices = inner.to_cell_slices(self.cell_size, self._grid_origin, self.grid_shape)

        return outer_slices, inner_slices

    def _has_interior_cells(self, inner_slices: tuple[slice, slice, slice]) -> bool:
        """Check if inner slices represent a non-empty region."""
        return all(s.stop > s.start for s in inner_slices)

    def _get_atom_slices_for_cells(
        self,
        t_idx: int,
        cell_slices: tuple[slice, slice, slice],
    ) -> list[tuple[int, int]]:
        """
        Get contiguous atom slices for cells in a 3D slice range at a specific timestep.

        Parameters
        ----------
        t_idx : int
            Timestep index (0-based).
        cell_slices : tuple[slice, slice, slice]
            Cell index slices (x, y, z).

        Returns
        -------
        list of (start, end) tuples
            Contiguous slices for atoms in the cells (global indices).
        """
        sx, sy, sz = cell_slices
        ny, nz = self.grid_shape[1], self.grid_shape[2]

        # Load only this timestep's offsets/counts (lazy per-timestep)
        if self._file is not None:
            offsets_t = self._file[f"{_CSR_GROUP}/offsets"][t_idx]
            counts_t = self._file[f"{_CSR_GROUP}/counts"][t_idx]
        else:
            offsets_t = self._offsets[t_idx]
            counts_t = self._counts[t_idx]

        t_offset = t_idx * self.n_atoms
        slices = []

        for ix in range(sx.start, sx.stop):
            for iy in range(sy.start, sy.stop):
                for iz in range(sz.start, sz.stop):
                    start = int(offsets_t[ix, iy, iz])
                    count = int(counts_t[ix, iy, iz])
                    if count > 0:
                        slices.append((start + t_offset, start + count + t_offset))

        return _merge_slices(slices)

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
        fields: list[str] | str | None = None,
        cell_level: bool = False,
        reduce: Literal["sum", "mean", "min", "max"] | None = None,
        axis: str | int | list[str | int] | None = None,
        snap: bool = False,
    ) -> dict[str, NDArray] | NDArray | float:
        """
        Query atoms or cell aggregates within a 4D region (space + time).

        Parameters
        ----------
        region : Region, optional
            4D query region with x, y, z spatial bounds and t time bounds.
            If None, returns all atoms across all timesteps.
        fields : str, list[str], optional
            Fields to return. If None, returns all fields.
        cell_level : bool, default False
            If True, return all atoms in overlapping cells (faster but less precise).
        reduce : {'sum', 'mean', 'min', 'max'}, optional
            If specified, return aggregates instead of atom data.
        axis : str, int, or list thereof, optional
            Axes to reduce over (only with reduce). None = scalar result.
        snap : bool, default False
            If True with reduce, snap to cell boundaries for pure O(1) queries.

        Returns
        -------
        dict[str, ndarray] | ndarray | float
            Atom data dict, or reduced scalar/array.
        """
        # Normalize inputs
        region = Region() if region is None else ensure_region(region)
        t_indices, t_values = self._timesteps_from_region(region)

        # Get cell slices
        outer_slices, inner_slices = self._region_to_cell_slices(region)
        sx, sy, sz = outer_slices
        has_interior = self._has_interior_cells(inner_slices)
        hull_slices_list = boundary_slices(outer_slices, inner_slices)
        has_boundary = bool(hull_slices_list) or not has_interior

        # =====================================================================
        # REDUCTION QUERIES
        # =====================================================================
        if reduce is not None:
            single_field = isinstance(fields, str)
            field_list = (
                self.cells.fields if fields is None
                else [fields] if single_field
                else list(fields)
            )

            # Validate fields
            for f in field_list:
                if f not in self.cells:
                    raise KeyError(f"No cell aggregates for field '{f}'")

            # Empty region check
            if not t_indices or sx.stop <= sx.start or sy.stop <= sy.start or sz.stop <= sz.start:
                result = {f: 0.0 for f in field_list}
                return result[fields] if single_field else result

            t_min, t_max = min(t_indices), max(t_indices)

            # Fast path: snap=True, axis reduction, or no boundary cells
            if snap or axis is not None or not has_boundary:
                result: dict[str, NDArray | float] = {}

                for field_name in field_list:
                    agg = self.cells[field_name]

                    if reduce == "mean":
                        sum_slice = agg._sum[t_min:t_max+1, sx, sy, sz]
                        counts_slice = self._counts[t_min:t_max+1, sx, sy, sz]

                        if axis is None:
                            total_sum, total_count = sum_slice.sum(), counts_slice.sum()
                            result[field_name] = total_sum / total_count if total_count > 0 else 0.0
                        else:
                            axis_tuple = tuple(_normalize_axis(axis) or [])
                            sum_reduced = sum_slice.sum(axis=axis_tuple)
                            counts_reduced = counts_slice.astype(np.float64).sum(axis=axis_tuple)
                            result[field_name] = _safe_divide(sum_reduced, counts_reduced)
                            if np.ndim(result[field_name]) == 0:
                                result[field_name] = float(result[field_name])
                    else:
                        data_slice = getattr(agg, f"_{reduce}")[t_min:t_max+1, sx, sy, sz]
                        if axis is None:
                            result[field_name] = float(getattr(data_slice, reduce)())
                        else:
                            axis_tuple = tuple(_normalize_axis(axis) or [])
                            reduced = getattr(data_slice, reduce)(axis=axis_tuple)
                            result[field_name] = float(reduced) if np.ndim(reduced) == 0 else reduced

                return result[fields] if single_field else result

            # Slow path: interior cells (precomputed) + boundary atoms (filtered)
            result_reduce: dict[str, float] = {}
            isx, isy, isz = inner_slices

            for field_name in field_list:
                agg = self.cells[field_name]

                # Interior contribution
                int_sum, int_count, int_min, int_max = 0.0, 0, np.inf, -np.inf
                if has_interior:
                    if reduce in ("sum", "mean"):
                        int_sum = float(agg._sum[t_min:t_max+1, isx, isy, isz].sum())
                    if reduce == "mean":
                        int_count = int(self._counts[t_min:t_max+1, isx, isy, isz].sum())
                    if reduce == "min":
                        slice_data = agg._min[t_min:t_max+1, isx, isy, isz]
                        counts_slice = self._counts[t_min:t_max+1, isx, isy, isz]
                        non_empty = counts_slice > 0
                        if non_empty.any():
                            int_min = float(slice_data[non_empty].min())
                    if reduce == "max":
                        slice_data = agg._max[t_min:t_max+1, isx, isy, isz]
                        counts_slice = self._counts[t_min:t_max+1, isx, isy, isz]
                        non_empty = counts_slice > 0
                        if non_empty.any():
                            int_max = float(slice_data[non_empty].max())

                # Boundary contribution (read atoms, filter, aggregate)
                bnd_sum, bnd_count, bnd_min, bnd_max = 0.0, 0, np.inf, -np.inf
                for hull_slice in hull_slices_list:
                    for t_idx in t_indices:
                        atom_slices = self._get_atom_slices_for_cells(t_idx, hull_slice)
                        if atom_slices:
                            coords = self._read_slices("coords", atom_slices)
                            data = self._read_slices(field_name, atom_slices)
                            mask = self._filter_by_bounds(region, coords)
                            filtered = data[mask]
                            if len(filtered) > 0:
                                if reduce in ("sum", "mean"):
                                    bnd_sum += float(filtered.sum())
                                if reduce == "mean":
                                    bnd_count += len(filtered)
                                if reduce == "min":
                                    bnd_min = min(bnd_min, float(filtered.min()))
                                if reduce == "max":
                                    bnd_max = max(bnd_max, float(filtered.max()))

                # Combine
                if reduce == "sum":
                    result_reduce[field_name] = int_sum + bnd_sum
                elif reduce == "mean":
                    total = int_sum + bnd_sum
                    cnt = int_count + bnd_count
                    result_reduce[field_name] = total / cnt if cnt > 0 else 0.0
                elif reduce == "min":
                    val = min(int_min, bnd_min)
                    result_reduce[field_name] = 0.0 if val == np.inf else val
                elif reduce == "max":
                    val = max(int_max, bnd_max)
                    result_reduce[field_name] = 0.0 if val == -np.inf else val

            return result_reduce[fields] if single_field else result_reduce

        # =====================================================================
        # ATOM-LEVEL QUERIES
        # =====================================================================
        if fields is None:
            fields = self.fields

        # Collect atom slices
        all_interior_slices: list[tuple[int, int]] = []
        all_boundary_slices: list[tuple[int, int]] = []
        interior_ts_counts: list[tuple[int, int]] = []
        boundary_ts_counts: list[tuple[int, int]] = []

        for t_idx, t_val in zip(t_indices, t_values):
            if has_interior:
                slices = self._get_atom_slices_for_cells(t_idx, inner_slices)
                if slices:
                    all_interior_slices.extend(slices)
                    interior_ts_counts.append((t_val, sum(e - s for s, e in slices)))

            for hull_slice in hull_slices_list:
                slices = self._get_atom_slices_for_cells(t_idx, hull_slice)
                if slices:
                    all_boundary_slices.extend(slices)
                    boundary_ts_counts.append((t_val, sum(e - s for s, e in slices)))

        # Empty result
        if not all_interior_slices and not all_boundary_slices:
            result = {name: np.array([], dtype=self[name].dtype) for name in fields}
            result["_timestep"] = np.array([], dtype=np.int64)
            return result

        def build_ts_array(ts_counts):
            if not ts_counts:
                return np.array([], dtype=np.int64)
            parts = [np.full(c, v, dtype=np.int64) for v, c in ts_counts]
            return np.concatenate(parts) if len(parts) > 1 else parts[0]

        # Read interior
        interior_data: dict[str, NDArray] = {}
        if all_interior_slices:
            for name in fields:
                interior_data[name] = self._read_slices(name, all_interior_slices)
            interior_data["_timestep"] = build_ts_array(interior_ts_counts)

        # Read boundary (with optional filtering)
        boundary_data: dict[str, NDArray] = {}
        if all_boundary_slices:
            for name in fields:
                boundary_data[name] = self._read_slices(name, all_boundary_slices)
            boundary_data["_timestep"] = build_ts_array(boundary_ts_counts)

            if not cell_level:
                coords = boundary_data["coords"] if "coords" in boundary_data else self._read_slices("coords", all_boundary_slices)
                mask = self._filter_by_bounds(region, coords)
                for name in list(fields) + ["_timestep"]:
                    boundary_data[name] = boundary_data[name][mask]

        # Combine
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
                result[name] = np.array([], dtype=self[name].dtype if name in fields else np.int64)

        # Units
        if self.use_units:
            for name in result:
                unit = ureg.dimensionless if name == "_timestep" else (
                    ureg.Unit(self._field_units.get(name)) if name in self._field_units else get_unit(name)
                )
                result[name] = Q_(result[name], unit)

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

        # Get outer cell slices (all overlapping cells)
        outer_slices, _ = self._region_to_cell_slices(region)
        sx, sy, sz = outer_slices

        result = []
        for t_idx in t_indices:
            # Sum counts over the cell slice
            if self._file is not None:
                counts_slice = self._file[f"{_CSR_GROUP}/counts"][t_idx, sx, sy, sz]
            else:
                counts_slice = self._counts[t_idx, sx, sy, sz]

            total = int(counts_slice.sum())
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
        use_units: bool = False,
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
        use_units : bool, default True
            If True, field accessors return pint Quantities with units attached.
            If False, returns plain numpy arrays (faster, less memory).
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

        # Identify numeric fields for aggregation
        numeric_fields = [
            name for name, data_list in fields_list.items()
            if _is_numeric_field(data_list[0]) and data_list[0].ndim == 1
        ]

        total_atoms = n_timesteps * n_atoms
        logger.info("Building spatial grid for %d timesteps, %d atoms each (%d total)", n_timesteps, n_atoms, total_atoms)

        show_progress = total_atoms >= TQDM_ATOM_THRESHOLD

        # Pre-allocate all output arrays (avoids list appending + concatenation)
        offsets = np.empty((n_timesteps,) + grid_shape, dtype=np.uint64)
        counts = np.empty((n_timesteps,) + grid_shape, dtype=np.uint32)
        source_idx = np.empty(total_atoms, dtype=np.uint32)
        coords_sorted = np.empty((total_atoms, 3), dtype=np.float32)
        fields_sorted: dict[str, NDArray] = {}
        for name, data_list in fields_list.items():
            fields_sorted[name] = np.empty((total_atoms,) + data_list[0].shape[1:], dtype=data_list[0].dtype)

        # Pre-allocate aggregate arrays
        agg_sum: dict[str, NDArray] = {name: np.empty((n_timesteps,) + grid_shape, dtype=np.float64) for name in numeric_fields}
        agg_min: dict[str, NDArray] = {name: np.empty((n_timesteps,) + grid_shape, dtype=np.float64) for name in numeric_fields}
        agg_max: dict[str, NDArray] = {name: np.empty((n_timesteps,) + grid_shape, dtype=np.float64) for name in numeric_fields}

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
        atom_range = np.arange(n_atoms, dtype=np.uint32)

        for t in range(n_timesteps):
            coords_t = coords_list[t]
            t_start = t * n_atoms
            t_end = t_start + n_atoms

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

            # Compute aggregates for numeric fields (using cell_indices, before sorting)
            for name in numeric_fields:
                field_t = fields_list[name][t].astype(np.float64, copy=False)
                sums, mins, maxs = _aggregate_field(cell_indices, field_t, n_cells)
                agg_sum[name][t] = sums.reshape(grid_shape)
                agg_min[name][t] = mins.reshape(grid_shape)
                agg_max[name][t] = maxs.reshape(grid_shape)

            # Write directly into pre-allocated arrays
            offsets[t] = offsets_flat.reshape(grid_shape)
            counts[t] = counts_flat.reshape(grid_shape)
            source_idx[t_start:t_end] = atom_range[sort_indices]
            coords_sorted[t_start:t_end] = coords_t[sort_indices]

            for name, data_list in fields_list.items():
                fields_sorted[name][t_start:t_end] = data_list[t][sort_indices]

            pbar.update(n_atoms)

        pbar.close()

        # Build fields cache (no copying needed - arrays already in final form)
        fields_cache = {"_source_idx": source_idx, "coords": coords_sorted}
        fields_cache.update(fields_sorted)

        # Calculate cell volume for density computations
        cell_volume = cs_x * cs_y * cs_z

        # Build all cumsums with shared progress bar
        counts_cumsum, field_cumsums = _build_all_cumsums(counts, agg_sum, numeric_fields)

        # Build cell aggregates
        cell_aggregates: dict[str, FieldAggregates] = {}
        for name in numeric_fields:
            cell_aggregates[name] = FieldAggregates(
                _sum=agg_sum[name],
                _min=agg_min[name],
                _max=agg_max[name],
                _cumsum=field_cumsums[name],
                _counts_ref=counts,
                _counts_cumsum=counts_cumsum,
                _cell_volume=cell_volume,
            )

        cells_accessor = CellsAccessor(counts, cell_aggregates, None, counts_cumsum, cell_volume)

        # Build field units mapping
        field_units = {name: str(get_unit(name)) for name in fields_cache}

        return cls(
            cell_size=cell_sizes,
            box_bounds=box_bounds,
            grid_shape=grid_shape,
            n_atoms=n_atoms,
            n_timesteps=n_timesteps,
            timestep_values=tuple(timestep_values),
            use_units=use_units,
            _offsets=offsets,
            _counts=counts,
            _fields_cache=fields_cache,
            _cells=cells_accessor,
            _field_units=field_units,
        )

    @classmethod
    def from_lammps(
        cls,
        path: str | Path,
        cell_size: CellSize = DEFAULT_CELL_SIZE,
        timesteps: list[int] | slice | None = None,
        columns: dict[str, int] | None = None,
        coord_type: CoordType = "auto",
        trim_to_source_box: bool = False,
        use_units: bool = False,
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
        trim_to_source_box : bool, default False
            If True, filter out atoms outside the LAMMPS box bounds and use
            the source box bounds as the grid bounds. Useful for unwrapped
            coordinates that extend beyond the simulation box.
        use_units : bool, default True
            If True, field accessors return pint Quantities with units attached.
            If False, returns plain numpy arrays (faster, less memory).

        Returns
        -------
        SpatialGrid
            Grid built from the LAMMPS data.
        """
        from atomkit.io.lammps import parse_lammps

        coords_list, fields_list, selected_timesteps, box_info = parse_lammps(
            path, timesteps=timesteps, columns=columns, coord_type=coord_type
        )

        # Build SourceBox early for trim logic
        source_box = SourceBox()
        if box_info.get("bounds"):
            source_box = SourceBox(
                bounds=tuple(box_info["bounds"]),
                tilt=tuple(box_info["tilt"]) if box_info.get("tilt") else None,
                boundary=box_info.get("boundary", ""),
            )

        # Trim atoms outside source box if requested
        box_bounds = None
        if trim_to_source_box and source_box.is_valid:
            xlo, xhi, ylo, yhi, zlo, zhi = source_box.bounds
            box_bounds = source_box.bounds  # Use source box as grid bounds

            # Filter atoms per timestep
            original_count = len(coords_list[0]) if coords_list else 0
            filtered_coords = []
            filtered_fields: dict[str, list] = {name: [] for name in fields_list}

            for t, coords_t in enumerate(coords_list):
                # Vectorized bounds check (works for both orthogonal and triclinic
                # since source_box.bounds stores the bounding box)
                mask = (
                    (coords_t[:, 0] >= xlo) & (coords_t[:, 0] <= xhi) &
                    (coords_t[:, 1] >= ylo) & (coords_t[:, 1] <= yhi) &
                    (coords_t[:, 2] >= zlo) & (coords_t[:, 2] <= zhi)
                )

                filtered_coords.append(coords_t[mask])
                for name, data_list in fields_list.items():
                    filtered_fields[name].append(data_list[t][mask])

            # Validate that all timesteps have the same atom count after filtering
            # (required by from_arrays which expects consistent n_atoms)
            filtered_counts = [len(c) for c in filtered_coords]
            if filtered_coords and len(set(filtered_counts)) > 1:
                min_count, max_count = min(filtered_counts), max(filtered_counts)
                raise ValueError(
                    f"trim_to_source_box: atom counts vary across timesteps after filtering "
                    f"(min={min_count}, max={max_count}). This happens when atoms move in/out "
                    f"of the source box. Consider disabling trim_to_source_box or ensuring "
                    f"all atoms stay within the box bounds."
                )

            filtered_count = filtered_counts[0] if filtered_counts else 0
            coords_list = filtered_coords
            fields_list = filtered_fields

            logger.info(
                "Trimmed to source box: %d -> %d atoms",
                original_count,
                filtered_count,
            )

        grid = cls.from_arrays(
            coords=coords_list,
            box_bounds=box_bounds,
            cell_size=cell_size,
            timestep_values=selected_timesteps,
            use_units=use_units,
            **fields_list,
        )

        grid.source_box = source_box
        return grid

    @classmethod
    def _migrate_add_cell_aggregates(
        cls,
        path: Path,
        grid_shape: tuple[int, int, int],
        n_timesteps: int,
        n_atoms: int,
    ) -> h5py.File:
        """
        Migrate old HDF5 files by computing and saving cell aggregates.

        Called automatically when loading a file without the _cells group.
        Returns the file handle reopened in read mode.
        """
        logger.info("Migrating %s: computing cell aggregates...", path)

        # Reopen in r+ mode to add data
        f = h5py.File(path, "r+")

        try:
            # Load required data
            counts = f[f"{_CSR_GROUP}/counts"][:]
            offsets = f[f"{_CSR_GROUP}/offsets"][:]
            fields_grp = f[_FIELDS_GROUP]

            # Build counts_cumsum for mean computation
            counts_cumsum = _build_cumsum_4d(counts.astype(np.float64)).astype(np.uint64)

            # Store counts_cumsum in CSR group
            if "_counts_cumsum" not in f[_CSR_GROUP]:
                f[_CSR_GROUP].create_dataset("_counts_cumsum", data=counts_cumsum)

            # Find numeric fields (excluding internal ones)
            numeric_fields = []
            for name in fields_grp.keys():
                if name.startswith("_") or name == "coords":
                    continue
                data = fields_grp[name]
                if _is_numeric_field(data):
                    numeric_fields.append(name)

            if not numeric_fields:
                logger.info("No numeric fields to aggregate")
                f.close()
                return h5py.File(path, "r")

            # Create _cells group and compute aggregates
            cells_grp = f.create_group("_cells")

            n_cells = np.prod(grid_shape) * n_timesteps
            show_progress = n_cells >= TQDM_ATOM_THRESHOLD
            pbar = tqdm(numeric_fields, desc="Migrating fields", disable=not show_progress)

            for name in pbar:
                pbar.set_postfix(field=name)
                field_data = fields_grp[name][:]

                agg = _compute_cell_aggregates(
                    field_data, counts, offsets, grid_shape, n_timesteps, n_atoms,
                    counts_cumsum=counts_cumsum,
                )

                field_grp = cells_grp.create_group(name)
                field_grp.create_dataset("sum", data=agg._sum)
                field_grp.create_dataset("min", data=agg._min)
                field_grp.create_dataset("max", data=agg._max)
                if agg._cumsum is not None:
                    field_grp.create_dataset("cumsum", data=agg._cumsum)

            f.flush()
            logger.info("Migration complete: added aggregates for %d fields", len(numeric_fields))

        except Exception:
            f.close()
            raise

        # Close and reopen in read mode
        f.close()
        return h5py.File(path, "r")

    @classmethod
    def load(cls, path: str | Path, use_units: bool = False) -> SpatialGrid:
        """
        Load a SpatialGrid from an HDF5 file.

        The file is opened in read mode with lazy loading (data read on demand).

        Parameters
        ----------
        path : str or Path
            Path to the HDF5 file.
        use_units : bool, default True
            If True, field accessors return pint Quantities with units attached.
            If False, returns plain numpy arrays (faster, less memory).

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

            # Handle cell_size: old format (scalar) vs new format (array)
            raw_cell_size = attrs["cell_size"]
            if np.ndim(raw_cell_size) == 0:
                cs = float(raw_cell_size)
                cell_size = (cs, cs, cs)
            else:
                cell_size = tuple(float(x) for x in raw_cell_size)

            box_bounds = tuple(attrs["box_bounds"])
            grid_shape = tuple(attrs["grid_shape"])
            n_atoms = int(attrs["n_atoms"])
            n_timesteps = int(attrs.get("n_timesteps", 1))
            timestep_values = tuple(attrs.get("timestep_values", [0]))

            # Source box info (optional, for backward compatibility)
            source_box_bounds = None
            source_box_tilt = None
            source_box_boundary = ""
            if "source_box_bounds" in attrs:
                source_box_bounds = tuple(attrs["source_box_bounds"])
            if "source_box_tilt" in attrs:
                source_box_tilt = tuple(attrs["source_box_tilt"])
            if "source_box_boundary" in attrs:
                raw_boundary = attrs["source_box_boundary"]
                source_box_boundary = raw_boundary.decode("utf-8") if isinstance(raw_boundary, bytes) else str(raw_boundary)

            source_box = SourceBox(
                bounds=source_box_bounds,
                tilt=source_box_tilt,
                boundary=source_box_boundary,
            )
        except Exception:
            f.close()
            raise

        logger.debug("Loaded grid from %s: %d timesteps, %d atoms", path, n_timesteps, n_atoms)

        # Migrate old files: compute cell aggregates if missing
        if "_cells" not in f:
            f.close()
            f = cls._migrate_add_cell_aggregates(
                path, grid_shape, n_timesteps, n_atoms
            )

        # Load field units from file or infer from field names
        field_units = {}
        if "_field_units" in f.attrs:
            import json
            field_units = json.loads(f.attrs["_field_units"])
        else:
            # Infer from field names
            if _FIELDS_GROUP in f:
                for name in f[_FIELDS_GROUP].keys():
                    field_units[name] = str(get_unit(name))

        return cls(
            cell_size=cell_size,
            box_bounds=box_bounds,
            grid_shape=grid_shape,
            n_atoms=n_atoms,
            n_timesteps=n_timesteps,
            timestep_values=timestep_values,
            source_box=source_box,
            use_units=use_units,
            _file=f,
            _field_units=field_units,
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

        # Count datasets for progress bar
        n_datasets = 2 + len(self._fields_cache)  # offsets, counts, fields
        if self._cells is not None and self._cells._aggregates:
            # sum/min/max/cumsum per field + counts_cumsum
            n_datasets += len(self._cells._aggregates) * 4 + 1

        total_atoms = self.n_timesteps * self.n_atoms
        show_progress = total_atoms >= TQDM_ATOM_THRESHOLD

        with h5py.File(path, "w") as f:
            # Store metadata as attributes
            f.attrs["cell_size"] = np.array(self.cell_size)
            f.attrs["box_bounds"] = np.array(self.box_bounds)
            f.attrs["grid_shape"] = np.array(self.grid_shape)
            f.attrs["n_atoms"] = self.n_atoms
            f.attrs["n_timesteps"] = self.n_timesteps
            f.attrs["timestep_values"] = np.array(self.timestep_values)

            # Source box info (consolidated SourceBox)
            if self.source_box.is_valid:
                f.attrs["source_box_bounds"] = np.array(self.source_box.bounds)
            if self.source_box.tilt is not None:
                f.attrs["source_box_tilt"] = np.array(self.source_box.tilt)
            if self.source_box.boundary:
                f.attrs["source_box_boundary"] = self.source_box.boundary

            # Field units (store as JSON for flexibility)
            if self._field_units:
                import json
                f.attrs["_field_units"] = json.dumps(self._field_units)

            pbar = tqdm(total=n_datasets, desc="Saving HDF5", disable=not show_progress)

            # CSR structure (4D: n_timesteps, nx, ny, nz)
            # Use raw arrays (strip units if present)
            csr = f.create_group(_CSR_GROUP)
            csr.create_dataset("offsets", data=strip_units(self.offsets), **compression_opts)
            pbar.update(1)
            csr.create_dataset("counts", data=strip_units(self.counts), **compression_opts)
            pbar.update(1)

            # Fields (concatenated: [t0_atoms, t1_atoms, ...])
            fields_grp = f.create_group(_FIELDS_GROUP)
            for name, data in self._fields_cache.items():
                fields_grp.create_dataset(name, data=data, **compression_opts)
                pbar.update(1)

            # Cell aggregates (precomputed sum/min/max/cumsum per cell)
            if self._cells is not None and self._cells._aggregates:
                # Store counts_cumsum for mean computation
                if self._cells._counts_cumsum is not None:
                    csr.create_dataset("_counts_cumsum", data=self._cells._counts_cumsum, **compression_opts)
                    pbar.update(1)

                cells_grp = f.create_group("_cells")
                for name, agg in self._cells._aggregates.items():
                    field_grp = cells_grp.create_group(name)
                    field_grp.create_dataset("sum", data=agg._sum, **compression_opts)
                    pbar.update(1)
                    field_grp.create_dataset("min", data=agg._min, **compression_opts)
                    pbar.update(1)
                    field_grp.create_dataset("max", data=agg._max, **compression_opts)
                    pbar.update(1)
                    # Store cumsum for O(1) region queries
                    if agg._cumsum is not None:
                        field_grp.create_dataset("cumsum", data=agg._cumsum, **compression_opts)
                        pbar.update(1)

            pbar.close()

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
    # Views and Slicing
    # -------------------------------------------------------------------------

    def view(
        self,
        x: tuple[float, float] | None = None,
        y: tuple[float, float] | None = None,
        z: tuple[float, float] | None = None,
    ) -> GridView:
        """
        Create a view into a subregion of the grid.

        The view shares the underlying data (no copy) and provides a subset
        of cells within the specified bounds.

        Parameters
        ----------
        x, y, z : tuple[float, float], optional
            Coordinate bounds (min, max) for each axis. None = full extent.

        Returns
        -------
        GridView
            A view constrained to the specified region.

        Examples
        --------
        >>> view = grid.view(x=(0, 50), z=(10, 100))
        >>> view.counts  # Only cells within bounds
        >>> view.box_bounds  # Adjusted bounds
        """
        cs_x, cs_y, cs_z = self.cell_size
        xlo, xhi, ylo, yhi, zlo, zhi = self.box_bounds
        nx, ny, nz = self.grid_shape

        def to_slice(bounds: tuple[float, float] | None, lo: float, cs: float, n: int) -> slice:
            if bounds is None:
                return slice(None)
            bmin, bmax = bounds
            i_min = max(0, int((bmin - lo) / cs))
            i_max = min(n, int(np.ceil((bmax - lo) / cs)))
            return slice(i_min, i_max)

        x_slice = to_slice(x, xlo, cs_x, nx)
        y_slice = to_slice(y, ylo, cs_y, ny)
        z_slice = to_slice(z, zlo, cs_z, nz)

        return GridView(self, x_slice, y_slice, z_slice)

    def view_source_box(self) -> GridView | None:
        """
        Create a view constrained to the source box bounds.

        Returns None if source_box is not defined.
        """
        if not self.source_box.is_valid:
            return None
        xlo, xhi, ylo, yhi, zlo, zhi = self.source_box.bounds
        return self.view(x=(xlo, xhi), y=(ylo, yhi), z=(zlo, zhi))

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
