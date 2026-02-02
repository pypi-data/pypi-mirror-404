"""
Databricks Example: LSH Transform on Delta Table

This example shows how to use fast_lsh_ann with Delta tables in Databricks.
The key insight: LSH model only needs (bucket_length, num_hash_tables, seed, dim)
to generate the random projections. No fitting on data required!

Workflow:
1. Create model once (just needs dim)
2. Broadcast model to workers
3. Transform partitions in parallel using Spark UDF
4. Write hashes back to Delta
5. Similarity join via hash-based grouping
"""

# =============================================================================
# OPTION 1: Using Spark UDF (recommended for large Delta tables)
# =============================================================================

def print_spark_code():
    """Print the Spark UDF code for copy-paste to Databricks."""
    code = '''
# ============= COPY THIS TO DATABRICKS =============
from pyspark.sql.functions import pandas_udf, col
from pyspark.sql.types import ArrayType, LongType
import pandas as pd
import numpy as np

# Configuration
DIM = 128  # Your embedding dimension
BUCKET_LENGTH = 2.0
NUM_HASH_TABLES = 5
SEED = 42

@pandas_udf(ArrayType(LongType()))
def transform_embeddings(embeddings_series: pd.Series) -> pd.Series:
    """Transform embeddings to LSH hashes."""
    from fast_lsh_ann import BucketedRandomProjectionLSH
    import numpy as np

    # Create model (same params = same random projections)
    lsh = BucketedRandomProjectionLSH(
        bucket_length=BUCKET_LENGTH,
        num_hash_tables=NUM_HASH_TABLES,
        seed=SEED
    )
    model = lsh.create_model(dim=DIM)

    # Transform batch
    vectors = np.vstack(embeddings_series.values).astype(np.float32)
    hashes = model.transform(vectors)
    return pd.Series([row.tolist() for row in hashes])

# Apply to Delta table
df = spark.read.format("delta").load("/path/to/embeddings")
df_with_hashes = df.withColumn("lsh_hashes", transform_embeddings(col("embedding")))
df_with_hashes.write.format("delta").mode("overwrite").save("/path/to/output")
# ====================================================
'''
    print(code)


def spark_udf_example():
    """
    Use Spark UDF to transform embeddings in parallel.
    Works with any Delta table size.
    """
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import udf, col, pandas_udf
        from pyspark.sql.types import ArrayType, LongType
        import pandas as pd
    except ImportError:
        print("PySpark not installed - this example runs in Databricks")
        print("See the code below for the implementation:")
        print_spark_code()
        return

    import numpy as np

    # In Databricks, spark is already available
    # spark = SparkSession.builder.getOrCreate()

    # ----- Step 1: Create model (no data needed!) -----
    from fast_lsh_ann import BucketedRandomProjectionLSH

    DIM = 128  # Your embedding dimension
    lsh = BucketedRandomProjectionLSH(
        bucket_length=2.0,
        num_hash_tables=5,
        seed=42
    )
    model = lsh.create_model(dim=DIM)

    # ----- Step 2: Broadcast model to workers -----
    # model_broadcast = spark.sparkContext.broadcast(model)

    # ----- Step 3: Define Pandas UDF for batch transform -----
    @pandas_udf(ArrayType(LongType()))
    def transform_embeddings(embeddings_series: pd.Series) -> pd.Series:
        """Transform a batch of embeddings to LSH hashes."""
        import numpy as np
        from fast_lsh_ann import BucketedRandomProjectionLSH

        # Recreate model (same params = same random projections)
        lsh = BucketedRandomProjectionLSH(
            bucket_length=2.0,
            num_hash_tables=5,
            seed=42
        )
        model = lsh.create_model(dim=DIM)

        # Stack embeddings into matrix
        vectors = np.vstack(embeddings_series.values).astype(np.float32)

        # Transform
        hashes = model.transform(vectors)

        # Return as list of lists
        return pd.Series([row.tolist() for row in hashes])

    # ----- Step 4: Apply to Delta table -----
    """
    # Read Delta table
    df = spark.read.format("delta").load("/path/to/embeddings")

    # Transform embeddings
    df_with_hashes = df.withColumn(
        "lsh_hashes",
        transform_embeddings(col("embedding"))
    )

    # Write back to Delta
    df_with_hashes.write.format("delta").mode("overwrite").save("/path/to/output")
    """

    print("Spark UDF example ready - uncomment Spark code to run in Databricks")


# =============================================================================
# OPTION 2: Using Polars for single-node processing
# =============================================================================

