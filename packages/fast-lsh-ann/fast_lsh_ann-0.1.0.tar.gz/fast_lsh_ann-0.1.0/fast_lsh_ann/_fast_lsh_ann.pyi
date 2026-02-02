"""Type stubs for fast_lsh_ann._fast_lsh_ann"""

from typing import List, Tuple
import numpy as np
from numpy.typing import NDArray

class BucketedRandomProjectionLSH:
    """
    Bucketed Random Projection LSH estimator.

    Similar to Spark's BucketedRandomProjectionLSH, this class implements
    Locality Sensitive Hashing using random projections for approximate
    nearest neighbor search with Euclidean distance.

    Args:
        bucket_length: The bucket length (width) for the hash function.
            Larger values create coarser buckets, increasing recall but slowing queries.
            Default: 2.0
        num_hash_tables: Number of hash tables to use.
            More tables increase recall at the cost of memory and indexing time.
            Default: 1
        seed: Random seed for reproducibility. Default: 42
    """

    bucket_length: float
    num_hash_tables: int
    seed: int

    def __init__(
        self,
        bucket_length: float = 2.0,
        num_hash_tables: int = 1,
        seed: int = 42,
    ) -> None: ...

    def fit(self, vectors: NDArray[np.float32]) -> BucketedRandomProjectionLSHModel:
        """
        Fit the estimator on a dataset.

        Args:
            vectors: A 2D numpy array of shape (n_samples, n_features)

        Returns:
            A fitted BucketedRandomProjectionLSHModel
        """
        ...

class BucketedRandomProjectionLSHModel:
    """
    Fitted BucketedRandomProjectionLSH model.

    This model can transform vectors to hash values, find approximate
    nearest neighbors, and perform similarity joins.
    """

    bucket_length: float
    num_hash_tables: int

    def transform(self, vectors: NDArray[np.float32]) -> NDArray[np.int64]:
        """
        Transform vectors to hash values.

        Args:
            vectors: A 2D numpy array of shape (n_samples, n_features)

        Returns:
            A 2D numpy array of shape (n_samples, num_hash_tables) with hash values
        """
        ...

    def approx_nearest_neighbors(
        self,
        vectors: NDArray[np.float32],
        query: NDArray[np.float32],
        k: int,
    ) -> List[Tuple[int, float]]:
        """
        Find approximate k nearest neighbors.

        Args:
            vectors: The dataset to search in (n_samples, n_features)
            query: A 1D query vector (n_features,)
            k: Number of nearest neighbors to return

        Returns:
            List of (index, distance) tuples sorted by distance
        """
        ...

    def batch_approx_nearest_neighbors(
        self,
        vectors: NDArray[np.float32],
        queries: NDArray[np.float32],
        k: int,
    ) -> List[List[Tuple[int, float]]]:
        """
        Find approximate k nearest neighbors for multiple queries (batch).

        Args:
            vectors: The dataset to search in (n_samples, n_features)
            queries: Multiple query vectors (n_queries, n_features)
            k: Number of nearest neighbors to return per query

        Returns:
            List of lists of (index, distance) tuples
        """
        ...

    def approx_similarity_join(
        self,
        vectors_a: NDArray[np.float32],
        vectors_b: NDArray[np.float32],
        threshold: float,
    ) -> List[Tuple[int, int, float]]:
        """
        Approximate similarity join.

        Find all pairs of vectors from two datasets within a distance threshold.

        Args:
            vectors_a: First dataset (n_a, n_features)
            vectors_b: Second dataset (n_b, n_features)
            threshold: Maximum distance threshold

        Returns:
            List of (idx_a, idx_b, distance) tuples
        """
        ...
