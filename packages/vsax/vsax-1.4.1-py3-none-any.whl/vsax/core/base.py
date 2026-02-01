"""Abstract base classes for VSA components."""

from abc import ABC, abstractmethod
from typing import cast

import jax.numpy as jnp
import numpy as np


class AbstractHypervector(ABC):
    """Base class for all hypervector representations.

    Wraps a JAX array and provides common operations for hypervectors.
    All concrete implementations must inherit from this class.

    Args:
        vec: The underlying JAX array representing the hypervector.
    """

    def __init__(self, vec: jnp.ndarray) -> None:
        """Initialize hypervector with underlying array.

        Args:
            vec: JAX array representing the hypervector.
        """
        self._vec = vec

    @property
    def vec(self) -> jnp.ndarray:
        """Return the underlying JAX array.

        Returns:
            The JAX array wrapped by this hypervector.
        """
        return self._vec

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the shape of the hypervector.

        Returns:
            Tuple representing the shape of the underlying array.
        """
        return cast(tuple[int, ...], self._vec.shape)

    @property
    def dtype(self) -> jnp.dtype:
        """Return the data type of the hypervector.

        Returns:
            JAX dtype of the underlying array.
        """
        return self._vec.dtype

    @abstractmethod
    def normalize(self) -> "AbstractHypervector":
        """Normalize the hypervector.

        The normalization method depends on the representation type.
        For example, complex vectors normalize to unit magnitude (phase-only),
        while real vectors use L2 normalization.

        Returns:
            Normalized hypervector of the same type.
        """
        pass

    def to_numpy(self) -> np.ndarray:
        """Convert the hypervector to a NumPy array.

        Returns:
            NumPy array representation of the hypervector.
        """
        return np.array(self._vec)

    def __repr__(self) -> str:
        """Return string representation of the hypervector.

        Returns:
            String showing class name, shape, and dtype.
        """
        return f"{self.__class__.__name__}(shape={self.shape}, dtype={self.dtype})"


class AbstractOpSet(ABC):
    """Base class for VSA operation sets.

    Defines the symbolic algebra operations for binding and bundling hypervectors.
    All operations work directly on JAX arrays, not on AbstractHypervector instances.

    Concrete implementations (FHRR, MAP, Binary) must implement all abstract methods.
    """

    @abstractmethod
    def bind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Bind two hypervectors together.

        Binding creates a composite representation that is dissimilar to both inputs
        but can be unbound using the inverse operation. The specific binding operation
        depends on the algebra (e.g., circular convolution for FHRR, elementwise
        multiplication for MAP).

        Args:
            a: First hypervector as JAX array.
            b: Second hypervector as JAX array.

        Returns:
            Bound hypervector as JAX array.
        """
        pass

    @abstractmethod
    def bundle(self, *vecs: jnp.ndarray) -> jnp.ndarray:
        """Bundle multiple hypervectors into a single representation.

        Bundling creates a superposition that is similar to all inputs.
        The bundled vector can be queried to retrieve the constituent vectors.

        Args:
            *vecs: Variable number of hypervectors as JAX arrays.

        Returns:
            Bundled hypervector as JAX array.
        """
        pass

    @abstractmethod
    def inverse(self, a: jnp.ndarray) -> jnp.ndarray:
        """Compute the inverse of a hypervector.

        The inverse is used to unbind: if c = bind(a, b), then
        unbind(c, b) = bind(c, inverse(b)) ≈ a.

        Args:
            a: Hypervector as JAX array.

        Returns:
            Inverse hypervector as JAX array.
        """
        pass

    def unbind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Unbind b from a to recover the original vector.

        If c = bind(a, b), then unbind(c, b) ≈ a.

        This provides an explicit, intuitive interface for unbinding operations.
        The default implementation uses: bind(a, inverse(b))

        Concrete operation sets may override this for efficiency or to provide
        specialized unbinding behavior.

        Args:
            a: Bound hypervector (result of bind operation).
            b: Hypervector to unbind.

        Returns:
            Recovered hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> from vsax.ops import FHRROperations
            >>> ops = FHRROperations()
            >>> x = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> y = jnp.exp(1j * jnp.array([0.3, 0.7, 1.1]))
            >>> bound = ops.bind(x, y)
            >>> recovered = ops.unbind(bound, y)
            >>> # recovered ≈ x (with high similarity)
        """
        return self.bind(a, self.inverse(b))

    def unbind_left(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Left-unbind: recover y from z = bind(x, y) given x.

        For non-commutative algebras (e.g., quaternions), this computes:
            inverse(a) * b

        which recovers y from z = bind(x, y) when given x.

        For commutative algebras, this is equivalent to unbind(b, a).

        The default implementation uses: bind(inverse(a), b)

        Args:
            a: Hypervector used as first argument in binding (x).
            b: Bound hypervector (z = bind(x, y)).

        Returns:
            Recovered hypervector (y) as JAX array.

        Example:
            >>> # For quaternions (non-commutative):
            >>> z = ops.bind(x, y)  # z = x * y
            >>> recovered_y = ops.unbind_left(x, z)  # x⁻¹ * z = y
            >>>
            >>> # For FHRR/MAP (commutative), equivalent to unbind:
            >>> z = ops.bind(x, y)
            >>> recovered_y = ops.unbind_left(x, z)  # same as unbind(z, x)
        """
        return self.bind(self.inverse(a), b)

    def permute(self, a: jnp.ndarray, shift: int) -> jnp.ndarray:
        """Permute a hypervector by circular shift.

        This is an optional operation. The default implementation performs
        a circular shift, but concrete classes may override with different
        permutation strategies.

        Args:
            a: Hypervector as JAX array.
            shift: Number of positions to shift (positive = right, negative = left).

        Returns:
            Permuted hypervector as JAX array.
        """
        return jnp.roll(a, shift)
