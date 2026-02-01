import numpy as np
from functools import lru_cache
import hashlib

# Try importing numba for JIT compilation (optional dependency)
try:
    from numba import jit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    # Fallback decorator that does nothing
    def jit(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


# Try importing getdist's ParamError for proper exception handling
try:
    from getdist.chains import ParamError
except ImportError:
    # Define a dummy exception if getdist is not available
    class ParamError(Exception):
        pass


def Rminus1(samples: dict):
    """
    Compute Gelman-Rubin R-1 statistic for multiple MCMC chains.
    Args:
        samples: dict mapping labels to MCMC chain objects (e.g., getdist MCSamples)

    Returns: list of R-1 values printed to console
    """
    return [
        print(f"The R-1 for {lbl} is {chain.getGelmanRubin():.3f}")
        for lbl, chain in samples.items()
    ]


def extract_powerlaw_params(
    chain, As_param_name=None, ns_param_name="n_s", fallback_As=None, fallback_ns=None
):
    """
    Extract and convert A_s and n_s parameters from MCMC chain.

    Automatically detects common A_s parameter naming conventions:
    - ln10^{10}A_s, ln_A_s_1e10, logA (logarithmic with 1e10 factor)
    - A_s, As (direct values)

    Args:
        chain: MCMC chain dictionary with parameter arrays
        As_param_name: Name of A_s parameter in chain (default: None, auto-detect)
        ns_param_name: Name of n_s parameter in chain (default: "n_s")
        fallback_As: Fallback value for A_s if not found in chain (default: None)
        fallback_ns: Fallback value for n_s if not found in chain (default: None)

    Returns:
        A_s: Array of A_s values (converted to standard A_s units)
        n_s: Array of n_s values

    Raises:
        KeyError: If required parameters not found in chain and no fallback provided
    """
    # Get available parameter names
    try:
        param_names = chain.getParamNames().list()
    except AttributeError:
        param_names = list(chain.keys()) if hasattr(chain, "keys") else []

    # Determine number of samples in chain
    try:
        # Try to get from getdist MCSamples
        n_samples = chain.numrows
    except AttributeError:
        # Try from dict-like structure
        try:
            first_param = next(iter(param_names))
            n_samples = len(chain[first_param])
        except (StopIteration, KeyError, TypeError):
            n_samples = None

    # Extract n_s - use try/except to handle both dict-like and getdist objects
    try:
        n_s = np.array(chain[ns_param_name])
    except (KeyError, IndexError, ParamError):
        if fallback_ns is not None:
            if n_samples is not None:
                n_s = np.full(n_samples, fallback_ns)
                print(
                    f"Using fallback n_s = {fallback_ns} (parameter '{ns_param_name}' not found in chain)"
                )
            else:
                raise ValueError(
                    f"Parameter '{ns_param_name}' not found and cannot determine chain size for fallback. "
                    f"Available parameters: {param_names}"
                )
        else:
            raise KeyError(
                f"Parameter '{ns_param_name}' not found in chain. "
                f"Available parameters: {param_names}"
            )

    # Auto-detect A_s parameter if not specified
    if As_param_name is None:
        # Common A_s parameter names in order of preference
        # Logarithmic forms (need conversion)
        ln_variants = [
            "ln10^{10}A_s",  # CosmoMC/CLASS default
            "ln_A_s_1e10",  # Cobaya/ACT style
            "logA",  # Some conventions
            "log(10^10 A_s)",  # Verbose form
        ]
        # Direct forms (no conversion needed)
        direct_variants = [
            "A_s",  # Direct
            "As",  # Short form
        ]

        # Try logarithmic variants first
        for variant in ln_variants:
            if variant in param_names:
                As_param_name = variant
                break

        # Try direct variants if no log form found
        if As_param_name is None:
            for variant in direct_variants:
                if variant in param_names:
                    As_param_name = variant
                    break

        # If still not found, check for fallback
        if As_param_name is None:
            if fallback_As is not None:
                if n_samples is not None:
                    print(
                        f"Using fallback A_s = {fallback_As:.3e} (no A_s parameter found in chain)"
                    )
                    return np.full(n_samples, fallback_As), n_s
                else:
                    raise ValueError(
                        f"No A_s parameter found and cannot determine chain size for fallback. "
                        f"Available parameters: {param_names}"
                    )
            else:
                raise KeyError(
                    f"No A_s parameter found in chain. Tried: {ln_variants + direct_variants}. "
                    f"Available parameters: {param_names}"
                )

    # Extract A_s values
    try:
        As_values = np.array(chain[As_param_name])
    except (KeyError, IndexError, ParamError):
        if fallback_As is not None:
            if n_samples is not None:
                print(
                    f"Using fallback A_s = {fallback_As:.3e} (parameter '{As_param_name}' not found in chain)"
                )
                return np.full(n_samples, fallback_As), n_s
            else:
                raise ValueError(
                    f"Parameter '{As_param_name}' not found and cannot determine chain size for fallback. "
                    f"Available parameters: {param_names}"
                )
        else:
            raise KeyError(
                f"Parameter '{As_param_name}' not found in chain. "
                f"Available parameters: {param_names}"
            )

    # Convert to standard A_s based on parameter name
    # Logarithmic forms: ln(10^10 * A_s) -> A_s = exp(value) / 10^10
    if any(x in As_param_name.lower() for x in ["ln", "log"]):
        if (
            "1e10" in As_param_name
            or "10^10" in As_param_name
            or "10^{10}" in As_param_name
        ):
            A_s = np.exp(As_values) / 1e10
        else:
            # Assume it's log10(A_s) if no scaling factor mentioned
            A_s = 10**As_values
    else:
        # Direct A_s value
        A_s = As_values

    return A_s, n_s


def k_to_ell(k, d=14000):
    # Relationship: ell ≈ k * d where d ≈ 14000 Mpc (comoving distance to last scattering)
    return k * d


def ell_to_k(ell, d=14000):
    # Relationship: ell ≈ k * d where d ≈ 14000 Mpc (comoving distance to last scattering)
    return ell / d


def get_bin_centers(k_start, k_end, Nbins):
    """
    Compute bin centers for CLASS binned_Pk implementation.
    Args:
        k_start: start of binning range
        k_end: end of binning range
        Nbins: number of bins
    Returns:
        bin_centers: array of bin center k values
    """

    # Compute bin centers (as CLASS does)
    log10_k_min = np.log10(k_start)
    log10_k_max = np.log10(k_end)
    delta_log10_k = (log10_k_max - log10_k_min) / Nbins

    bin_centers = np.array(
        [10 ** (log10_k_min + (i + 0.5) * delta_log10_k) for i in range(Nbins)]
    )
    return bin_centers


def get_Binned_Pk(k_start=1e-2, k_end=1e-1, Nbins=10):
    """
    Create a binned power spectrum function matching CLASS binned_Pk implementation.

    This implements the exact algorithm from CLASS primordial.c:primordial_binned_spectrum()

    Returns enhancement/suppression factor delta(k) where P(k) = P_powerlaw(k) * [1 + delta(k)]
    Expects delta_values with length Nbins (e.g., [custom1, ..., custom10] for 10 bins)

    When A_s and n_s are provided, returns full P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
    Otherwise returns just the enhancement factor [1 + delta(k)]

    The interpolation is linear in log(k) space between bin centers.
    """

    bin_centers = get_bin_centers(k_start, k_end, Nbins)

    def compute_delta_k(k, delta_values):
        """
        Compute delta(k) for given k values using CLASS algorithm.

        Args:
            k: wavenumber array or scalar
            delta_values: bin amplitudes (length Nbins)
        """
        k = np.atleast_1d(k)
        delta_k = np.zeros_like(k)

        for i, k_val in enumerate(k):
            if k_val < k_start or k_val > k_end:
                # Outside binning range: delta = 0
                delta_k[i] = 0.0
            else:
                # Inside binning range: linear interpolation in log(k) space
                log_k = np.log(k_val)

                # Find which bin k belongs to
                found = False
                for i_bin in range(Nbins - 1):
                    log_k_left = np.log(bin_centers[i_bin])
                    log_k_right = np.log(bin_centers[i_bin + 1])

                    if log_k >= log_k_left and log_k <= log_k_right:
                        # Linear interpolation between bins
                        delta_left = delta_values[i_bin]
                        delta_right = delta_values[i_bin + 1]
                        delta_k[i] = delta_left + (delta_right - delta_left) * (
                            log_k - log_k_left
                        ) / (log_k_right - log_k_left)
                        found = True
                        break

                # Handle edge cases
                if not found:
                    if k_val <= bin_centers[0]:
                        delta_k[i] = delta_values[0]
                    elif k_val >= bin_centers[-1]:
                        delta_k[i] = delta_values[-1]

        return delta_k

    def Binned_Pk(k, delta_values, A_s=None, n_s=None, k_pivot=0.05):
        """
        Compute enhancement factor or full power spectrum.

        Args:
            k: wavenumber array
            delta_values: bin amplitudes (length Nbins, e.g., [custom1, ..., custom10])
            A_s: scalar amplitude (optional). If provided with n_s, returns full P(k)
            n_s: scalar spectral index (optional). If provided with A_s, returns full P(k)
            k_pivot: pivot scale in Mpc^-1 (default: 0.05, standard for Planck)

        Returns:
            If A_s and n_s provided: P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
            Otherwise: 1 + delta(k) for each k
        """
        enhancement = 1.0 + compute_delta_k(k, delta_values)

        if A_s is not None and n_s is not None:
            k = np.atleast_1d(k)
            powerlaw = A_s * (k / k_pivot) ** (n_s - 1)
            return powerlaw * enhancement

        return enhancement

    return Binned_Pk


def get_Binned_Pk_vectorized(k_start=1e-2, k_end=1e-1, Nbins=10):
    """
    Vectorized version matching CLASS binned_Pk implementation.
    Much faster for batch operations with multiple samples.

    Uses linear interpolation in log(k) space between bin centers,
    exactly as CLASS does in primordial.c:primordial_binned_spectrum()

    When A_s and n_s arrays are provided, computes full P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
    for multiple samples simultaneously using broadcasting.
    """
    # Compute bin centers (as CLASS does)
    log10_k_min = np.log10(k_start)
    log10_k_max = np.log10(k_end)
    delta_log10_k = (log10_k_max - log10_k_min) / Nbins

    bin_centers = np.array(
        [10 ** (log10_k_min + (i + 0.5) * delta_log10_k) for i in range(Nbins)]
    )
    log_bin_centers = np.log(bin_centers)

    def compute_delta_k_vectorized(k, delta_values):
        """
        Vectorized computation of delta(k) for multiple samples.

        Args:
            k: array of k values, shape (n_k,)
            delta_values: array of shape (n_samples, Nbins) or (Nbins,)

        Returns:
            delta_k: array of shape (n_samples, n_k) or (n_k,)
        """
        k = np.atleast_1d(k)
        delta_values = np.atleast_2d(delta_values)
        n_samples, n_bins = delta_values.shape
        n_k = len(k)

        # Initialize output
        delta_k = np.zeros((n_samples, n_k))

        # Compute log(k) once
        log_k = np.log(k)

        # Masks for k range
        in_range = (k >= k_start) & (k <= k_end)

        # For each sample (this is still faster than looping over all k)
        for i_sample in range(n_samples):
            deltas = delta_values[i_sample]

            # Vectorized interpolation for k values in range
            for i_k in np.where(in_range)[0]:
                k_val = k[i_k]
                lk = log_k[i_k]

                # Handle edge cases first
                if k_val <= bin_centers[0]:
                    delta_k[i_sample, i_k] = deltas[0]
                elif k_val >= bin_centers[-1]:
                    delta_k[i_sample, i_k] = deltas[-1]
                else:
                    # Find bin using searchsorted (fast)
                    i_bin = np.searchsorted(log_bin_centers, lk) - 1
                    if i_bin >= 0 and i_bin < n_bins - 1:
                        # Linear interpolation in log(k) space
                        log_k_left = log_bin_centers[i_bin]
                        log_k_right = log_bin_centers[i_bin + 1]
                        delta_left = deltas[i_bin]
                        delta_right = deltas[i_bin + 1]

                        delta_k[i_sample, i_k] = delta_left + (
                            delta_right - delta_left
                        ) * (lk - log_k_left) / (log_k_right - log_k_left)

        # If input was 1D delta_values, return 1D result
        if delta_values.shape[0] == 1:
            return delta_k[0]
        return delta_k

    def Binned_Pk_vectorized(k, delta_values, A_s=None, n_s=None, k_pivot=0.05):
        """
        Vectorized binned power spectrum.

        Args:
            k: array of k values, shape (n_k,)
            delta_values: array of shape (n_samples, Nbins) or (Nbins,)
                         bin amplitudes (e.g., [custom1, ..., custom10])
            A_s: array of A_s values, shape (n_samples,) or scalar (optional)
            n_s: array of n_s values, shape (n_samples,) or scalar (optional)
            k_pivot: pivot scale in Mpc^-1 (default: 0.05, standard for Planck)

        Returns:
            If A_s and n_s provided: P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
                Shape: (n_samples, n_k) or (n_k,)
            Otherwise: Enhancement factor 1 + delta(k)
                Shape: (n_samples, n_k) or (n_k,)
        """
        enhancement = 1.0 + compute_delta_k_vectorized(k, delta_values)

        if A_s is not None and n_s is not None:
            k = np.atleast_1d(k)
            A_s = np.atleast_1d(A_s)
            n_s = np.atleast_1d(n_s)

            # Compute power-law with broadcasting
            # A_s and n_s: (n_samples,) -> (n_samples, 1)
            # k: (n_k,) -> (1, n_k)
            # Result: (n_samples, n_k)
            powerlaw = A_s[:, None] * (k[None, :] / k_pivot) ** (n_s[:, None] - 1)

            # Handle 1D case
            if powerlaw.shape[0] == 1:
                powerlaw = powerlaw[0]

            return powerlaw * enhancement

        return enhancement

    return Binned_Pk_vectorized


if HAS_NUMBA:

    @jit(nopython=True)
    def _compute_delta_k_numba(k, delta_values, bin_centers, k_start, k_end):
        """
        Numba-accelerated delta(k) computation matching CLASS algorithm.

        Args:
            k: array of k values (n_k,)
            delta_values: array of bin amplitudes (Nbins,) for ONE sample
            bin_centers: array of bin center k values (Nbins,)
            k_start, k_end: binning range

        Returns:
            delta_k: array of delta values (n_k,)
        """
        n_k = len(k)
        n_bins = len(bin_centers)
        delta_k = np.zeros(n_k)

        log_bin_centers = np.log(bin_centers)

        for i in range(n_k):
            k_val = k[i]

            if k_val < k_start or k_val > k_end:
                delta_k[i] = 0.0
            else:
                log_k = np.log(k_val)

                # Handle edge cases
                if k_val <= bin_centers[0]:
                    delta_k[i] = delta_values[0]
                elif k_val >= bin_centers[-1]:
                    delta_k[i] = delta_values[-1]
                else:
                    # Find bin and interpolate
                    for i_bin in range(n_bins - 1):
                        log_k_left = log_bin_centers[i_bin]
                        log_k_right = log_bin_centers[i_bin + 1]

                        if log_k >= log_k_left and log_k <= log_k_right:
                            delta_left = delta_values[i_bin]
                            delta_right = delta_values[i_bin + 1]
                            delta_k[i] = delta_left + (delta_right - delta_left) * (
                                log_k - log_k_left
                            ) / (log_k_right - log_k_left)
                            break

        return delta_k

    @jit(nopython=True, parallel=True)
    def _compute_all_samples_numba(
        k,
        delta_array,
        bin_centers,
        k_start,
        k_end,
        A_s_array=None,
        n_s_array=None,
        k_pivot=0.05,
    ):
        """
        Numba-accelerated computation for all samples.

        Args:
            k: output k values (n_k,)
            delta_array: parameter samples (n_samples, Nbins) - just the custom values
            bin_centers: bin centers (Nbins,)
            k_start, k_end: binning range
            A_s_array: array of A_s values (n_samples,) - optional
            n_s_array: array of n_s values (n_samples,) - optional
            k_pivot: pivot scale in Mpc^-1 (default: 0.05)

        Returns:
            results: enhancement factor or full P(k), shape (n_samples, n_k)
                If A_s and n_s provided: P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
                Otherwise: 1 + delta(k)
        """
        n_samples = delta_array.shape[0]
        n_k = len(k)
        results = np.zeros((n_samples, n_k))

        include_powerlaw = A_s_array is not None and n_s_array is not None

        for i in range(n_samples):
            delta_k = _compute_delta_k_numba(
                k, delta_array[i], bin_centers, k_start, k_end
            )
            enhancement = 1.0 + delta_k

            if include_powerlaw:
                # Compute power-law for this sample
                A_s = A_s_array[i]
                n_s = n_s_array[i]
                for j in range(n_k):
                    powerlaw = A_s * (k[j] / k_pivot) ** (n_s - 1)
                    results[i, j] = powerlaw * enhancement[j]
            else:
                results[i] = enhancement

        return results


def _make_cache_key(
    k,
    chain,
    nbins,
    k_start,
    k_end,
    method,
    param_name_pattern,
    include_powerlaw,
    As_param_name,
    ns_param_name,
    k_pivot,
):
    """
    Create a hashable cache key from function arguments.

    Uses blake2b hashing of serialized parameters to create a compact,
    deterministic key that can be used with lru_cache.
    """
    # Convert k array to bytes
    k_bytes = np.asarray(k).tobytes()

    # Extract parameter data from chain and convert to bytes
    bins = [param_name_pattern.format(i=i) for i in range(1, nbins + 1)]

    # Check if delta bins exist
    has_delta_bins = True
    try:
        try:
            param_names = chain.getParamNames().list()
        except AttributeError:
            param_names = list(chain.keys()) if hasattr(chain, "keys") else []
        if bins[0] not in param_names:
            has_delta_bins = False
    except:
        try:
            test = chain[bins[0]]
        except (KeyError, IndexError):
            has_delta_bins = False

    # Build hashable components
    hash_components = [
        k_bytes,
        str(nbins).encode(),
        str(k_start).encode(),
        str(k_end).encode(),
        method.encode(),
        param_name_pattern.encode(),
        str(include_powerlaw).encode(),
        str(As_param_name).encode() if As_param_name else b"None",
        ns_param_name.encode(),
        str(k_pivot).encode(),
        str(has_delta_bins).encode(),
    ]

    # Add chain parameter data to hash
    if has_delta_bins:
        for bin_name in bins:
            try:
                bin_data = np.asarray(chain[bin_name])
                hash_components.append(bin_data.tobytes())
            except:
                pass

    # Add power-law parameters if needed
    if include_powerlaw or not has_delta_bins:
        try:
            A_s, n_s = extract_powerlaw_params(chain, As_param_name, ns_param_name)
            hash_components.append(A_s.tobytes())
            hash_components.append(n_s.tobytes())
        except:
            pass

    # Create hash
    combined = b"".join(hash_components)
    cache_key = hashlib.blake2b(combined, digest_size=16).hexdigest()

    return cache_key


@lru_cache(maxsize=128)
def _compute_Pk_samples_cached(cache_key, k_tuple, method, use_numba):
    """
    Cached computation function - called by compute_Pk_samples.

    This function is cached using lru_cache. The actual computation is done here,
    but parameters are passed through the cache_key hash to enable caching of
    non-hashable objects like chain dictionaries.

    Note: This function returns None and is not called directly. The real
    computation happens in compute_Pk_samples which uses the cache_key
    for memoization via a module-level cache dictionary.
    """
    # This is a placeholder - actual caching is done via _PK_CACHE dictionary
    return None


# Module-level cache for computed samples
_PK_CACHE = {}
_CACHE_HITS = 0
_CACHE_MISSES = 0


def clear_Pk_cache():
    """
    Clear the power spectrum computation cache.

    Useful for freeing memory or ensuring fresh computations.
    Also resets cache statistics.
    """
    global _PK_CACHE, _CACHE_HITS, _CACHE_MISSES
    _PK_CACHE.clear()
    _CACHE_HITS = 0
    _CACHE_MISSES = 0
    print("Power spectrum cache cleared.")


def get_Pk_cache_info():
    """
    Get information about the power spectrum cache.

    Returns:
        dict with keys: 'size', 'hits', 'misses', 'hit_rate', 'total_calls'
    """
    total = _CACHE_HITS + _CACHE_MISSES
    hit_rate = _CACHE_HITS / total if total > 0 else 0.0
    return {
        "size": len(_PK_CACHE),
        "hits": _CACHE_HITS,
        "misses": _CACHE_MISSES,
        "hit_rate": hit_rate,
        "total_calls": total,
    }


def compute_Pk_samples(
    k,
    chain,
    nbins=10,
    k_start=1e-2,
    k_end=1e-1,
    method="vectorized",
    use_numba=None,
    param_name_pattern="delta_{i}",
    include_powerlaw=False,
    As_param_name=None,
    ns_param_name="n_s",
    k_pivot=0.05,
    use_cache=True,
    fallback_As=None,
    fallback_ns=None,
):
    """
    Compute binned power spectrum samples from MCMC chain with caching.
    Matches the CLASS binned_Pk algorithm exactly.

    This function is flexible: if delta_i bins are missing in the chain,
    it will automatically compute a pure power-law P(k) = A_s * (k/k_pivot)^(n_s-1).

    **Caching:** Results are cached based on input parameters. Repeated calls with
    the same k array, chain data, and parameters will return cached results instantly.
    Use clear_Pk_cache() to free memory or get_Pk_cache_info() for cache statistics.

    Args:
        k: array of k values where to evaluate the spectrum
        chain: MCMC chain dictionary with parameter keys
        nbins: number of bins (default: 10)
        k_start: minimum k for binning range (default: 1e-2)
        k_end: maximum k for binning range (default: 1e-1)
        method: 'original', 'vectorized', or 'numba' (default: 'vectorized')
        use_numba: bool or None. If None, auto-detect numba availability
        param_name_pattern: string pattern for parameter names with {i} placeholder
                           (default: "delta_{i}", also supports "custom{i}", etc.)
        include_powerlaw: bool, if True computes full P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
                         if False (default), returns only [1 + delta(k)]
                         Note: If delta bins are missing, power-law params are always extracted
        As_param_name: name of A_s parameter in chain (default: None, auto-detects common names:
                      ln10^{10}A_s, ln_A_s_1e10, logA, A_s, As, etc.)
        ns_param_name: name of n_s parameter in chain (default: "n_s")
        k_pivot: pivot scale in Mpc^-1 (default: 0.05, standard for Planck)
        use_cache: bool, if True (default) uses caching; set to False for testing/debugging
        fallback_As: fallback value for A_s if not found in chain (default: None, raises error if missing)
        fallback_ns: fallback value for n_s if not found in chain (default: None, raises error if missing)

    Returns:
        samples: list of power spectrum samples (each has shape matching k grid)
                If delta bins present and include_powerlaw=True: P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
                If delta bins present and include_powerlaw=False: [1 + delta(k)]
                If delta bins missing: P(k) = A_s * (k/k_pivot)^(n_s-1) (pure power-law)

    Performance notes:
        - 'vectorized': ~10-100x faster than 'original' for large chains
        - 'numba': ~10-50x faster if numba is available and chain is large
        - For small chains (<1000 samples), overhead may dominate
        - **Caching**: Repeated calls with same parameters are instant (cache hit)

    Example:
        # Compute deviations only (default)
        samples = compute_Pk_samples(k, chain, nbins=20)

        # Compute full power spectrum
        samples = compute_Pk_samples(k, chain, nbins=20, include_powerlaw=True)

        # With power-law only chains (no delta bins):
        samples = compute_Pk_samples(k, chain_powerlaw)  # returns P(k) = A_s * (k/k_pivot)^(n_s-1)

        # Clear cache to free memory
        clear_Pk_cache()

        # Check cache statistics
        info = get_Pk_cache_info()
        print(f"Cache hit rate: {info['hit_rate']:.1%}")
    """
    global _PK_CACHE, _CACHE_HITS, _CACHE_MISSES

    # Create cache key
    if use_cache:
        cache_key = _make_cache_key(
            k,
            chain,
            nbins,
            k_start,
            k_end,
            method,
            param_name_pattern,
            include_powerlaw,
            As_param_name,
            ns_param_name,
            k_pivot,
        )

        # Check cache
        if cache_key in _PK_CACHE:
            _CACHE_HITS += 1
            if _CACHE_HITS == 1:  # First hit
                print(f"✓ Using cached results (cache hit #{_CACHE_HITS})")
            elif _CACHE_HITS % 10 == 0:  # Every 10 hits
                info = get_Pk_cache_info()
                print(
                    f"✓ Cache hit #{_CACHE_HITS} (hit rate: {info['hit_rate']:.1%}, {info['size']} entries)"
                )
            return _PK_CACHE[cache_key]

        _CACHE_MISSES += 1
    # Auto-detect numba
    if use_numba is None:
        use_numba = HAS_NUMBA and method == "numba"

    if method == "numba" and not HAS_NUMBA:
        print("Warning: Numba not available, falling back to vectorized method")
        method = "vectorized"

    bins = [param_name_pattern.format(i=i) for i in range(1, nbins + 1)]

    # Check if delta bins exist in the chain
    has_delta_bins = True
    try:
        # Try to get parameter names
        try:
            param_names = chain.getParamNames().list()
        except AttributeError:
            param_names = list(chain.keys()) if hasattr(chain, "keys") else []

        # Check if first bin exists
        if bins[0] not in param_names:
            has_delta_bins = False
    except:
        # If we can't check, try to extract and catch the error
        try:
            test = chain[bins[0]]
        except (KeyError, IndexError):
            has_delta_bins = False

    # If no delta bins, compute pure power-law P(k)
    if not has_delta_bins:
        print(
            "Delta bins not found in chain. Computing pure power-law P(k) = A_s * (k/k_pivot)^(n_s-1)"
        )
        A_s_array, n_s_array = extract_powerlaw_params(
            chain, As_param_name, ns_param_name, fallback_As, fallback_ns
        )
        n_samples = len(A_s_array)

        # Compute power-law for all samples
        k_array = np.atleast_1d(k)
        A_s_2d = A_s_array[:, None]  # Shape: (n_samples, 1)
        n_s_2d = n_s_array[:, None]  # Shape: (n_samples, 1)
        k_2d = k_array[None, :]  # Shape: (1, n_k)

        # Vectorized computation: (n_samples, n_k)
        powerlaw = A_s_2d * (k_2d / k_pivot) ** (n_s_2d - 1)

        # Return as list for compatibility
        samples = [powerlaw[i] for i in range(n_samples)]

        if use_cache:
            _PK_CACHE[cache_key] = samples
        return samples

    # Extract delta array: shape (n_samples, n_bins)
    delta_array = np.array([chain[bin] for bin in bins]).T
    n_samples = delta_array.shape[0]

    # Extract power-law parameters if requested
    A_s_array = None
    n_s_array = None
    if include_powerlaw:
        A_s_array, n_s_array = extract_powerlaw_params(
            chain, As_param_name, ns_param_name, fallback_As, fallback_ns
        )

    # Compute bin centers (as CLASS does)
    bin_centers = get_bin_centers(k_start, k_end, nbins)

    if method == "original":
        # Original implementation with loop
        from tqdm.auto import tqdm

        Pk = get_Binned_Pk(k_start=k_start, k_end=k_end, Nbins=nbins)
        samples = []
        for i, delta_vals in enumerate(tqdm(delta_array, desc="Computing samples")):
            if include_powerlaw:
                binned_factor = Pk(
                    k, delta_vals, A_s=A_s_array[i], n_s=n_s_array[i], k_pivot=k_pivot
                )
            else:
                binned_factor = Pk(k, delta_vals)
            samples.append(binned_factor)

    elif method == "numba" and use_numba:
        # Numba-accelerated version
        if include_powerlaw:
            print(
                f"Computing {n_samples} samples with Numba acceleration (full P(k))..."
            )
            results = _compute_all_samples_numba(
                k,
                delta_array,
                bin_centers,
                k_start,
                k_end,
                A_s_array,
                n_s_array,
                k_pivot,
            )
        else:
            print(f"Computing {n_samples} samples with Numba acceleration...")
            results = _compute_all_samples_numba(
                k, delta_array, bin_centers, k_start, k_end
            )
        samples = [results[i] for i in range(n_samples)]

    else:  # method == 'vectorized' (default)
        # Fully vectorized NumPy implementation
        if include_powerlaw:
            print(f"Computing {n_samples} samples with vectorized NumPy (full P(k))...")
        else:
            print(f"Computing {n_samples} samples with vectorized NumPy...")

        Pk_vectorized = get_Binned_Pk_vectorized(
            k_start=k_start, k_end=k_end, Nbins=nbins
        )

        # Compute all samples at once using broadcasting
        if include_powerlaw:
            results = Pk_vectorized(
                k, delta_array, A_s=A_s_array, n_s=n_s_array, k_pivot=k_pivot
            )
        else:
            results = Pk_vectorized(k, delta_array)

        # Return as list for compatibility with original
        # Handle both 1D (single sample) and 2D (multiple samples) cases
        if results.ndim == 1:
            samples = [results]
        else:
            samples = [results[i] for i in range(n_samples)]

    # Store in cache if caching is enabled
    if use_cache:
        _PK_CACHE[cache_key] = samples
        if len(_PK_CACHE) > 256:  # Soft limit warning
            print(
                f"⚠ Cache size ({len(_PK_CACHE)}) is large. Consider calling clear_Pk_cache() to free memory."
            )

    return samples


def compute_Pk_samples_fast(
    k,
    chain,
    nbins=10,
    k_start=1e-2,
    k_end=1e-1,
    include_powerlaw=False,
    As_param_name=None,
    ns_param_name="n_s",
    k_pivot=0.05,
    use_cache=True,
):
    """
    Convenience function: automatically choose the fastest method with caching.

    Args:
        k: array of k values
        chain: MCMC chain dictionary
        nbins: number of bins
        k_start: minimum k for binning range
        k_end: maximum k for binning range
        include_powerlaw: bool, if True computes full P(k) = A_s * (k/k_pivot)^(n_s-1) * [1 + delta(k)]
        As_param_name: name of A_s parameter in chain (default: None, auto-detects)
        ns_param_name: name of n_s parameter in chain (default: "n_s")
        k_pivot: pivot scale in Mpc^-1 (default: 0.05, standard for Planck)
        use_cache: bool, if True (default) uses caching
    """
    method = "numba" if HAS_NUMBA else "vectorized"
    return compute_Pk_samples(
        k,
        chain,
        nbins=nbins,
        k_start=k_start,
        k_end=k_end,
        method=method,
        include_powerlaw=include_powerlaw,
        As_param_name=As_param_name,
        ns_param_name=ns_param_name,
        k_pivot=k_pivot,
        use_cache=use_cache,
    )


def compute_ns_eff(k, Pk_samples_dict):
    """
    Compute the effective spectral tilt n_s(k) - 1 = d ln P(k) / d ln k for power spectrum samples.

    This quantifies the scale-dependence of the primordial power spectrum:
    - For pure power-law: n_s(k) - 1 = constant (the primordial tilt parameter)
    - For features: n_s(k) - 1 varies with scale, revealing oscillations/steps

    Useful for identifying and visualizing deviations from scale-invariance.

    Args:
        k: array of k values where the spectra were evaluated
        Pk_samples_dict: dictionary mapping labels to lists of P(k) samples
                        e.g., {"chain1": [Pk_sample1, Pk_sample2, ...], "chain2": [...]}

    Returns:
        dict: dictionary mapping labels to n_s(k)-1 arrays with shape (n_samples, n_k)
              e.g., {"chain1": np.ndarray, "chain2": np.ndarray}

    Example:
        >>> k = np.logspace(-3, -1, 100)
        >>> Pk_samples = {"Planck": compute_Pk_samples(k, chain, include_powerlaw=True)}
        >>> ns_eff = compute_ns_eff(k, Pk_samples)
        >>> ns_eff["Planck"].shape  # (n_samples, 100)
    """
    k_array = np.atleast_1d(k)

    # Validate inputs
    if len(k_array) < 2:
        raise ValueError(
            "Cannot compute spectral tilt derivative with fewer than 2 k-points"
        )

    # Precompute ln(k) once for all chains
    ln_k = np.log(k_array)

    ns_eff_dict = {}

    for label, samples in Pk_samples_dict.items():
        # Convert samples list to 2D array for vectorized computation
        Pk_array = np.array(samples)  # Shape: (n_samples, n_k)

        # Validate P(k) > 0
        if np.any(Pk_array <= 0):
            raise ValueError(
                f"Power spectrum for '{label}' contains non-positive values. "
                "Cannot compute logarithmic derivative."
            )

        # Compute n_s(k) - 1 = d ln P(k) / d ln k
        ln_Pk = np.log(Pk_array)  # Shape: (n_samples, n_k)

        # np.gradient uses 2nd-order central differences (interior) and
        # 1st-order at boundaries - optimal for smooth spectra
        ns_eff = np.gradient(ln_Pk, ln_k, axis=1)  # Shape: (n_samples, n_k)

        ns_eff_dict[label] = ns_eff

    return ns_eff_dict


def compute_ns_eff_fast(k, Pk_samples):
    """
    Compute effective spectral tilt for a single list of P(k) samples.

    Convenience function for when you have samples from a single chain.

    Args:
        k: array of k values where the spectra were evaluated
        Pk_samples: list of P(k) samples (each has shape matching k)

    Returns:
        np.ndarray: effective tilt (n_s-1) with shape (n_samples, n_k)

    Example:
        >>> k = np.logspace(-3, -1, 100)
        >>> Pk_samples = compute_Pk_samples(k, chain, include_powerlaw=True)
        >>> ns_eff = compute_ns_eff_fast(k, Pk_samples)
    """
    result = compute_ns_eff(k, {"_single": Pk_samples})
    return result["_single"]


def compute_cls(
    chain,
    n_samples=100,
    nbins=20,
    k_start=1e-3,
    k_end=0.23,
    param_name_pattern="delta_{i}",
    lmax=2500,
    baseline_params=None,
    As_param_name=None,
    ns_param_name="n_s",
    k_pivot=0.05,
    include_ell_factor=True,
    residuals=False,
):
    """
    Compute CMB power spectra (TT, TE, EE) from MCMC chain samples using CLASS.

    This function selects N random samples from the chain and computes theoretical
    CMB Cls for each sample using the CLASS Boltzmann code.

    Args:
        chain: MCMC chain dictionary with parameter arrays
        n_samples: Number of random samples to select from chain (default: 100)
        nbins: Number of bins for binned primordial power spectrum (default: 20)
        k_start: Minimum k for binning range in Mpc^-1 (default: 1e-3)
        k_end: Maximum k for binning range in Mpc^-1 (default: 0.23)
        param_name_pattern: Pattern for bin parameter names with {i} placeholder (default: "delta_{i}")
        lmax: Maximum multipole to compute (default: 2500)
        baseline_params: Dict of baseline CLASS parameters. If None, uses standard ΛCDM values.
                        Should include: omega_b, omega_cdm, h, tau_reio, etc.
        As_param_name: Name of A_s parameter in chain (default: None, auto-detects)
        ns_param_name: Name of n_s parameter in chain (default: "n_s")
        k_pivot: Pivot scale in Mpc^-1 (default: 0.05)

    Returns:
        dict: Dictionary with keys 'ell', 'TT', 'TE', 'EE', each containing:
              - 'ell': array of multipole values (same for all spectra)
              - 'TT'/'TE'/'EE': array of shape (n_samples, n_ell) with Cl values in μK²

    Example:
        >>> cls_dict = compute_cls(chain, n_samples=200, nbins=20, lmax=2500)
        >>> ells = cls_dict['ell']
        >>> tt_samples = cls_dict['TT']  # shape: (200, n_ell)
        >>> te_samples = cls_dict['TE']
        >>> ee_samples = cls_dict['EE']
    """
    try:
        from classy import Class
    except ImportError:
        raise ImportError(
            "CLASS Python wrapper not installed. Install it with: pip install classy"
        )

    # Default baseline parameters (Planck 2018 best-fit)
    if baseline_params is None:
        baseline_params = {
            "omega_b": 0.02238280,
            "omega_cdm": 0.1201075,
            "h": 0.6781,
            "tau_reio": 0.0544,
            "N_ur": 2.0328,
            "N_ncdm": 1,
            "m_ncdm": 0.06,
            "output": "tCl,pCl,lCl",
            "lensing": "yes",
            "l_max_scalars": lmax,
        }

    # Get available parameters
    try:
        param_names = chain.getParamNames().list()
    except AttributeError:
        param_names = list(chain.keys()) if hasattr(chain, "keys") else []

    # Check if delta bins exist (binned features vs power-law only)
    bins = [param_name_pattern.format(i=i) for i in range(1, nbins + 1)]
    has_delta_bins = bins[0] in param_names

    # Extract cosmological parameters
    A_s_array, n_s_array = extract_powerlaw_params(chain, As_param_name, ns_param_name)
    total_samples = len(A_s_array)

    # Extract all cosmological parameters from chain (marginalizing over all 6 ΛCDM params)
    # Note: MontePython chains store omega_b as 100*omega_b
    # Priority order: try common naming variations for each parameter
    cosmo_param_map = {
        "omega_b": ["omega_b", "omegab", "Omega_b"],
        "omega_cdm": ["omega_cdm", "omegacdm", "Omega_cdm", "omega_c"],
        "h": ["h", "H0"],  # H0 will be converted to h
        "tau_reio": ["tau_reio", "tau", "re_optical_depth"],
    }

    chain_cosmo_params = {}
    for class_name, chain_variants in cosmo_param_map.items():
        found = False
        for variant in chain_variants:
            if variant in param_names:
                values = np.array(chain[variant])

                # Apply necessary conversions
                if class_name == "omega_b":
                    # MontePython stores omega_b as 100*omega_b
                    values = values / 100.0
                elif class_name == "h" and variant == "H0":
                    # Convert H0 to h (H0 = 100h km/s/Mpc)
                    values = values / 100.0

                chain_cosmo_params[class_name] = values
                found = True
                break

        if found:
            print(f"  Found {class_name} in chain (using {variant})")

    # Print summary of what we're marginalizing over
    print(
        f"\nMarginalizing over {len(chain_cosmo_params) + 2} cosmological parameters:"
    )
    print(f"  - A_s, n_s (from chain)")
    for param in chain_cosmo_params.keys():
        print(f"  - {param} (from chain)")
    missing = set(cosmo_param_map.keys()) - set(chain_cosmo_params.keys())
    if missing:
        print(f"  Using baseline values for: {', '.join(missing)}")
    if has_delta_bins:
        print(f"  + {nbins} bin amplitudes (delta_1 to delta_{nbins})")

    # Extract delta values if present
    if has_delta_bins:
        delta_array = np.array(
            [chain[bin] for bin in bins]
        ).T  # shape: (total_samples, nbins)
    else:
        delta_array = None

    # Randomly select n_samples indices
    if n_samples > total_samples:
        print(
            f"Warning: Requested {n_samples} samples but chain has {total_samples}. Using all samples."
        )
        n_samples = total_samples
        sample_indices = np.arange(total_samples)
    else:
        sample_indices = np.random.choice(total_samples, size=n_samples, replace=False)

    print(f"Computing CMB Cls for {n_samples} samples (lmax={lmax})...")

    # Initialize storage for results
    ells = None
    tt_results = []
    te_results = []
    ee_results = []

    # Loop over selected samples
    from tqdm.auto import tqdm

    if residuals:
        base_cosmo = Class()
        base_cosmo.set(baseline_params)
        base_cosmo.compute()
        base_cls = base_cosmo.lensed_cl(lmax)

        base_factor = (
            base_cls["ell"][2:] * (base_cls["ell"][2:] + 1) / (2 * np.pi)
            if include_ell_factor
            else 1.0
        )
        tt_base = base_factor * base_cls["tt"][2:] * 1e12
        te_base = base_factor * base_cls["te"][2:] * 1e12
        ee_base = base_factor * base_cls["ee"][2:] * 1e12

    for idx in tqdm(sample_indices, desc="Computing Cl's with CLASS"):
        # Prepare CLASS parameters for this sample
        class_params = baseline_params.copy()

        # Set output and precision
        # class_params["output"] = "tCl,pCl,lCl"
        # class_params["lensing"] = "yes"
        # class_params["l_max_scalars"] = lmax

        # Set primordial parameters
        class_params["A_s"] = A_s_array[idx]
        class_params["n_s"] = n_s_array[idx]
        class_params["k_pivot"] = k_pivot

        # Override baseline params with chain values if available
        for class_name, values in chain_cosmo_params.items():
            class_params[class_name] = values[idx]

        # Set binned primordial spectrum if delta bins present
        if has_delta_bins:
            class_params["P_k_ini type"] = "binned_Pk"
            class_params["k_min_bin"] = k_start
            class_params["k_max_bin"] = k_end
            class_params["num_bins"] = nbins

            # Add individual bin amplitudes
            delta_vals = delta_array[idx]
            for i, delta in enumerate(delta_vals, 1):
                class_params[f"delta_{i}"] = delta

        # Run CLASS
        try:
            cosmo = Class()
            cosmo.set(class_params)
            cosmo.compute()

            # Get lensed Cls (in μK²)
            cls = cosmo.lensed_cl(lmax)

            # Extract ells (only once)
            if ells is None:
                ells = cls["ell"][2:]

            # Compute ell factor if requested
            factor = ells * (ells + 1) / (2 * np.pi) if include_ell_factor else 1.0
            # Extract spectra and convert to μK² (CLASS returns in K²)
            tt_results.append(factor * cls["tt"][2:] * 1e12)  # K² -> μK²
            te_results.append(factor * cls["te"][2:] * 1e12)
            ee_results.append(factor * cls["ee"][2:] * 1e12)

            # Clean up
            cosmo.struct_cleanup()
            cosmo.empty()

        except Exception as e:
            print(f"Warning: CLASS failed for sample {idx}: {e}")
            # Append NaN arrays to maintain consistent array sizes
            if ells is not None:
                tt_results.append(np.full_like(ells, np.nan, dtype=float))
                te_results.append(np.full_like(ells, np.nan, dtype=float))
                ee_results.append(np.full_like(ells, np.nan, dtype=float))

    # Convert lists to arrays
    tt_array = np.array(tt_results)  # shape: (n_samples, n_ell)
    te_array = np.array(te_results)
    ee_array = np.array(ee_results)

    if residuals:
        tt_array -= tt_base[None, :]
        te_array -= te_base[None, :]
        ee_array -= ee_base[None, :]

    print(f"Successfully computed Cls for {n_samples} samples")
    print(f"Output shapes: ell={ells.shape}, TT/TE/EE={tt_array.shape}")

    return {
        "ell": ells,
        "TT": tt_array,
        "TE": te_array,
        "EE": ee_array,
    }


def compute_overlap_metric(
    chain1, chain2, bin_index: int, param_pattern: str = "delta_{i}"
) -> float:
    """
    Compute overlap between two posterior distributions for a given bin.

    Uses Bhattacharyya coefficient (overlap integral):
    BC = ∫ √(p1(x) * p2(x)) dx

    BC = 1: Perfect overlap
    BC = 0: No overlap

    Args:
        chain1: First MCMC chain
        chain2: Second MCMC chain
        bin_index: Bin index (1-indexed)
        param_pattern: Parameter name pattern

    Returns:
        overlap: Bhattacharyya coefficient (0 to 1)
    """
    param_name = param_pattern.format(i=bin_index)
    samples1 = np.array(chain1[param_name])
    samples2 = np.array(chain2[param_name])

    # Estimate distributions using KDE
    from scipy.stats import gaussian_kde

    kde1 = gaussian_kde(samples1)
    kde2 = gaussian_kde(samples2)

    # Compute overlap on a grid
    x_min = min(samples1.min(), samples2.min())
    x_max = max(samples1.max(), samples2.max())
    x_grid = np.linspace(x_min, x_max, 1000)

    p1 = kde1(x_grid)
    p2 = kde2(x_grid)

    # Bhattacharyya coefficient
    overlap = np.trapezoid(np.sqrt(p1 * p2), x_grid)

    return overlap
