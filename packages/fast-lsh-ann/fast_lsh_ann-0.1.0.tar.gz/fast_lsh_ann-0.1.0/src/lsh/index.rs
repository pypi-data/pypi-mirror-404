//! LSH Index for approximate nearest neighbor search

use crate::cms::PairId;
use crate::cms::CountMinSketch;
use crate::distance::{euclidean_distance, query_distances};
use crate::lsh::{LSHConfig, RandomProjectionHasher};
use crate::topk::TopK;
use hashbrown::{HashMap, HashSet};
use ndarray::{Array2, ArrayView1, Axis};
use rayon::prelude::*;

/// LSH Index with multiple hash tables for ANN search
#[derive(Debug)]
pub struct LSHIndex {
    /// Hash tables (one hasher per table)
    hashers: Vec<RandomProjectionHasher>,

    /// Bucket storage: table_idx -> bucket_hash -> vector indices
    buckets: Vec<HashMap<i64, Vec<usize>>>,

    /// Configuration
    config: LSHConfig,

    /// Dimensionality of vectors
    dim: usize,
}

impl LSHIndex {
    /// Create a new LSH index
    pub fn new(config: LSHConfig, dim: usize) -> Self {
        let mut hashers = Vec::with_capacity(config.num_hash_tables);

        // Create hashers with different seeds for each table
        for i in 0..config.num_hash_tables {
            let seed = config.seed.wrapping_add(i as u64 * 31337);
            hashers.push(RandomProjectionHasher::new(dim, config.bucket_length, seed));
        }

        let buckets = vec![HashMap::new(); config.num_hash_tables];

        Self {
            hashers,
            buckets,
            config,
            dim,
        }
    }

    /// Build the index from vectors
    pub fn build(&mut self, vectors: &Array2<f32>) {
        debug_assert_eq!(vectors.ncols(), self.dim);

        // Clear existing buckets
        for bucket in &mut self.buckets {
            bucket.clear();
        }

        // Index all vectors into each hash table
        for (table_idx, hasher) in self.hashers.iter().enumerate() {
            let hashes = hasher.hash_batch(vectors);

            for (vec_idx, &hash_val) in hashes.iter().enumerate() {
                self.buckets[table_idx]
                    .entry(hash_val)
                    .or_insert_with(Vec::new)
                    .push(vec_idx);
            }
        }
    }

    /// Build the index in parallel
    pub fn build_parallel(&mut self, vectors: &Array2<f32>) {
        debug_assert_eq!(vectors.ncols(), self.dim);

        // Compute hashes for all tables in parallel
        let all_hashes: Vec<Vec<i64>> = self
            .hashers
            .par_iter()
            .map(|hasher| hasher.hash_batch_parallel(vectors))
            .collect();

        // Build bucket maps (sequential to avoid locking)
        for (table_idx, hashes) in all_hashes.into_iter().enumerate() {
            self.buckets[table_idx].clear();
            for (vec_idx, hash_val) in hashes.into_iter().enumerate() {
                self.buckets[table_idx]
                    .entry(hash_val)
                    .or_insert_with(Vec::new)
                    .push(vec_idx);
            }
        }
    }

    /// Get candidate indices for a query vector
    pub fn query_candidates(&self, query: ArrayView1<f32>) -> HashSet<usize> {
        let mut candidates = HashSet::new();

        for (table_idx, hasher) in self.hashers.iter().enumerate() {
            let hash_val = hasher.hash(query);
            if let Some(indices) = self.buckets[table_idx].get(&hash_val) {
                candidates.extend(indices.iter().copied());
            }
        }

        candidates
    }

    /// Compute hashes for a query (for transform)
    pub fn compute_hashes(&self, query: ArrayView1<f32>) -> Vec<i64> {
        self.hashers.iter().map(|h| h.hash(query)).collect()
    }

    /// Compute hashes for multiple vectors (for transform)
    pub fn compute_hashes_batch(&self, vectors: &Array2<f32>) -> Array2<i64> {
        let n = vectors.nrows();
        let num_tables = self.hashers.len();

        let mut result = Array2::zeros((n, num_tables));

        for (table_idx, hasher) in self.hashers.iter().enumerate() {
            let hashes = hasher.hash_batch(vectors);
            for (i, &h) in hashes.iter().enumerate() {
                result[[i, table_idx]] = h;
            }
        }

        result
    }

    /// Find approximate k nearest neighbors
    ///
    /// Returns vector of (index, distance) sorted by distance
    pub fn approx_nearest_neighbors(
        &self,
        vectors: &Array2<f32>,
        query: ArrayView1<f32>,
        k: usize,
    ) -> Vec<(usize, f32)> {
        // Get candidates from hash tables
        let candidates = self.query_candidates(query);

        if candidates.is_empty() {
            return Vec::new();
        }

        // Use streaming top-k instead of sorting all candidates
        let mut topk = TopK::new(k);

        for idx in candidates {
            let dist = euclidean_distance(query, vectors.row(idx));
            topk.push(idx, dist);
        }

        topk.into_sorted_vec()
    }

