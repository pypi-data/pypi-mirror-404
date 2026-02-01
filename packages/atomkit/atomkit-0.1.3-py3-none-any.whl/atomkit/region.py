"""
Region definition and manipulation for 4D (space + time) queries.

Regions support flexible bounds specification:
- Tuple (min, max): explicit range
- Single value: slice at that point (cells intersecting that coordinate)
- None or omitted: unbounded (-inf, inf)

Examples
--------
>>> Region(x=(0, 10), y=(0, 10), z=(0, 10))  # Spatial box, all timesteps
>>> Region(x=5.0)  # Slice at x=5, all y/z/t
>>> Region(t=100)  # Single timestep 100, all space
>>> Region(x=(0, 10), t=(0, 1000))  # 4D region
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator

# Infinity constants
INF = math.inf
NEG_INF = -math.inf

# Type for axis bounds: tuple, single value, or None
AxisBounds = tuple[float, float] | float | None

# Legacy tuple format for backwards compatibility
RegionTuple = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]


def _normalize_bounds(value: AxisBounds, axis: str = "") -> tuple[float, float]:
    """
    Normalize axis bounds to (min, max) tuple.

    - None -> (-inf, inf)
    - Single value -> (value, value) for point/slice queries
    - Tuple -> pass through with validation
    """
    if value is None:
        return (NEG_INF, INF)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = float(value)
        if math.isnan(v):
            raise ValueError(f"Bounds for {axis or 'axis'} cannot be NaN")
        return (v, v)
    if isinstance(value, tuple) and len(value) == 2:
        lo, hi = float(value[0]), float(value[1])
        if math.isnan(lo) or math.isnan(hi):
            raise ValueError(f"Bounds for {axis or 'axis'} cannot be NaN")
        if lo > hi:
            raise ValueError(f"Invalid bounds for {axis or 'axis'}: min ({lo}) > max ({hi})")
        return (lo, hi)
    raise ValueError(f"Invalid bounds: {value!r}. Expected (min, max), single value, or None.")


@dataclass(frozen=True, slots=True)
class Region:
    """
    4D axis-aligned bounding box for space-time queries.

    Each axis can be specified as:
    - (min, max) tuple: explicit range
    - Single value: slice at that point (e.g., x=5.0 means cells containing x=5)
    - None (default): unbounded, matches everything

    For time axis (t), values are timestep VALUES (not indices).
    Single t value means exactly that timestep.

    Attributes
    ----------
    x, y, z : tuple[float, float]
        Spatial bounds (min, max) in Angstroms.
    t : tuple[float, float]
        Temporal bounds (min, max) as timestep values.

    Examples
    --------
    >>> Region(x=(0, 100), y=(-50, 50), z=(-10, 10))  # 3D box, all time
    >>> Region(x=5.0)  # YZ plane at x=5
    >>> Region(t=100)  # All space at timestep 100
    >>> Region(x=(0, 10), y=(0, 10), z=(0, 10), t=(0, 1000))  # Full 4D
    >>> Region()  # Everything (all space, all time)
    """

    x: tuple[float, float] = (NEG_INF, INF)
    y: tuple[float, float] = (NEG_INF, INF)
    z: tuple[float, float] = (NEG_INF, INF)
    t: tuple[float, float] = (NEG_INF, INF)

    def __init__(
        self,
        x: AxisBounds = None,
        y: AxisBounds = None,
        z: AxisBounds = None,
        t: AxisBounds = None,
    ):
        object.__setattr__(self, 'x', _normalize_bounds(x, 'x'))
        object.__setattr__(self, 'y', _normalize_bounds(y, 'y'))
        object.__setattr__(self, 'z', _normalize_bounds(z, 'z'))
        object.__setattr__(self, 't', _normalize_bounds(t, 't'))

    # -------------------------------------------------------------------------
    # Constructors
    # -------------------------------------------------------------------------

    @classmethod
    def from_tuple(cls, t: RegionTuple) -> Region:
        """Create Region from legacy 3D tuple format."""
        return cls(x=t[0], y=t[1], z=t[2])

    @classmethod
    def from_bounds(
        cls,
        xmin: float, xmax: float,
        ymin: float, ymax: float,
        zmin: float, zmax: float,
        tmin: float | None = None,
        tmax: float | None = None,
    ) -> Region:
        """Create Region from explicit min/max bounds."""
        t_bounds = None if tmin is None and tmax is None else (
            tmin if tmin is not None else NEG_INF,
            tmax if tmax is not None else INF,
        )
        return cls(
            x=(xmin, xmax),
            y=(ymin, ymax),
            z=(zmin, zmax),
            t=t_bounds,
        )

    @classmethod
    def everything(cls) -> Region:
        """Create region that matches everything (all space, all time)."""
        return cls()

    @classmethod
    def spatial(
        cls,
        x: AxisBounds = None,
        y: AxisBounds = None,
        z: AxisBounds = None,
    ) -> Region:
        """Create spatial-only region (all timesteps)."""
        return cls(x=x, y=y, z=z, t=None)

    @classmethod
    def at_time(cls, t: float | int) -> Region:
        """Create region for a single timestep (all space)."""
        return cls(t=t)

    def spatial_bounds(self) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        """Return just the spatial bounds as a 3-tuple (legacy format)."""
        return (self.x, self.y, self.z)

    # -------------------------------------------------------------------------
    # Geometric operations
    # -------------------------------------------------------------------------

    def volume(self) -> float:
        """
        Calculate spatial volume of the region.

        Returns inf if any spatial axis is unbounded.
        Returns 0 if any axis is a point (slice query).
        """
        dx = self.x[1] - self.x[0]
        dy = self.y[1] - self.y[0]
        dz = self.z[1] - self.z[0]
        return dx * dy * dz

    def center(self) -> tuple[float, float, float]:
        """
        Return spatial center point of the region.

        Returns inf/-inf for unbounded axes.
        """
        return (
            (self.x[0] + self.x[1]) / 2,
            (self.y[0] + self.y[1]) / 2,
            (self.z[0] + self.z[1]) / 2,
        )

    def size(self) -> tuple[float, float, float]:
        """Return (width_x, width_y, width_z) of the region."""
        return (
            self.x[1] - self.x[0],
            self.y[1] - self.y[0],
            self.z[1] - self.z[0],
        )

    def contains_point(self, x: float, y: float, z: float, t: float | None = None) -> bool:
        """Check if a point is inside the region."""
        in_space = (
            self.x[0] <= x <= self.x[1] and
            self.y[0] <= y <= self.y[1] and
            self.z[0] <= z <= self.z[1]
        )
        if t is None:
            return in_space
        return in_space and self.t[0] <= t <= self.t[1]

    def expand(self, padding: float, temporal_padding: float = 0) -> Region:
        """
        Return new region expanded by padding in all directions.

        Parameters
        ----------
        padding : float
            Spatial padding (added to all x/y/z bounds).
        temporal_padding : float, default 0
            Temporal padding (added to t bounds).
        """
        return Region(
            x=(self.x[0] - padding, self.x[1] + padding),
            y=(self.y[0] - padding, self.y[1] + padding),
            z=(self.z[0] - padding, self.z[1] + padding),
            t=(self.t[0] - temporal_padding, self.t[1] + temporal_padding),
        )

    def intersects(self, other: Region | RegionTuple) -> bool:
        """Check if this region intersects another (in both space and time)."""
        if not isinstance(other, Region):
            other = Region.from_tuple(other)
        return (
            self.x[0] <= other.x[1] and self.x[1] >= other.x[0] and
            self.y[0] <= other.y[1] and self.y[1] >= other.y[0] and
            self.z[0] <= other.z[1] and self.z[1] >= other.z[0] and
            self.t[0] <= other.t[1] and self.t[1] >= other.t[0]
        )

    def with_time(self, t: AxisBounds) -> Region:
        """Return new region with different time bounds."""
        return Region(x=self.x, y=self.y, z=self.z, t=t)

    def with_spatial(
        self,
        x: AxisBounds = None,
        y: AxisBounds = None,
        z: AxisBounds = None,
    ) -> Region:
        """Return new region with different spatial bounds (keeps time)."""
        return Region(
            x=x if x is not None else self.x,
            y=y if y is not None else self.y,
            z=z if z is not None else self.z,
            t=self.t,
        )

    # -------------------------------------------------------------------------
    # Subdivision
    # -------------------------------------------------------------------------

    def subdivide(
        self,
        nx: int = 1,
        ny: int = 1,
        nz: int = 1,
        nt: int = 1,
    ) -> list[Region]:
        """
        Subdivide region into nx * ny * nz * nt sub-regions.

        Parameters
        ----------
        nx, ny, nz : int, default 1
            Number of divisions along each spatial axis.
        nt : int, default 1
            Number of divisions along time axis.

        Returns
        -------
        list[Region]
            List of sub-regions, ordered by (ix, iy, iz, it) with it varying fastest.

        Raises
        ------
        ValueError
            If any axis is unbounded (can't subdivide infinity).
        """
        if nx < 1 or ny < 1 or nz < 1 or nt < 1:
            raise ValueError("Subdivisions must be >= 1")

        def _has_inf(bounds: tuple[float, float]) -> bool:
            return bounds[0] == NEG_INF or bounds[1] == INF

        if _has_inf(self.x) or _has_inf(self.y) or _has_inf(self.z):
            raise ValueError("Cannot subdivide region with infinite spatial bounds")
        if nt > 1 and _has_inf(self.t):
            raise ValueError("Cannot subdivide region with infinite time bounds")

        dx = (self.x[1] - self.x[0]) / nx
        dy = (self.y[1] - self.y[0]) / ny
        dz = (self.z[1] - self.z[0]) / nz
        dt = (self.t[1] - self.t[0]) / nt if nt > 1 else 0

        regions = []
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    for it in range(nt):
                        t_bounds = self.t if nt == 1 else (
                            self.t[0] + it * dt,
                            self.t[0] + (it + 1) * dt,
                        )
                        sub = Region(
                            x=(self.x[0] + ix * dx, self.x[0] + (ix + 1) * dx),
                            y=(self.y[0] + iy * dy, self.y[0] + (iy + 1) * dy),
                            z=(self.z[0] + iz * dz, self.z[0] + (iz + 1) * dz),
                            t=t_bounds,
                        )
                        regions.append(sub)

        return regions

    def iter_subdivide(
        self,
        nx: int = 1,
        ny: int = 1,
        nz: int = 1,
        nt: int = 1,
    ) -> Iterator[Region]:
        """
        Iterate over subdivisions without building full list.

        Yields sub-regions in same order as subdivide().
        """
        if nx < 1 or ny < 1 or nz < 1 or nt < 1:
            raise ValueError("Subdivisions must be >= 1")

        def _has_inf(bounds: tuple[float, float]) -> bool:
            return bounds[0] == NEG_INF or bounds[1] == INF

        if _has_inf(self.x) or _has_inf(self.y) or _has_inf(self.z):
            raise ValueError("Cannot subdivide region with infinite spatial bounds")
        if nt > 1 and _has_inf(self.t):
            raise ValueError("Cannot subdivide region with infinite time bounds")

        dx = (self.x[1] - self.x[0]) / nx
        dy = (self.y[1] - self.y[0]) / ny
        dz = (self.z[1] - self.z[0]) / nz
        dt = (self.t[1] - self.t[0]) / nt if nt > 1 else 0

        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    for it in range(nt):
                        t_bounds = self.t if nt == 1 else (
                            self.t[0] + it * dt,
                            self.t[0] + (it + 1) * dt,
                        )
                        yield Region(
                            x=(self.x[0] + ix * dx, self.x[0] + (ix + 1) * dx),
                            y=(self.y[0] + iy * dy, self.y[0] + (iy + 1) * dy),
                            z=(self.z[0] + iz * dz, self.z[0] + (iz + 1) * dz),
                            t=t_bounds,
                        )

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        def _is_point(bounds: tuple[float, float]) -> bool:
            return bounds[0] == bounds[1] and bounds[0] != NEG_INF

        parts = []
        if self.x != (NEG_INF, INF):
            parts.append(f"x={self.x[0]}" if _is_point(self.x) else f"x={self.x}")
        if self.y != (NEG_INF, INF):
            parts.append(f"y={self.y[0]}" if _is_point(self.y) else f"y={self.y}")
        if self.z != (NEG_INF, INF):
            parts.append(f"z={self.z[0]}" if _is_point(self.z) else f"z={self.z}")
        if self.t != (NEG_INF, INF):
            parts.append(f"t={self.t[0]}" if _is_point(self.t) else f"t={self.t}")

        return f"Region({', '.join(parts)})" if parts else "Region()"


def ensure_region(r: Region | RegionTuple) -> Region:
    """Convert tuple to Region if needed."""
    if isinstance(r, Region):
        return r
    return Region.from_tuple(r)


__all__ = [
    "Region",
    "RegionTuple",
    "AxisBounds",
    "ensure_region",
    "INF",
    "NEG_INF",
]
