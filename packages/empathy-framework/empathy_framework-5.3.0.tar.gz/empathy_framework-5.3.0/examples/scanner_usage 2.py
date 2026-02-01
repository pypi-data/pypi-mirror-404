"""Examples of using the optimized project scanner.

Demonstrates:
1. Parallel scanner for fast full scans
2. Incremental scanning for quick updates
3. Optional dependency analysis
4. Worker count configuration

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from empathy_os.project_index import ParallelProjectScanner, ProjectIndex, ProjectScanner


def example_1_quick_scan():
    """Example 1: Quick scan without dependencies.

    Use when you need a fast file listing without dependency graph.
    Perfect for quick health checks or file discovery.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Quick Scan (No Dependencies)")
    print("=" * 70)

    # Create parallel scanner
    scanner = ParallelProjectScanner(project_root=".", workers=4)

    # Scan without dependency analysis (fastest)
    records, summary = scanner.scan(analyze_dependencies=False)

    print(f"\n✅ Scanned {summary.total_files:,} files")
    print(f"   Source files: {summary.source_files:,}")
    print(f"   Test files: {summary.test_files:,}")
    print(f"   Test coverage: {summary.test_coverage_avg:.1f}%")

    # Find stale files (tests not updated when source changed)
    stale_files = [r for r in records if r.is_stale]
    print(f"\n⚠️  {len(stale_files)} stale files need attention:")
    for record in stale_files[:5]:  # Show first 5
        print(f"   {record.path} (stale for {record.staleness_days} days)")


def example_2_full_scan_with_dependencies():
    """Example 2: Full scan with dependency analysis.

    Use for comprehensive analysis including impact scoring.
    Perfect for CI/CD pipelines and test prioritization.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Full Scan (With Dependencies)")
    print("=" * 70)

    # Use auto worker count (all CPU cores)
    scanner = ParallelProjectScanner(project_root=".")

    # Full scan with dependency graph
    records, summary = scanner.scan(analyze_dependencies=True)

    print(f"\n✅ Scanned {summary.total_files:,} files with dependency graph")

    # Find high-impact files (imported by many others)
    high_impact = sorted(records, key=lambda r: r.imported_by_count, reverse=True)[:10]
    print("\n🔥 Top 10 high-impact files:")
    for record in high_impact:
        print(f"   {record.path}: imported by {record.imported_by_count} files")

    # Find critical untested files (high impact but no tests)
    critical_untested = [r for r in high_impact if not r.tests_exist]
    print(f"\n⚠️  {len(critical_untested)} critical files without tests:")
    for record in critical_untested[:5]:
        print(f"   {record.path} (impact: {record.imported_by_count})")


def example_3_incremental_update():
    """Example 3: Incremental update using git diff.

    Use for fast updates during development.
    Only scans files changed since last commit.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Incremental Update (Git Diff)")
    print("=" * 70)

    # Create index
    index = ProjectIndex(project_root=".", workers=4, use_parallel=True)

    # Load existing index or create new one
    if not index.load():
        print("📝 No existing index found, creating initial index...")
        index.refresh(analyze_dependencies=False)  # Fast initial scan
        print(f"   ✅ Created index with {len(index._records):,} files")
    else:
        print(f"📂 Loaded existing index with {len(index._records):,} files")

    # Incremental update (only changed files)
    try:
        updated, removed = index.refresh_incremental(analyze_dependencies=False)
        print("\n✅ Incremental update complete:")
        print(f"   Updated: {updated} files")
        print(f"   Removed: {removed} files")

        if updated + removed == 0:
            print("   No changes detected!")
    except RuntimeError as e:
        print(f"\n⚠️  Incremental update not available: {e}")
        print("   Falling back to full refresh...")
        index.refresh(analyze_dependencies=False)


