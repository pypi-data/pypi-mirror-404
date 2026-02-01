"""
Atomkit - Atom-level analysis toolkit for molecular dynamics trajectories.
"""

from atomkit.region import Region, RegionTuple, ensure_region, INF, NEG_INF
from atomkit.spatial_grid import (
    SpatialGrid,
    SourceBox,
    GridView,
    CellsAccessor,
    FieldAggregates,
    preprocess_lammps,
)
from atomkit.io.lammps import CoordType
from atomkit._version import __version__
__all__ = [
    "SpatialGrid",
    "SourceBox",
    "GridView",
    "CellsAccessor",
    "FieldAggregates",
    "Region",
    "RegionTuple",
    "ensure_region",
    "preprocess_lammps",
    "INF",
    "NEG_INF",
    "CoordType",
]


def __getattr__(name: str):
    """Lazy import for optional modules."""
    if name == "viz":
        from atomkit import viz
        return viz
    raise AttributeError(f"module 'atomkit' has no attribute {name!r}")
