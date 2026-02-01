"""Quaternion hypervector representation for Quaternion VSA."""

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.ops.quaternion import qnorm, qnormalize


class QuaternionHypervector(AbstractHypervector):
    """Quaternion-valued hypervector for non-commutative VSA.

    QuaternionHypervector uses quaternions to represent hypervectors, where
    each quaternion coordinate is a 4-tuple (a, b, c, d) representing
    q = a + bi + cj + dk. This enables non-commutative binding via the
    Hamilton product.

    The storage format is (D, 4) where:
    - D is the number of quaternion coordinates (the VSA dimensionality)
    - 4 is the quaternion components (a, b, c, d)

    The normalization operation projects all quaternions to unit length on S³.

    Args:
        vec: Quaternion-valued JAX array of shape (..., D, 4).

    Raises:
        ValueError: If the last dimension is not 4.

    Example:
        >>> import jax.numpy as jnp
        >>> # Create a hypervector with 512 quaternion coordinates
        >>> vec = jnp.ones((512, 4)) / 2  # All unit quaternions (0.5, 0.5, 0.5, 0.5)
        >>> hv = QuaternionHypervector(vec)
        >>> normalized = hv.normalize()
    """

    def __init__(self, vec: jnp.ndarray) -> None:
        """Initialize quaternion hypervector.

        Args:
            vec: Quaternion-valued JAX array of shape (..., D, 4).

        Raises:
            ValueError: If the last dimension is not 4.
        """
        if vec.shape[-1] != 4:
            raise ValueError(
                f"QuaternionHypervector requires last dimension to be 4, got {vec.shape[-1]}"
            )
        super().__init__(vec)

    def normalize(self) -> "QuaternionHypervector":
        """Normalize all quaternions to unit length.

        Projects each quaternion onto the unit 3-sphere S³.

        Returns:
            New QuaternionHypervector with all quaternions having magnitude 1.0.

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.array([[1, 2, 3, 4], [5, 6, 7, 8]])  # Not unit
            >>> hv = QuaternionHypervector(vec.astype(float))
            >>> normalized = hv.normalize()
            >>> # All quaternions now have unit norm
        """
        normalized = qnormalize(self._vec)
        return QuaternionHypervector(normalized)

    @property
    def dim(self) -> int:
        """Return the number of quaternion coordinates.

        This is the VSA dimensionality D, not the total number of floats.

        Returns:
            Number of quaternion coordinates (D).
        """
        return int(self._vec.shape[-2])

    @property
    def quaternion_norms(self) -> jnp.ndarray:
        """Return the norm of each quaternion coordinate.

        Returns:
            Array of shape (..., D) containing quaternion magnitudes.
        """
        return qnorm(self._vec)

    @property
    def scalar_part(self) -> jnp.ndarray:
        """Extract scalar (real) component of each quaternion.

        The scalar part is the 'a' in q = a + bi + cj + dk.

        Returns:
            Array of shape (..., D) containing scalar parts.
        """
        return self._vec[..., 0]

    @property
    def vector_part(self) -> jnp.ndarray:
        """Extract vector (imaginary) components of each quaternion.

        The vector part is (b, c, d) in q = a + bi + cj + dk.

        Returns:
            Array of shape (..., D, 3) containing vector parts.
        """
        return self._vec[..., 1:]

    def is_unit(self, atol: float = 1e-6) -> bool:
        """Check if all quaternions are unit quaternions.

        Args:
            atol: Absolute tolerance for norm comparison.

        Returns:
            True if all quaternions have magnitude approximately 1.0.
        """
        norms = self.quaternion_norms
        return bool(jnp.allclose(norms, 1.0, atol=atol))
