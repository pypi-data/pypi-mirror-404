"""
TDD Tests for Fast LSH ANN - Write tests first, then implement.

These tests define the expected API and behavior based on Spark's
BucketedRandomProjectionLSH interface.
"""

import numpy as np
import pytest


class TestBucketedRandomProjectionLSH:
    """Tests for the BucketedRandomProjectionLSH estimator."""

    def test_import(self):
        """Should be importable from the package."""
        from fast_lsh_ann import BucketedRandomProjectionLSH
        assert BucketedRandomProjectionLSH is not None

    def test_create_with_defaults(self):
        """Should create estimator with default parameters."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        lsh = BucketedRandomProjectionLSH()
        assert lsh.bucket_length == 2.0
        assert lsh.num_hash_tables == 1
        assert lsh.seed is not None

    def test_create_with_params(self):
        """Should create estimator with custom parameters."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        lsh = BucketedRandomProjectionLSH(
            bucket_length=3.5,
            num_hash_tables=5,
            seed=12345
        )
        assert lsh.bucket_length == 3.5
        assert lsh.num_hash_tables == 5
        assert lsh.seed == 12345

    def test_fit_returns_model(self):
        """fit() should return a BucketedRandomProjectionLSHModel."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        lsh = BucketedRandomProjectionLSH(bucket_length=2.0, seed=42)
        vectors = np.random.randn(100, 8).astype(np.float32)

        model = lsh.fit(vectors)

        # Should return a model object
        assert model is not None
        assert hasattr(model, 'transform')
        assert hasattr(model, 'approx_nearest_neighbors')
        assert hasattr(model, 'approx_similarity_join')

    def test_fit_is_deterministic(self):
        """fit() with same seed should produce identical models."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        vectors = np.random.randn(50, 8).astype(np.float32)

        lsh1 = BucketedRandomProjectionLSH(bucket_length=2.0, seed=42)
        lsh2 = BucketedRandomProjectionLSH(bucket_length=2.0, seed=42)

        model1 = lsh1.fit(vectors)
        model2 = lsh2.fit(vectors)

        # Transform should produce identical results
        hashes1 = model1.transform(vectors)
        hashes2 = model2.transform(vectors)

        np.testing.assert_array_equal(hashes1, hashes2)


