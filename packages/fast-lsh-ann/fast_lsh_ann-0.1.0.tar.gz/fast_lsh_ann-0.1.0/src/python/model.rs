//! Python binding for BucketedRandomProjectionLSHModel

use crate::lsh::{LSHConfig, LSHIndex};
use ndarray::{Array1, Array2};
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;
use pyo3::types::PyAnyMethods;
use pyo3::IntoPyObject;

/// Fitted BucketedRandomProjectionLSH model
///
/// This model can transform vectors to hash values, find approximate
/// nearest neighbors, and perform similarity joins.
#[pyclass(name = "BucketedRandomProjectionLSHModel", module = "fast_lsh_ann")]
pub struct PyBucketedRandomProjectionLSHModel {
    index: LSHIndex,
}

impl PyBucketedRandomProjectionLSHModel {
    pub fn new(index: LSHIndex) -> Self {
        Self { index }
    }
}

/// Helper to convert any array to f32
fn to_array2_f32(py: Python<'_>, arr: &Bound<'_, PyAny>) -> PyResult<Array2<f32>> {
    let numpy = py.import("numpy")?;
    let float32 = numpy.getattr("float32")?;
    let arr_f32 = arr.call_method1("astype", (float32,))?;
    let arr_readonly: PyReadonlyArray2<f32> = arr_f32.extract()?;
    Ok(arr_readonly.as_array().to_owned())
}

fn to_array1_f32(py: Python<'_>, arr: &Bound<'_, PyAny>) -> PyResult<Array1<f32>> {
    let numpy = py.import("numpy")?;
    let float32 = numpy.getattr("float32")?;
    let arr_f32 = arr.call_method1("astype", (float32,))?;
    let arr_readonly: PyReadonlyArray1<f32> = arr_f32.extract()?;
    Ok(arr_readonly.as_array().to_owned())
}

#[pymethods]
impl PyBucketedRandomProjectionLSHModel {
    /// Create a new model (used by pickle)
    #[new]
    #[pyo3(signature = (bucket_length=2.0, num_hash_tables=1, seed=42, dim=128))]
    fn py_new(bucket_length: f32, num_hash_tables: usize, seed: u64, dim: usize) -> Self {
        let config = LSHConfig::new(bucket_length, num_hash_tables, seed);
        let index = LSHIndex::new(config, dim);
        Self { index }
    }

    /// Get bucket length
    #[getter]
    fn bucket_length(&self) -> f32 {
        self.index.bucket_length()
    }

    /// Get number of hash tables
    #[getter]
    fn num_hash_tables(&self) -> usize {
        self.index.num_hash_tables()
    }

