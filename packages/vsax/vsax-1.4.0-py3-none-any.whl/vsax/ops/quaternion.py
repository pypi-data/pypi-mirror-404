"""Quaternion operations for Quaternion Hypervector VSA.

Quaternion hypervectors use the Hamilton product for binding, which is
NON-COMMUTATIVE, making them suitable for order-sensitive role/filler bindings.

Quaternion representation: q = a + bi + cj + dk
Storage format: (D, 4) array where last axis is (a, b, c, d)
"""

import jax.numpy as jnp

from vsax.core.base import AbstractOpSet

# =============================================================================
# Pure Quaternion Algebra Functions
# =============================================================================


def qmul(p: jnp.ndarray, q: jnp.ndarray) -> jnp.ndarray:
    """Hamilton product of two quaternions.

    For quaternions p = (p0, p1, p2, p3) and q = (q0, q1, q2, q3), the
    Hamilton product is defined as:

        p * q = (p0*q0 - p1*q1 - p2*q2 - p3*q3,
                 p0*q1 + p1*q0 + p2*q3 - p3*q2,
                 p0*q2 - p1*q3 + p2*q0 + p3*q1,
                 p0*q3 + p1*q2 - p2*q1 + p3*q0)

    This operation is NON-COMMUTATIVE: qmul(p, q) != qmul(q, p) in general.

    Args:
        p: First quaternion array of shape (..., 4).
        q: Second quaternion array of shape (..., 4).

    Returns:
        Hamilton product of shape (..., 4).

    Example:
        >>> import jax.numpy as jnp
        >>> i = jnp.array([0, 1, 0, 0])  # i
        >>> j = jnp.array([0, 0, 1, 0])  # j
        >>> k = qmul(i, j)  # i * j = k
        >>> # k should be [0, 0, 0, 1]
    """
    # Extract components (last axis is quaternion components)
    p0, p1, p2, p3 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    q0, q1, q2, q3 = q[..., 0], q[..., 1], q[..., 2], q[..., 3]

    # Hamilton product formula
    r0 = p0 * q0 - p1 * q1 - p2 * q2 - p3 * q3
    r1 = p0 * q1 + p1 * q0 + p2 * q3 - p3 * q2
    r2 = p0 * q2 - p1 * q3 + p2 * q0 + p3 * q1
    r3 = p0 * q3 + p1 * q2 - p2 * q1 + p3 * q0

    return jnp.stack([r0, r1, r2, r3], axis=-1)


def qconj(q: jnp.ndarray) -> jnp.ndarray:
    """Quaternion conjugate.

    For quaternion q = (a, b, c, d), the conjugate is:
        q* = (a, -b, -c, -d)

    Args:
        q: Quaternion array of shape (..., 4).

    Returns:
        Conjugate quaternion of shape (..., 4).

    Example:
        >>> import jax.numpy as jnp
        >>> q = jnp.array([1, 2, 3, 4])
        >>> qconj(q)  # [1, -2, -3, -4]
    """
    return q.at[..., 1:].multiply(-1)


def qnorm_squared(q: jnp.ndarray) -> jnp.ndarray:
    """Squared norm of quaternion.

    For quaternion q = (a, b, c, d):
        |q|² = a² + b² + c² + d²

    Args:
        q: Quaternion array of shape (..., 4).

    Returns:
        Squared norm of shape (...,).

    Example:
        >>> import jax.numpy as jnp
        >>> q = jnp.array([1, 2, 3, 4])
        >>> qnorm_squared(q)  # 1 + 4 + 9 + 16 = 30
    """
    return jnp.sum(q**2, axis=-1)


def qnorm(q: jnp.ndarray) -> jnp.ndarray:
    """Norm (magnitude) of quaternion.

    For quaternion q = (a, b, c, d):
        |q| = sqrt(a² + b² + c² + d²)

    Args:
        q: Quaternion array of shape (..., 4).

    Returns:
        Norm of shape (...,).
    """
    return jnp.sqrt(qnorm_squared(q))


def qinverse(q: jnp.ndarray) -> jnp.ndarray:
    """Quaternion inverse.

    For quaternion q:
        q⁻¹ = q* / |q|²

    For unit quaternions, the inverse equals the conjugate.

    Args:
        q: Quaternion array of shape (..., 4).

    Returns:
        Inverse quaternion of shape (..., 4).

    Example:
        >>> import jax.numpy as jnp
        >>> q = jnp.array([1, 0, 0, 0])  # identity
        >>> qinverse(q)  # [1, 0, 0, 0]
    """
    conj = qconj(q)
    norm_sq = qnorm_squared(q)
    # Add small epsilon for numerical stability
    epsilon = 1e-10
    return conj / (norm_sq[..., None] + epsilon)


def qnormalize(q: jnp.ndarray) -> jnp.ndarray:
    """Normalize quaternion to unit length.

    Projects quaternion onto the unit 3-sphere S³.

    Args:
        q: Quaternion array of shape (..., 4).

    Returns:
        Unit quaternion of shape (..., 4) with |q| = 1.

    Example:
        >>> import jax.numpy as jnp
        >>> q = jnp.array([1, 1, 1, 1])  # norm = 2
        >>> unit_q = qnormalize(q)  # norm = 1
    """
    norm = qnorm(q)
    epsilon = 1e-10
    return q / (norm[..., None] + epsilon)