class TestBucketedRandomProjectionLSHModel:
    """Tests for the fitted model."""

    @pytest.fixture
    def fitted_model(self):
        """Create a fitted model for testing."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        np.random.seed(42)
        vectors = np.random.randn(100, 16).astype(np.float32)

        lsh = BucketedRandomProjectionLSH(
            bucket_length=2.0,
            num_hash_tables=3,
            seed=42
        )
        return lsh.fit(vectors), vectors

    def test_transform_returns_hashes(self, fitted_model):
        """transform() should return hash values for each vector."""
        model, vectors = fitted_model

        hashes = model.transform(vectors)

        # Should return array of shape (n_vectors, num_hash_tables)
        assert hashes.shape == (100, 3)
        assert hashes.dtype in [np.int32, np.int64]

    def test_transform_single_vector(self, fitted_model):
        """transform() should work with a single vector."""
        model, vectors = fitted_model

        single = vectors[0:1]  # Keep 2D shape
        hashes = model.transform(single)

        assert hashes.shape == (1, 3)

    def test_approx_nearest_neighbors_returns_results(self, fitted_model):
        """approx_nearest_neighbors() should return k nearest neighbors."""
        model, vectors = fitted_model

        query = np.random.randn(16).astype(np.float32)
        k = 5

        results = model.approx_nearest_neighbors(vectors, query, k)

        # Should return list of (index, distance) tuples
        assert len(results) <= k
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

        # Indices should be valid
        indices = [r[0] for r in results]
        assert all(0 <= idx < len(vectors) for idx in indices)

        # Distances should be non-negative
        distances = [r[1] for r in results]
        assert all(d >= 0 for d in distances)

        # Results should be sorted by distance
        assert distances == sorted(distances)

    def test_approx_nearest_neighbors_finds_exact_match(self, fitted_model):
        """Should find the exact vector when it exists in dataset."""
        model, vectors = fitted_model

        # Query with an existing vector
        query = vectors[42].copy()

        results = model.approx_nearest_neighbors(vectors, query, k=1)

        # Should find the exact match with distance ~0
        assert len(results) >= 1
        idx, dist = results[0]
        assert idx == 42
        assert dist < 1e-5

    def test_approx_similarity_join(self, fitted_model):
        """approx_similarity_join() should find pairs within threshold."""
        model, vectors = fitted_model

        # Create a second dataset with some similar vectors
        vectors_b = vectors[:20].copy() + np.random.randn(20, 16).astype(np.float32) * 0.5

        threshold = 5.0
        pairs = model.approx_similarity_join(vectors, vectors_b, threshold)

        # Should return list of (idx_a, idx_b, distance) tuples
        assert isinstance(pairs, list)
        for pair in pairs:
            assert len(pair) == 3
            idx_a, idx_b, dist = pair
            assert 0 <= idx_a < len(vectors)
            assert 0 <= idx_b < len(vectors_b)
            assert dist <= threshold

    def test_bucket_length_accessible(self, fitted_model):
        """Model should expose bucket_length parameter."""
        model, _ = fitted_model
        assert model.bucket_length == 2.0


class TestPerformance:
    """Performance and scaling tests."""

    def test_handles_large_dataset(self):
        """Should handle 100K vectors efficiently."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        # 100K vectors of 128 dimensions (typical embedding size)
        vectors = np.random.randn(100_000, 128).astype(np.float32)

        lsh = BucketedRandomProjectionLSH(
            bucket_length=4.0,
            num_hash_tables=5,
            seed=42
        )

        # Fit should complete without error
        model = lsh.fit(vectors)

        # Query should work
        query = np.random.randn(128).astype(np.float32)
        results = model.approx_nearest_neighbors(vectors, query, k=10)

        assert len(results) <= 10

    def test_batch_nearest_neighbors(self):
        """Should support batch queries for efficiency."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        vectors = np.random.randn(1000, 32).astype(np.float32)
        queries = np.random.randn(100, 32).astype(np.float32)

        lsh = BucketedRandomProjectionLSH(bucket_length=2.0, seed=42)
        model = lsh.fit(vectors)

        # Batch query method
        if hasattr(model, 'batch_approx_nearest_neighbors'):
            results = model.batch_approx_nearest_neighbors(vectors, queries, k=5)
            assert len(results) == 100
            assert all(len(r) <= 5 for r in results)


class TestEdgeCases:
    """Edge case handling tests."""

    def test_empty_result_when_no_candidates(self):
        """Should return empty when no vectors in matching buckets."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        # Very small bucket length = fine-grained buckets
        lsh = BucketedRandomProjectionLSH(bucket_length=0.001, seed=42)
        vectors = np.random.randn(10, 4).astype(np.float32)
        model = lsh.fit(vectors)

        # Query very far from all vectors
        query = np.ones(4).astype(np.float32) * 1000
        results = model.approx_nearest_neighbors(vectors, query, k=5)

        # May return empty or fewer results
        assert len(results) <= 5

    def test_k_larger_than_dataset(self):
        """Should handle k > dataset size gracefully."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        lsh = BucketedRandomProjectionLSH(bucket_length=10.0, seed=42)
        vectors = np.random.randn(5, 4).astype(np.float32)
        model = lsh.fit(vectors)

        query = np.random.randn(4).astype(np.float32)
        results = model.approx_nearest_neighbors(vectors, query, k=100)

        # Should return at most 5 results
        assert len(results) <= 5

    def test_similarity_join_threshold_zero(self):
        """Threshold=0 should only find exact matches."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        lsh = BucketedRandomProjectionLSH(bucket_length=2.0, seed=42)
        vectors = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
        model = lsh.fit(vectors)

        # vectors[0] and vectors[2] are identical
        pairs = model.approx_similarity_join(vectors, vectors, threshold=0.0)

        # Should find self-matches and the duplicate pair
        exact_pairs = [(p[0], p[1]) for p in pairs if p[2] == 0.0]
        assert (0, 2) in exact_pairs or (2, 0) in exact_pairs

    def test_different_dtypes_converted(self):
        """Should accept float64 and convert to float32."""
        from fast_lsh_ann import BucketedRandomProjectionLSH

        lsh = BucketedRandomProjectionLSH(bucket_length=2.0, seed=42)
        vectors_f64 = np.random.randn(10, 4)  # float64 by default

        # Should not raise
        model = lsh.fit(vectors_f64)
        hashes = model.transform(vectors_f64)

        assert hashes.shape[0] == 10