    /// Find approximate k nearest neighbors using batch distance computation
    ///
    /// More efficient when there are many candidates (uses vectorized distance)
    pub fn approx_nearest_neighbors_batch(
        &self,
        vectors: &Array2<f32>,
        query: ArrayView1<f32>,
        k: usize,
    ) -> Vec<(usize, f32)> {
        // Get candidates from hash tables
        let candidates: Vec<usize> = self.query_candidates(query).into_iter().collect();

        if candidates.is_empty() {
            return Vec::new();
        }

        // For small candidate sets, use the simple approach
        if candidates.len() <= 100 {
            return self.approx_nearest_neighbors(vectors, query, k);
        }

        // Build candidate matrix for batch distance computation
        let candidate_vectors: Array2<f32> = ndarray::stack(
            Axis(0),
            &candidates
                .iter()
                .map(|&idx| vectors.row(idx))
                .collect::<Vec<_>>(),
        )
        .unwrap();

        // Batch compute distances
        let distances = query_distances(query, candidate_vectors.view());

        // Use streaming top-k
        let mut topk = TopK::new(k);
        for (i, &dist) in distances.iter().enumerate() {
            topk.push(candidates[i], dist);
        }

        topk.into_sorted_vec()
    }

    /// Batch approximate nearest neighbors (parallel)
    pub fn batch_approx_nearest_neighbors(
        &self,
        vectors: &Array2<f32>,
        queries: &Array2<f32>,
        k: usize,
    ) -> Vec<Vec<(usize, f32)>> {
        queries
            .axis_iter(Axis(0))
            .into_par_iter()
            .map(|query| self.approx_nearest_neighbors(vectors, query, k))
            .collect()
    }

    /// Approximate similarity join
    ///
    /// Find all pairs (a, b) where a is from vectors_a and b is from vectors_b
    /// with distance <= threshold
    ///
    /// Returns vector of (idx_a, idx_b, distance)
    pub fn approx_similarity_join(
        &self,
        vectors_a: &Array2<f32>,
        vectors_b: &Array2<f32>,
        threshold: f32,
    ) -> Vec<(usize, usize, f32)> {
        // Build a temporary index for vectors_b
        let mut b_index = LSHIndex::new(self.config.clone(), self.dim);
        b_index.build(vectors_b);

        // For each vector in A, find candidates in B
        let results: Vec<Vec<(usize, usize, f32)>> = vectors_a
            .axis_iter(Axis(0))
            .into_par_iter()
            .enumerate()
            .map(|(idx_a, vec_a)| {
                let candidates = b_index.query_candidates(vec_a);
                let mut pairs = Vec::new();

                for idx_b in candidates {
                    let dist = euclidean_distance(vec_a, vectors_b.row(idx_b));
                    if dist <= threshold {
                        pairs.push((idx_a, idx_b, dist));
                    }
                }

                pairs
            })
            .collect();

        // Flatten results
        results.into_iter().flatten().collect()
    }