def qidentity(shape: tuple[int, ...] = ()) -> jnp.ndarray:
    """Create identity quaternion(s).

    The identity quaternion is (1, 0, 0, 0).

    Args:
        shape: Shape of output array (excluding quaternion dimension).
               Default () returns a single quaternion of shape (4,).

    Returns:
        Identity quaternion(s) of shape (*shape, 4).

    Example:
        >>> qidentity()  # [1, 0, 0, 0]
        >>> qidentity((10,))  # Shape (10, 4), all identity quaternions
    """
    result = jnp.zeros((*shape, 4))
    return result.at[..., 0].set(1.0)


# =============================================================================
# Quaternion Operation Set
# =============================================================================


class QuaternionOperations(AbstractOpSet):
    """Quaternion VSA operations using Hamilton product for binding.

    Quaternion Hypervectors (QHV) use the Hamilton product for binding,
    which is NON-COMMUTATIVE. This makes them suitable for order-sensitive
    role/filler bindings where bind(role, filler) != bind(filler, role).

    Key properties:
    - Binding: Hamilton product (non-commutative, associative)
    - Bundling: Sum + normalize to unit quaternions
    - Inverse: Quaternion inverse (conjugate / norm²)
    - Unbind: Right-unbind recovers x from bind(x, y) given y
    - Unbind-left: Left-unbind recovers y from bind(x, y) given x

    Vector shape: (D, 4) where D is the number of quaternion coordinates.

    Example:
        >>> import jax
        >>> import jax.numpy as jnp
        >>> from vsax.ops import QuaternionOperations
        >>> from vsax.sampling import sample_quaternion_random
        >>>
        >>> ops = QuaternionOperations()
        >>> key = jax.random.PRNGKey(0)
        >>> vecs = sample_quaternion_random(dim=512, n=2, key=key)
        >>> x, y = vecs[0], vecs[1]
        >>>
        >>> # Non-commutative binding
        >>> xy = ops.bind(x, y)
        >>> yx = ops.bind(y, x)
        >>> # xy != yx (different results)
        >>>
        >>> # Right-unbind: recover x from xy using y
        >>> recovered_x = ops.unbind(xy, y)
        >>>
        >>> # Left-unbind: recover y from xy using x
        >>> recovered_y = ops.unbind_left(x, xy)
    """

    def bind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Bind two quaternion hypervectors using Hamilton product.

        This operation is NON-COMMUTATIVE: bind(a, b) != bind(b, a).

        Args:
            a: First quaternion hypervector of shape (..., D, 4).
            b: Second quaternion hypervector of shape (..., D, 4).

        Returns:
            Bound quaternion hypervector of shape (..., D, 4).
        """
        return qmul(a, b)

    def bundle(self, *vecs: jnp.ndarray) -> jnp.ndarray:
        """Bundle multiple quaternion hypervectors.

        Sums the vectors and normalizes to unit quaternions.

        Args:
            *vecs: Variable number of quaternion hypervectors.

        Returns:
            Bundled quaternion hypervector, normalized to unit length.

        Raises:
            ValueError: If no vectors are provided.
        """
        if len(vecs) == 0:
            raise ValueError("bundle() requires at least one vector")

        # Sum all vectors
        result = jnp.sum(jnp.stack(vecs), axis=0)

        # Normalize to unit quaternions
        return qnormalize(result)

    def inverse(self, a: jnp.ndarray) -> jnp.ndarray:
        """Compute the quaternion inverse.

        For unit quaternions, this equals the conjugate.

        Args:
            a: Quaternion hypervector of shape (..., D, 4).

        Returns:
            Inverse quaternion hypervector of shape (..., D, 4).
        """
        return qinverse(a)

    def unbind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Right-unbind: recover x from z = bind(x, y) given y.

        Computes: z * y⁻¹ = x

        For quaternion binding z = x * y, right multiplication by y⁻¹
        recovers x: z * y⁻¹ = x * y * y⁻¹ = x

        Args:
            a: Bound quaternion hypervector (z = bind(x, y)).
            b: Quaternion hypervector to unbind (y).

        Returns:
            Recovered quaternion hypervector (x).
        """
        return qmul(a, qinverse(b))

    def unbind_left(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Left-unbind: recover y from z = bind(x, y) given x.

        Computes: x⁻¹ * z = y

        For quaternion binding z = x * y, left multiplication by x⁻¹
        recovers y: x⁻¹ * z = x⁻¹ * x * y = y

        Args:
            a: Quaternion hypervector used in binding (x).
            b: Bound quaternion hypervector (z = bind(x, y)).

        Returns:
            Recovered quaternion hypervector (y).
        """
        return qmul(qinverse(a), b)

    def permute(self, a: jnp.ndarray, shift: int) -> jnp.ndarray:
        """Permute a quaternion hypervector by circular shift.

        Shifts along the first axis (quaternion coordinate dimension),
        not the last axis (quaternion components).

        Args:
            a: Quaternion hypervector of shape (..., D, 4).
            shift: Number of positions to shift.

        Returns:
            Permuted quaternion hypervector.
        """
        # Roll along the second-to-last axis (D dimension)
        return jnp.roll(a, shift, axis=-2)
