"""
Atomkit - Atom-level analysis toolkit for molecular dynamics trajectories.
"""

from atomkit.region import Region, RegionTuple, ensure_region, INF, NEG_INF
from atomkit.spatial_grid import SpatialGrid, preprocess_lammps

__version__ = "0.1.1"
__all__ = [
    "SpatialGrid",
    "Region",
    "RegionTuple",
    "ensure_region",
    "preprocess_lammps",
    "INF",
    "NEG_INF",
]


def __getattr__(name: str):
    """Lazy import for optional modules."""
    if name == "viz":
        from atomkit import viz
        return viz
    raise AttributeError(f"module 'atomkit' has no attribute {name!r}")
