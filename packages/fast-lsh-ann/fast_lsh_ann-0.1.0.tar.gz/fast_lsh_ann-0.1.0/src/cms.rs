//! Count-Min Sketch implementation
//!
//! A probabilistic data structure for frequency estimation in streams.
//! Uses multiple hash functions to map items to counters, takes the
//! minimum count across all hash functions to reduce overestimation.
//!
//! Reference: https://redis.io/blog/count-min-sketch-the-art-and-science-of-estimating-stuff/

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

/// Count-Min Sketch for frequency estimation
///
/// # Example
/// ```ignore
/// let mut cms = CountMinSketch::new(1000, 5, 42);
/// cms.increment(&"apple");
/// cms.increment(&"apple");
/// cms.increment(&"banana");
/// assert_eq!(cms.estimate(&"apple"), 2);
/// assert_eq!(cms.estimate(&"banana"), 1);
/// ```
#[derive(Debug, Clone)]
pub struct CountMinSketch {
    /// 2D array of counters: [depth][width]
    counters: Vec<Vec<u32>>,

    /// Width of each row (number of counters per hash function)
    width: usize,

    /// Depth (number of hash functions / rows)
    depth: usize,

    /// Seeds for each hash function
    seeds: Vec<u64>,
}

impl CountMinSketch {
    /// Create a new Count-Min Sketch
    ///
    /// # Arguments
    /// * `width` - Number of counters per row (more = less collision = more accurate)
    /// * `depth` - Number of hash functions/rows (more = lower error probability)
    /// * `seed` - Random seed for hash function generation
    ///
    /// # Memory
    /// Uses `width * depth * 4` bytes for counters
    pub fn new(width: usize, depth: usize, seed: u64) -> Self {
        let counters = vec![vec![0u32; width]; depth];

        // Generate different seeds for each hash function
        let mut seeds = Vec::with_capacity(depth);
        for i in 0..depth {
            seeds.push(seed.wrapping_add((i as u64).wrapping_mul(0x9E3779B97F4A7C15)));
        }

        Self {
            counters,
            width,
            depth,
            seeds,
        }
    }

    /// Create CMS with error bounds
    ///
    /// # Arguments
    /// * `epsilon` - Error tolerance (0.01 = 1% error)
    /// * `delta` - Probability of exceeding error (0.01 = 99% confidence)
    /// * `seed` - Random seed
    pub fn with_error_bounds(epsilon: f64, delta: f64, seed: u64) -> Self {
        // width = ceil(e / epsilon)
        // depth = ceil(ln(1 / delta))
        let width = (std::f64::consts::E / epsilon).ceil() as usize;
        let depth = (1.0 / delta).ln().ceil() as usize;
        Self::new(width.max(1), depth.max(1), seed)
    }

    /// Hash an item to get its index in a specific row
    #[inline]
    fn hash_index<T: Hash>(&self, item: &T, row: usize) -> usize {
        let mut hasher = DefaultHasher::new();
        self.seeds[row].hash(&mut hasher);
        item.hash(&mut hasher);
        (hasher.finish() as usize) % self.width
    }

    /// Increment the count for an item
    #[inline]
    pub fn increment<T: Hash>(&mut self, item: &T) {
        self.add(item, 1);
    }

    /// Add a count to an item
    #[inline]
    pub fn add<T: Hash>(&mut self, item: &T, count: u32) {
        for row in 0..self.depth {
            let idx = self.hash_index(item, row);
            self.counters[row][idx] = self.counters[row][idx].saturating_add(count);
        }
    }

    /// Estimate the count for an item
    ///
    /// Returns the minimum count across all hash functions.
    /// This is always >= true count (never underestimates).
    #[inline]
    pub fn estimate<T: Hash>(&self, item: &T) -> u32 {
        let mut min_count = u32::MAX;
        for row in 0..self.depth {
            let idx = self.hash_index(item, row);
            min_count = min_count.min(self.counters[row][idx]);
        }
        min_count
    }

