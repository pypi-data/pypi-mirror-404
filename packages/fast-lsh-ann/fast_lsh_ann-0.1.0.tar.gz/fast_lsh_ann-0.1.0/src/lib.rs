//! Fast LSH ANN - Bucketed Random Projection LSH for Approximate Nearest Neighbor search
//!
//! This crate provides a high-performance implementation of Locality Sensitive Hashing
//! using random projections, compatible with Apache Spark's BucketedRandomProjectionLSH API.

mod cms;
mod distance;
mod heavy_hitters;
mod lsh;
mod python;
mod topk;

use pyo3::prelude::*;

/// Python module for fast_lsh_ann
#[pymodule]
fn _fast_lsh_ann(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<python::PyBucketedRandomProjectionLSH>()?;
    m.add_class::<python::PyBucketedRandomProjectionLSHModel>()?;
    Ok(())
}