def polars_chunked_example():
    """
    Use Polars to process Delta/Parquet in chunks.
    Good for single-node processing of medium datasets.
    """
    import polars as pl
    import numpy as np
    from fast_lsh_ann import BucketedRandomProjectionLSH

    # Create model
    DIM = 128
    lsh = BucketedRandomProjectionLSH(
        bucket_length=2.0,
        num_hash_tables=5,
        seed=42
    )
    model = lsh.create_model(dim=DIM)

    # Simulate reading from Delta (in practice: pl.scan_delta or pl.scan_parquet)
    # For demo, create sample data
    n_vectors = 10000
    vectors = np.random.randn(n_vectors, DIM).astype(np.float32)
    ids = list(range(n_vectors))

    df = pl.DataFrame({
        "id": ids,
        "embedding": vectors.tolist()
    })

    print(f"Input DataFrame: {df.shape}")

    # Transform in chunks
    CHUNK_SIZE = 1000
    results = []

    for i in range(0, len(df), CHUNK_SIZE):
        chunk = df.slice(i, CHUNK_SIZE)

        # Extract embeddings as numpy array
        embeddings = np.array(chunk["embedding"].to_list(), dtype=np.float32)

        # Transform
        hashes = model.transform(embeddings)

        # Add hashes to chunk
        chunk_with_hashes = chunk.with_columns(
            pl.Series("lsh_hashes", hashes.tolist())
        )
        results.append(chunk_with_hashes)

    # Combine results
    df_result = pl.concat(results)
    print(f"Output DataFrame: {df_result.shape}")
    print(f"Sample row:\n{df_result.head(1)}")

    return df_result


# =============================================================================
# OPTION 3: Similarity Join via Hash Grouping
# =============================================================================

def similarity_join_example():
    """
    Perform similarity join by grouping on hash values.
    This is the scalable approach for large datasets.
    """
    import polars as pl
    import numpy as np
    from fast_lsh_ann import BucketedRandomProjectionLSH

    # Create model
    DIM = 32
    lsh = BucketedRandomProjectionLSH(
        bucket_length=4.0,
        num_hash_tables=3,
        seed=42
    )
    model = lsh.create_model(dim=DIM)

    # Create two datasets
    np.random.seed(42)
    n_a, n_b = 1000, 500

    vectors_a = np.random.randn(n_a, DIM).astype(np.float32)
    vectors_b = np.random.randn(n_b, DIM).astype(np.float32)

    # Make some vectors similar
    vectors_b[:50] = vectors_a[:50] + np.random.randn(50, DIM).astype(np.float32) * 0.1

    # Transform both
    hashes_a = model.transform(vectors_a)
    hashes_b = model.transform(vectors_b)

    # Create DataFrames with hash columns
    df_a = pl.DataFrame({
        "id_a": range(n_a),
        "embedding_a": vectors_a.tolist(),
        **{f"hash_{i}": hashes_a[:, i].tolist() for i in range(hashes_a.shape[1])}
    })

    df_b = pl.DataFrame({
        "id_b": range(n_b),
        "embedding_b": vectors_b.tolist(),
        **{f"hash_{i}": hashes_b[:, i].tolist() for i in range(hashes_b.shape[1])}
    })

    print(f"Dataset A: {df_a.shape}, Dataset B: {df_b.shape}")

    # Join on any matching hash (OR of all hash tables)
    # This is the candidate generation step
    candidates = set()

    for hash_col in [f"hash_{i}" for i in range(hashes_a.shape[1])]:
        joined = df_a.select(["id_a", hash_col]).join(
            df_b.select(["id_b", hash_col]),
            on=hash_col,
            how="inner"
        )
        for row in joined.iter_rows():
            candidates.add((row[0], row[1]))

    print(f"Candidate pairs from LSH: {len(candidates)}")

    # Compute exact distances for candidates
    def euclidean_dist(v1, v2):
        return np.sqrt(np.sum((np.array(v1) - np.array(v2)) ** 2))

    threshold = 5.0
    similar_pairs = []

    for id_a, id_b in candidates:
        v_a = vectors_a[id_a]
        v_b = vectors_b[id_b]
        dist = euclidean_dist(v_a, v_b)
        if dist <= threshold:
            similar_pairs.append((id_a, id_b, dist))

    print(f"Similar pairs (dist <= {threshold}): {len(similar_pairs)}")
    print(f"Sample pairs: {similar_pairs[:5]}")

    return similar_pairs


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Databricks / Large Scale LSH Examples")
    print("=" * 60)

    print("\n--- Polars Chunked Example ---")
    polars_chunked_example()

    print("\n--- Similarity Join Example ---")
    similarity_join_example()

    print("\n--- Spark UDF Example ---")
    spark_udf_example()
