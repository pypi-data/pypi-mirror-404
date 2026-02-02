#!/usr/bin/env python3
"""
Benchmark: fast_lsh_ann (Rust) vs PySpark BucketedRandomProjectionLSH

This script compares the performance of:
1. Pure Rust stack: deltalake + polars + fast_lsh_ann
2. Spark stack: Delta Lake + Spark + BucketedRandomProjectionLSH

Run without Spark (Rust only):
    python benchmarks/spark_vs_rust.py --rust-only

Run with Spark comparison:
    python benchmarks/spark_vs_rust.py

Run with custom sizes:
    python benchmarks/spark_vs_rust.py --sizes 1000,10000,100000
"""

import argparse
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

# Check for optional dependencies
try:
    import polars as pl
    from deltalake import DeltaTable, write_deltalake
    HAS_DELTA = True
except ImportError:
    HAS_DELTA = False
    print("Warning: deltalake/polars not installed. Run: uv pip install deltalake polars")

try:
    from pyspark.sql import SparkSession
    from pyspark.ml.feature import BucketedRandomProjectionLSH as SparkLSH
    from pyspark.ml.linalg import Vectors, VectorUDT
    from pyspark.sql.types import StructType, StructField, IntegerType, ArrayType, FloatType
    HAS_SPARK = True
except ImportError:
    HAS_SPARK = False


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    n_vectors: int
    dim: int
    operation: str
    time_seconds: float
    throughput: float  # vectors/sec or pairs/sec


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.1f} µs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.3f} s"


def create_test_delta(path: str, n_vectors: int, dim: int, seed: int = 42):
    """Create a Delta table with random embeddings."""
    np.random.seed(seed)
    embeddings = np.random.randn(n_vectors, dim).astype(np.float32)

    df = pl.DataFrame({
        "id": range(n_vectors),
        "embedding": embeddings.tolist(),
    })

    write_deltalake(path, df.to_arrow(), mode="overwrite")
    return embeddings


def benchmark_rust(
    delta_path: str,
    n_vectors: int,
    dim: int,
    bucket_length: float = 2.0,
    num_hash_tables: int = 5,
    seed: int = 42,
) -> List[BenchmarkResult]:
    """Benchmark the Rust implementation."""
    from fast_lsh_ann import BucketedRandomProjectionLSH, read_delta_embeddings

    results = []

    # 1. Read Delta table
    start = time.perf_counter()
    embeddings, ids = read_delta_embeddings(delta_path, "embedding", "id")
    read_time = time.perf_counter() - start
    results.append(BenchmarkResult(
        name="Rust",
        n_vectors=n_vectors,
        dim=dim,
        operation="read_delta",
        time_seconds=read_time,
        throughput=n_vectors / read_time,
    ))

    # 2. Create model + Transform
    lsh = BucketedRandomProjectionLSH(
        bucket_length=bucket_length,
        num_hash_tables=num_hash_tables,
        seed=seed,
    )

    start = time.perf_counter()
    model = lsh.create_model(dim=dim)
    hashes = model.transform(embeddings)
    transform_time = time.perf_counter() - start
    results.append(BenchmarkResult(
        name="Rust",
        n_vectors=n_vectors,
        dim=dim,
        operation="transform",
        time_seconds=transform_time,
        throughput=n_vectors / transform_time,
    ))

    # 3. Similarity join (self-join on subset)
    subset_size = min(5000, n_vectors)
    subset_a = embeddings[:subset_size]
    subset_b = embeddings[:subset_size] + np.random.randn(subset_size, dim).astype(np.float32) * 0.5

    start = time.perf_counter()
    pairs = model.approx_similarity_join(subset_a, subset_b, threshold=5.0)
    join_time = time.perf_counter() - start
    results.append(BenchmarkResult(
        name="Rust",
        n_vectors=subset_size,
        dim=dim,
        operation="similarity_join",
        time_seconds=join_time,
        throughput=(subset_size * subset_size) / join_time,  # potential pairs/sec
    ))

    # 3b. CMS-accelerated similarity join
    start = time.perf_counter()
    pairs_cms = model.approx_similarity_join_cms(
        subset_a, subset_b, threshold=5.0,
        min_collisions=num_hash_tables // 2 + 1,  # Require majority collision
    )
    join_cms_time = time.perf_counter() - start
    results.append(BenchmarkResult(
        name="Rust",
        n_vectors=subset_size,
        dim=dim,
        operation="similarity_join_cms",
        time_seconds=join_cms_time,
        throughput=(subset_size * subset_size) / join_cms_time,
    ))

    # 3c. Analyze join statistics (helpful for tuning)
    stats = model.analyze_similarity_join(subset_a, subset_b)
    print(f"    Join stats: {stats[0]:,} total collisions, {stats[1]:,} tracked pairs, max={stats[2]}")

    # 4. Batch nearest neighbors
    n_queries = 100
    queries = np.random.randn(n_queries, dim).astype(np.float32)

    start = time.perf_counter()
    nn_results = model.batch_approx_nearest_neighbors(embeddings, queries, k=10)
    nn_time = time.perf_counter() - start
    results.append(BenchmarkResult(
        name="Rust",
        n_vectors=n_vectors,
        dim=dim,
        operation=f"batch_nn_{n_queries}",
        time_seconds=nn_time,
        throughput=n_queries / nn_time,
    ))

    return results


