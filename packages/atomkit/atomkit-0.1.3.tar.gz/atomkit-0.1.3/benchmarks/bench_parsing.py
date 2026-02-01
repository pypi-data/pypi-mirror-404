#!/usr/bin/env python3
"""Benchmark polars threads and zstd compression levels.

Usage:
    python benchmarks/bench_parsing.py [path/to/file.lammpstrj]

If no file is provided, searches for *.lammpstrj in the project root.
"""

import argparse
import os
import tempfile
import time
from pathlib import Path

import numpy as np


def find_test_file() -> Path | None:
    """Find a LAMMPS trajectory file for benchmarking."""
    # Look in project root (parent of benchmarks/)
    project_root = Path(__file__).parent.parent
    candidates = list(project_root.glob("*.lammpstrj"))
    if candidates:
        # Pick largest file for more meaningful benchmark
        return max(candidates, key=lambda p: p.stat().st_size)
    return None


def benchmark_polars_threads(test_file: Path):
    """Benchmark different thread counts for polars parsing."""
    import atomkit._constants as constants
    from atomkit.io.lammps import parse_lammps

    # Get CPU count
    cpu_count = os.cpu_count() or 4
    thread_counts = [1, 2, 4, 8, 16, cpu_count]
    thread_counts = sorted(set(t for t in thread_counts if t <= cpu_count))

    print(f"\n{'='*60}")
    print(f"POLARS THREAD BENCHMARK (CPU count: {cpu_count})")
    print(f"File: {test_file.name}")
    print(f"{'='*60}\n")

    results = []

    for n_threads in thread_counts:
        # Patch the constant
        constants.POLARS_N_THREADS = n_threads

        # Reload the module to pick up the new constant
        import importlib
        import atomkit.io.lammps as lammps_module
        importlib.reload(lammps_module)

        # Warm up / ensure file is cached
        if n_threads == thread_counts[0]:
            print("Warming up (loading file into OS cache)...")
            _ = lammps_module.parse_lammps(test_file, timesteps=slice(0, 1))

        # Benchmark: parse first 2 timesteps (enough to see thread impact)
        times = []
        for run in range(3):
            start = time.perf_counter()
            coords, fields, ts = lammps_module.parse_lammps(test_file, timesteps=slice(0, 2))
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_time = np.mean(times)
        std_time = np.std(times)
        n_atoms = len(coords[0]) * len(coords)
        atoms_per_sec = n_atoms / avg_time

        results.append({
            'threads': n_threads,
            'time': avg_time,
            'std': std_time,
            'atoms_per_sec': atoms_per_sec,
        })

        print(f"Threads: {n_threads:2d} | Time: {avg_time:.3f}s ± {std_time:.3f}s | {atoms_per_sec/1e6:.2f}M atoms/s")

    # Find best
    best = min(results, key=lambda x: x['time'])
    print(f"\nBest: {best['threads']} threads ({best['time']:.3f}s)")

    return results


def benchmark_zstd_compression(test_file: Path):
    """Benchmark different zstd compression levels."""
    from atomkit import SpatialGrid

    print(f"\n{'='*60}")
    print("ZSTD COMPRESSION BENCHMARK")
    print(f"File: {test_file.name}")
    print(f"{'='*60}\n")

    # Load data once (just 1 timestep to keep it fast)
    print("Loading data...")
    grid = SpatialGrid.from_lammps(test_file, cell_size=4.0, timesteps=slice(0, 1))
    print(f"Loaded: {grid.n_atoms:,} atoms, {len(grid.fields)} fields\n")

    # Test compression levels
    levels = [1, 3, 5, 7, 9, 12, 15, 19, 22]
    results = []

    print(f"{'Level':>5} | {'Size (MB)':>10} | {'Write (s)':>10} | {'Read (s)':>10} | {'Ratio':>8}")
    print("-" * 55)

    with tempfile.TemporaryDirectory() as tmpdir:
        for level in levels:
            out_path = Path(tmpdir) / f"test_level_{level}.h5"

            # Benchmark write
            start = time.perf_counter()
            grid.save(out_path, compression_level=level)
            write_time = time.perf_counter() - start

            file_size = out_path.stat().st_size / (1024 * 1024)  # MB

            # Benchmark read (full load + query)
            read_times = []
            for _ in range(3):
                start = time.perf_counter()
                with SpatialGrid.load(out_path) as loaded:
                    # Force read all data
                    _ = loaded.query()
                read_time = time.perf_counter() - start
                read_times.append(read_time)

            avg_read = np.mean(read_times)

            # Compression ratio (vs level 1)
            if level == 1:
                base_size = file_size
            ratio = base_size / file_size

            results.append({
                'level': level,
                'size_mb': file_size,
                'write_s': write_time,
                'read_s': avg_read,
                'ratio': ratio,
            })

            print(f"{level:>5} | {file_size:>10.2f} | {write_time:>10.3f} | {avg_read:>10.3f} | {ratio:>8.2f}x")

    print("\nNotes:")
    print("- Ratio is relative to level 1")
    print("- Higher levels = smaller files but slower writes")
    print("- Read speed is mostly limited by decompression, not disk")

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark atomkit parsing and compression")
    parser.add_argument("file", nargs="?", help="LAMMPS trajectory file (auto-detected if not provided)")
    parser.add_argument("--threads-only", action="store_true", help="Only run thread benchmark")
    parser.add_argument("--compression-only", action="store_true", help="Only run compression benchmark")
    args = parser.parse_args()

    # Find test file
    if args.file:
        test_file = Path(args.file)
    else:
        test_file = find_test_file()

    if test_file is None or not test_file.exists():
        print(f"Test file not found: {test_file or '(none)'}")
        print("Usage: python benchmarks/bench_parsing.py path/to/file.lammpstrj")
        return 1

    print(f"Using test file: {test_file} ({test_file.stat().st_size / 1e6:.1f} MB)")

    # Run benchmarks
    thread_results = None
    compression_results = None

    if not args.compression_only:
        thread_results = benchmark_polars_threads(test_file)

    if not args.threads_only:
        compression_results = benchmark_zstd_compression(test_file)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    if thread_results:
        best_threads = min(thread_results, key=lambda x: x['time'])
        print(f"Recommended POLARS_N_THREADS: {best_threads['threads']}")

    if compression_results:
        # Find sweet spot for compression (good ratio, reasonable speed)
        for r in compression_results:
            r['score'] = r['ratio'] / (r['write_s'] * 0.3 + r['read_s'] * 0.7)

        best_compression = max(compression_results, key=lambda x: x['score'])
        print(f"Recommended DEFAULT_COMPRESSION_LEVEL: {best_compression['level']} (balanced)")

        fastest_read = min(compression_results, key=lambda x: x['read_s'])
        print(f"Fastest read: level {fastest_read['level']} ({fastest_read['read_s']:.3f}s)")

        best_ratio = max(compression_results, key=lambda x: x['ratio'])
        print(f"Best compression: level {best_ratio['level']} ({best_ratio['size_mb']:.2f} MB, {best_ratio['ratio']:.2f}x)")

    return 0


if __name__ == "__main__":
    exit(main() or 0)
