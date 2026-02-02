//! Python binding for BucketedRandomProjectionLSH estimator

use crate::lsh::{LSHConfig, LSHIndex};
use crate::python::PyBucketedRandomProjectionLSHModel;
use ndarray::Array2;
use numpy::PyReadonlyArray2;
use pyo3::prelude::*;
use pyo3::types::PyAnyMethods;

/// BucketedRandomProjectionLSH estimator
///
/// Similar to Spark's BucketedRandomProjectionLSH, this class implements
/// Locality Sensitive Hashing using random projections for approximate
/// nearest neighbor search with Euclidean distance.
#[pyclass(name = "BucketedRandomProjectionLSH", module = "fast_lsh_ann")]
#[derive(Debug, Clone)]
pub struct PyBucketedRandomProjectionLSH {
    bucket_length: f32,
    num_hash_tables: usize,
    seed: u64,
}

#[pymethods]
impl PyBucketedRandomProjectionLSH {
    /// Create a new BucketedRandomProjectionLSH estimator
    ///
    /// # Arguments
    /// * `bucket_length` - The bucket length (width) for the hash function.
    ///   Larger values create coarser buckets, increasing recall but slowing queries.
    /// * `num_hash_tables` - Number of hash tables to use.
    ///   More tables increase recall at the cost of memory and indexing time.
    /// * `seed` - Random seed for reproducibility.
    #[new]
    #[pyo3(signature = (bucket_length=2.0, num_hash_tables=1, seed=42))]
    fn new(bucket_length: f32, num_hash_tables: usize, seed: u64) -> PyResult<Self> {
        if bucket_length <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "bucket_length must be positive",
            ));
        }
        if num_hash_tables == 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "num_hash_tables must be at least 1",
            ));
        }
        Ok(Self {
            bucket_length,
            num_hash_tables,
            seed,
        })
    }

    /// Get bucket length
    #[getter]
    fn bucket_length(&self) -> f32 {
        self.bucket_length
    }

    /// Get number of hash tables
    #[getter]
    fn num_hash_tables(&self) -> usize {
        self.num_hash_tables
    }

    /// Get random seed
    #[getter]
    fn seed(&self) -> u64 {
        self.seed
    }

    /// Fit the estimator on a dataset
    ///
    /// # Arguments
    /// * `vectors` - A 2D numpy array of shape (n_samples, n_features)
    ///
    /// # Returns
    /// * A fitted BucketedRandomProjectionLSHModel
    fn fit(&self, py: Python<'_>, vectors: &Bound<'_, PyAny>) -> PyResult<PyBucketedRandomProjectionLSHModel> {
        // Convert to float32 if needed
        let numpy = py.import("numpy")?;
        let float32 = numpy.getattr("float32")?;
        let vectors_f32 = vectors.call_method1("astype", (float32,))?;
        let vectors_array: PyReadonlyArray2<f32> = vectors_f32.extract()?;

        let vectors_array: Array2<f32> = vectors_array.as_array().to_owned();
        let dim = vectors_array.ncols();

        let config = LSHConfig::new(self.bucket_length, self.num_hash_tables, self.seed);

        // Build index (release GIL during computation)
        let index = py.allow_threads(|| {
            let mut index = LSHIndex::new(config, dim);
            index.build_parallel(&vectors_array);
            index
        });

        Ok(PyBucketedRandomProjectionLSHModel::new(index))
    }

    /// Create a model without fitting on data
    ///
    /// This is useful for distributed processing where you want to:
    /// 1. Create the model once with fixed random projections
    /// 2. Transform data in parallel across partitions
    ///
    /// # Arguments
    /// * `dim` - Dimensionality of the vectors
    ///
    /// # Returns
    /// * A BucketedRandomProjectionLSHModel ready for transform operations
    fn create_model(&self, py: Python<'_>, dim: usize) -> PyResult<PyBucketedRandomProjectionLSHModel> {
        let config = LSHConfig::new(self.bucket_length, self.num_hash_tables, self.seed);

        let index = py.allow_threads(|| {
            LSHIndex::new(config, dim)
        });

        Ok(PyBucketedRandomProjectionLSHModel::new(index))
    }
}
