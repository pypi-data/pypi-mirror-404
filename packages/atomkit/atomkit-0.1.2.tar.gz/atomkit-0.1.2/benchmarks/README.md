# Benchmarks

Performance benchmarks for atomkit. These are not run as part of the regular test suite.

## Running

```bash
# Run all benchmarks
uv run python benchmarks/bench_parsing.py

# Or with standard python
python benchmarks/bench_parsing.py
```

## Available Benchmarks

### bench_parsing.py

Benchmarks for:
- **Polars thread count**: Tests different `n_threads` values for CSV parsing
- **ZSTD compression levels**: Tests size vs speed tradeoffs for compression levels 1-22

Requires a LAMMPS trajectory file. Edit `TEST_FILE` path in the script.

## Results Summary (2026-01)

**Polars Threads** (1.67M atoms, 16-core machine):
- 2 threads optimal (memory-bound, not CPU-bound)
- More threads add overhead without benefit

**ZSTD Compression** (stress tensor data):
- Level 3: best balance (fast writes, ~1% larger than max compression)
- Level 15+: ~10% smaller but 30-100x slower writes
- Read speed constant across all levels
