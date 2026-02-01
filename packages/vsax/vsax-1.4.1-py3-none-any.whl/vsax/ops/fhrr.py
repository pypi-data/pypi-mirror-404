"""Fourier Holographic Reduced Representation operations."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractOpSet


class FHRROperations(AbstractOpSet):
    """FHRR operations using FFT-based circular convolution.

    Fourier Holographic Reduced Representation (FHRR) uses circular convolution
    for binding and complex addition for bundling. These operations work best
    with complex-valued hypervectors.

    Binding is implemented via circular convolution in the frequency domain:
        bind(a, b) = IFFT(FFT(a) ⊙ FFT(b))

    where ⊙ denotes element-wise multiplication.

    Example:
        >>> import jax
        >>> import jax.numpy as jnp
        >>> from vsax.representations import ComplexHypervector
        >>>
        >>> ops = FHRROperations()
        >>> key = jax.random.PRNGKey(0)
        >>> a = jnp.exp(1j * jax.random.uniform(key, (512,), minval=0, maxval=2*jnp.pi))
        >>> b = jnp.exp(1j * jax.random.uniform(key, (512,), minval=0, maxval=2*jnp.pi))
        >>>
        >>> bound = ops.bind(a, b)
        >>> assert bound.shape == a.shape
    """

    def bind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Bind two hypervectors using circular convolution.

        Implemented via FFT: IFFT(FFT(a) * FFT(b))

        This operation is:
        - Commutative: bind(a, b) = bind(b, a)
        - Associative: bind(a, bind(b, c)) = bind(bind(a, b), c)
        - Invertible: bind(bind(a, b), inverse(b)) ≈ a

        Args:
            a: First hypervector as JAX array.
            b: Second hypervector as JAX array.

        Returns:
            Bound hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> a = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> b = jnp.exp(1j * jnp.array([0.3, 0.7, 1.1]))
            >>> result = ops.bind(a, b)
            >>> assert jnp.iscomplexobj(result)
        """
        # Circular convolution via FFT
        fft_a = jnp.fft.fft(a)
        fft_b = jnp.fft.fft(b)
        return jnp.fft.ifft(fft_a * fft_b)

    def bundle(self, *vecs: jnp.ndarray) -> jnp.ndarray:
        """Bundle multiple hypervectors using complex addition and normalization.

        The bundled vector is similar to all input vectors and can be queried
        to retrieve the constituents.

        Args:
            *vecs: Variable number of hypervectors as JAX arrays.

        Returns:
            Bundled hypervector as JAX array, normalized to unit magnitude.

        Raises:
            ValueError: If no vectors are provided.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> a = jnp.exp(1j * jnp.array([0.0, 0.5, 1.0]))
            >>> b = jnp.exp(1j * jnp.array([0.3, 0.7, 1.1]))
            >>> c = jnp.exp(1j * jnp.array([0.6, 0.9, 1.3]))
            >>> result = ops.bundle(a, b, c)
            >>> assert jnp.allclose(jnp.abs(result), 1.0, atol=0.1)
        """
        if len(vecs) == 0:
            raise ValueError("bundle() requires at least one vector")

        # Sum all vectors
        result = jnp.sum(jnp.stack(vecs), axis=0)

        # Normalize to unit magnitude (phase-only)
        return result / jnp.abs(result)

    def inverse(self, a: jnp.ndarray) -> jnp.ndarray:
        """Compute the inverse for unbinding.

        For circular convolution (FHRR), the inverse requires:
        - Complex vectors: inv(a) = ifft(conj(fft(a)) / (|fft(a)|² + ε))
        - Real vectors: inv(a) = reversed vector (time-domain equivalent)

        This ensures that bind(bind(x, a), inverse(a)) ≈ x with high accuracy.

        The division by |fft(a)|² is essential for proper deconvolution.
        For unit-magnitude vectors in frequency domain (proper FHRR vectors),
        this reduces to approximately conj(fft(a)), but for general complex
        vectors, the normalization is necessary.

        Args:
            a: Hypervector as JAX array.

        Returns:
            Inverse hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> from vsax.similarity import cosine_similarity
            >>> ops = FHRROperations()
            >>> a = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> x = jnp.exp(1j * jnp.array([0.3, 0.7, 1.1]))
            >>> inv_a = ops.inverse(a)
            >>> bound = ops.bind(x, a)
            >>> recovered = ops.bind(bound, inv_a)
            >>> # recovered should be very similar to x (>99% similarity)
        """
        if jnp.iscomplexobj(a):
            # Inverse for circular convolution with proper deconvolution
            fft_a = jnp.fft.fft(a)
            epsilon = 1e-10
            inv_fft = jnp.conj(fft_a) / (jnp.abs(fft_a) ** 2 + epsilon)
            return jnp.fft.ifft(inv_fft)
        else:
            # Reverse for real vectors (circular convolution inverse)
            # Note: index 0 stays in place, rest are reversed
            return jnp.concatenate([a[:1], jnp.flip(a[1:])])

    def unbind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Unbind b from a using circular deconvolution.

        Implements unbinding via FFT-based circular deconvolution:
            unbind(a, b) = ifft(fft(a) * conj(fft(b)) / (|fft(b)|² + ε))

        This is equivalent to bind(a, inverse(b)) but more efficient as it
        performs only one FFT round-trip instead of two.

        For circular convolution: if c = a ⊛ b, then to recover a we need:
            a = ifft(fft(c) * conj(fft(b)) / |fft(b)|²)
        where ⊛ denotes circular convolution.

        The division by |fft(b)|² is essential for proper deconvolution.
        A small epsilon (1e-10) is added for numerical stability.

        Args:
            a: Bound hypervector as JAX array.
            b: Hypervector to unbind as JAX array.

        Returns:
            Recovered hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> from vsax.similarity import cosine_similarity
            >>> ops = FHRROperations()
            >>> x = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> y = jnp.exp(1j * jnp.array([0.3, 0.7, 1.1]))
            >>>
            >>> # Bind and unbind
            >>> bound = ops.bind(x, y)
            >>> recovered = ops.unbind(bound, y)
            >>>
            >>> # Should recover x with high similarity
            >>> similarity = cosine_similarity(x, recovered)
            >>> # similarity > 0.99 with corrected inverse
        """
        # Circular deconvolution via FFT
        fft_a = jnp.fft.fft(a)
        fft_b = jnp.fft.fft(b)
        # Proper deconvolution: divide by magnitude squared with epsilon for stability
        epsilon = 1e-10
        return jnp.fft.ifft(fft_a * jnp.conj(fft_b) / (jnp.abs(fft_b) ** 2 + epsilon))

    def fractional_power(self, a: jnp.ndarray, exponent: Union[float, jnp.ndarray]) -> jnp.ndarray:
        """Raise complex hypervector to fractional power.

        For complex vectors v = exp(i*θ), this computes v^r = exp(i*r*θ).
        This enables continuous encoding of scalar values using phase rotation.

        Properties:
            - Continuous: small changes in exponent produce small output changes
            - Compositional: (v^r1)^r2 = v^(r1*r2)
            - Invertible: v^r ⊗ v^(-r) = identity

        This operation is fundamental for:
            - Fractional Power Encoding (FPE)
            - Spatial Semantic Pointers (SSP)
            - Vector Function Architecture (VFA)

        Args:
            a: Complex hypervector as JAX array.
            exponent: Scalar or array of exponents to raise the vector to.

        Returns:
            Hypervector raised to the given power as JAX array.

        Raises:
            TypeError: If input array is not complex-valued.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> # Create a unit complex vector
            >>> a = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> # Raise to fractional power
            >>> powered = ops.fractional_power(a, 0.5)
            >>> # Test compositionality: (a^0.5)^2 ≈ a
            >>> composed = ops.fractional_power(powered, 2.0)
            >>> assert jnp.allclose(composed, a, atol=1e-6)
        """
        if not jnp.iscomplexobj(a):
            raise TypeError(
                "fractional_power only works with complex-valued arrays. "
                "Use ComplexHypervector for fractional power encoding."
            )
        return jnp.power(a, exponent)

    def permute(self, a: jnp.ndarray, shift: int) -> jnp.ndarray:
        """Permute a hypervector by circular rotation.

        Args:
            a: Hypervector as JAX array.
            shift: Number of positions to rotate (positive = right, negative = left).

        Returns:
            Permuted hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> a = jnp.array([1, 2, 3, 4, 5])
            >>> rotated = ops.permute(a, 2)
            >>> assert jnp.array_equal(rotated, jnp.array([4, 5, 1, 2, 3]))
        """
        return jnp.roll(a, shift)
