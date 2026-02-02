//! Distance metrics for LSH

mod euclidean;

pub use euclidean::euclidean_distance;
pub use euclidean::pairwise_distances;
pub use euclidean::pairwise_squared_distances;
pub use euclidean::query_distances;
#[allow(unused_imports)]
pub use euclidean::squared_euclidean_distance;
