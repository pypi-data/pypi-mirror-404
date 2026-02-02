//! Random Projection Hasher for LSH
//!
//! Implements the hash function: h(v) = floor((v·r + b) / w)
//! where:
//!   - v is the input vector
//!   - r is a random projection vector (from Gaussian distribution)
//!   - b is a random offset in [0, w)
//!   - w is the bucket width (bucket_length)

use ndarray::{Array1, Array2, ArrayView1, Axis};
use ndarray_rand::rand_distr::{Normal, Uniform};
use ndarray_rand::RandomExt;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use rayon::prelude::*;

/// Random projection hasher for a single hash table
#[derive(Debug, Clone)]
pub struct RandomProjectionHasher {
    /// Random projection vector (one projection per table in BRP-LSH)
    /// Shape: (dim,)
    projection: Array1<f32>,

    /// Random offset
    offset: f32,

    /// Bucket width
    bucket_length: f32,
}

impl RandomProjectionHasher {
    /// Create a new hasher with random projection
    ///
    /// # Arguments
    /// * `dim` - Dimensionality of input vectors
    /// * `bucket_length` - Width of each bucket
    /// * `seed` - Random seed for reproducibility
    pub fn new(dim: usize, bucket_length: f32, seed: u64) -> Self {
        let mut rng = ChaCha8Rng::seed_from_u64(seed);

        // Generate random projection vector from standard normal distribution
        let normal = Normal::new(0.0, 1.0).unwrap();
        let projection = Array1::random_using(dim, normal, &mut rng);

        // Generate random offset uniformly in [0, bucket_length)
        let uniform = Uniform::new(0.0, bucket_length);
        let offset = rand::Rng::sample(&mut rng, uniform);

        Self {
            projection,
            offset,
            bucket_length,
        }
    }

    /// Hash a single vector
    ///
    /// Returns the bucket index
    #[inline]
    pub fn hash(&self, vector: ArrayView1<f32>) -> i64 {
        let dot = self.projection.dot(&vector);
        ((dot + self.offset) / self.bucket_length).floor() as i64
    }

    /// Hash multiple vectors in batch
    ///
    /// # Arguments
    /// * `vectors` - Shape: (n_vectors, dim)
    ///
    /// # Returns
    /// * Array of shape (n_vectors,) containing bucket indices
    pub fn hash_batch(&self, vectors: &Array2<f32>) -> Array1<i64> {
        // Compute dot products: vectors @ projection
        let dots = vectors.dot(&self.projection);
        dots.mapv(|x| ((x + self.offset) / self.bucket_length).floor() as i64)
    }

    /// Hash multiple vectors in parallel
    pub fn hash_batch_parallel(&self, vectors: &Array2<f32>) -> Vec<i64> {
        vectors
            .axis_iter(Axis(0))
            .into_par_iter()
            .map(|row| self.hash(row))
            .collect()
    }

    /// Get the dimensionality
    #[allow(dead_code)]
    pub fn dim(&self) -> usize {
        self.projection.len()
    }

    /// Get the bucket length
    #[allow(dead_code)]
    pub fn bucket_length(&self) -> f32 {
        self.bucket_length
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::array;

    #[test]
    fn test_hasher_creation() {
        let hasher = RandomProjectionHasher::new(128, 2.0, 42);
        assert_eq!(hasher.dim(), 128);
        assert_eq!(hasher.bucket_length(), 2.0);
    }

    #[test]
    fn test_hash_is_deterministic() {
        let hasher1 = RandomProjectionHasher::new(4, 2.0, 42);
        let hasher2 = RandomProjectionHasher::new(4, 2.0, 42);

        let vector = array![1.0f32, 2.0, 3.0, 4.0];
        let hash1 = hasher1.hash(vector.view());
        let hash2 = hasher2.hash(vector.view());

        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_similar_vectors_same_bucket() {
        let hasher = RandomProjectionHasher::new(4, 100.0, 42); // Large bucket

        let v1 = array![1.0f32, 2.0, 3.0, 4.0];
        let v2 = array![1.01f32, 2.01, 3.01, 4.01]; // Very close

        let h1 = hasher.hash(v1.view());
        let h2 = hasher.hash(v2.view());

        // With a large bucket, similar vectors should hash to same bucket
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_batch_hash_matches_individual() {
        let hasher = RandomProjectionHasher::new(4, 2.0, 42);

        let vectors = array![[1.0f32, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]];

        let batch_hashes = hasher.hash_batch(&vectors);

        let h0 = hasher.hash(vectors.row(0));
        let h1 = hasher.hash(vectors.row(1));

        assert_eq!(batch_hashes[0], h0);
        assert_eq!(batch_hashes[1], h1);
    }

    #[test]
    fn test_parallel_batch_matches_sequential() {
        let hasher = RandomProjectionHasher::new(4, 2.0, 42);
        let vectors = array![
            [1.0f32, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0]
        ];

        let sequential = hasher.hash_batch(&vectors);
        let parallel = hasher.hash_batch_parallel(&vectors);

        assert_eq!(sequential.to_vec(), parallel);
    }
}
