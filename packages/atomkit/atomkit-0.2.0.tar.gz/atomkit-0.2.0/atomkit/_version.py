"""Version information for atomkit.

Single source of truth is pyproject.toml - we read it at runtime.
Falls back to parsing pyproject.toml directly when running from source.
"""

from pathlib import Path

__version__: str


def _read_version_from_pyproject() -> str | None:
    """Try to read version from pyproject.toml when not installed."""
    try:
        import tomllib
    except ImportError:
        return None

    # Look for pyproject.toml relative to this file
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return None

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version")
    except Exception:
        return None


try:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("atomkit")
    except PackageNotFoundError:
        # Package not installed - try reading pyproject.toml directly
        __version__ = _read_version_from_pyproject() or "0.0.0.dev0"
except ImportError:
    # Python < 3.8 fallback (shouldn't happen given requires-python >= 3.10)
    __version__ = _read_version_from_pyproject() or "0.0.0.dev0"
