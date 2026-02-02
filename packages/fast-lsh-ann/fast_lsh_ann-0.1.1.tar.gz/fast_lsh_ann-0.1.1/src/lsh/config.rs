//! Configuration for LSH index

/// Configuration for the LSH index
#[derive(Debug, Clone)]
pub struct LSHConfig {
    /// The bucket length (width) for the hash function
    /// Larger values = coarser buckets = more candidates = higher recall but slower
    pub bucket_length: f32,

    /// Number of hash tables to use
    /// More tables = higher recall but more memory and slower indexing
    pub num_hash_tables: usize,

    /// Random seed for reproducibility
    pub seed: u64,
}

impl Default for LSHConfig {
    fn default() -> Self {
        Self {
            bucket_length: 2.0,
            num_hash_tables: 1,
            seed: 42,
        }
    }
}

impl LSHConfig {
    pub fn new(bucket_length: f32, num_hash_tables: usize, seed: u64) -> Self {
        Self {
            bucket_length,
            num_hash_tables,
            seed,
        }
    }

    pub fn validate(&self) -> Result<(), &'static str> {
        if self.bucket_length <= 0.0 {
            return Err("bucket_length must be positive");
        }
        if self.num_hash_tables == 0 {
            return Err("num_hash_tables must be at least 1");
        }
        Ok(())
    }
}