def benchmark_spark(
    delta_path: str,
    n_vectors: int,
    dim: int,
    bucket_length: float = 2.0,
    num_hash_tables: int = 5,
    seed: int = 42,
) -> List[BenchmarkResult]:
    """Benchmark the Spark implementation."""
    if not HAS_SPARK:
        print("Spark not available, skipping Spark benchmark")
        return []

    results = []

    # Create Spark session
    spark = SparkSession.builder \
        .appName("LSH Benchmark") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    try:
        # 1. Read Delta table
        start = time.perf_counter()
        df = spark.read.format("delta").load(delta_path)

        # Convert embedding array to Vector
        from pyspark.sql.functions import udf, col
        to_vector = udf(lambda x: Vectors.dense(x), VectorUDT())
        df = df.withColumn("features", to_vector(col("embedding")))
        df.cache()
        df.count()  # Force materialization
        read_time = time.perf_counter() - start

        results.append(BenchmarkResult(
            name="Spark",
            n_vectors=n_vectors,
            dim=dim,
            operation="read_delta",
            time_seconds=read_time,
            throughput=n_vectors / read_time,
        ))

        # 2. Fit + Transform
        start = time.perf_counter()
        brp = SparkLSH(
            inputCol="features",
            outputCol="hashes",
            bucketLength=bucket_length,
            numHashTables=num_hash_tables,
            seed=seed,
        )
        model = brp.fit(df)
        transformed = model.transform(df)
        transformed.cache()
        transformed.count()  # Force materialization
        transform_time = time.perf_counter() - start

        results.append(BenchmarkResult(
            name="Spark",
            n_vectors=n_vectors,
            dim=dim,
            operation="transform",
            time_seconds=transform_time,
            throughput=n_vectors / transform_time,
        ))

        # 3. Similarity join (self-join on subset)
        subset_size = min(5000, n_vectors)
        df_subset = df.limit(subset_size)
        df_subset.cache()
        df_subset.count()

        start = time.perf_counter()
        joined = model.approxSimilarityJoin(df_subset, df_subset, 5.0, distCol="distance")
        n_pairs = joined.count()
        join_time = time.perf_counter() - start

        results.append(BenchmarkResult(
            name="Spark",
            n_vectors=subset_size,
            dim=dim,
            operation="similarity_join",
            time_seconds=join_time,
            throughput=(subset_size * subset_size) / join_time,
        ))

        # 4. Approximate nearest neighbors (single query, repeated)
        n_queries = 100
        query_vec = Vectors.dense(np.random.randn(dim).astype(float).tolist())

        start = time.perf_counter()
        for _ in range(n_queries):
            nn_result = model.approxNearestNeighbors(df, query_vec, 10)
            nn_result.collect()
        nn_time = time.perf_counter() - start

        results.append(BenchmarkResult(
            name="Spark",
            n_vectors=n_vectors,
            dim=dim,
            operation=f"batch_nn_{n_queries}",
            time_seconds=nn_time,
            throughput=n_queries / nn_time,
        ))

    finally:
        spark.stop()

    return results