    /// Transform vectors to hash values
    ///
    /// # Arguments
    /// * `vectors` - A 2D numpy array of shape (n_samples, n_features)
    ///
    /// # Returns
    /// * A 2D numpy array of shape (n_samples, num_hash_tables) with hash values
    fn transform<'py>(
        &self,
        py: Python<'py>,
        vectors: &Bound<'_, PyAny>,
    ) -> PyResult<Bound<'py, PyArray2<i64>>> {
        let vectors_array = to_array2_f32(py, vectors)?;
        let hashes = py.allow_threads(|| self.index.compute_hashes_batch(&vectors_array));
        Ok(hashes.into_pyarray(py))
    }

    /// Find approximate k nearest neighbors
    ///
    /// # Arguments
    /// * `vectors` - The dataset to search in (n_samples, n_features)
    /// * `query` - A 1D query vector (n_features,)
    /// * `k` - Number of nearest neighbors to return
    ///
    /// # Returns
    /// * List of (index, distance) tuples sorted by distance
    fn approx_nearest_neighbors(
        &self,
        py: Python<'_>,
        vectors: &Bound<'_, PyAny>,
        query: &Bound<'_, PyAny>,
        k: usize,
    ) -> PyResult<Vec<(usize, f32)>> {
        let vectors_array = to_array2_f32(py, vectors)?;
        let query_array = to_array1_f32(py, query)?;

        let results = py.allow_threads(|| {
            self.index
                .approx_nearest_neighbors(&vectors_array, query_array.view(), k)
        });

        Ok(results)
    }

    /// Find approximate k nearest neighbors for multiple queries (batch)
    ///
    /// # Arguments
    /// * `vectors` - The dataset to search in (n_samples, n_features)
    /// * `queries` - Multiple query vectors (n_queries, n_features)
    /// * `k` - Number of nearest neighbors to return per query
    ///
    /// # Returns
    /// * List of lists of (index, distance) tuples
    fn batch_approx_nearest_neighbors(
        &self,
        py: Python<'_>,
        vectors: &Bound<'_, PyAny>,
        queries: &Bound<'_, PyAny>,
        k: usize,
    ) -> PyResult<Vec<Vec<(usize, f32)>>> {
        let vectors_array = to_array2_f32(py, vectors)?;
        let queries_array = to_array2_f32(py, queries)?;

        let results = py.allow_threads(|| {
            self.index
                .batch_approx_nearest_neighbors(&vectors_array, &queries_array, k)
        });

        Ok(results)
    }

    /// Approximate similarity join
    ///
    /// Find all pairs of vectors from two datasets within a distance threshold.
    ///
    /// # Arguments
    /// * `vectors_a` - First dataset (n_a, n_features)
    /// * `vectors_b` - Second dataset (n_b, n_features)
    /// * `threshold` - Maximum distance threshold
    ///
    /// # Returns
    /// * List of (idx_a, idx_b, distance) tuples
    fn approx_similarity_join(
        &self,
        py: Python<'_>,
        vectors_a: &Bound<'_, PyAny>,
        vectors_b: &Bound<'_, PyAny>,
        threshold: f32,
    ) -> PyResult<Vec<(usize, usize, f32)>> {
        let vectors_a_array = to_array2_f32(py, vectors_a)?;
        let vectors_b_array = to_array2_f32(py, vectors_b)?;

        let results = py.allow_threads(|| {
            self.index
                .approx_similarity_join(&vectors_a_array, &vectors_b_array, threshold)
        });

        Ok(results)
    }

    /// CMS-accelerated approximate similarity join (memory-efficient)
    ///
    /// Uses Count-Min Sketch with two-pass algorithm:
    /// - Pass 1: Count all collisions in CMS (fixed ~10MB memory)
    /// - Pass 2: Re-iterate, query CMS, compute distance only if count >= threshold
    ///
    /// Memory usage is O(cms_width * 5 * 4 bytes) instead of O(num_pairs * 24 bytes).
    /// For 30M pairs, this saves ~700MB of memory.
    ///
    /// # Arguments
    /// * `vectors_a` - First dataset (n_a, n_features)
    /// * `vectors_b` - Second dataset (n_b, n_features)
    /// * `threshold` - Maximum distance threshold
    /// * `min_collisions` - Minimum hash table collisions required (default: num_tables/2)
    /// * `cms_width` - CMS width (default: 500000, more = fewer false positives)
    ///
    /// # Returns
    /// * List of (idx_a, idx_b, distance) tuples
    #[pyo3(signature = (vectors_a, vectors_b, threshold, min_collisions=None, cms_width=None))]
    fn approx_similarity_join_cms(
        &self,
        py: Python<'_>,
        vectors_a: &Bound<'_, PyAny>,
        vectors_b: &Bound<'_, PyAny>,
        threshold: f32,
        min_collisions: Option<usize>,
        cms_width: Option<usize>,
    ) -> PyResult<Vec<(usize, usize, f32)>> {
        let vectors_a_array = to_array2_f32(py, vectors_a)?;
        let vectors_b_array = to_array2_f32(py, vectors_b)?;

        let results = py.allow_threads(|| {
            self.index.approx_similarity_join_cms(
                &vectors_a_array,
                &vectors_b_array,
                threshold,
                min_collisions,
                cms_width,
            )
        });

        Ok(results)
    }

    /// Analyze similarity join before running it
    ///
    /// Returns statistics to help tune parameters for the actual join.
    ///
    /// # Arguments
    /// * `vectors_a` - First dataset (n_a, n_features)
    /// * `vectors_b` - Second dataset (n_b, n_features)
    ///
    /// # Returns
    /// * Tuple of (total_collisions, cms_memory_bytes, num_hash_tables)
    fn analyze_similarity_join(
        &self,
        py: Python<'_>,
        vectors_a: &Bound<'_, PyAny>,
        vectors_b: &Bound<'_, PyAny>,
    ) -> PyResult<(usize, usize, usize)> {
        let vectors_a_array = to_array2_f32(py, vectors_a)?;
        let vectors_b_array = to_array2_f32(py, vectors_b)?;

        let results = py.allow_threads(|| {
            self.index
                .analyze_similarity_join(&vectors_a_array, &vectors_b_array)
        });

        Ok(results)
    }

    /// Get dimensionality
    #[getter]
    fn dim(&self) -> usize {
        self.index.dim()
    }

    /// Get seed
    #[getter]
    fn seed(&self) -> u64 {
        self.index.seed()
    }

    /// Pickle support using __reduce__
    fn __reduce__(&self, py: Python<'_>) -> PyResult<PyObject> {
        let (bucket_length, num_hash_tables, seed, dim) = self.index.get_params();

        // Import the class from our module
        let module = py.import("fast_lsh_ann")?;
        let cls = module.getattr("BucketedRandomProjectionLSHModel")?;

        // Return (class, args) tuple for reconstruction
        let args = (bucket_length, num_hash_tables, seed, dim);
        Ok((cls, args).into_pyobject(py)?.into())
    }
}
