"""
Benchmark script for Fast LSH ANN

Tests performance with increasing dataset sizes from 100 to 100k vectors.
"""

import time
import numpy as np
from fast_lsh_ann import BucketedRandomProjectionLSH


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.1f} µs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.3f} s"


def benchmark_size(n_vectors: int, dim: int = 128, num_hash_tables: int = 5):
    """Run benchmark for a specific dataset size."""
    print(f"\n{'='*60}")
    print(f"Dataset: {n_vectors:,} vectors x {dim} dimensions")
    print(f"{'='*60}")

    # Generate random vectors
    np.random.seed(42)
    vectors = np.random.randn(n_vectors, dim).astype(np.float32)

    # Create estimator
    lsh = BucketedRandomProjectionLSH(
        bucket_length=4.0,
        num_hash_tables=num_hash_tables,
        seed=42
    )

    # Benchmark fit
    start = time.perf_counter()
    model = lsh.fit(vectors)
    fit_time = time.perf_counter() - start
    print(f"  Fit time:                {format_time(fit_time):>12}")

    # Benchmark transform
    start = time.perf_counter()
    hashes = model.transform(vectors)
    transform_time = time.perf_counter() - start
    print(f"  Transform time:          {format_time(transform_time):>12}")

    # Benchmark single query
    query = np.random.randn(dim).astype(np.float32)
    start = time.perf_counter()
    results = model.approx_nearest_neighbors(vectors, query, k=10)
    single_query_time = time.perf_counter() - start
    print(f"  Single query (k=10):     {format_time(single_query_time):>12}  (found {len(results)} results)")

    # Benchmark batch queries (100 queries)
    n_queries = min(100, n_vectors // 10)
    queries = np.random.randn(n_queries, dim).astype(np.float32)
    start = time.perf_counter()
    batch_results = model.batch_approx_nearest_neighbors(vectors, queries, k=10)
    batch_query_time = time.perf_counter() - start
    avg_query_time = batch_query_time / n_queries
    print(f"  Batch query ({n_queries:>3} queries): {format_time(batch_query_time):>12}  ({format_time(avg_query_time)}/query)")

    # Benchmark similarity join (with smaller subset for large datasets)
    n_join = min(1000, n_vectors)
    vectors_a = vectors[:n_join]
    vectors_b = vectors[:n_join] + np.random.randn(n_join, dim).astype(np.float32) * 0.5

    start = time.perf_counter()
    pairs = model.approx_similarity_join(vectors_a, vectors_b, threshold=5.0)
    join_time = time.perf_counter() - start
    print(f"  Similarity join ({n_join:>4}x{n_join:<4}): {format_time(join_time):>8}  (found {len(pairs):,} pairs)")

    # Calculate throughput
    vectors_per_sec = n_vectors / fit_time
    queries_per_sec = n_queries / batch_query_time
    print(f"\n  Throughput:")
    print(f"    Index:  {vectors_per_sec:,.0f} vectors/sec")
    print(f"    Query:  {queries_per_sec:,.0f} queries/sec")

    return {
        "n_vectors": n_vectors,
        "fit_time": fit_time,
        "transform_time": transform_time,
        "single_query_time": single_query_time,
        "batch_query_time": batch_query_time,
        "join_time": join_time,
        "n_results": len(results),
        "n_pairs": len(pairs),
    }


def main():
    print("=" * 60)
    print("Fast LSH ANN Benchmark")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Dimensions:       128")
    print(f"  Hash tables:      5")
    print(f"  Bucket length:    4.0")
    print(f"  k (neighbors):    10")

    # Test sizes: 100, 1k, 10k, 100k
    sizes = [100, 1_000, 10_000, 100_000]
    results = []

    for size in sizes:
        result = benchmark_size(size)
        results.append(result)

    # Summary table
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"\n{'Size':>10} | {'Fit':>10} | {'Query':>10} | {'Batch/q':>10} | {'Join':>10}")
    print("-" * 60)
    for r in results:
        print(
            f"{r['n_vectors']:>10,} | "
            f"{format_time(r['fit_time']):>10} | "
            f"{format_time(r['single_query_time']):>10} | "
            f"{format_time(r['batch_query_time']/100):>10} | "
            f"{format_time(r['join_time']):>10}"
        )

    print("\nDone!")


if __name__ == "__main__":
    main()