def run_benchmark(
    sizes: List[int],
    dim: int = 128,
    bucket_length: float = 2.0,
    num_hash_tables: int = 5,
    rust_only: bool = False,
) -> List[BenchmarkResult]:
    """Run the full benchmark suite."""
    all_results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for n_vectors in sizes:
            print(f"\n{'='*60}")
            print(f"Benchmarking with {n_vectors:,} vectors (dim={dim})")
            print(f"{'='*60}")

            delta_path = os.path.join(tmpdir, f"embeddings_{n_vectors}")

            # Create test data
            print(f"Creating Delta table...")
            create_test_delta(delta_path, n_vectors, dim)

            # Benchmark Rust
            print(f"\n--- Rust (fast_lsh_ann) ---")
            rust_results = benchmark_rust(
                delta_path, n_vectors, dim, bucket_length, num_hash_tables
            )
            all_results.extend(rust_results)
            for r in rust_results:
                print(f"  {r.operation}: {format_time(r.time_seconds)} ({r.throughput:,.0f}/sec)")

            # Benchmark Spark
            if not rust_only and HAS_SPARK:
                print(f"\n--- Spark (BucketedRandomProjectionLSH) ---")
                spark_results = benchmark_spark(
                    delta_path, n_vectors, dim, bucket_length, num_hash_tables
                )
                all_results.extend(spark_results)
                for r in spark_results:
                    print(f"  {r.operation}: {format_time(r.time_seconds)} ({r.throughput:,.0f}/sec)")

    return all_results


def print_summary(results: List[BenchmarkResult]):
    """Print a summary comparison table."""
    print("\n" + "=" * 80)
    print("SUMMARY: Rust vs Spark")
    print("=" * 80)

    # Group by operation and size
    from collections import defaultdict
    grouped = defaultdict(dict)

    for r in results:
        key = (r.n_vectors, r.operation)
        grouped[key][r.name] = r

    # Print header
    print(f"\n{'Size':>10} | {'Operation':<20} | {'Rust':>12} | {'Spark':>12} | {'Speedup':>10}")
    print("-" * 80)

    for (n_vectors, operation), times in sorted(grouped.items()):
        rust_time = times.get("Rust")
        spark_time = times.get("Spark")

        rust_str = format_time(rust_time.time_seconds) if rust_time else "N/A"
        spark_str = format_time(spark_time.time_seconds) if spark_time else "N/A"

        if rust_time and spark_time:
            speedup = spark_time.time_seconds / rust_time.time_seconds
            speedup_str = f"{speedup:.1f}x"
        else:
            speedup_str = "N/A"

        print(f"{n_vectors:>10,} | {operation:<20} | {rust_str:>12} | {spark_str:>12} | {speedup_str:>10}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark fast_lsh_ann vs Spark LSH")
    parser.add_argument(
        "--sizes",
        type=str,
        default="1000,10000,100000",
        help="Comma-separated list of dataset sizes to test",
    )
    parser.add_argument(
        "--dim",
        type=int,
        default=128,
        help="Embedding dimension",
    )
    parser.add_argument(
        "--rust-only",
        action="store_true",
        help="Only run Rust benchmark (skip Spark)",
    )
    parser.add_argument(
        "--bucket-length",
        type=float,
        default=2.0,
        help="LSH bucket length",
    )
    parser.add_argument(
        "--num-hash-tables",
        type=int,
        default=5,
        help="Number of hash tables",
    )

    args = parser.parse_args()

    if not HAS_DELTA:
        print("Error: deltalake and polars are required.")
        print("Install with: uv pip install deltalake polars")
        return

    sizes = [int(s.strip()) for s in args.sizes.split(",")]

    print("=" * 60)
    print("fast_lsh_ann Benchmark")
    print("=" * 60)
    print(f"Sizes: {sizes}")
    print(f"Dimension: {args.dim}")
    print(f"Bucket length: {args.bucket_length}")
    print(f"Hash tables: {args.num_hash_tables}")
    print(f"Spark available: {HAS_SPARK}")

    results = run_benchmark(
        sizes=sizes,
        dim=args.dim,
        bucket_length=args.bucket_length,
        num_hash_tables=args.num_hash_tables,
        rust_only=args.rust_only,
    )

    print_summary(results)

    print("\nDone!")


if __name__ == "__main__":
    main()
