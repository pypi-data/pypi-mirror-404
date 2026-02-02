//! Euclidean distance computations
//!
//! Includes both single-pair and batch distance computations.
//! Batch computation uses the matmul trick:
//!   ‖A - B‖² = ‖A‖² + ‖B‖² - 2(A · B)

use ndarray::{Array1, Array2, ArrayView1, ArrayView2, Axis};

/// Compute squared Euclidean distance between two vectors
/// This is faster than euclidean_distance when you only need to compare distances
#[inline]
pub fn squared_euclidean_distance(a: ArrayView1<f32>, b: ArrayView1<f32>) -> f32 {
    debug_assert_eq!(a.len(), b.len());
    a.iter()
        .zip(b.iter())
        .map(|(&x, &y)| {
            let diff = x - y;
            diff * diff
        })
        .sum()
}

/// Compute Euclidean distance between two vectors
#[inline]
pub fn euclidean_distance(a: ArrayView1<f32>, b: ArrayView1<f32>) -> f32 {
    squared_euclidean_distance(a, b).sqrt()
}

/// Compute row-wise squared norms for a matrix
/// Returns array of shape (n_rows,) where each element is ‖row‖²
#[inline]
pub fn row_norms_squared(a: ArrayView2<f32>) -> Array1<f32> {
    a.map_axis(Axis(1), |row| row.iter().map(|x| x * x).sum())
}

/// Compute pairwise squared Euclidean distances between two matrices
///
/// Uses the identity: ‖a - b‖² = ‖a‖² + ‖b‖² - 2(a · b)
///
/// # Arguments
/// * `a` - Matrix of shape (n_a, dim)
/// * `b` - Matrix of shape (n_b, dim)
///
/// # Returns
/// * Matrix of shape (n_a, n_b) where result[i, j] = ‖a[i] - b[j]‖²
pub fn pairwise_squared_distances(a: ArrayView2<f32>, b: ArrayView2<f32>) -> Array2<f32> {
    let n_a = a.nrows();
    let n_b = b.nrows();

    // ‖a‖² for each row of a: shape (n_a,)
    let a_sq = row_norms_squared(a);

    // ‖b‖² for each row of b: shape (n_b,)
    let b_sq = row_norms_squared(b);

    // a · b^T: shape (n_a, n_b)
    let dot = a.dot(&b.t());

    // ‖a - b‖² = ‖a‖² + ‖b‖² - 2(a · b)
    let mut result = Array2::zeros((n_a, n_b));
    for i in 0..n_a {
        for j in 0..n_b {
            result[[i, j]] = a_sq[i] + b_sq[j] - 2.0 * dot[[i, j]];
        }
    }

    result
}

/// Compute pairwise Euclidean distances between two matrices
///
/// # Arguments
/// * `a` - Matrix of shape (n_a, dim)
/// * `b` - Matrix of shape (n_b, dim)
///
/// # Returns
/// * Matrix of shape (n_a, n_b) where result[i, j] = ‖a[i] - b[j]‖
pub fn pairwise_distances(a: ArrayView2<f32>, b: ArrayView2<f32>) -> Array2<f32> {
    pairwise_squared_distances(a, b).mapv(|x| x.max(0.0).sqrt())
}

/// Compute distances from a single query to multiple vectors
///
/// # Arguments
/// * `query` - Single query vector of shape (dim,)
/// * `vectors` - Matrix of shape (n_vectors, dim)
///
/// # Returns
/// * Array of shape (n_vectors,) with distances
pub fn query_distances(query: ArrayView1<f32>, vectors: ArrayView2<f32>) -> Array1<f32> {
    let query_sq: f32 = query.iter().map(|x| x * x).sum();
    let vectors_sq = row_norms_squared(vectors);
    let dots = vectors.dot(&query);

    let mut result = Array1::zeros(vectors.nrows());
    for i in 0..vectors.nrows() {
        let sq_dist = query_sq + vectors_sq[i] - 2.0 * dots[i];
        result[i] = sq_dist.max(0.0).sqrt();
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::array;

    #[test]
    fn test_euclidean_distance_3_4_5_triangle() {
        let a = array![0.0f32, 0.0, 0.0];
        let b = array![3.0f32, 4.0, 0.0];
        assert!((euclidean_distance(a.view(), b.view()) - 5.0).abs() < 1e-6);
    }

    #[test]
    fn test_squared_euclidean_distance() {
        let a = array![0.0f32, 0.0];
        let b = array![3.0f32, 4.0];
        assert!((squared_euclidean_distance(a.view(), b.view()) - 25.0).abs() < 1e-6);
    }

    #[test]
    fn test_distance_to_self_is_zero() {
        let a = array![1.0f32, 2.0, 3.0, 4.0];
        assert!(euclidean_distance(a.view(), a.view()).abs() < 1e-10);
    }

    #[test]
    fn test_distance_is_symmetric() {
        let a = array![1.0f32, 2.0, 3.0];
        let b = array![4.0f32, 5.0, 6.0];
        let d1 = euclidean_distance(a.view(), b.view());
        let d2 = euclidean_distance(b.view(), a.view());
        assert!((d1 - d2).abs() < 1e-10);
    }

    #[test]
    fn test_row_norms_squared() {
        let a = array![[3.0f32, 4.0], [1.0, 0.0]];
        let norms = row_norms_squared(a.view());
        assert!((norms[0] - 25.0).abs() < 1e-6); // 3² + 4² = 25
        assert!((norms[1] - 1.0).abs() < 1e-6); // 1² + 0² = 1
    }

    #[test]
    fn test_pairwise_distances() {
        let a = array![[0.0f32, 0.0], [3.0, 4.0]];
        let b = array![[0.0f32, 0.0], [1.0, 0.0]];

        let dists = pairwise_distances(a.view(), b.view());

        // a[0] to b[0]: 0
        assert!(dists[[0, 0]].abs() < 1e-6);
        // a[0] to b[1]: 1
        assert!((dists[[0, 1]] - 1.0).abs() < 1e-6);
        // a[1] to b[0]: 5 (3-4-5 triangle)
        assert!((dists[[1, 0]] - 5.0).abs() < 1e-6);
        // a[1] to b[1]: sqrt((3-1)² + 4²) = sqrt(20)
        assert!((dists[[1, 1]] - 20.0_f32.sqrt()).abs() < 1e-5);
    }

    #[test]
    fn test_pairwise_matches_single() {
        let a = array![[1.0f32, 2.0, 3.0], [4.0, 5.0, 6.0]];
        let b = array![[7.0f32, 8.0, 9.0], [0.0, 0.0, 0.0]];

        let batch_dists = pairwise_distances(a.view(), b.view());

        // Verify against single-pair computation
        for i in 0..a.nrows() {
            for j in 0..b.nrows() {
                let single_dist = euclidean_distance(a.row(i), b.row(j));
                assert!(
                    (batch_dists[[i, j]] - single_dist).abs() < 1e-5,
                    "Mismatch at [{}, {}]: batch={}, single={}",
                    i,
                    j,
                    batch_dists[[i, j]],
                    single_dist
                );
            }
        }
    }

    #[test]
    fn test_query_distances() {
        let query = array![0.0f32, 0.0];
        let vectors = array![[3.0f32, 4.0], [1.0, 0.0], [0.0, 0.0]];

        let dists = query_distances(query.view(), vectors.view());

        assert!((dists[0] - 5.0).abs() < 1e-6);
        assert!((dists[1] - 1.0).abs() < 1e-6);
        assert!(dists[2].abs() < 1e-6);
    }
}
