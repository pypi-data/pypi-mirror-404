"""Random sampling functions for generating basis hypervectors."""

from typing import Optional

import jax
import jax.numpy as jnp


def sample_random(dim: int, n: int, key: Optional[jax.random.PRNGKey] = None) -> jnp.ndarray:
    """Sample n random real-valued vectors from normal distribution.

    Generates random vectors with elements drawn from a standard normal
    distribution N(0, 1). These are suitable for use with MAP operations.

    Args:
        dim: Dimensionality of each vector.
        n: Number of vectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).

    Returns:
        JAX array of shape (n, dim) containing sampled vectors.

    Example:
        >>> import jax
        >>> key = jax.random.PRNGKey(42)
        >>> vectors = sample_random(512, 10, key)
        >>> assert vectors.shape == (10, 512)
        >>> assert not jnp.iscomplexobj(vectors)
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    return jax.random.normal(key, shape=(n, dim))


def sample_complex_random(
    dim: int, n: int, key: Optional[jax.random.PRNGKey] = None
) -> jnp.ndarray:
    """Sample n random complex-valued vectors with random phases.

    Generates unit-magnitude complex vectors with uniformly random phases
    in [0, 2π). These are suitable for use with FHRR operations.

    The vectors have the form: exp(i * θ) where θ ~ Uniform(0, 2π).

    Args:
        dim: Dimensionality of each vector.
        n: Number of vectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).

    Returns:
        JAX array of shape (n, dim) containing complex unit-magnitude vectors.

    Example:
        >>> import jax
        >>> key = jax.random.PRNGKey(42)
        >>> vectors = sample_complex_random(512, 10, key)
        >>> assert vectors.shape == (10, 512)
        >>> assert jnp.iscomplexobj(vectors)
        >>> # All magnitudes should be 1.0
        >>> assert jnp.allclose(jnp.abs(vectors), 1.0)
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    # Sample random phases uniformly in [0, 2π)
    phases = jax.random.uniform(key, shape=(n, dim), minval=0, maxval=2 * jnp.pi)

    # Convert to complex unit vectors
    return jnp.exp(1j * phases)


