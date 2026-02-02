//! Top-K Heavy Hitters using Count-Min Sketch
//!
//! Combines CMS for frequency estimation with a min-heap to track
//! the top-k most frequent items.
//!
//! Reference: https://veerpalbrar.github.io/blog/Solving-Top-K-Frequent-Objects-with-Count-Min-Sketch/

use crate::cms::{CountMinSketch, PairId};
use std::collections::HashMap;

/// Top-K Heavy Hitters tracker
///
/// Uses Count-Min Sketch for frequency estimation and a min-heap
/// to efficiently track the top-k most frequent items.
///
/// # Example
/// ```ignore
/// let mut hh = HeavyHitters::new(10, 1000, 5, 42);
///
/// // Track items
/// for item in stream {
///     hh.observe(item);
/// }
///
/// // Get top-k
/// let top_items = hh.top_k();
/// ```
#[derive(Debug)]
pub struct HeavyHitters<T: Clone + Eq + std::hash::Hash> {
    /// Count-Min Sketch for frequency estimation
    cms: CountMinSketch,

    /// Map from item to its count (tracks top-k items)
    item_counts: HashMap<T, u32>,

    /// Maximum number of items to track
    k: usize,
}

impl<T: Clone + Eq + std::hash::Hash> HeavyHitters<T> {
    /// Create a new Heavy Hitters tracker
    ///
    /// # Arguments
    /// * `k` - Number of top items to track
    /// * `cms_width` - Width of CMS (more = more accurate)
    /// * `cms_depth` - Depth of CMS (more = lower error probability)
    /// * `seed` - Random seed
    pub fn new(k: usize, cms_width: usize, cms_depth: usize, seed: u64) -> Self {
        Self {
            cms: CountMinSketch::new(cms_width, cms_depth, seed),
            item_counts: HashMap::with_capacity(k + 1),
            k,
        }
    }

    /// Create with CMS error bounds
    pub fn with_error_bounds(k: usize, epsilon: f64, delta: f64, seed: u64) -> Self {
        Self {
            cms: CountMinSketch::with_error_bounds(epsilon, delta, seed),
            item_counts: HashMap::with_capacity(k + 1),
            k,
        }
    }

    /// Observe an item (increment its count)
    ///
    /// Returns the new estimated count for the item.
    pub fn observe(&mut self, item: T) -> u32 {
        // Increment in CMS and get new count
        let new_count = self.cms.increment_and_estimate(&item);

        // Check if item is already tracked
        if self.item_counts.contains_key(&item) {
            // Update count in item_counts
            self.item_counts.insert(item, new_count);
            return new_count;
        }

        // Item not yet tracked - check if it should be in top-k
        if self.item_counts.len() < self.k {
            // Haven't filled k items yet, just add
            self.item_counts.insert(item, new_count);
        } else {
            // Find the item with minimum TRUE count in item_counts
            // (heap counts may be stale since we don't update heap on every observe)
            let min_entry = self
                .item_counts
                .iter()
                .min_by_key(|(_, &count)| count)
                .map(|(item, &count)| (item.clone(), count));

            if let Some((min_item, min_count)) = min_entry {
                if new_count > min_count {
                    // New item has higher count than minimum - replace it
                    self.item_counts.remove(&min_item);
                    self.item_counts.insert(item, new_count);
                }
            }
        }

        new_count
    }

    /// Get the current minimum count threshold
    ///
    /// Items with count <= this won't be in top-k
    pub fn threshold(&self) -> u32 {
        if self.item_counts.len() < self.k {
            0
        } else {
            self.item_counts.values().copied().min().unwrap_or(0)
        }
    }

    /// Get the estimated count for an item
    pub fn estimate(&self, item: &T) -> u32 {
        self.cms.estimate(item)
    }

    /// Check if an item is currently in the top-k
    pub fn contains(&self, item: &T) -> bool {
        self.item_counts.contains_key(item)
    }

    /// Get the top-k items with their counts
    ///
    /// Returns items sorted by count (descending)
    pub fn top_k(&self) -> Vec<(T, u32)> {
        let mut items: Vec<_> = self
            .item_counts
            .iter()
            .map(|(item, &count)| (item.clone(), count))
            .collect();
        items.sort_by(|a, b| b.1.cmp(&a.1));
        items
    }

    /// Get number of items currently tracked
    pub fn len(&self) -> usize {
        self.item_counts.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.item_counts.is_empty()
    }

    /// Clear all data
    pub fn clear(&mut self) {
        self.cms.clear();
        self.item_counts.clear();
    }
}

/// Specialized Heavy Hitters for tracking pair collisions
///
/// Optimized for similarity join where we track (id_a, id_b) pairs.
#[derive(Debug)]
pub struct PairHeavyHitters {
    inner: HeavyHitters<PairId>,
}