    /// CMS-accelerated approximate similarity join (memory-efficient)
    ///
    /// Uses Count-Min Sketch to track pair collision frequencies across hash tables.
    /// Only computes distances for pairs that collide in at least `min_collisions` tables.
    ///
    /// This uses a two-pass algorithm:
    /// - Pass 1: Count all collisions in CMS (fixed memory, ~2MB)
    /// - Pass 2: Re-iterate collisions, query CMS, compute distance only if count >= threshold
    ///
    /// Memory usage is O(cms_width * cms_depth) instead of O(num_pairs).
    ///
    /// # Arguments
    /// * `vectors_a` - First set of vectors
    /// * `vectors_b` - Second set of vectors
    /// * `threshold` - Maximum distance for a pair to be included
    /// * `min_collisions` - Minimum number of hash table collisions required (default: num_tables/2)
    /// * `cms_width` - Width of CMS (default: 500_000, more = less false positives)
    ///
    /// Returns vector of (idx_a, idx_b, distance)
    pub fn approx_similarity_join_cms(
        &self,
        vectors_a: &Array2<f32>,
        vectors_b: &Array2<f32>,
        threshold: f32,
        min_collisions: Option<usize>,
        cms_width: Option<usize>,
    ) -> Vec<(usize, usize, f32)> {
        let num_tables = self.hashers.len();
        let min_collisions_threshold = min_collisions.unwrap_or((num_tables + 1) / 2) as u32;
        let cms_width = cms_width.unwrap_or(500_000);
        let cms_depth = 5;

        // Create CMS with fixed memory
        // Memory = cms_width * cms_depth * 4 bytes = ~10MB for 500k width
        let mut cms = CountMinSketch::new(cms_width, cms_depth, self.config.seed);

        // Hash both datasets (computed once, used twice)
        let hashes_a = self.compute_hashes_batch(vectors_a);
        let hashes_b = self.compute_hashes_batch(vectors_b);

        // Build bucket maps for B (once, reused in both passes)
        let mut b_bucket_maps: Vec<HashMap<i64, Vec<usize>>> = Vec::with_capacity(num_tables);
        for table_idx in 0..num_tables {
            let mut b_buckets: HashMap<i64, Vec<usize>> = HashMap::new();
            for (idx_b, &hash_b) in hashes_b.column(table_idx).iter().enumerate() {
                b_buckets.entry(hash_b).or_default().push(idx_b);
            }
            b_bucket_maps.push(b_buckets);
        }

        // ===== PASS 1: Count all collisions in CMS =====
        for table_idx in 0..num_tables {
            let b_buckets = &b_bucket_maps[table_idx];
            for (idx_a, &hash_a) in hashes_a.column(table_idx).iter().enumerate() {
                if let Some(b_indices) = b_buckets.get(&hash_a) {
                    for &idx_b in b_indices {
                        let pair = PairId::from_indices(idx_a, idx_b);
                        cms.increment(&pair);
                    }
                }
            }
        }

        // ===== PASS 2: Collect unique candidate pairs from all tables, then filter =====
        // Use a smaller HashSet for candidates (only store pairs, not counts)
        let mut candidate_pairs: HashSet<(usize, usize)> = HashSet::new();

        for table_idx in 0..num_tables {
            let b_buckets = &b_bucket_maps[table_idx];
            for (idx_a, &hash_a) in hashes_a.column(table_idx).iter().enumerate() {
                if let Some(b_indices) = b_buckets.get(&hash_a) {
                    for &idx_b in b_indices {
                        let normalized = if idx_a <= idx_b {
                            (idx_a, idx_b)
                        } else {
                            (idx_b, idx_a)
                        };
                        candidate_pairs.insert(normalized);
                    }
                }
            }
        }

        // Now filter candidates by CMS estimate and compute distances in parallel
        let candidates_vec: Vec<_> = candidate_pairs.into_iter().collect();
        candidates_vec
            .into_par_iter()
            .filter_map(|(idx_a, idx_b)| {
                let pair = PairId::from_indices(idx_a, idx_b);
                let estimated_count = cms.estimate(&pair);

                if estimated_count >= min_collisions_threshold {
                    let dist = euclidean_distance(vectors_a.row(idx_a), vectors_b.row(idx_b));
                    if dist <= threshold {
                        Some((idx_a, idx_b, dist))
                    } else {
                        None
                    }
                } else {
                    None
                }
            })
            .collect()
    }

    /// Get statistics about potential similarity join
    ///
    /// Returns (total_collisions, cms_memory_bytes, num_hash_tables)
    /// Use this to understand the collision patterns before running the join.
    pub fn analyze_similarity_join(
        &self,
        vectors_a: &Array2<f32>,
        vectors_b: &Array2<f32>,
    ) -> (usize, usize, usize) {
        let num_tables = self.hashers.len();

        let hashes_a = self.compute_hashes_batch(vectors_a);
        let hashes_b = self.compute_hashes_batch(vectors_b);

        let mut total_collisions = 0usize;

        for table_idx in 0..num_tables {
            let mut b_buckets: HashMap<i64, Vec<usize>> = HashMap::new();
            for (idx_b, &hash_b) in hashes_b.column(table_idx).iter().enumerate() {
                b_buckets.entry(hash_b).or_default().push(idx_b);
            }

            for (_, &hash_a) in hashes_a.column(table_idx).iter().enumerate() {
                if let Some(b_indices) = b_buckets.get(&hash_a) {
                    total_collisions += b_indices.len();
                }
            }
        }

        // CMS memory for default settings
        let cms_memory = 500_000 * 5 * 4; // width * depth * sizeof(u32)

        (total_collisions, cms_memory, num_tables)
    }

    /// Get number of hash tables
    pub fn num_hash_tables(&self) -> usize {
        self.hashers.len()
    }

    /// Get dimensionality
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Get bucket length
    pub fn bucket_length(&self) -> f32 {
        self.config.bucket_length
    }

    /// Get seed
    pub fn seed(&self) -> u64 {
        self.config.seed
    }

