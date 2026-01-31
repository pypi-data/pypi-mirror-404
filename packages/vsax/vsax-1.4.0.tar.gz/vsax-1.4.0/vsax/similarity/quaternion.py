"""Quaternion similarity metric for quaternion hypervectors."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.utils.coerce import coerce_to_array


def quaternion_similarity(
    a: Union[AbstractHypervector, jnp.ndarray],
    b: Union[AbstractHypervector, jnp.ndarray],
) -> float:
    """Compute similarity between two quaternion hypervectors.

    For quaternion hypervectors of shape (D, 4), this computes the average
    dot product across all quaternion coordinates:

        similarity = mean(sum(a * b, axis=-1))

    For unit quaternions, this equals the average cosine of the geodesic
    distance on S³.

    Args:
        a: First quaternion hypervector (AbstractHypervector or jnp.ndarray).
        b: Second quaternion hypervector (AbstractHypervector or jnp.ndarray).

    Returns:
        Similarity as a float in range [-1, 1].

    Raises:
        ValueError: If vectors have different shapes or last dimension is not 4.

    Example:
        >>> import jax
        >>> from vsax.sampling import sample_quaternion_random
        >>> from vsax.similarity import quaternion_similarity
        >>>
        >>> key = jax.random.PRNGKey(42)
        >>> vectors = sample_quaternion_random(512, 2, key)
        >>> x, y = vectors[0], vectors[1]
        >>>
        >>> # Same vector has similarity 1.0
        >>> assert abs(quaternion_similarity(x, x) - 1.0) < 1e-6
        >>>
        >>> # Random vectors have low similarity
        >>> sim = quaternion_similarity(x, y)
        >>> assert abs(sim) < 0.5
    """
    # Coerce to arrays
    vec_a = coerce_to_array(a)
    vec_b = coerce_to_array(b)

    # Validate shapes
    if vec_a.shape != vec_b.shape:
        raise ValueError(
            f"Shape mismatch: vectors must have same shape, got {vec_a.shape} and {vec_b.shape}"
        )

    if vec_a.shape[-1] != 4:
        raise ValueError(
            f"quaternion_similarity requires last dimension to be 4, got {vec_a.shape[-1]}"
        )

    # Compute dot product for each quaternion coordinate
    # For unit quaternions: dot(q1, q2) = cos(θ/2) where θ is geodesic distance
    dot_products = jnp.sum(vec_a * vec_b, axis=-1)

    # Average across all quaternion coordinates
    similarity = jnp.mean(dot_products)

    # Return as Python float
    return float(similarity)