impl PairHeavyHitters {
    /// Create a new pair collision tracker
    pub fn new(k: usize, cms_width: usize, cms_depth: usize, seed: u64) -> Self {
        Self {
            inner: HeavyHitters::new(k, cms_width, cms_depth, seed),
        }
    }

    /// Create with error bounds
    pub fn with_error_bounds(k: usize, epsilon: f64, delta: f64, seed: u64) -> Self {
        Self {
            inner: HeavyHitters::with_error_bounds(k, epsilon, delta, seed),
        }
    }

    /// Record a collision between two items
    ///
    /// Returns the collision count for this pair.
    #[inline]
    pub fn record_collision(&mut self, id_a: usize, id_b: usize) -> u32 {
        let pair = PairId::from_indices(id_a, id_b);
        self.inner.observe(pair)
    }

    /// Get estimated collision count for a pair
    #[inline]
    pub fn collision_count(&self, id_a: usize, id_b: usize) -> u32 {
        let pair = PairId::from_indices(id_a, id_b);
        self.inner.estimate(&pair)
    }

    /// Get top-k pairs by collision count
    ///
    /// Returns Vec of ((id_a, id_b), count)
    pub fn top_pairs(&self) -> Vec<((usize, usize), u32)> {
        self.inner
            .top_k()
            .into_iter()
            .map(|(pair, count)| ((pair.id_a as usize, pair.id_b as usize), count))
            .collect()
    }

    /// Get the minimum collision count to be in top-k
    pub fn threshold(&self) -> u32 {
        self.inner.threshold()
    }

    /// Check if a pair is in the top-k
    pub fn contains_pair(&self, id_a: usize, id_b: usize) -> bool {
        let pair = PairId::from_indices(id_a, id_b);
        self.inner.contains(&pair)
    }

    /// Get number of pairs tracked
    pub fn len(&self) -> usize {
        self.inner.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    /// Clear all data
    pub fn clear(&mut self) {
        self.inner.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_heavy_hitters_basic() {
        let mut hh: HeavyHitters<&str> = HeavyHitters::new(3, 10000, 10, 42);

        // Add items with different frequencies
        for _ in 0..100 {
            hh.observe("apple");
        }
        for _ in 0..50 {
            hh.observe("banana");
        }
        for _ in 0..25 {
            hh.observe("cherry");
        }
        for _ in 0..10 {
            hh.observe("date");
        }

        let top = hh.top_k();
        assert_eq!(top.len(), 3);

        // Top 3 should be apple, banana, cherry
        // They should be in the top-3 (order may vary slightly due to CMS approximation)
        let top_items: Vec<&str> = top.iter().map(|(item, _)| *item).collect();
        assert!(top_items.contains(&"apple"));
        assert!(top_items.contains(&"banana"));
        assert!(top_items.contains(&"cherry"));
        assert!(!top_items.contains(&"date")); // date should NOT be in top-3

        // Apple should have highest count
        assert!(top[0].1 >= 100);
    }

    #[test]
    fn test_heavy_hitters_threshold() {
        let mut hh: HeavyHitters<i32> = HeavyHitters::new(2, 1000, 5, 42);

        hh.observe(1);
        hh.observe(1);
        hh.observe(2);

        // Threshold should be count of smallest item in top-k
        assert!(hh.threshold() >= 1);
    }

    #[test]
    fn test_pair_heavy_hitters() {
        let mut phh = PairHeavyHitters::new(3, 1000, 5, 42);

        // Record collisions
        for _ in 0..10 {
            phh.record_collision(1, 2);
        }
        for _ in 0..5 {
            phh.record_collision(3, 4);
        }
        for _ in 0..3 {
            phh.record_collision(5, 6);
        }

        let top = phh.top_pairs();
        assert_eq!(top.len(), 3);
        assert_eq!(top[0].0, (1, 2));
        assert_eq!(top[0].1, 10);
    }

    #[test]
    fn test_pair_heavy_hitters_order_independent() {
        let mut phh = PairHeavyHitters::new(10, 1000, 5, 42);

        phh.record_collision(1, 2);
        phh.record_collision(2, 1); // Same pair, different order

        assert_eq!(phh.collision_count(1, 2), 2);
        assert_eq!(phh.collision_count(2, 1), 2);
    }

    #[test]
    fn test_heavy_hitters_update_existing() {
        let mut hh: HeavyHitters<i32> = HeavyHitters::new(2, 1000, 5, 42);

        // Fill top-k
        hh.observe(1);
        hh.observe(2);

        // Item 1 should be updated, not added again
        for _ in 0..10 {
            hh.observe(1);
        }

        assert_eq!(hh.len(), 2);
        assert!(hh.estimate(&1) >= 11);
    }
}
