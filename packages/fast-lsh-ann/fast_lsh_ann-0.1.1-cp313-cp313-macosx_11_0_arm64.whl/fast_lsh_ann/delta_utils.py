"""
Delta Lake utilities for fast_lsh_ann.

Provides zero-copy integration with Delta tables using the pure Rust stack:
- deltalake (Rust) for reading Delta
- polars (Rust) for DataFrame operations
- fast_lsh_ann (Rust) for LSH

No Spark required!
"""

from typing import Iterator, Optional, Tuple, List
import numpy as np

try:
    import polars as pl
    from deltalake import DeltaTable
    HAS_DELTA = True
except ImportError:
    HAS_DELTA = False


def check_dependencies():
    """Check if Delta dependencies are installed."""
    if not HAS_DELTA:
        raise ImportError(
            "Delta utilities require 'deltalake' and 'polars'. "
            "Install with: uv pip install deltalake polars"
        )


def read_delta_embeddings(
    path: str,
    embedding_column: str = "embedding",
    id_column: Optional[str] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Read embeddings from a Delta table.

    Args:
        path: Path to Delta table
        embedding_column: Name of the column containing embeddings
        id_column: Optional ID column to return

    Returns:
        Tuple of (embeddings array, optional ids array)
    """
    check_dependencies()

    dt = DeltaTable(path)
    df = pl.from_arrow(dt.to_pyarrow_table())

    # Extract embeddings as numpy array
    embeddings = np.vstack(df[embedding_column].to_list()).astype(np.float32)

    ids = None
    if id_column and id_column in df.columns:
        ids = df[id_column].to_numpy()

    return embeddings, ids


def read_delta_embeddings_chunked(
    path: str,
    embedding_column: str = "embedding",
    id_column: Optional[str] = None,
    chunk_size: int = 10000,
) -> Iterator[Tuple[np.ndarray, Optional[np.ndarray], int]]:
    """
    Read embeddings from a Delta table in chunks.

    Yields:
        Tuple of (embeddings chunk, optional ids chunk, start_index)
    """
    check_dependencies()

    dt = DeltaTable(path)
    df = pl.from_arrow(dt.to_pyarrow_table())

    total_rows = len(df)

    for start in range(0, total_rows, chunk_size):
        chunk = df.slice(start, chunk_size)

        embeddings = np.vstack(chunk[embedding_column].to_list()).astype(np.float32)

        ids = None
        if id_column and id_column in chunk.columns:
            ids = chunk[id_column].to_numpy()

        yield embeddings, ids, start


def read_delta_lazy(
    path: str,
    embedding_column: str = "embedding",
    id_column: Optional[str] = None,
    row_limit: Optional[int] = None,
) -> pl.LazyFrame:
    """
    Get a lazy frame for a Delta table.

    This allows building a query plan before execution.
    """
    check_dependencies()

    dt = DeltaTable(path)
    lf = pl.scan_pyarrow_dataset(dt.to_pyarrow_dataset())

    columns = [embedding_column]
    if id_column:
        columns.append(id_column)

    lf = lf.select(columns)

    if row_limit:
        lf = lf.limit(row_limit)

    return lf


class DeltaLSHProcessor:
    """
    Process Delta table embeddings with LSH.

    Example:
        processor = DeltaLSHProcessor(
            bucket_length=2.0,
            num_hash_tables=5,
            seed=42
        )

        # Transform and get hashes
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
    """

    def __init__(
        self,
        bucket_length: float = 2.0,
        num_hash_tables: int = 5,
        seed: int = 42,
    ):
        check_dependencies()
        from fast_lsh_ann import BucketedRandomProjectionLSH

        self.bucket_length = bucket_length
        self.num_hash_tables = num_hash_tables
        self.seed = seed
        self._lsh = BucketedRandomProjectionLSH(
            bucket_length=bucket_length,
            num_hash_tables=num_hash_tables,
            seed=seed,
        )
        self._model = None
        self._dim = None

    def _ensure_model(self, dim: int):
        """Ensure model is created with correct dimensions."""
        if self._model is None or self._dim != dim:
            self._model = self._lsh.create_model(dim=dim)
            self._dim = dim

    def transform_delta(
        self,
        path: str,
        embedding_column: str = "embedding",
        id_column: Optional[str] = "id",
        chunk_size: int = 50000,
    ) -> pl.DataFrame:
        """
        Transform all embeddings in a Delta table to LSH hashes.

        Args:
            path: Path to Delta table
            embedding_column: Column containing embeddings
            id_column: Optional ID column to preserve
            chunk_size: Process in chunks of this size

        Returns:
            Polars DataFrame with id and hash columns
        """
        results = []

        for embeddings, ids, start_idx in read_delta_embeddings_chunked(
            path, embedding_column, id_column, chunk_size
        ):
            self._ensure_model(embeddings.shape[1])
            hashes = self._model.transform(embeddings)

            chunk_data = {
                f"hash_{i}": hashes[:, i].tolist()
                for i in range(hashes.shape[1])
            }

            if ids is not None:
                chunk_data["id"] = ids.tolist()
            else:
                chunk_data["id"] = list(range(start_idx, start_idx + len(embeddings)))

            results.append(pl.DataFrame(chunk_data))

        return pl.concat(results)

    def similarity_join_delta(
        self,
        path_a: str,
        path_b: str,
        threshold: float,
        embedding_column: str = "embedding",
        id_column: Optional[str] = "id",
        chunk_size: int = 10000,
    ) -> List[Tuple[int, int, float]]:
        """
        Perform similarity join between two Delta tables.

        Args:
            path_a: Path to first Delta table
            path_b: Path to second Delta table
            threshold: Distance threshold
            embedding_column: Column containing embeddings
            id_column: ID column name
            chunk_size: Process in chunks

        Returns:
            List of (id_a, id_b, distance) tuples
        """
        # Load both datasets
        embeddings_a, ids_a = read_delta_embeddings(path_a, embedding_column, id_column)
        embeddings_b, ids_b = read_delta_embeddings(path_b, embedding_column, id_column)

        self._ensure_model(embeddings_a.shape[1])

        # Use the Rust similarity join
        pairs = self._model.approx_similarity_join(embeddings_a, embeddings_b, threshold)

        # Map back to original IDs if available
        if ids_a is not None and ids_b is not None:
            pairs = [(ids_a[a], ids_b[b], d) for a, b, d in pairs]

        return pairs

    def transform_and_save(
        self,
        input_path: str,
        output_path: str,
        embedding_column: str = "embedding",
        id_column: Optional[str] = "id",
        chunk_size: int = 50000,
    ):
        """
        Transform Delta table and save with hash columns.

        Args:
            input_path: Input Delta table path
            output_path: Output Delta table path
            embedding_column: Column containing embeddings
            id_column: ID column to preserve
            chunk_size: Chunk size for processing
        """
        from deltalake import write_deltalake

        result_df = self.transform_delta(
            input_path, embedding_column, id_column, chunk_size
        )

        write_deltalake(output_path, result_df.to_arrow(), mode="overwrite")


def create_sample_delta(
    path: str,
    n_vectors: int = 10000,
    dim: int = 128,
    seed: int = 42,
):
    """
    Create a sample Delta table with random embeddings for testing.

    Args:
        path: Path to create Delta table
        n_vectors: Number of vectors
        dim: Embedding dimension
        seed: Random seed
    """
    check_dependencies()
    from deltalake import write_deltalake

    np.random.seed(seed)
    embeddings = np.random.randn(n_vectors, dim).astype(np.float32)

    df = pl.DataFrame({
        "id": range(n_vectors),
        "embedding": embeddings.tolist(),
    })

    write_deltalake(path, df.to_arrow(), mode="overwrite")
    print(f"Created Delta table at {path} with {n_vectors} vectors of dim {dim}")
