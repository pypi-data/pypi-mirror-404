"""
Fast LSH ANN - High-performance Bucketed Random Projection LSH

A Rust-powered Python library for approximate nearest neighbor search
using Locality Sensitive Hashing with random projections.

Compatible with Apache Spark's BucketedRandomProjectionLSH API.

Example:
    >>> from fast_lsh_ann import BucketedRandomProjectionLSH
    >>> import numpy as np
    >>>
    >>> # Create estimator
    >>> lsh = BucketedRandomProjectionLSH(bucket_length=2.0, num_hash_tables=5, seed=42)
    >>>
    >>> # Fit on vectors
    >>> vectors = np.random.randn(10000, 128).astype(np.float32)
    >>> model = lsh.fit(vectors)
    >>>
    >>> # Find nearest neighbors
    >>> query = np.random.randn(128).astype(np.float32)
    >>> results = model.approx_nearest_neighbors(vectors, query, k=10)
    >>> print(results)  # [(idx, distance), ...]
"""

from fast_lsh_ann._fast_lsh_ann import (
    BucketedRandomProjectionLSH,
    BucketedRandomProjectionLSHModel,
)

# Delta utilities (optional, requires deltalake + polars)
try:
    from fast_lsh_ann.delta_utils import (
        DeltaLSHProcessor,
        read_delta_embeddings,
        read_delta_embeddings_chunked,
        create_sample_delta,
    )
    from fast_lsh_ann.streaming import (
        StreamingLSHProcessor,
        ChunkResult,
    )
    _HAS_DELTA = True
except ImportError:
    _HAS_DELTA = False

__all__ = [
    "BucketedRandomProjectionLSH",
    "BucketedRandomProjectionLSHModel",
]

if _HAS_DELTA:
    __all__ += [
        "DeltaLSHProcessor",
        "read_delta_embeddings",
        "read_delta_embeddings_chunked",
        "create_sample_delta",
        "StreamingLSHProcessor",
        "ChunkResult",
    ]

__version__ = "0.1.0"
