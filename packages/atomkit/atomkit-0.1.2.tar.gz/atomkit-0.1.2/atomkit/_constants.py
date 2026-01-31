"""Internal constants for atomkit."""

import os

# Show progress bar when processing more than this many atoms
TQDM_ATOM_THRESHOLD = 1_000_000

# Default grid cell size in Angstroms
DEFAULT_CELL_SIZE = 4.0

# Default zstd compression level (1-22, higher = smaller but slower)
# Level 3 is a good balance: fast writes with minimal size penalty.
# For archival, consider level 15 (slower writes, ~10% smaller).
DEFAULT_COMPRESSION_LEVEL = 3

# Number of threads for polars CSV parsing.
# Benchmarks show 2 threads is optimal - parsing is memory-bound, not CPU-bound.
# Override via ATOMKIT_POLARS_THREADS environment variable.
POLARS_N_THREADS = int(os.environ.get("ATOMKIT_POLARS_THREADS", "2"))

# Padding factor for auto-computed box bounds (multiplied by cell_size)
BOX_PADDING_FACTOR = 0.5