    /// Increment and return the new estimated count
    #[inline]
    pub fn increment_and_estimate<T: Hash>(&mut self, item: &T) -> u32 {
        let mut min_count = u32::MAX;
        for row in 0..self.depth {
            let idx = self.hash_index(item, row);
            self.counters[row][idx] = self.counters[row][idx].saturating_add(1);
            min_count = min_count.min(self.counters[row][idx]);
        }
        min_count
    }

    /// Clear all counters
    pub fn clear(&mut self) {
        for row in &mut self.counters {
            row.fill(0);
        }
    }

    /// Get memory usage in bytes
    pub fn memory_usage(&self) -> usize {
        self.width * self.depth * std::mem::size_of::<u32>()
    }

    /// Get width
    pub fn width(&self) -> usize {
        self.width
    }

    /// Get depth
    pub fn depth(&self) -> usize {
        self.depth
    }
}

/// A pair ID for tracking collisions between two items
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct PairId {
    pub id_a: u64,
    pub id_b: u64,
}

impl PairId {
    /// Create a new pair ID (order-independent)
    pub fn new(id_a: u64, id_b: u64) -> Self {
        // Normalize order so (a, b) == (b, a)
        if id_a <= id_b {
            Self { id_a, id_b }
        } else {
            Self { id_a: id_b, id_b: id_a }
        }
    }

    /// Create from usize indices
    pub fn from_indices(idx_a: usize, idx_b: usize) -> Self {
        Self::new(idx_a as u64, idx_b as u64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cms_basic() {
        let mut cms = CountMinSketch::new(1000, 5, 42);

        cms.increment(&"apple");
        cms.increment(&"apple");
        cms.increment(&"banana");

        assert_eq!(cms.estimate(&"apple"), 2);
        assert_eq!(cms.estimate(&"banana"), 1);
        assert_eq!(cms.estimate(&"cherry"), 0);
    }

    #[test]
    fn test_cms_add() {
        let mut cms = CountMinSketch::new(1000, 5, 42);

        cms.add(&"apple", 100);
        assert_eq!(cms.estimate(&"apple"), 100);
    }

    #[test]
    fn test_cms_increment_and_estimate() {
        let mut cms = CountMinSketch::new(1000, 5, 42);

        assert_eq!(cms.increment_and_estimate(&"apple"), 1);
        assert_eq!(cms.increment_and_estimate(&"apple"), 2);
        assert_eq!(cms.increment_and_estimate(&"apple"), 3);
    }

    #[test]
    fn test_cms_never_underestimates() {
        let mut cms = CountMinSketch::new(100, 3, 42);

        // Add many items to create collisions
        for i in 0..1000 {
            cms.add(&i, 1);
        }

        // Estimate should be >= actual count for any item
        for i in 0..1000 {
            assert!(cms.estimate(&i) >= 1);
        }
    }

    #[test]
    fn test_cms_with_error_bounds() {
        let cms = CountMinSketch::with_error_bounds(0.01, 0.01, 42);
        // Should have reasonable dimensions
        assert!(cms.width() > 0);
        assert!(cms.depth() > 0);
    }

    #[test]
    fn test_cms_clear() {
        let mut cms = CountMinSketch::new(100, 3, 42);
        cms.increment(&"apple");
        cms.increment(&"banana");

        cms.clear();

        assert_eq!(cms.estimate(&"apple"), 0);
        assert_eq!(cms.estimate(&"banana"), 0);
    }

    #[test]
    fn test_pair_id_order_independent() {
        let pair1 = PairId::new(1, 2);
        let pair2 = PairId::new(2, 1);
        assert_eq!(pair1, pair2);
    }

    #[test]
    fn test_pair_id_hashing() {
        use std::collections::HashSet;

        let mut set = HashSet::new();
        set.insert(PairId::new(1, 2));

        assert!(set.contains(&PairId::new(1, 2)));
        assert!(set.contains(&PairId::new(2, 1))); // Order independent
        assert!(!set.contains(&PairId::new(1, 3)));
    }
}