def example_4_worker_count_tuning():
    """Example 4: Worker count configuration.

    Shows how to tune worker count for different scenarios.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Worker Count Tuning")
    print("=" * 70)

    import multiprocessing as mp
    import time

    cpu_count = mp.cpu_count()
    print(f"\n💻 System has {cpu_count} CPU cores")

    # Test different worker counts
    worker_counts = [1, 2, cpu_count // 2, cpu_count]
    results = []

    for workers in worker_counts:
        print(f"\n⏱️  Testing with {workers} worker(s)...")

        scanner = ParallelProjectScanner(project_root=".", workers=workers)

        start = time.perf_counter()
        records, summary = scanner.scan(analyze_dependencies=False)
        duration = time.perf_counter() - start

        files_per_sec = summary.total_files / duration if duration > 0 else 0

        results.append(
            {"workers": workers, "time": duration, "rate": files_per_sec}
        )

        print(f"   Time: {duration:.4f}s")
        print(f"   Rate: {files_per_sec:.0f} files/sec")

    # Find optimal configuration
    best = min(results, key=lambda r: r["time"])
    print(f"\n🏆 Best configuration: {best['workers']} workers")
    print(f"   Time: {best['time']:.4f}s")
    print(f"   Rate: {best['rate']:.0f} files/sec")


def example_5_project_index_api():
    """Example 5: Using ProjectIndex for persistent state.

    Shows how to use ProjectIndex for managing index state with auto-save.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: ProjectIndex API")
    print("=" * 70)

    # Create index with parallel scanning enabled
    index = ProjectIndex(project_root=".", workers=4, use_parallel=True)

    # Option 1: Load existing index
    if index.load():
        print(f"📂 Loaded existing index with {len(index._records):,} files")
        print(f"   Generated at: {index._generated_at}")

        # Quick incremental update
        try:
            updated, removed = index.refresh_incremental(analyze_dependencies=False)
            print(f"\n✅ Updated {updated} files, removed {removed}")
        except (RuntimeError, ValueError):
            # Not a git repo or no existing index
            pass

    else:
        # Option 2: Create new index
        print("📝 Creating new index...")
        index.refresh(analyze_dependencies=True)  # Full scan
        print(f"   ✅ Created index with {len(index._records):,} files")

    # Query the index
    print("\n📊 Index statistics:")
    print(f"   Total files: {index._summary.total_files:,}")
    print(f"   Source files: {index._summary.source_files:,}")
    print(f"   Test files: {index._summary.test_files:,}")
    print(f"   Files needing attention: {index._summary.files_needing_attention}")

    # Update specific file metadata
    if index._records:
        first_file = list(index._records.keys())[0]
        index.update_file(first_file, custom_tag="example", priority="high")
        print(f"\n✏️  Updated metadata for {first_file}")


def example_6_sequential_vs_parallel():
    """Example 6: Compare sequential vs parallel performance.

    Demonstrates the performance difference between scanners.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Sequential vs Parallel Comparison")
    print("=" * 70)

    import time

    # Sequential scan
    print("\n⏱️  Sequential scanner...")
    scanner_seq = ProjectScanner(project_root=".")
    start = time.perf_counter()
    records_seq, summary_seq = scanner_seq.scan(analyze_dependencies=False)
    time_seq = time.perf_counter() - start

    print(f"   Time: {time_seq:.4f}s")
    print(f"   Files: {summary_seq.total_files:,}")

    # Parallel scan
    print("\n⏱️  Parallel scanner...")
    scanner_par = ParallelProjectScanner(project_root=".")
    start = time.perf_counter()
    records_par, summary_par = scanner_par.scan(analyze_dependencies=False)
    time_par = time.perf_counter() - start

    print(f"   Time: {time_par:.4f}s")
    print(f"   Files: {summary_par.total_files:,}")

    # Compare
    speedup = time_seq / time_par if time_par > 0 else 0
    improvement = ((time_seq - time_par) / time_seq * 100) if time_seq > 0 else 0

    print("\n📊 Comparison:")
    print(f"   Speedup: {speedup:.2f}x")
    print(f"   Improvement: {improvement:.1f}%")

    if speedup >= 2.0:
        print("\n✅ Parallel processing is highly effective!")
    elif speedup >= 1.5:
        print("\n✅ Parallel processing provides moderate benefit")
    else:
        print("\n⚠️  Parallel overhead may not be worth it for this codebase size")


def main():
    """Run all examples."""
    print("=" * 70)
    print("PROJECT SCANNER USAGE EXAMPLES")
    print("Empathy Framework - Optimized Scanner Demonstrations")
    print("=" * 70)

    try:
        # Run examples
        example_1_quick_scan()
        example_2_full_scan_with_dependencies()
        example_3_incremental_update()
        example_4_worker_count_tuning()
        example_5_project_index_api()
        example_6_sequential_vs_parallel()

        print("\n" + "=" * 70)
        print("✅ ALL EXAMPLES COMPLETE")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
