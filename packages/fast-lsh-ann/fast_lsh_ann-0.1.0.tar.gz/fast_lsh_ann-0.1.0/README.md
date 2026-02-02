# Fast LSH ANN

High-performance Bucketed Random Projection LSH for Approximate Nearest Neighbor search.

Built this coz Spark's LSH was too slow for my use case. Its a pure Rust stack that beats Spark on single-node workloads:
- `deltalake` (Rust) -> `polars` (Rust) -> `fast_lsh_ann` (Rust)
- No JVM, no Spark overhead, no serialization penalties

## Installation

```bash
uv add fast_lsh_ann

# if u need Delta Lake support
uv add fast_lsh_ann deltalake polars
```

## Quick Start

```python
from fast_lsh_ann import BucketedRandomProjectionLSH
import numpy as np

# Create estimator
lsh = BucketedRandomProjectionLSH(
    bucket_length=2.0,
    num_hash_tables=5,
    seed=42
)

# Fit on vectors (use float32 for memory eficiency)
vectors = np.random.randn(100000, 128).astype(np.float32)
model = lsh.fit(vectors)

# Or create model without data (for distributed processing)
model = lsh.create_model(dim=128)

# Transform to hashes
hashes = model.transform(vectors)

# Find k nearest neighbors
query = np.random.randn(128).astype(np.float32)
results = model.approx_nearest_neighbors(vectors, query, k=10)
# Returns: [(idx, distance), ...]

# Batch queries (runs in parallel)
queries = np.random.randn(100, 128).astype(np.float32)
batch_results = model.batch_approx_nearest_neighbors(vectors, queries, k=10)

# Similarity join
vectors_b = np.random.randn(1000, 128).astype(np.float32)
pairs = model.approx_similarity_join(vectors, vectors_b, threshold=5.0)
# Returns: [(idx_a, idx_b, distance), ...]
```

## Delta Lake Integration

You can process Delta tables directly without Spark:

```python
from fast_lsh_ann import DeltaLSHProcessor, StreamingLSHProcessor

# Simple processing
processor = DeltaLSHProcessor(
    bucket_length=2.0,
    num_hash_tables=5,
    seed=42
)

# Transform Delta table
result_df = processor.transform_delta(
    "/path/to/delta",
    embedding_column="embedding"
)

# Similarity join between two Delta tables
pairs = processor.similarity_join_delta(
    "/path/to/delta_a",
    "/path/to/delta_b",
    threshold=5.0
)
```

## Streaming for Large Files

If your files are larger than memory, use the streaming processor:

```python
from fast_lsh_ann import StreamingLSHProcessor

processor = StreamingLSHProcessor(
    bucket_length=2.0,
    num_hash_tables=5,
    seed=42,
    chunk_size=50000,  # Process 50k vectors at a time
)

# Stream transform n write to Delta
processor.transform_to_delta(
    input_path="/path/to/large_delta",
    output_path="/path/to/output",
    embedding_column="embedding",
)

# Stream similarity join
for pairs_chunk in processor.similarity_join_streaming(
    path_a="/path/to/delta_a",
    path_b="/path/to/delta_b",
    threshold=5.0,
):
    save_pairs(pairs_chunk)
```

## Benchmarks

Run the benchmark to compare Rust vs Spark:

```bash
# Rust only
python benchmarks/spark_vs_rust.py --rust-only --sizes 1000,10000,100000

# With Spark (requires PySpark)
python benchmarks/spark_vs_rust.py --sizes 1000,10000,100000
```

Example results on M1 Mac, single node:

| Size | Operation | Rust | Throughput |
|------|-----------|------|------------|
| 100K | read_delta | 825ms | 121K/sec |
| 100K | transform | 451ms | 222K/sec |
| 100K | batch_nn (100 queries) | 3.8ms | 26K queries/sec |

## Pickle Support

Models are picklable so you can use em in distributed processing:

```python
import pickle

# Serialize (only 84 bytes!)
pickled = pickle.dumps(model)

# Deserialize
model2 = pickle.loads(pickled)
```

## API Reference

### BucketedRandomProjectionLSH

```python
BucketedRandomProjectionLSH(
    bucket_length: float = 2.0,  # Width of hash buckets
    num_hash_tables: int = 1,    # Number of hash tables (more = higher recall)
    seed: int = 42               # Random seed for reproducibility
)
```

Methods:
- `fit(vectors)` - Fit on data and create model
- `create_model(dim)` - Create model without data (useful for distributed use)

### BucketedRandomProjectionLSHModel

Properties:
- `bucket_length` - Bucket width
- `num_hash_tables` - Number of hash tables
- `dim` - Vector dimensionality
- `seed` - Random seed

Methods:
- `transform(vectors)` - Get hash values for vectors
- `approx_nearest_neighbors(vectors, query, k)` - Find k approximate nearest neighbors
- `batch_approx_nearest_neighbors(vectors, queries, k)` - Batch queries (parallel)
- `approx_similarity_join(vectors_a, vectors_b, threshold)` - Find all pairs within distance threshold
- `approx_similarity_join_cms(vectors_a, vectors_b, threshold, min_collisions)` - Memory-efficient join using Count-Min Sketch (slower but uses fixed ~10MB memory regardless of pair count)

## Development

```bash
# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install maturin numpy pytest deltalake polars

# Build and install in dev mode
maturin develop

# Run tests
pytest python_tests/ -v

# Run Rust tests
cargo test
```

## When to Use This vs Spark

| Scenario | Recommendation |
|----------|---------------|
| Data fits on single node | Use this library |
| Need Spark cluster features | Use Spark LSH |
| Interactive queries | Use this library |
| ETL pipeline already in Spark | Stick with Spark LSH |
| No Spark infrastructure | Use this library |

## License

MIT
