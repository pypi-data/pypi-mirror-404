"""
Unit handling for atomkit using Pint.

Provides a shared unit registry and utilities for working with units
in molecular dynamics data (LAMMPS metal units by default).
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, TypeVar, Callable, Any

import numpy as np
import pint

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Shared unit registry for atomkit
ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# Type alias for quantities
Quantity = pint.Quantity

# Common units in LAMMPS metal style
# https://docs.lammps.org/units.html
LAMMPS_METAL_UNITS = {
    # Coordinates / distances
    "coords": ureg.angstrom,
    "x": ureg.angstrom,
    "y": ureg.angstrom,
    "z": ureg.angstrom,
    "xu": ureg.angstrom,
    "yu": ureg.angstrom,
    "zu": ureg.angstrom,
    "xs": ureg.dimensionless,  # scaled coords are dimensionless (0-1)
    "ys": ureg.dimensionless,
    "zs": ureg.dimensionless,
    # Velocities
    "vx": ureg.angstrom / ureg.picosecond,
    "vy": ureg.angstrom / ureg.picosecond,
    "vz": ureg.angstrom / ureg.picosecond,
    # Forces
    "fx": ureg.eV / ureg.angstrom,
    "fy": ureg.eV / ureg.angstrom,
    "fz": ureg.eV / ureg.angstrom,
    # Energy
    "ke": ureg.eV,
    "pe": ureg.eV,
    "etotal": ureg.eV,
    "c_pe": ureg.eV,
    "c_ke": ureg.eV,
    # Stress (per-atom stress in LAMMPS is stress*volume in bar*Å³)
    "stress": ureg.bar * ureg.angstrom**3,
    "c_stress": ureg.bar * ureg.angstrom**3,
    "c_stress[1]": ureg.bar * ureg.angstrom**3,
    "c_stress[2]": ureg.bar * ureg.angstrom**3,
    "c_stress[3]": ureg.bar * ureg.angstrom**3,
    "c_stress[4]": ureg.bar * ureg.angstrom**3,
    "c_stress[5]": ureg.bar * ureg.angstrom**3,
    "c_stress[6]": ureg.bar * ureg.angstrom**3,
    # Pressure components (virial stress)
    "v_sxx": ureg.bar * ureg.angstrom**3,
    "v_syy": ureg.bar * ureg.angstrom**3,
    "v_szz": ureg.bar * ureg.angstrom**3,
    "v_sxy": ureg.bar * ureg.angstrom**3,
    "v_sxz": ureg.bar * ureg.angstrom**3,
    "v_syz": ureg.bar * ureg.angstrom**3,
    # Mass
    "mass": ureg.gram / ureg.mol,  # atomic mass units
    # Charge
    "q": ureg.elementary_charge,
    # Temperature
    "c_temp": ureg.kelvin,
    # Time
    "time": ureg.picosecond,
    # IDs (dimensionless)
    "id": ureg.dimensionless,
    "atom_id": ureg.dimensionless,
    "type": ureg.dimensionless,
    "mol": ureg.dimensionless,
    # Counts
    "counts": ureg.dimensionless,
}

# Default unit for unknown fields
DEFAULT_UNIT = ureg.dimensionless


def get_unit(field_name: str) -> pint.Unit:
    """Get the unit for a field name.

    Tries exact match first, then checks for partial matches
    (e.g., "c_stress[1]" matches "c_stress").

    Parameters
    ----------
    field_name : str
        The field name to look up.

    Returns
    -------
    pint.Unit
        The unit for this field, or dimensionless if unknown.
    """
    # Exact match
    if field_name in LAMMPS_METAL_UNITS:
        return LAMMPS_METAL_UNITS[field_name]

    # Check for prefix matches (e.g., "c_stress[1]" -> "c_stress")
    for pattern, unit in LAMMPS_METAL_UNITS.items():
        if field_name.startswith(pattern):
            return unit

    # Check for suffix matches (e.g., "v_mystress" containing "stress")
    lower_name = field_name.lower()
    if "stress" in lower_name:
        return ureg.bar * ureg.angstrom**3
    if "energy" in lower_name or lower_name.endswith("_pe") or lower_name.endswith("_ke"):
        return ureg.eV
    if "force" in lower_name:
        return ureg.eV / ureg.angstrom
    if "vel" in lower_name:
        return ureg.angstrom / ureg.picosecond
    if "temp" in lower_name:
        return ureg.kelvin

    return DEFAULT_UNIT


def strip_units(value: Any) -> Any:
    """Strip units from a value, returning the magnitude.

    Works with scalars, arrays, and nested structures.
    If value has no units, returns as-is.
    """
    if isinstance(value, pint.Quantity):
        return value.magnitude
    if isinstance(value, dict):
        return {k: strip_units(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(strip_units(v) for v in value)
    return value


def attach_units(value: NDArray | float, unit: pint.Unit) -> Quantity:
    """Attach units to a value.

    Parameters
    ----------
    value : array or scalar
        The numerical value(s).
    unit : pint.Unit
        The unit to attach.

    Returns
    -------
    Quantity
        Value with units attached.
    """
    return Q_(value, unit)


def maybe_strip(value: Any, use_units: bool) -> Any:
    """Conditionally strip units based on flag.

    Parameters
    ----------
    value : Any
        Value that may have units.
    use_units : bool
        If True, return as-is. If False, strip units.

    Returns
    -------
    Any
        Original value if use_units=True, magnitude if False.
    """
    if use_units:
        return value
    return strip_units(value)


F = TypeVar("F", bound=Callable)


def units_property(unit: pint.Unit | str | None = None, field_name: str | None = None):
    """Decorator for properties that should return values with units.

    The decorated property should return raw numpy arrays. This decorator
    will attach units based on the grid's use_units setting.

    Parameters
    ----------
    unit : pint.Unit or str, optional
        The unit to attach. If None, uses field_name to look up.
    field_name : str, optional
        Field name for unit lookup. If None and unit is None,
        returns dimensionless.

    Example
    -------
    >>> class MyClass:
    ...     use_units: bool = True
    ...
    ...     @units_property(ureg.angstrom)
    ...     def coords(self):
    ...         return self._coords  # raw numpy array
    """
    def decorator(func: F) -> property:
        @wraps(func)
        def wrapper(self):
            raw_value = func(self)
            if not getattr(self, "use_units", True):
                return raw_value

            # Determine unit
            if unit is not None:
                u = ureg.Unit(unit) if isinstance(unit, str) else unit
            elif field_name is not None:
                u = get_unit(field_name)
            else:
                u = ureg.dimensionless

            return Q_(raw_value, u)

        return property(wrapper)

    return decorator