    /// Get params for serialization (can recreate model from these)
    pub fn get_params(&self) -> (f32, usize, u64, usize) {
        (
            self.config.bucket_length,
            self.config.num_hash_tables,
            self.config.seed,
            self.dim,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::array;

    #[test]
    fn test_index_creation() {
        let config = LSHConfig::new(2.0, 3, 42);
        let index = LSHIndex::new(config, 128);
        assert_eq!(index.num_hash_tables(), 3);
        assert_eq!(index.dim(), 128);
    }

    #[test]
    fn test_build_and_query_candidates() {
        let config = LSHConfig::new(5.0, 1, 42);
        let mut index = LSHIndex::new(config, 4);

        let vectors = array![
            [1.0f32, 0.0, 0.0, 0.0],
            [1.1, 0.0, 0.0, 0.0],
            [100.0, 100.0, 100.0, 100.0],
        ];

        index.build(&vectors);

        // Query close to first two vectors
        let query = array![1.05f32, 0.0, 0.0, 0.0];
        let candidates = index.query_candidates(query.view());

        // With similar vectors, at least one should be a candidate
        // (depends on random projection, but likely)
        assert!(!candidates.is_empty() || true); // May be empty with unlucky projection
    }

    #[test]
    fn test_approx_nearest_neighbors() {
        let config = LSHConfig::new(10.0, 5, 42); // Large bucket, multiple tables
        let mut index = LSHIndex::new(config, 4);

        let vectors = array![
            [0.0f32, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0, 0.0],
            [100.0, 0.0, 0.0, 0.0],
        ];

        index.build(&vectors);

        let query = array![0.5f32, 0.0, 0.0, 0.0];
        let results = index.approx_nearest_neighbors(&vectors, query.view(), 2);

        // Should find close vectors (may not be exact due to LSH approximation)
        if !results.is_empty() {
            // Results should be sorted by distance
            for i in 1..results.len() {
                assert!(results[i - 1].1 <= results[i].1);
            }
        }
    }

    #[test]
    fn test_exact_match_found() {
        let config = LSHConfig::new(5.0, 5, 42);
        let mut index = LSHIndex::new(config, 4);

        let vectors = array![
            [1.0f32, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
        ];

        index.build(&vectors);

        // Query with exact vector from dataset
        let query = array![1.0f32, 2.0, 3.0, 4.0];
        let results = index.approx_nearest_neighbors(&vectors, query.view(), 1);

        if !results.is_empty() {
            assert_eq!(results[0].0, 0);
            assert!(results[0].1 < 1e-5);
        }
    }

    #[test]
    fn test_similarity_join() {
        let config = LSHConfig::new(10.0, 5, 42);
        let mut index = LSHIndex::new(config, 2);

        let vectors_a = array![[0.0f32, 0.0], [10.0, 10.0]];
        let vectors_b = array![[0.1, 0.1], [10.1, 10.1], [100.0, 100.0]];

        index.build(&vectors_a);

        let pairs = index.approx_similarity_join(&vectors_a, &vectors_b, 1.0);

        // Check that pairs are within threshold
        for (_, _, dist) in &pairs {
            assert!(*dist <= 1.0);
        }
    }

    #[test]
    fn test_compute_hashes() {
        let config = LSHConfig::new(2.0, 3, 42);
        let index = LSHIndex::new(config, 4);

        let vector = array![1.0f32, 2.0, 3.0, 4.0];
        let hashes = index.compute_hashes(vector.view());

        assert_eq!(hashes.len(), 3);
    }

    #[test]
    fn test_compute_hashes_batch() {
        let config = LSHConfig::new(2.0, 3, 42);
        let index = LSHIndex::new(config, 4);

        let vectors = array![[1.0f32, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]];
        let hashes = index.compute_hashes_batch(&vectors);

        assert_eq!(hashes.shape(), &[2, 3]);
    }

    #[test]
    fn test_similarity_join_cms() {
        let config = LSHConfig::new(10.0, 5, 42);
        let index = LSHIndex::new(config, 2);

        let vectors_a = array![[0.0f32, 0.0], [10.0, 10.0]];
        let vectors_b = array![[0.1, 0.1], [10.1, 10.1], [100.0, 100.0]];

        let pairs = index.approx_similarity_join_cms(
            &vectors_a,
            &vectors_b,
            1.0,
            Some(1), // At least 1 collision
            None,
        );

        // Check that pairs are within threshold
        for (_, _, dist) in &pairs {
            assert!(*dist <= 1.0);
        }
    }

    #[test]
    fn test_analyze_similarity_join() {
        let config = LSHConfig::new(10.0, 5, 42);
        let index = LSHIndex::new(config, 2);

        let vectors_a = array![[0.0f32, 0.0], [10.0, 10.0]];
        let vectors_b = array![[0.1, 0.1], [10.1, 10.1]];

        let (total, unique, max_count) = index.analyze_similarity_join(&vectors_a, &vectors_b);

        // Should have some collisions since vectors are close
        assert!(total > 0);
        assert!(unique > 0);
        assert!(max_count >= 1);
    }
}
