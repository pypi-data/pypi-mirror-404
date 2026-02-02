//! Streaming top-k selection using BinaryHeap
//!
//! O(n log k) instead of O(n log n) for full sort

use std::cmp::Ordering;
use std::collections::BinaryHeap;

/// A scored item for the heap (index, distance)
/// We use a max-heap, so we reverse the comparison to get min-distance at top
#[derive(Debug, Clone, Copy)]
pub struct ScoredItem {
    pub index: usize,
    pub distance: f32,
}

impl PartialEq for ScoredItem {
    fn eq(&self, other: &Self) -> bool {
        self.distance == other.distance
    }
}

impl Eq for ScoredItem {}

impl PartialOrd for ScoredItem {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for ScoredItem {
    fn cmp(&self, other: &Self) -> Ordering {
        // Normal comparison: larger distance = larger item
        // BinaryHeap is a max-heap, so largest distance will be at top
        // This is what we want: we keep k smallest, and the largest of those is at top
        // so we can easily check if a new item should replace it
        self.distance
            .partial_cmp(&other.distance)
            .unwrap_or(Ordering::Equal)
    }
}

/// Streaming top-k selector
///
/// Maintains a max-heap of size k. As items are pushed:
/// - If heap has < k items, push the item
/// - If item's distance < max distance in heap, pop max and push item
///
/// This is O(n log k) instead of O(n log n) for sorting all items.
pub struct TopK {
    heap: BinaryHeap<ScoredItem>,
    k: usize,
}

impl TopK {
    /// Create a new top-k selector
    pub fn new(k: usize) -> Self {
        Self {
            heap: BinaryHeap::with_capacity(k + 1),
            k,
        }
    }

    /// Push an item. Only keeps if it's in the top k.
    #[inline]
    pub fn push(&mut self, index: usize, distance: f32) {
        if self.heap.len() < self.k {
            self.heap.push(ScoredItem { index, distance });
        } else if let Some(max) = self.heap.peek() {
            if distance < max.distance {
                self.heap.pop();
                self.heap.push(ScoredItem { index, distance });
            }
        }
    }

    /// Push multiple items at once
    pub fn push_batch(&mut self, items: impl Iterator<Item = (usize, f32)>) {
        for (index, distance) in items {
            self.push(index, distance);
        }
    }

    /// Get the current max distance in the heap (useful for early termination)
    #[inline]
    pub fn threshold(&self) -> Option<f32> {
        self.heap.peek().map(|item| item.distance)
    }

    /// Extract results sorted by distance (ascending)
    pub fn into_sorted_vec(self) -> Vec<(usize, f32)> {
        let mut items: Vec<_> = self.heap.into_vec();
        // Sort by distance ascending
        items.sort_by(|a, b| {
            a.distance
                .partial_cmp(&b.distance)
                .unwrap_or(Ordering::Equal)
        });
        items.iter().map(|item| (item.index, item.distance)).collect()
    }

    /// Get current number of items
    pub fn len(&self) -> usize {
        self.heap.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }
}

/// Find top-k smallest distances from a distance array
pub fn top_k_from_distances(distances: &[f32], k: usize) -> Vec<(usize, f32)> {
    let mut topk = TopK::new(k);
    for (i, &d) in distances.iter().enumerate() {
        topk.push(i, d);
    }
    topk.into_sorted_vec()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_topk_basic() {
        let mut topk = TopK::new(3);
        topk.push(0, 5.0);
        topk.push(1, 2.0);
        topk.push(2, 8.0);
        topk.push(3, 1.0);
        topk.push(4, 3.0);

        let results = topk.into_sorted_vec();
        assert_eq!(results.len(), 3);
        assert_eq!(results[0], (3, 1.0)); // smallest
        assert_eq!(results[1], (1, 2.0));
        assert_eq!(results[2], (4, 3.0));
    }

    #[test]
    fn test_topk_less_than_k() {
        let mut topk = TopK::new(5);
        topk.push(0, 5.0);
        topk.push(1, 2.0);

        let results = topk.into_sorted_vec();
        assert_eq!(results.len(), 2);
        assert_eq!(results[0], (1, 2.0));
        assert_eq!(results[1], (0, 5.0));
    }

    #[test]
    fn test_topk_from_distances() {
        let distances = vec![5.0, 2.0, 8.0, 1.0, 3.0];
        let results = top_k_from_distances(&distances, 3);

        assert_eq!(results.len(), 3);
        assert_eq!(results[0].0, 3); // index 3 has distance 1.0
        assert_eq!(results[1].0, 1); // index 1 has distance 2.0
        assert_eq!(results[2].0, 4); // index 4 has distance 3.0
    }

    #[test]
    fn test_topk_threshold() {
        let mut topk = TopK::new(2);
        assert!(topk.threshold().is_none());

        topk.push(0, 5.0);
        assert_eq!(topk.threshold(), Some(5.0));

        topk.push(1, 3.0);
        assert_eq!(topk.threshold(), Some(5.0)); // max is still 5.0

        topk.push(2, 1.0);
        assert_eq!(topk.threshold(), Some(3.0)); // 5.0 was popped
    }
}