def sample_fhrr_random(dim: int, n: int, key: Optional[jax.random.PRNGKey] = None) -> jnp.ndarray:
    """Sample n random real-valued vectors suitable for FHRR operations.

    Generates random vectors by sampling in the frequency domain with
    conjugate symmetry, ensuring the IFFT produces real-valued results.
    This is the mathematically correct way to generate random vectors
    for FHRR circular convolution operations.

    The frequency-domain representation satisfies:
    - F[0] is real (DC component)
    - F[k] = conj(F[D-k]) for k=1..D-1 (conjugate symmetry)
    - For even D: F[D/2] is real (Nyquist frequency)

    This ensures that ifft(F) produces real-valued vectors (imaginary part
    is negligible numerical noise), which are suitable for FHRR binding and
    unbinding operations with high accuracy.

    Args:
        dim: Dimensionality of each vector (must be >= 2).
        n: Number of vectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).

    Returns:
        JAX array of shape (n, dim) containing real-valued vectors
        suitable for FHRR operations.

    Raises:
        ValueError: If dim < 2.

    Example:
        >>> import jax
        >>> from vsax.ops import FHRROperations
        >>> from vsax.similarity import cosine_similarity
        >>> key = jax.random.PRNGKey(42)
        >>> vectors = sample_fhrr_random(512, 10, key)
        >>> assert vectors.shape == (10, 512)
        >>> assert not jnp.iscomplexobj(vectors)
        >>>
        >>> # Use with FHRR operations
        >>> ops = FHRROperations()
        >>> a, b = vectors[0], vectors[1]
        >>> bound = ops.bind(a, b)
        >>> recovered = ops.unbind(bound, b)
        >>> # High similarity due to correct sampling
        >>> assert cosine_similarity(recovered, a) > 0.99

    Note:
        This function differs from sample_complex_random() in that it enforces
        conjugate symmetry in the frequency domain, guaranteeing real-valued
        time-domain vectors. Use this function for FHRR applications that work
        in the time domain with real-valued vectors.
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    if dim < 2:
        raise ValueError("dim must be at least 2 for FHRR sampling")

    # Split key for sampling multiple vectors
    keys = jax.random.split(key, n)

    def sample_one_vector(subkey: jax.random.PRNGKey) -> jnp.ndarray:
        """Sample a single real-valued FHRR vector."""
        # For FHRR, we need unit magnitude in frequency domain (phasors)
        # This ensures that conjugate-based inverse works perfectly
        # All frequency components have magnitude = 1.0, only phases vary

        # Sample phases for independent frequency components
        # For conjugate symmetry, we only need to sample half the phases
        if dim % 2 == 0:
            # Even dimension
            n_independent = dim // 2 - 1  # Exclude DC (0) and Nyquist (dim/2)

            # Sample phases for positive frequencies (k=1 to k=dim/2-1)
            phases_half = jax.random.uniform(
                subkey, shape=(n_independent,), minval=0, maxval=2 * jnp.pi
            )

            # Build full phase array with conjugate symmetry
            # Initialize all phases to 0
            phases = jnp.zeros(dim)

            # DC component (k=0): phase = 0 (must be real)
            # Nyquist (k=dim/2): phase = 0 (must be real)

            # Positive frequencies (k=1 to k=dim/2-1)
            phases = phases.at[1 : dim // 2].set(phases_half)

            # Negative frequencies (k=dim/2+1 to k=dim-1)
            # Must be conjugate of positive: phases[D-k] = -phases[k]
            phases = phases.at[dim // 2 + 1 :].set(-jnp.flip(phases_half))
        else:
            # Odd dimension (no Nyquist frequency)
            n_independent = (dim - 1) // 2  # Exclude DC only

            # Sample phases for positive frequencies
            phases_half = jax.random.uniform(
                subkey, shape=(n_independent,), minval=0, maxval=2 * jnp.pi
            )

            # Build full phase array
            phases = jnp.zeros(dim)

            # DC component (k=0): phase = 0 (must be real)

            # Positive frequencies (k=1 to k=(dim-1)/2)
            phases = phases.at[1 : n_independent + 1].set(phases_half)

            # Negative frequencies (conjugate symmetric)
            phases = phases.at[n_independent + 1 :].set(-jnp.flip(phases_half))

        # Construct complex frequency-domain vector with UNIT MAGNITUDE
        # F[k] = exp(i * phase[k])  (phasors with magnitude = 1)
        # This ensures that conjugate-based inverse works perfectly
        freq_vec = jnp.exp(1j * phases)

        # IFFT to get time-domain vector
        time_vec = jnp.fft.ifft(freq_vec)

        # Should be real (imaginary part is negligible due to conjugate symmetry)
        # Take real part to eliminate numerical noise
        return jnp.real(time_vec)

    # Sample all vectors using vmap for efficiency
    vectors = jax.vmap(sample_one_vector)(keys)

    return vectors


def sample_quaternion_random(
    dim: int, n: int, key: Optional[jax.random.PRNGKey] = None
) -> jnp.ndarray:
    """Sample n random unit quaternion hypervectors.

    Generates random hypervectors where each coordinate is a unit quaternion
    uniformly distributed on the 3-sphere S³. This is achieved by sampling
    from N(0, I₄) and normalizing.

    The output shape is (n, dim, 4) where:
    - n is the number of hypervectors
    - dim is the number of quaternion coordinates
    - 4 is the quaternion components (a, b, c, d)

    Args:
        dim: Number of quaternion coordinates per hypervector.
        n: Number of hypervectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).

    Returns:
        JAX array of shape (n, dim, 4) containing unit quaternion hypervectors.

    Example:
        >>> import jax
        >>> key = jax.random.PRNGKey(42)
        >>> vectors = sample_quaternion_random(512, 10, key)
        >>> assert vectors.shape == (10, 512, 4)
        >>> # All quaternions should be unit length
        >>> norms = jnp.linalg.norm(vectors, axis=-1)
        >>> assert jnp.allclose(norms, 1.0, atol=1e-6)
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    # Sample from N(0, I₄) and normalize to unit quaternions
    raw = jax.random.normal(key, shape=(n, dim, 4))
    norms = jnp.linalg.norm(raw, axis=-1, keepdims=True)
    epsilon = 1e-10
    return raw / (norms + epsilon)


def sample_binary_random(
    dim: int, n: int, key: Optional[jax.random.PRNGKey] = None, bipolar: bool = True
) -> jnp.ndarray:
    """Sample n random binary vectors.

    Generates random binary vectors with values uniformly sampled from:
    - Bipolar mode: {-1, +1}
    - Binary mode: {0, 1}

    These are suitable for use with Binary VSA operations.

    Args:
        dim: Dimensionality of each vector.
        n: Number of vectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).
        bipolar: If True, sample from {-1, +1}. If False, sample from {0, 1}.

    Returns:
        JAX array of shape (n, dim) containing binary values.

    Example:
        >>> import jax
        >>> key = jax.random.PRNGKey(42)
        >>>
        >>> # Bipolar sampling
        >>> bipolar_vecs = sample_binary_random(512, 10, key, bipolar=True)
        >>> assert bipolar_vecs.shape == (10, 512)
        >>> assert jnp.all(jnp.isin(bipolar_vecs, jnp.array([-1, 1])))
        >>>
        >>> # Binary sampling
        >>> binary_vecs = sample_binary_random(512, 10, key, bipolar=False)
        >>> assert jnp.all(jnp.isin(binary_vecs, jnp.array([0, 1])))
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    if bipolar:
        # Sample from {-1, +1}
        return jax.random.choice(key, jnp.array([-1, 1]), shape=(n, dim))
    else:
        # Sample from {0, 1}
        return jax.random.choice(key, jnp.array([0, 1]), shape=(n, dim))
