"""
Streaming processor for large Delta tables.

Processes Delta tables chunk-by-chunk to handle files larger than memory.
Supports:
- Transform with streaming write
- Chunked similarity join
- Memory-efficient batch processing
"""

from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple, Callable
import numpy as np

try:
    import polars as pl
    from deltalake import DeltaTable, write_deltalake
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


def _check_deps():
    if not HAS_DEPS:
        raise ImportError(
            "Streaming requires 'deltalake' and 'polars'. "
            "Install with: uv pip install deltalake polars"
        )


@dataclass
class ChunkResult:
    """Result from processing a single chunk."""
    chunk_idx: int
    start_row: int
    n_rows: int
    hashes: np.ndarray
    ids: Optional[np.ndarray] = None


class StreamingLSHProcessor:
    """
    Process large Delta tables in a streaming fashion.

    This processor reads and processes data in chunks, never loading
    the entire dataset into memory at once.

    Example:
        processor = StreamingLSHProcessor(
            bucket_length=2.0,
            num_hash_tables=5,
            seed=42,
            chunk_size=50000,
        )

        # Stream transform and write results
        processor.transform_to_delta(
            input_path="/path/to/input",
            output_path="/path/to/output",
            embedding_column="embedding",
        )

        # Stream similarity join
        for pairs_chunk in processor.similarity_join_streaming(
            path_a="/path/to/delta_a",
            path_b="/path/to/delta_b",
            threshold=5.0,
        ):
            # Process each chunk of pairs
            save_pairs(pairs_chunk)
    """

    def __init__(
        self,
        bucket_length: float = 2.0,
        num_hash_tables: int = 5,
        seed: int = 42,
        chunk_size: int = 50000,
        dim: Optional[int] = None,
    ):
        _check_deps()
        from fast_lsh_ann import BucketedRandomProjectionLSH

        self.bucket_length = bucket_length
        self.num_hash_tables = num_hash_tables
        self.seed = seed
        self.chunk_size = chunk_size
        self._dim = dim

        self._lsh = BucketedRandomProjectionLSH(
            bucket_length=bucket_length,
            num_hash_tables=num_hash_tables,
            seed=seed,
        )
        self._model = None

    def _ensure_model(self, dim: int):
        """Create model if not exists or dim changed."""
        if self._model is None or self._dim != dim:
            self._model = self._lsh.create_model(dim=dim)
            self._dim = dim

    def _iter_chunks(
        self,
        path: str,
        embedding_column: str,
        id_column: Optional[str] = None,
    ) -> Iterator[Tuple[np.ndarray, Optional[np.ndarray], int]]:
        """Iterate over chunks of a Delta table."""
        dt = DeltaTable(path)

        # Use PyArrow dataset for efficient chunked reading
        dataset = dt.to_pyarrow_dataset()

        start_row = 0
        for batch in dataset.to_batches(batch_size=self.chunk_size):
            df = pl.from_arrow(batch)

            embeddings = np.vstack(df[embedding_column].to_list()).astype(np.float32)

            ids = None
            if id_column and id_column in df.columns:
                ids = df[id_column].to_numpy()

            yield embeddings, ids, start_row
            start_row += len(embeddings)

    def transform_streaming(
        self,
        path: str,
        embedding_column: str = "embedding",
        id_column: Optional[str] = None,
    ) -> Iterator[ChunkResult]:
        """
        Transform a Delta table in streaming fashion.

        Yields ChunkResult for each processed chunk.
        """
        for chunk_idx, (embeddings, ids, start_row) in enumerate(
            self._iter_chunks(path, embedding_column, id_column)
        ):
            self._ensure_model(embeddings.shape[1])
            hashes = self._model.transform(embeddings)

            yield ChunkResult(
                chunk_idx=chunk_idx,
                start_row=start_row,
                n_rows=len(embeddings),
                hashes=hashes,
                ids=ids,
            )

    def transform_to_delta(
        self,
        input_path: str,
        output_path: str,
        embedding_column: str = "embedding",
        id_column: Optional[str] = "id",
        include_embeddings: bool = False,
    ):
        """
        Transform Delta table and write results to new Delta table.

        Args:
            input_path: Input Delta table path
            output_path: Output Delta table path
            embedding_column: Column containing embeddings
            id_column: ID column to preserve
            include_embeddings: Whether to include original embeddings in output
        """
        first_chunk = True

        for chunk_result in self.transform_streaming(input_path, embedding_column, id_column):
            # Build output dataframe
            data = {
                f"hash_{i}": chunk_result.hashes[:, i].tolist()
                for i in range(chunk_result.hashes.shape[1])
            }

            if chunk_result.ids is not None:
                data["id"] = chunk_result.ids.tolist()
            else:
                data["id"] = list(range(
                    chunk_result.start_row,
                    chunk_result.start_row + chunk_result.n_rows
                ))

            df = pl.DataFrame(data)

            # Write chunk
            mode = "overwrite" if first_chunk else "append"
            write_deltalake(output_path, df.to_arrow(), mode=mode)
            first_chunk = False

            print(f"  Wrote chunk {chunk_result.chunk_idx}: rows {chunk_result.start_row} - {chunk_result.start_row + chunk_result.n_rows}")

    def similarity_join_streaming(
        self,
        path_a: str,
        path_b: str,
        threshold: float,
        embedding_column: str = "embedding",
        id_column: Optional[str] = "id",
    ) -> Iterator[List[Tuple[int, int, float]]]:
        """
        Perform similarity join in streaming fashion.

        Strategy:
        1. Load and hash dataset B entirely (assumed smaller or fits in memory)
        2. Stream through dataset A in chunks
        3. For each chunk of A, find matches in B

        Yields:
            List of (id_a, id_b, distance) tuples for each chunk
        """
        # Load dataset B (assumed to fit in memory)
        dt_b = DeltaTable(path_b)
        df_b = pl.from_arrow(dt_b.to_pyarrow_table())

        embeddings_b = np.vstack(df_b[embedding_column].to_list()).astype(np.float32)
        ids_b = df_b[id_column].to_numpy() if id_column in df_b.columns else np.arange(len(embeddings_b))

        self._ensure_model(embeddings_b.shape[1])

        # Hash dataset B
        hashes_b = self._model.transform(embeddings_b)

        # Build hash -> indices lookup for B
        from collections import defaultdict
        hash_to_indices_b = defaultdict(list)
        for idx in range(len(hashes_b)):
            for table_idx in range(hashes_b.shape[1]):
                hash_val = hashes_b[idx, table_idx]
                hash_to_indices_b[(table_idx, hash_val)].append(idx)

        # Stream through dataset A
        for embeddings_a, ids_a_chunk, start_row in self._iter_chunks(
            path_a, embedding_column, id_column
        ):
            if ids_a_chunk is None:
                ids_a_chunk = np.arange(start_row, start_row + len(embeddings_a))

            hashes_a = self._model.transform(embeddings_a)

            # Find candidates and compute distances
            pairs = []
            for idx_a in range(len(embeddings_a)):
                candidates_b = set()

                # Check all hash tables
                for table_idx in range(hashes_a.shape[1]):
                    hash_val = hashes_a[idx_a, table_idx]
                    candidates_b.update(hash_to_indices_b.get((table_idx, hash_val), []))

                # Compute exact distances for candidates
                for idx_b in candidates_b:
                    dist = np.sqrt(np.sum((embeddings_a[idx_a] - embeddings_b[idx_b]) ** 2))
                    if dist <= threshold:
                        pairs.append((ids_a_chunk[idx_a], ids_b[idx_b], float(dist)))

            yield pairs

    def similarity_join_chunked_both(
        self,
        path_a: str,
        path_b: str,
        threshold: float,
        embedding_column: str = "embedding",
        id_column: Optional[str] = "id",
        output_path: Optional[str] = None,
    ) -> Optional[int]:
        """
        Similarity join when both datasets are large.

        Strategy: Nested loop over chunks (O(chunks_a * chunks_b))

        Returns:
            Total number of pairs found (if no output_path)
            or writes to output_path and returns None
        """
        total_pairs = 0
        first_write = True

        # Iterate over chunks of A
        for embeddings_a, ids_a, start_a in self._iter_chunks(path_a, embedding_column, id_column):
            if ids_a is None:
                ids_a = np.arange(start_a, start_a + len(embeddings_a))

            self._ensure_model(embeddings_a.shape[1])
            hashes_a = self._model.transform(embeddings_a)

            # For each chunk of A, iterate over all chunks of B
            for embeddings_b, ids_b, start_b in self._iter_chunks(path_b, embedding_column, id_column):
                if ids_b is None:
                    ids_b = np.arange(start_b, start_b + len(embeddings_b))

                hashes_b = self._model.transform(embeddings_b)

                # Build hash lookup for this B chunk
                from collections import defaultdict
                hash_to_indices_b = defaultdict(list)
                for idx in range(len(hashes_b)):
                    for table_idx in range(hashes_b.shape[1]):
                        hash_val = hashes_b[idx, table_idx]
                        hash_to_indices_b[(table_idx, hash_val)].append(idx)

                # Find pairs
                pairs = []
                for idx_a in range(len(embeddings_a)):
                    candidates_b = set()
                    for table_idx in range(hashes_a.shape[1]):
                        hash_val = hashes_a[idx_a, table_idx]
                        candidates_b.update(hash_to_indices_b.get((table_idx, hash_val), []))

                    for idx_b in candidates_b:
                        dist = np.sqrt(np.sum((embeddings_a[idx_a] - embeddings_b[idx_b]) ** 2))
                        if dist <= threshold:
                            pairs.append((int(ids_a[idx_a]), int(ids_b[idx_b]), float(dist)))

                total_pairs += len(pairs)

                # Write results if output path specified
                if output_path and pairs:
                    df = pl.DataFrame({
                        "id_a": [p[0] for p in pairs],
                        "id_b": [p[1] for p in pairs],
                        "distance": [p[2] for p in pairs],
                    })
                    mode = "overwrite" if first_write else "append"
                    write_deltalake(output_path, df.to_arrow(), mode=mode)
                    first_write = False

        if output_path:
            return None
        return total_pairs


def benchmark_streaming(
    n_vectors: int = 100000,
    dim: int = 128,
    chunk_size: int = 10000,
):
    """Benchmark streaming processor."""
    import tempfile
    import time
    import os

    _check_deps()
    from fast_lsh_ann import create_sample_delta

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input")
        output_path = os.path.join(tmpdir, "output")

        # Create sample data
        print(f"Creating sample Delta table with {n_vectors:,} vectors...")
        create_sample_delta(input_path, n_vectors, dim)

        # Process with streaming
        processor = StreamingLSHProcessor(
            bucket_length=2.0,
            num_hash_tables=5,
            seed=42,
            chunk_size=chunk_size,
        )

        print(f"\nStreaming transform (chunk_size={chunk_size:,})...")
        start = time.perf_counter()
        processor.transform_to_delta(input_path, output_path)
        elapsed = time.perf_counter() - start

        print(f"\nCompleted in {elapsed:.2f}s ({n_vectors/elapsed:,.0f} vectors/sec)")

        # Verify output
        dt = DeltaTable(output_path)
        df = pl.from_arrow(dt.to_pyarrow_table())
        print(f"Output table: {len(df):,} rows, {len(df.columns)} columns")


if __name__ == "__main__":
    benchmark_streaming()
