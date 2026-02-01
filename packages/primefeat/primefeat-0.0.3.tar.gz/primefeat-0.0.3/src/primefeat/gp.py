"""
Gaussian Process utilities for primordial feature analysis.

This module provides core GP functionality for modeling smooth variations
in the primordial power spectrum and testing for localized features.

Key capabilities:
1. Covariance matrix computation with proper kernel design
2. Log-marginal likelihood landscape visualization
3. Hyperparameter optimization and validation
4. Bin resolution constraints for finite data

Physical interpretation:
- Length scale $\\ell$: Characteristic scale of smooth variations in log(k) space
- Signal variance $\\sigma^2$: Amplitude of deviations from power-law
- Noise variance $\\sigma_n^2$: Uncorrelated measurement/cosmic variance uncertainty
"""

import numpy as np
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from scipy.linalg import cho_factor, cho_solve
from sklearn.gaussian_process.kernels import (
    RBF,
    ConstantKernel,
    RationalQuadratic,
    ExpSineSquared,
    Kernel,
)
import warnings


# =============================================================================
# KERNEL ABSTRACTION LAYER
# =============================================================================


class KernelType(Enum):
    """
    Supported GP kernel types. Each kernel captures different correlation structures:

    RBF:
        - Infinitely differentiable, very smooth functions
        - Single characteristic length scale
        - Default choice for most applications

    RATIONAL_QUADRATIC:
        - Equivalent to sum of RBF kernels with different length scales
        - Parameter $\\alpha$ weights large vs small scale variations
        - $\\alpha \\to \\infty$ recovers RBF; small $\\alpha$ emphasizes multi-scale structure

    PERIODIC:
        - Exactly repeating functions with period $p$
        - Length scale controls smoothness within each period
        - Use for oscillatory signals (e.g., primordial features)

    LOCALLY_PERIODIC:
        - Product of RBF $\\times$ Periodic
        - Periodic structure with slowly varying envelope
        - RBF length scale controls how far periodicity persists
    """

    RBF = "rbf"
    RATIONAL_QUADRATIC = "rational_quadratic"
    PERIODIC = "periodic"
    LOCALLY_PERIODIC = "locally_periodic"


@dataclass
class KernelConfig:
    """
    Configuration for GP kernel.

    Encapsulates all kernel hyperparameters in a clean structure,
    avoiding proliferation of flat function parameters.

    Attributes:
        kernel_type: Type of kernel (RBF, RQ, Periodic, etc.)
        sigma: Signal standard deviation (amplitude)
        length_scale: Primary length scale parameter
        params: Additional kernel-specific parameters
                - For RQ: {'alpha': float}
                - For Periodic: {'period': float}
                - For LocallyPeriodic: {'period': float, 'length_scale_rbf': float}

    Mathematical Formulas:
    ---------------------

    **RBF (Squared Exponential)**:

    $$k(x, x') = \\sigma^2 \\exp\\left(-\\frac{|x - x'|^2}{2\\ell^2}\\right)$$

    **Rational Quadratic**:

    $$k(x, x') = \\sigma^2 \\left(1 + \\frac{|x - x'|^2}{2\\alpha\\ell^2}\\right)^{-\\alpha}$$

    Equivalent to infinite mixture of RBF kernels with Gamma-distributed
    length scales. $\\alpha$ controls the relative weighting:

    - $\\alpha \\to \\infty$: approaches RBF
    - $\\alpha$ small: more emphasis on long-range correlations

    **Periodic** (ExpSineSquared):

    $$k(x, x') = \\sigma^2 \\exp\\left(-\\frac{2\\sin^2(\\pi|x - x'| / p)}{\\ell^2}\\right)$$

    where $p$ is the period. Exactly periodic with period $p$.
    Length scale $\\ell$ controls smoothness of the periodic function.

    **Locally Periodic** (Product Kernel):

    $$k(x, x') = \\sigma^2 \\, k_{\\text{RBF}}(x, x'; \\ell_{\\text{RBF}}) \\times k_{\\text{Per}}(x, x'; \\ell_{\\text{per}}, p)$$

    Periodic structure that varies slowly in amplitude:

    - $\\ell_{\\text{RBF}}$: controls envelope decay (how far periodicity persists)
    - $\\ell_{\\text{per}}$: controls smoothness of periodic component
    - $p$: period of oscillation

    Examples:
        >>> # RBF kernel
        >>> config = KernelConfig(KernelType.RBF, sigma=0.1, length_scale=0.5)

        >>> # Rational Quadratic kernel
        >>> config = KernelConfig(
        ...     KernelType.RATIONAL_QUADRATIC,
        ...     sigma=0.1,
        ...     length_scale=0.5,
        ...     params={'alpha': 2.0}
        ... )

        >>> # Periodic kernel
        >>> config = KernelConfig(
        ...     KernelType.PERIODIC,
        ...     sigma=0.1,
        ...     length_scale=0.3,
        ...     params={'period': 1.5}
        ... )

        >>> # Locally Periodic = RBF × Periodic
        >>> config = KernelConfig(
        ...     KernelType.LOCALLY_PERIODIC,
        ...     sigma=0.1,
        ...     length_scale=0.3,  # Periodic length scale
        ...     params={'period': 1.5, 'length_scale_rbf': 2.0}
        ... )
    """

    kernel_type: KernelType
    sigma: float
    length_scale: float
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate kernel-specific parameters."""
        # Ensure params is always a dict (handles None if passed explicitly)
        if self.params is None:
            object.__setattr__(self, "params", {})

        # Validate required params for each kernel type
        if self.kernel_type == KernelType.RATIONAL_QUADRATIC:
            if "alpha" not in self.params:
                raise ValueError(
                    "Rational Quadratic kernel requires 'alpha' parameter. "
                    "alpha controls mixture of length scales: alpha -> infinity is RBF, small alpha "
                    "emphasizes multi-scale structure. Typical values: 0.5-10."
                )
            if self.params["alpha"] <= 0:
                raise ValueError(f"alpha must be positive, got {self.params['alpha']}")

        elif self.kernel_type == KernelType.PERIODIC:
            if "period" not in self.params:
                raise ValueError(
                    "Periodic kernel requires 'period' parameter. "
                    "This is the exact repetition period in $\\log(k)$ space."
                )
            if self.params["period"] <= 0:
                raise ValueError(
                    f"period must be positive, got {self.params['period']}"
                )

        elif self.kernel_type == KernelType.LOCALLY_PERIODIC:
            if "period" not in self.params:
                raise ValueError("Locally Periodic kernel requires 'period' parameter.")
            if "length_scale_rbf" not in self.params:
                raise ValueError(
                    "Locally Periodic kernel requires 'length_scale_rbf' parameter. "
                    "This controls the envelope decay of the periodic structure."
                )
            if self.params["period"] <= 0:
                raise ValueError(
                    f"period must be positive, got {self.params['period']}"
                )
            if self.params["length_scale_rbf"] <= 0:
                raise ValueError(
                    f"length_scale_rbf must be positive, got {self.params['length_scale_rbf']}"
                )

        # Validate common parameters
        if self.sigma <= 0:
            raise ValueError(f"sigma must be positive, got {self.sigma}")
        if self.length_scale <= 0:
            raise ValueError(f"length_scale must be positive, got {self.length_scale}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for serialization."""
        result = {
            "kernel_type": self.kernel_type.value,
            "sigma": self.sigma,
            "length_scale": self.length_scale,
        }
        if self.params:
            result.update(self.params)
        return result

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "KernelConfig":
        """Create from flat dictionary."""
        kernel_type = KernelType(d["kernel_type"])
        sigma = d["sigma"]
        length_scale = d["length_scale"]

        # Extract kernel-specific params
        params = {}
        for key in ["alpha", "period", "length_scale_rbf"]:
            if key in d:
                params[key] = d[key]

        return cls(
            kernel_type=kernel_type,
            sigma=sigma,
            length_scale=length_scale,
            params=params,
        )

    def describe(self) -> str:
        """Return human-readable description of kernel."""
        if self.kernel_type == KernelType.RBF:
            return f"RBF(sigma={self.sigma:.4f}, l={self.length_scale:.4f})"
        elif self.kernel_type == KernelType.RATIONAL_QUADRATIC:
            return (
                f"RationalQuadratic(sigma={self.sigma:.4f}, l={self.length_scale:.4f}, "
                f"alpha={self.params['alpha']:.2f})"
            )
        elif self.kernel_type == KernelType.PERIODIC:
            return (
                f"Periodic(sigma={self.sigma:.4f}, l={self.length_scale:.4f}, "
                f"p={self.params['period']:.4f})"
            )
        elif self.kernel_type == KernelType.LOCALLY_PERIODIC:
            return (
                f"LocallyPeriodic(sigma={self.sigma:.4f}, l_per={self.length_scale:.4f}, "
                f"p={self.params['period']:.4f}, l_rbf={self.params['length_scale_rbf']:.4f})"
            )
        return f"Unknown({self.kernel_type})"


def build_kernel(config: KernelConfig) -> Kernel:
    """
    Build sklearn kernel from configuration.

    This is the single source of truth for kernel construction,
    ensuring consistency across the codebase.

    Args:
        config: Kernel configuration

    Returns:
        sklearn Kernel object (without noise component)

    Raises:
        ValueError: If kernel type is unknown or params are invalid

    Examples:
        >>> config = KernelConfig(KernelType.RBF, sigma=0.1, length_scale=0.5)
        >>> kernel = build_kernel(config)
        >>> K = kernel(log_k)  # Evaluate covariance matrix
    """
    if config.kernel_type == KernelType.RBF:
        signal_kernel = RBF(
            length_scale=config.length_scale, length_scale_bounds="fixed"
        )

    elif config.kernel_type == KernelType.RATIONAL_QUADRATIC:
        alpha = config.params["alpha"]
        signal_kernel = RationalQuadratic(
            length_scale=config.length_scale,
            alpha=alpha,
            length_scale_bounds="fixed",
            alpha_bounds="fixed",
        )

    elif config.kernel_type == KernelType.PERIODIC:
        period = config.params["period"]
        # sklearn's ExpSineSquared is the periodic kernel
        signal_kernel = ExpSineSquared(
            length_scale=config.length_scale,
            periodicity=period,
            length_scale_bounds="fixed",
            periodicity_bounds="fixed",
        )

    elif config.kernel_type == KernelType.LOCALLY_PERIODIC:
        # Product of RBF and Periodic
        period = config.params["period"]
        length_scale_rbf = config.params["length_scale_rbf"]

        rbf_kernel = RBF(length_scale=length_scale_rbf, length_scale_bounds="fixed")

        periodic_kernel = ExpSineSquared(
            length_scale=config.length_scale,
            periodicity=period,
            length_scale_bounds="fixed",
            periodicity_bounds="fixed",
        )

        signal_kernel = rbf_kernel * periodic_kernel

    else:
        raise ValueError(f"Unknown kernel type: {config.kernel_type}")

    # Apply signal amplitude: sigma^2 * kernel
    full_kernel = (
        ConstantKernel(config.sigma**2, constant_value_bounds="fixed") * signal_kernel
    )

    return full_kernel


def build_noise_covariance(
    n: int,
    noise_level: Optional[float] = None,
    noise_cov: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Build noise covariance matrix.

    Supports two modes:

    1. Diagonal noise (simple): $\\sigma_n^2 I$
    2. Full posterior covariance (recommended for MCMC): $\\Sigma_{\\text{post}}$

    Args:
        n: Number of data points
        noise_level: Diagonal noise standard deviation (used if noise_cov=None)
        noise_cov: Full N×N posterior covariance matrix

    Returns:
        Noise covariance matrix (n, n)

    Raises:
        ValueError: If neither noise_level nor noise_cov provided, or shape mismatch
    """
    if noise_cov is not None:
        if noise_cov.shape != (n, n):
            raise ValueError(
                f"noise_cov must be shape ({n}, {n}), got {noise_cov.shape}"
            )
        return noise_cov
    elif noise_level is not None:
        return noise_level**2 * np.eye(n)
    else:
        raise ValueError("Either noise_level or noise_cov must be provided")


def _safe_cholesky(
    K: np.ndarray, max_regularization: float = 1e-4, warn: bool = True
) -> Tuple[np.ndarray, bool]:
    """
    Compute Cholesky decomposition with adaptive regularization.

    Args:
        K: Positive semi-definite covariance matrix
        max_regularization: Maximum regularization to add if ill-conditioned
        warn: Whether to issue warnings

    Returns:
        (L, lower): Cholesky factor and lower flag for cho_solve

    Note:
        Returns tuple compatible with scipy's cho_factor output.
    """
    try:
        L, lower = cho_factor(K, lower=True)
        return L, lower
    except np.linalg.LinAlgError:
        # Check condition number to diagnose issue
        try:
            cond = np.linalg.cond(K)
        except np.linalg.LinAlgError:
            cond = np.inf

        # Adaptive regularization based on condition number
        if cond > 1e10:
            reg = max_regularization
        elif cond > 1e6:
            reg = 1e-6
        else:
            reg = 1e-8

        if warn:
            warnings.warn(
                f"Cholesky factorization failed (condition number: {cond:.2e}). "
                f"Adding regularization {reg:.2e} to diagonal."
            )

        K_reg = K + reg * np.eye(len(K))
        L, lower = cho_factor(K_reg, lower=True)
        return L, lower


# =============================================================================
# KERNEL VISUALIZATION AND COMPARISON UTILITIES
# =============================================================================


def compute_kernel_matrix(
    log_k: np.ndarray,
    kernel_config: KernelConfig,
) -> np.ndarray:
    """
    Compute kernel covariance matrix (signal only, no noise).

    Useful for visualizing kernel structure and comparing kernels.

    Args:
        log_k: $\\log(k)$ values, shape (n,) or (n, 1)
        kernel_config: Kernel configuration

    Returns:
        K_signal: Signal covariance matrix (n, n)
    """
    log_k = np.asarray(log_k).reshape(-1, 1)
    kernel = build_kernel(kernel_config)
    return kernel(log_k)


def compare_kernels(
    log_k: np.ndarray,
    configs: Dict[str, KernelConfig],
) -> Dict[str, np.ndarray]:
    """
    Compute kernel matrices for multiple configurations.

    Useful for comparing how different kernels represent correlation structure.

    Args:
        log_k: $\\log(k)$ values, shape (n,) or (n, 1)
        configs: Dictionary mapping names to KernelConfig objects

    Returns:
        Dictionary mapping names to kernel matrices

    Examples:
        >>> log_k = np.linspace(-7, -1.5, 20)
        >>> configs = {
        ...     'RBF': KernelConfig(KernelType.RBF, 0.1, 0.5),
        ...     'RQ_low_alpha': KernelConfig(KernelType.RATIONAL_QUADRATIC, 0.1, 0.5, {'alpha': 0.5}),
        ...     'RQ_high_alpha': KernelConfig(KernelType.RATIONAL_QUADRATIC, 0.1, 0.5, {'alpha': 10.0}),
        ... }
        >>> matrices = compare_kernels(log_k, configs)
    """
    log_k = np.asarray(log_k).reshape(-1, 1)
    return {name: build_kernel(config)(log_k) for name, config in configs.items()}


def compute_bin_resolution(nbins: int, k_start: float, k_end: float) -> Dict[str, Any]:
    """
    Compute resolution limits imposed by finite binning.

    With finite bins over a finite $k$-range, we cannot resolve arbitrarily
    small correlation lengths. This function computes the minimum resolvable
    length scale and warns if requested parameters are below this limit.

    Args:
        nbins: Number of bins
        k_start: Start of $k$-range in Mpc^-1
        k_end: End of $k$-range in Mpc^-1

    Returns:
        Dictionary with:
            - delta_log_k: Bin spacing in $\\log(k)$ space
            - log_k_range: Total range in $\\log(k)$ space
            - min_resolvable_length: Minimum length scale we can constrain (~2 bins)
            - max_sensible_length: Maximum useful length scale (~half range)

    Examples:
        >>> res = compute_bin_resolution(20, 0.001, 0.23)
        >>> print(f"Min length scale: {res['min_resolvable_length']:.3f}")
        >>> print(f"Max length scale: {res['max_sensible_length']:.3f}")
    """
    log_k_range = np.log(k_end) - np.log(k_start)
    delta_log_k = log_k_range / nbins

    # Nyquist-like limit: need at least ~2 bins to resolve a feature
    min_resolvable_length = 2 * delta_log_k

    # Features spanning > half the range are not well-constrained
    max_sensible_length = log_k_range / 2

    return {
        "delta_log_k": delta_log_k,
        "log_k_range": log_k_range,
        "min_resolvable_length": min_resolvable_length,
        "max_sensible_length": max_sensible_length,
        "recommended_length_range": (min_resolvable_length, max_sensible_length),
    }


def validate_hyperparameters(
    sigma: float,
    length_scale: float,
    nbins: int,
    k_start: float,
    k_end: float,
    warn: bool = True,
) -> bool:
    """
    Validate GP hyperparameters against bin resolution limits.

    Args:
        sigma: Signal standard deviation
        length_scale: RBF kernel length scale in $\\log(k)$ space
        nbins: Number of bins
        k_start: Start of $k$-range in Mpc^-1
        k_end: End of $k$-range in Mpc^-1
        warn: Whether to print warnings

    Returns:
        is_valid: True if parameters are within reasonable bounds
    """
    res = compute_bin_resolution(nbins, k_start, k_end)

    is_valid = True

    # Check length scale
    if length_scale < res["min_resolvable_length"]:
        if warn:
            warnings.warn(
                f"Length scale l={length_scale:.3f} is below minimum resolvable "
                f"scale {res['min_resolvable_length']:.3f}. "
                f"With {nbins} bins, features narrower than ~2 bins cannot be distinguished "
                f"from noise. Consider using l >= {res['min_resolvable_length']:.3f}."
            )
        is_valid = False

    if length_scale > res["max_sensible_length"]:
        if warn:
            warnings.warn(
                f"Length scale l={length_scale:.3f} is larger than half the $k$-range "
                f"({res['max_sensible_length']:.3f}). Such broad features are poorly "
                f"constrained by the data. Consider using l <= {res['max_sensible_length']:.3f}."
            )
        is_valid = False

    # Check sigma
    if sigma < 0:
        raise ValueError(f"Signal variance sigma must be non-negative, got {sigma}")

    if sigma > 1.0:
        if warn:
            warnings.warn(
                f"Signal amplitude sigma={sigma:.3f} is very large (>1.0). "
                f"This implies order-unity deviations from the power-law, "
                f"which may not be physically motivated."
            )

    return is_valid


def build_gp_covariance(
    log_k: np.ndarray,
    length_scale: Optional[float] = None,
    sigma: Optional[float] = None,
    noise_level: Optional[float] = 0.01,
    noise_cov: Optional[np.ndarray] = None,
    return_cholesky: bool = False,
    kernel_config: Optional[KernelConfig] = None,
) -> np.ndarray:
    """
    Build GP covariance matrix for given kernel configuration.

    $$K = K_{\\text{signal}}(\\text{config}) + \\Sigma_{\\text{noise}}$$

    Supports multiple kernel types through KernelConfig:

    - RBF (Squared Exponential): default, infinitely smooth
    - Rational Quadratic: multi-scale structure
    - Periodic: exactly repeating patterns
    - Locally Periodic: periodic with varying amplitude

    Args:
        log_k: $\\log(k)$ values, shape (n, 1) or (n,)
        noise_level: Diagonal noise standard deviation (used if noise_cov=None)
        noise_cov: Full N×N posterior covariance matrix (RECOMMENDED for MCMC bins).
                   If provided, this accounts for bin-bin correlations.
                   Extract from MCMC: np.cov(delta_samples.T)
        return_cholesky: If True, return Cholesky factor instead of K
        kernel_config: KernelConfig object specifying kernel type and parameters (NEW)
        length_scale: (Backward compatibility) RBF kernel length scale in $\\log(k)$ space
        sigma: (Backward compatibility) Signal standard deviation (GP amplitude)

    Returns:
        K: Covariance matrix (n, n)
        or L: Lower Cholesky factor if return_cholesky=True

    Examples:
        Rational Quadratic kernel:

        >>> config = KernelConfig(
        ...     KernelType.RATIONAL_QUADRATIC,
        ...     sigma=0.1,
        ...     length_scale=0.5,
        ...     params={'alpha': 2.0}
        ... )
        >>> K = build_gp_covariance(log_k, kernel_config=config, noise_level=0.01)

        Periodic kernel:

        >>> config = KernelConfig(
        ...     KernelType.PERIODIC,
        ...     sigma=0.1,
        ...     length_scale=0.3,
        ...     params={'period': 1.5}
        ... )
        >>> K = build_gp_covariance(log_k, kernel_config=config, noise_level=0.01)

        Backward compatible RBF (old API):

        >>> K = build_gp_covariance(log_k, length_scale=0.5, sigma=0.1, noise_level=0.01)

        Full posterior covariance (MCMC bins):

        >>> delta_samples = np.array([chain[f'delta_{i}'] for i in range(1, 21)]).T
        >>> posterior_cov = np.cov(delta_samples.T)
        >>> K = build_gp_covariance(log_k, kernel_config=config, noise_cov=posterior_cov)
    """
    log_k = np.asarray(log_k).reshape(-1, 1)
    n = len(log_k)

    # === BACKWARD COMPATIBILITY ===
    # If old API used (length_scale, sigma), create RBF kernel config
    if kernel_config is None:
        if length_scale is None or sigma is None:
            raise ValueError(
                "Either provide kernel_config, or both length_scale and sigma "
                "for backward compatibility with RBF kernel"
            )
        kernel_config = KernelConfig(
            kernel_type=KernelType.RBF, sigma=sigma, length_scale=length_scale
        )

    # === BUILD SIGNAL KERNEL ===
    signal_kernel = build_kernel(kernel_config)
    K_signal = signal_kernel(log_k)

    # === BUILD NOISE COVARIANCE ===
    K_noise = build_noise_covariance(n, noise_level, noise_cov)

    # === TOTAL COVARIANCE ===
    K = K_signal + K_noise

    if return_cholesky:
        L, lower = _safe_cholesky(K)
        return L

    return K


def compute_log_marginal_likelihood(
    delta_values: np.ndarray,
    log_k: np.ndarray,
    length_scale: Optional[float] = None,
    sigma: Optional[float] = None,
    noise_level: Optional[float] = 0.01,
    noise_cov: Optional[np.ndarray] = None,
    kernel_config: Optional[KernelConfig] = None,
) -> float:
    """
    Compute log-marginal likelihood for given GP hyperparameters.

    $$\\log p(\\delta | \\theta) = -\\frac{1}{2} \\delta^T K^{-1} \\delta - \\frac{1}{2} \\log|K| - \\frac{n}{2} \\log(2\\pi)$$

    where $K = K_{\\text{signal}}(\\theta) + \\Sigma_{\\text{noise}}$

    This is the probability of observing the data $\\delta$ under the GP model
    with hyperparameters $\\theta$. Higher values indicate better fit.

    Components:

    - Data fit term: $-\\frac{1}{2} \\delta^T K^{-1} \\delta$ (reward fitting the data)
    - Complexity penalty: $-\\frac{1}{2} \\log|K|$ (penalize overly flexible models)
    - Normalization: $-\\frac{n}{2} \\log(2\\pi)$

    Args:
        delta_values: Observed $\\delta(k)$ values values, shape (n,)
        log_k: $\\log(k)$ values, shape (n, 1) or (n,)
        noise_level: Diagonal noise standard deviation (used if noise_cov=None)
        noise_cov: Full N×N posterior covariance matrix (RECOMMENDED for MCMC bins)
        kernel_config: KernelConfig object specifying kernel (NEW - preferred)
        length_scale: (Backward compatibility) RBF kernel length scale
        sigma: (Backward compatibility) Signal standard deviation

    Returns:
        lml: Log-marginal likelihood

    Examples:
        With kernel configuration (recommended):

        >>> config = KernelConfig(
        ...     KernelType.PERIODIC,
        ...     sigma=0.1,
        ...     length_scale=0.3,
        ...     params={'period': 1.5}
        ... )
        >>> lml = compute_log_marginal_likelihood(delta, log_k, kernel_config=config)

        Backward compatible RBF (old API):

        >>> lml = compute_log_marginal_likelihood(delta, log_k, 0.5, 0.1)
    """
    log_k = np.asarray(log_k).reshape(-1, 1)
    delta_values = np.asarray(delta_values).ravel()
    n = len(delta_values)

    # Build covariance matrix (handles backward compatibility internally)
    K = build_gp_covariance(
        log_k,
        length_scale=length_scale,
        sigma=sigma,
        noise_level=noise_level,
        noise_cov=noise_cov,
        kernel_config=kernel_config,
    )

    # Cholesky factorization for numerical stability
    try:
        L, lower = cho_factor(K, lower=True)
    except np.linalg.LinAlgError:
        # Singular matrix - return very low likelihood
        return -np.inf

    # log|K| = log|LL^T| = 2 log|L| = 2 * sum(log(diag(L)))
    log_det_K = 2 * np.sum(np.log(np.diag(L)))

    # Compute delta^T K^{-1} delta using Cholesky solve
    K_inv_delta = cho_solve((L, lower), delta_values)
    quad_form = delta_values @ K_inv_delta

    # Log-marginal likelihood
    lml = -0.5 * quad_form - 0.5 * log_det_K - 0.5 * n * np.log(2 * np.pi)

    return lml


def _compute_lml_from_K(delta_values: np.ndarray, K: np.ndarray, n: int) -> float:
    """
    Compute log-marginal likelihood from a pre-built covariance matrix K.

    This is a helper function for compute_lml_landscape() when using
    full posterior covariance instead of diagonal noise.

    Args:
        delta_values: Observed $\\delta(k)$ values values, shape (n,)
        K: Pre-built covariance matrix, shape (n, n)
        n: Number of data points

    Returns:
        lml: Log-marginal likelihood
    """
    try:
        L, lower = cho_factor(K, lower=True)
    except np.linalg.LinAlgError:
        return -np.inf

    # Compute log|K| = 2 * sum(log(diag(L)))
    log_det_K = 2 * np.sum(np.log(np.diag(L)))

    # Compute delta^T K^{-1} delta
    K_inv_delta = cho_solve((L, lower), delta_values)
    quad_form = delta_values @ K_inv_delta

    # Log-marginal likelihood
    const_term = -0.5 * n * np.log(2 * np.pi)
    lml = -0.5 * quad_form - 0.5 * log_det_K + const_term

    return lml


def estimate_sigma_range_from_data(
    delta_values: np.ndarray,
    noise_level: float,
    lower_bound_factor: float = 0.1,
    upper_bound_factor: float = 3.0,
    min_sigma: float = 1e-4,
) -> Tuple[float, float]:
    """
    Estimate appropriate sigma range from empirical data characteristics.

    Strategy:

    1. Lower bound: $\\max(\\text{noise\\_level} \\times \\text{lower\\_bound\\_factor}, \\text{min\\_sigma})$
       - Should be above noise floor to ensure signal is detectable
       - Allows exploring "weak signal" regime

    2. Upper bound: $\\text{empirical\\_std} \\times \\text{upper\\_bound\\_factor}$
       - Covers "strong signal" regime where deviations are large
       - Factor of 3 ensures we explore well beyond typical variations

    This ensures the search space adapts to data scale while maintaining
    physical interpretability ($\\sigma \\ll \\text{noise}$ is undetectable, $\\sigma \\gg \\sigma_\\mathrm{data}$
    implies implausibly large deviations).

    Args:
        delta_values: Observed $\\delta(k)$ values values, shape (n,)
        noise_level: Fixed noise standard deviation sigma_n
        lower_bound_factor: Multiplier for noise level to set lower bound
        upper_bound_factor: Multiplier for empirical std to set upper bound
        min_sigma: Absolute minimum sigma to consider (prevents degeneracy)

    Returns:
        (sigma_min, sigma_max): Recommended sigma range

    Examples:
        >>> delta = np.random.randn(20) * 0.05 + 0.02  # Small signal
        >>> sigma_range = estimate_sigma_range_from_data(delta, noise_level=0.01)
        >>> print(f"Auto sigma range: [{sigma_range[0]:.4f}, {sigma_range[1]:.4f}]")
    """
    delta_values = np.asarray(delta_values).ravel()

    # Empirical statistics
    empirical_std = np.std(delta_values, ddof=1)

    # Handle edge case: all zeros or constant data
    if empirical_std < min_sigma:
        warnings.warn(
            f"Data has very small variance (std={empirical_std:.2e}). "
            f"Using fallback sigma range based on noise level."
        )
        empirical_std = noise_level * 2

    # Lower bound: slightly above noise level
    # Rationale: sigma << noise_level means signal is undetectable
    sigma_min = max(noise_level * lower_bound_factor, min_sigma)

    # Upper bound: multiple of empirical std
    # Rationale: sigma >> empirical_std implies stronger signal than observed
    # Factor of 3 allows exploration of "strong signal" hypothesis
    sigma_max = empirical_std * upper_bound_factor

    # Sanity check: upper should be meaningfully larger than lower
    if sigma_max < 2 * sigma_min:
        sigma_max = sigma_min * 10
        warnings.warn(
            f"Auto-determined sigma range is narrow. Expanding to [{sigma_min:.4f}, {sigma_max:.4f}]"
        )

    return (float(sigma_min), float(sigma_max))


def estimate_noise_level_from_chain(
    chain: Dict[str, np.ndarray],
    nbins: int = 20,
    param_pattern: str = "delta_{i}",
) -> float:
    """
    Estimate noise level directly from MCMC chain posterior uncertainties.

    This is the PREFERRED method when you have access to the full MCMC chain,
    as it uses the actual posterior standard deviations rather than empirical
    variance of the posterior mean.

    Args:
        chain: MCMC chain object (dict-like with delta_i parameters)
        nbins: Number of bins
        param_pattern: Parameter name pattern (use {i} for bin index)

    Returns:
        noise_level: Mean posterior standard deviation across bins

    Note:
        Examples:

            >>> # With full chain
            >>> noise = estimate_noise_level_from_chain(chain, nbins=20)
            >>> landscape = compute_lml_landscape(delta_mean, log_k, noise_level=noise, ...)
    """
    stds = []
    for i in range(1, nbins + 1):
        param_name = param_pattern.format(i=i)
        if param_name in chain:
            stds.append(np.std(chain[param_name], ddof=1))

    if len(stds) == 0:
        raise ValueError(f"No parameters found matching pattern '{param_pattern}'")

    # Return mean of posterior standard deviations
    return float(np.mean(stds))


def estimate_noise_level_from_data(
    delta_values: np.ndarray,
    fraction_of_std: float = 0.5,
    min_noise: float = 1e-3,
) -> float:
    """
    Estimate appropriate noise level from data characteristics.

    For a single realization (posterior mean), we estimate the noise level
    as a fraction of the empirical standard deviation. This represents the
    typical uncertainty/scatter in the data.

    This is a FALLBACK method. If you have access to the full MCMC chain,
    prefer using estimate_noise_level_from_chain() instead.

    Args:
        delta_values: Observed $\\delta(k)$ values values, shape (n,)
        fraction_of_std: What fraction of std to use (default: 0.5 = half the variation)
        min_noise: Minimum noise level to avoid numerical issues

    Returns:
        noise_level: Estimated noise standard deviation

    Examples:
        >>> delta = np.random.randn(20) * 0.05
        >>> noise = estimate_noise_level_from_data(delta)
        >>> print(f"Estimated noise: {noise:.4f}")

    Note:
        If you have access to the full MCMC chain, prefer using:

            >>> from primefeat.gp import estimate_noise_level_from_chain
            >>> noise_level = estimate_noise_level_from_chain(chain, nbins=20)

        This gives a more accurate estimate of bin-wise uncertainties.
    """
    delta_values = np.asarray(delta_values).ravel()
    empirical_std = np.std(delta_values, ddof=1)

    # Estimate noise as fraction of empirical variation
    return float(max(empirical_std * fraction_of_std, min_noise))


def estimate_length_scale_from_autocorrelation(
    delta_values: np.ndarray,
    log_k: np.ndarray,
    min_correlation: float = 0.1,
    fallback_quantile: float = 0.3,
) -> float:
    """
    Estimate correlation length scale from empirical autocorrelation structure.

    This function is simpler than significance.estimate_correlation_length() because
    we're working with a single realization (delta_values) rather than posterior samples.

    Strategy:

    1. Compute pairwise distances in $\\log(k)$ space
    2. Compute delta-delta correlations via $(\\delta_i - \\text{mean})(\\delta_j - \\text{mean}) / \\text{var}$
    3. Fit exponential decay: $\\text{corr}(d) \\sim \\exp(-d / \\ell)$
    4. Return characteristic length scale $\\ell$

    If insufficient correlation structure is present, falls back to a quantile
    of the log_k range (e.g., 30% of range).

    Args:
        delta_values: Observed $\\delta(k)$ values values, shape (n,)
        log_k: $\\log(k)$ values, shape (n, 1) or (n,)
        min_correlation: Minimum correlation threshold for fitting
        fallback_quantile: Fraction of log_k range to use if fit fails

    Returns:
        length_scale: Estimated correlation length in $\\log(k)$ units

    Examples:
        >>> log_k = np.linspace(-7, -1.5, 20)
        >>> delta = np.sin(log_k) * 0.1 + np.random.randn(20) * 0.02
        >>> ell = estimate_length_scale_from_autocorrelation(delta, log_k)
        >>> print(f"Estimated length scale: {ell:.3f}")
    """
    delta_values = np.asarray(delta_values).ravel()
    log_k = np.asarray(log_k).ravel()
    n = len(delta_values)

    if n < 3:
        # Cannot estimate correlation with < 3 points
        log_k_range = np.ptp(log_k) if n > 1 else 1.0
        return fallback_quantile * log_k_range

    # Center the data
    delta_centered = delta_values - np.mean(delta_values)
    variance = np.var(delta_values, ddof=1)

    if variance < 1e-10:
        # No variance → no correlation structure
        log_k_range = np.ptp(log_k)
        return fallback_quantile * log_k_range

    # Compute pairwise distances and correlations
    distances = []
    correlations = []

    for i in range(n):
        for j in range(i + 1, n):
            dist = abs(log_k[j] - log_k[i])
            # Empirical correlation: <(delta_i - mean)(delta_j - mean)> / var
            corr = (delta_centered[i] * delta_centered[j]) / variance

            if corr > min_correlation:
                distances.append(dist)
                correlations.append(corr)

    if len(distances) < 3:
        # Insufficient correlation structure for fitting
        log_k_range = np.ptp(log_k)
        fallback_length = fallback_quantile * log_k_range
        return fallback_length

    distances = np.array(distances)
    correlations = np.array(correlations)

    # Fit exponential decay: corr = exp(-dist / l)
    # Taking log: log(corr) = -dist / l
    # So: l = -mean(dist) / mean(log(corr))

    log_corr = np.log(correlations)
    length_scale = -np.mean(distances) / np.mean(log_corr)

    # Sanity check: length scale should be positive and reasonable
    log_k_range = np.ptp(log_k)
    if length_scale <= 0 or length_scale > 2 * log_k_range:
        # Fit failed or unreasonable → use fallback
        length_scale = fallback_quantile * log_k_range

    return float(length_scale)


def validate_hyperparameter_ranges(
    sigma_range: Tuple[float, float],
    length_scale_range: Tuple[float, float],
    noise_level: Optional[float],
    empirical_std: float,
    resolution_info: Optional[Dict] = None,
    warn: bool = True,
) -> bool:
    """
    Validate user-provided hyperparameter ranges for reasonableness.

    This function warns users if their specified ranges are likely to produce
    poor results due to:

    - Sigma too close to noise level (undetectable signal)
    - Sigma $\\gg$ empirical variation (implausibly large deviations)
    - Length scale below resolution limit (aliasing)
    - Length scale $>$ half the domain (poorly constrained)

    Args:
        sigma_range: (min, max) for signal standard deviation
        length_scale_range: (min, max) for length scale
        noise_level: Fixed noise standard deviation
        empirical_std: Standard deviation of $\\delta(k)$ values values
        resolution_info: Output from compute_bin_resolution() (optional)
        warn: Whether to print warnings

    Returns:
        is_valid: True if ranges pass all checks
    """
    is_valid = True

    sigma_min, sigma_max = sigma_range
    ell_min, ell_max = length_scale_range

    # Check sigma range (only if noise_level is provided)
    if noise_level is not None and sigma_max < noise_level:
        if warn:
            warnings.warn(
                f"Sigma upper bound ({sigma_max:.4f}) is below noise level ({noise_level:.4f}). "
                f"Signal will be completely dominated by noise. Consider increasing sigma_range."
            )
        is_valid = False

    if sigma_min > empirical_std * 2:
        if warn:
            warnings.warn(
                f"Sigma lower bound ({sigma_min:.4f}) is much larger than empirical std ({empirical_std:.4f}). "
                f"You may be searching in an implausibly large signal regime. Consider lowering sigma_range."
            )
        is_valid = False

    if sigma_max > empirical_std * 10:
        if warn:
            warnings.warn(
                f"Sigma upper bound ({sigma_max:.4f}) is >> empirical std ({empirical_std:.4f}). "
                f"This implies order-unity deviations from power-law, which may not be physically motivated."
            )
        is_valid = False

    # Check length scale range against resolution limits
    if resolution_info is not None:
        min_resolvable = resolution_info["min_resolvable_length"]
        max_sensible = resolution_info["max_sensible_length"]

        if ell_min < min_resolvable:
            if warn:
                warnings.warn(
                    f"Length scale lower bound ({ell_min:.3f}) is below minimum resolvable "
                    f"scale ({min_resolvable:.3f}). Features this narrow cannot be distinguished "
                    f"from noise with current binning. Consider using l_min >= {min_resolvable:.3f}."
                )
            is_valid = False

        if ell_max > max_sensible:
            if warn:
                warnings.warn(
                    f"Length scale upper bound ({ell_max:.3f}) exceeds half the domain "
                    f"({max_sensible:.3f}). Such broad features are poorly constrained. "
                    f"Consider using l_max <= {max_sensible:.3f}."
                )
            is_valid = False

    return is_valid


def compute_lml_landscape(
    delta_values: np.ndarray,
    log_k: np.ndarray,
    sigma_range: Optional[Tuple[float, float]] = None,
    length_scale_range: Optional[Tuple[float, float]] = None,
    n_sigma: int = 50,
    n_length: int = 50,
    noise_level: Optional[float] = None,
    posterior_cov: Optional[np.ndarray] = None,
    nbins: Optional[int] = None,
    k_start: Optional[float] = None,
    k_end: Optional[float] = None,
    auto_sigma_factor: float = 3.0,
    auto_length_fallback: float = 0.3,
    validate_ranges: bool = True,
    kernel_type: KernelType = KernelType.RBF,
    kernel_params: Optional[Dict[str, Any]] = None,
) -> Dict:
    """
    Compute log-marginal likelihood landscape in $(\\sigma, \\ell)$ hyperparameter space.

    This visualizes how well different GP models explain the data, allowing us to:

    1. Test whether signal variance $\\sigma$ is significantly non-zero (evidence for features)
    2. Infer characteristic length scale $\\ell$ of features (sharp vs smooth)
    3. Assess parameter uncertainty and degeneracies (ridge structures)
    4. Compute Bayes factors for model comparison (signal vs noise)

    Supports multiple kernel types:
    - RBF (default): Infinitely smooth, single length scale
    - RATIONAL_QUADRATIC: Multi-scale structure (set kernel_params={'alpha': value})
    - PERIODIC: Exactly repeating patterns (set kernel_params={'period': value})
    - LOCALLY_PERIODIC: Periodic with decay (set kernel_params={'period': p, 'length_scale_rbf': l})

    Intelligent automatic hyperparameter range selection!
    - If sigma_range=None, estimates appropriate bounds from empirical data variance
    - If length_scale_range=None, combines bin resolution + empirical autocorrelation
    - Validates user-provided ranges and warns about unreasonable choices
    - Transparently reports what ranges were selected and why

    Mathematical Framework:
    ----------------------
    The log-marginal likelihood is:

    $$\\log p(\\delta | \\theta) = -\\frac{1}{2} \\delta^T K^{-1} \\delta - \\frac{1}{2} \\log|K| - \\frac{n}{2} \\log(2\\pi)$$

    where $K(\\theta) = K_{\\text{signal}}(\\sigma, \\ell, \\text{kernel\\_params}) + \\Sigma_{\\text{noise}}$

    Interpretation of Landscape Features:
    -------------------------------------

    - **Peak at** $\\sigma \\approx 0$: Data consistent with noise (null hypothesis)
    - **Peak at** $\\sigma > 0$: Evidence for signal beyond noise
    - **Small** $\\ell$ **at maximum**: Sharp, localized features (e.g., resonances)
    - **Large** $\\ell$ **at maximum**: Smooth, broad features (e.g., running)
    - **Narrow peak**: Well-constrained hyperparameters
    - **Ridge structure**: $\\sigma$-$\\ell$ degeneracy (multiple models fit equally well)

    Bayes Factor Interpretation:
    ----------------------------
    $\\text{BF} = \\exp(\\text{LML}_{\\text{signal}} - \\text{LML}_{\\text{noise}})$ compares signal vs noise models:

    - BF > 10: Strong evidence for features
    - BF > 3: Moderate evidence
    - BF < 3: Weak/no evidence

    Bin Resolution Constraints:
    ---------------------------
    With nbins bins over finite $k$-range, we cannot resolve arbitrarily small $\\ell$.

    - Minimum resolvable: $\\ell_{\\text{min}} \\approx 2 \\Delta\\log(k) \\approx 2 \\times \\log{k_\\mathrm{range}} / \\text{nbins}$
    - Maximum sensible: $\\ell_{\\text{max}} \\approx \\log{k_\\mathrm{range}} / 2$

    Automatic Range Selection Strategy:
    ------------------------------------
    **Sigma range** (if None):

    - Lower: $\\max(\\text{noise\\_level} \\times 0.1, 10^{-4})$ - slightly above noise floor
    - Upper: $\\text{empirical\\_std} \\times \\text{auto\\_sigma\\_factor}$ - covers strong signal regime
    - Adapts to data scale while maintaining physical interpretability

    **Length scale range** (if None):

    - Lower: $0.8 \\times \\ell_{\\text{min}}$ (from bin resolution)
    - Upper: $1.2 \\times \\ell_{\\text{max}}$ (from bin resolution)
    - Optionally refined by empirical autocorrelation if available

    Args:
        delta_values: Observed $\\delta(k)$ values values (single sample or posterior mean), shape (n,)
        log_k: $\\log(k)$ values, shape (n, 1) or (n,)
        sigma_range: (min, max) for signal std (None = auto-determine from data)
        length_scale_range: (min, max) for length scale (None = auto from resolution)
        n_sigma: Number of sigma grid points
        n_length: Number of length scale grid points
        noise_level: Fixed diagonal noise $\\sigma_n^2$ (used if posterior_cov=None).
                     DEPRECATED: Use posterior_cov instead for proper statistics
        posterior_cov: Full posterior covariance matrix (RECOMMENDED, nbins x nbins).
                      If provided, uses $\\Sigma_{\\text{post}}$ instead of diagonal noise.
                      Extract from MCMC: np.cov(delta_samples.T)
        nbins: Number of bins for automatic length scale range (recommended)
        k_start: Start of $k$-range in Mpc^-1 for automatic length scale range
        k_end: End of $k$-range in Mpc^-1 for automatic length scale range
        auto_sigma_factor: Multiplier for empirical_std when auto-determining sigma_max
        auto_length_fallback: Fraction of log_k range for length scale estimation fallback
        validate_ranges: If True, validate user-provided ranges and warn if unreasonable
        kernel_type: Type of kernel to use (default: KernelType.RBF)
        kernel_params: Fixed kernel-specific parameters (not explored in landscape).
                       RQ: {'alpha': float} - mixture parameter.
                       Periodic: {'period': float} - oscillation period.
                       LocallyPeriodic: {'period': float, 'length_scale_rbf': float}

    Returns:
        Dictionary containing:
            sigma_grid: 1D array of sigma values
            length_scale_grid: 1D array of l values
            lml_grid: 2D array of log-marginal likelihoods (n_sigma, n_length)
            optimal_sigma: ML estimate of sigma
            optimal_length_scale: ML estimate of l
            max_lml: Maximum log-marginal likelihood
            null_lml: LML at sigma approx 0 (null hypothesis)
            bayes_factor: exp(max_lml - null_lml)
            resolution_info: Bin resolution diagnostics
            auto_selected_ranges: Dict with 'sigma_range', 'length_scale_range', 'method'

    Examples:
        Automatic range selection:

        >>> from primefeat.compute import get_bin_centers
        >>> bin_centers = get_bin_centers(0.001, 0.23, 20)
        >>> log_k = np.log(bin_centers).reshape(-1, 1)
        >>> delta_mean = np.array([chain[f'delta_{i}'].mean() for i in range(1, 21)])
        >>> # Let function auto-determine ranges
        >>> landscape = compute_lml_landscape(
        ...     delta_mean, log_k,
        ...     nbins=20, k_start=0.001, k_end=0.23
        ... )
        >>> print(f"Auto-selected sigma: {landscape['auto_selected_ranges']['sigma_range']}")
        >>> if landscape['bayes_factor'] > 10:
        ...     print(f"Strong evidence! l = {landscape['optimal_length_scale']:.3f}")

        Manual ranges with validation:

        >>> # Provide your own ranges - function will validate them
        >>> landscape = compute_lml_landscape(
        ...     delta_mean, log_k,
        ...     sigma_range=(0.001, 0.2),
        ...     length_scale_range=(0.1, 1.5),
        ...     nbins=20, k_start=0.001, k_end=0.23
        ... )
    """
    log_k = np.asarray(log_k).reshape(-1, 1)
    delta_values = np.asarray(delta_values).ravel()
    n = len(delta_values)

    # Compute empirical statistics for range estimation
    empirical_std = np.std(delta_values, ddof=1)
    empirical_mean = np.abs(np.mean(delta_values))

    # Determine noise model: full covariance or diagonal
    use_full_cov = posterior_cov is not None
    if use_full_cov:
        noise_method = "full posterior covariance (RECOMMENDED)"
        # For reporting, show typical scale
        noise_scale = np.sqrt(np.mean(np.diag(posterior_cov)))
    else:
        # Auto-estimate noise level if not provided
        if noise_level is None:
            noise_level = estimate_noise_level_from_data(
                delta_values, fraction_of_std=0.5
            )
            noise_method = "diagonal noise (auto, 0.5 × empirical_std)"
        else:
            noise_method = "diagonal noise (user-provided)"
        noise_scale = noise_level

    print("=" * 70)
    print("HYPERPARAMETER RANGE SELECTION")
    print("=" * 70)
    print(f"Data characteristics:")
    print(f"  N bins: {n}")
    print(f"  Empirical mean: {empirical_mean:.4f}")
    print(f"  Empirical std: {empirical_std:.4f}")
    print(f"  Noise model: {noise_method}")
    if use_full_cov:
        print(f"  Noise scale (√diag): {noise_scale:.4f}")
    else:
        print(f"  Noise level (diagonal): {noise_scale:.4f}")

    # Track what was auto-selected vs user-provided
    auto_selected_ranges = {
        "sigma_range": None,
        "length_scale_range": None,
        "sigma_method": "user-provided",
        "length_method": "user-provided",
    }

    # === SIGMA RANGE SELECTION ===
    if sigma_range is None:
        # Auto-determine from data
        sigma_range = estimate_sigma_range_from_data(
            delta_values, noise_level, upper_bound_factor=auto_sigma_factor
        )
        auto_selected_ranges["sigma_range"] = sigma_range
        auto_selected_ranges["sigma_method"] = "auto (empirical variance)"

        print(
            f"\nAuto-selected sigma range: [{sigma_range[0]:.4f}, {sigma_range[1]:.4f}]"
        )
        print(f"  Lower bound: max(noise × 0.1, 1e-4) = {sigma_range[0]:.4f}")
        print(
            f"  Upper bound: empirical_std × {auto_sigma_factor:.1f} = {sigma_range[1]:.4f}"
        )
        print(
            f"  Rationale: Lower explores weak signal, upper explores {auto_sigma_factor}σ regime"
        )
    else:
        # User-provided - validate it
        auto_selected_ranges["sigma_range"] = sigma_range
        print(
            f"\nUsing user-provided sigma range: [{sigma_range[0]:.4f}, {sigma_range[1]:.4f}]"
        )

    # === LENGTH SCALE RANGE SELECTION ===
    # First, compute bin resolution if parameters provided
    resolution_info = None
    if nbins is not None and k_start is not None and k_end is not None:
        resolution_info = compute_bin_resolution(nbins, k_start, k_end)

    if length_scale_range is None:
        # Auto-determine based on resolution + empirical correlation
        if resolution_info is not None:
            # Use bin resolution as primary constraint
            min_ell, max_ell = resolution_info["recommended_length_range"]
            # Extend range slightly for exploration
            length_scale_range = (0.8 * min_ell, 1.2 * max_ell)

            auto_selected_ranges["length_scale_range"] = length_scale_range
            auto_selected_ranges["length_method"] = "auto (bin resolution)"

            print(
                f"\nAuto-selected length scale range: [{length_scale_range[0]:.3f}, {length_scale_range[1]:.3f}]"
            )
            print(
                f"  Based on {nbins} bins over $\\Delta\\log(k)$ = {resolution_info['log_k_range']:.2f}"
            )
            print(f"  Min resolvable: {min_ell:.3f} (Nyquist: ~2 bins)")
            print(f"  Max sensible: {max_ell:.3f} (half domain)")

            # Optionally refine with empirical autocorrelation
            try:
                empirical_ell = estimate_length_scale_from_autocorrelation(
                    delta_values, log_k.ravel(), fallback_quantile=auto_length_fallback
                )
                print(f"  Empirical correlation length: {empirical_ell:.3f}")

                # If empirical estimate is within resolution bounds, suggest it
                if min_ell <= empirical_ell <= max_ell:
                    print(f"  → Empirical estimate is within resolvable range (good!)")
                else:
                    print(
                        f"  → Empirical estimate outside resolvable range (using resolution bounds)"
                    )

            except Exception as e:
                print(f"  Note: Could not estimate empirical correlation length ({e})")
        else:
            # No resolution info - use empirical estimate only
            try:
                empirical_ell = estimate_length_scale_from_autocorrelation(
                    delta_values, log_k.ravel(), fallback_quantile=auto_length_fallback
                )
                # Build range around empirical estimate
                length_scale_range = (0.5 * empirical_ell, 2.0 * empirical_ell)

                auto_selected_ranges["length_scale_range"] = length_scale_range
                auto_selected_ranges["length_method"] = "auto (empirical autocorr)"

                print(
                    f"\nAuto-selected length scale range: [{length_scale_range[0]:.3f}, {length_scale_range[1]:.3f}]"
                )
                print(f"  Based on empirical autocorrelation: ℓ ≈ {empirical_ell:.3f}")
                print(f"  Warning: No resolution info provided (nbins, k_start, k_end)")
            except Exception as e:
                # Complete fallback
                log_k_range = np.ptp(log_k)
                length_scale_range = (0.1 * log_k_range, 0.5 * log_k_range)

                auto_selected_ranges["length_scale_range"] = length_scale_range
                auto_selected_ranges["length_method"] = "auto (fallback)"

                print(
                    f"\nUsing fallback length scale range: [{length_scale_range[0]:.3f}, {length_scale_range[1]:.3f}]"
                )
                print(
                    f"  Based on {auto_length_fallback * 100:.0f}% of $\\log(k)$ range"
                )
                print(f"  Warning: Could not estimate from data ({e})")
    else:
        # User-provided
        auto_selected_ranges["length_scale_range"] = length_scale_range
        print(
            f"\nUsing user-provided length scale range: [{length_scale_range[0]:.3f}, {length_scale_range[1]:.3f}]"
        )

    # === VALIDATION ===
    if validate_ranges:
        print(f"\nValidating hyperparameter ranges...")
        is_valid = validate_hyperparameter_ranges(
            sigma_range,
            length_scale_range,
            noise_level,
            empirical_std,
            resolution_info,
            warn=True,
        )
        if is_valid:
            print("  ✓ All ranges pass validation checks")
        else:
            print("  ⚠ Some validation warnings above - review carefully")

    print("=" * 70 + "\n")

    # Create 2D grid
    sigma_grid = np.linspace(sigma_range[0], sigma_range[1], n_sigma)
    length_scale_grid = np.linspace(
        length_scale_range[0], length_scale_range[1], n_length
    )

    lml_grid = np.zeros((n_sigma, n_length))

    # Ensure kernel_params is a dict
    if kernel_params is None:
        kernel_params = {}

    print(f"\nComputing log-marginal likelihood on {n_sigma} × {n_length} grid...")
    print(f"  Kernel: {kernel_type.value}")
    if kernel_params:
        print(f"  Kernel params: {kernel_params}")
    print(f"  σ range: [{sigma_range[0]:.4f}, {sigma_range[1]:.4f}]")
    print(f"  ℓ range: [{length_scale_range[0]:.3f}, {length_scale_range[1]:.3f}]")

    # OPTIMIZATION: Pre-compute base kernel matrices (without sigma scaling)
    # This reduces kernel evaluations from n_sigma × n_length to just n_length
    print("  Pre-computing kernel matrices...")
    base_kernels = []
    for length_scale in length_scale_grid:
        # Build kernel config with sigma=1 (we'll scale by sigma² later)
        config = KernelConfig(
            kernel_type=kernel_type,
            sigma=1.0,  # Unit amplitude - will scale later
            length_scale=length_scale,
            params=kernel_params,
        )
        kernel = build_kernel(config)
        base_kernels.append(kernel(log_k))

    # Pre-compute noise covariance (constant across grid)
    if use_full_cov:
        K_noise = posterior_cov
    else:
        K_noise = noise_level**2 * np.eye(n)

    # Compute LML for each (σ, ℓ) pair
    for i, sigma in enumerate(sigma_grid):
        if (i + 1) % max(1, n_sigma // 5) == 0:
            print(f"  Progress: {i + 1}/{n_sigma}")

        for j, length_scale in enumerate(length_scale_grid):
            # Scale pre-computed kernel by σ²
            K_signal = sigma**2 * base_kernels[j]

            # Total covariance
            K = K_signal + K_noise

            # Compute LML
            try:
                lml_grid[i, j] = _compute_lml_from_K(delta_values, K, n)
            except Exception:
                lml_grid[i, j] = -np.inf

    # Find maximum
    max_idx = np.unravel_index(np.argmax(lml_grid), lml_grid.shape)
    optimal_sigma = sigma_grid[max_idx[0]]
    optimal_length_scale = length_scale_grid[max_idx[1]]
    max_lml = lml_grid[max_idx]

    # Null hypothesis: σ ≈ 0 (pure noise)
    # Use smallest sigma in grid as proxy
    null_idx = 0
    null_lml = lml_grid[null_idx, :].max()  # Best fit with minimal sigma

    # Bayes factor: signal vs noise
    bayes_factor = np.exp(max_lml - null_lml)

    print(f"\n{'=' * 60}")
    print("RESULTS:")
    print(f"{'=' * 60}")
    print(f"Kernel: {kernel_type.value}")
    if kernel_params:
        for k, v in kernel_params.items():
            print(f"  {k} = {v}")
    print(f"\nOptimal hyperparameters:")
    print(f"  σ (signal std) = {optimal_sigma:.4f}")
    print(f"  ℓ (length scale) = {optimal_length_scale:.4f}")
    print(f"  Max LML = {max_lml:.2f}")
    print(f"\nNull hypothesis (σ ≈ {sigma_grid[0]:.4f}):")
    print(f"  LML = {null_lml:.2f}")
    print(f"  Bayes factor (signal/noise) = {bayes_factor:.2e}")

    # Interpret Bayes factor
    if bayes_factor > 100:
        print("  → DECISIVE evidence for signal (BF > 100)")
    elif bayes_factor > 10:
        print("  → STRONG evidence for signal (BF > 10)")
    elif bayes_factor > 3:
        print("  → MODERATE evidence for signal (BF > 3)")
    else:
        print("  → WEAK/NO evidence for signal (BF < 3)")

    # Interpret length scale
    if resolution_info is not None:
        delta_log_k = resolution_info["delta_log_k"]
        n_bins_spanned = optimal_length_scale / delta_log_k
        print(f"\nFeature characterization:")
        print(f"  Length scale spans ~{n_bins_spanned:.1f} bins")
        if n_bins_spanned < 3:
            print("  → SHARP, localized features (few-bin scale)")
        elif n_bins_spanned < 8:
            print("  → MODERATE-scale features")
        else:
            print("  → BROAD, smooth features (many-bin scale)")

    print(f"{'=' * 60}\n")

    return {
        "sigma_grid": sigma_grid,
        "length_scale_grid": length_scale_grid,
        "lml_grid": lml_grid,
        "optimal_sigma": optimal_sigma,
        "optimal_length_scale": optimal_length_scale,
        "max_lml": max_lml,
        "null_lml": null_lml,
        "bayes_factor": bayes_factor,
        "delta_values": delta_values,
        "log_k": log_k,
        "resolution_info": resolution_info,
        "noise_level": noise_level,
        "auto_selected_ranges": auto_selected_ranges,
        "kernel_type": kernel_type,
        "kernel_params": kernel_params,
    }


def compare_kernel_likelihoods(
    delta_values: np.ndarray,
    log_k: np.ndarray,
    kernel_configs: Dict[str, KernelConfig],
    noise_level: Optional[float] = None,
    noise_cov: Optional[np.ndarray] = None,
) -> Dict[str, Dict]:
    """
    Compare log-marginal likelihoods for different kernel configurations.

    This function computes the LML for each provided kernel configuration,
    allowing direct comparison of how well different kernels explain the data.

    Args:
        delta_values: Observed $\\delta(k)$ values values, shape (n,)
        log_k: $\\log(k)$ values, shape (n,) or (n, 1)
        kernel_configs: Dictionary mapping names to KernelConfig objects
        noise_level: Diagonal noise standard deviation (if noise_cov not provided)
        noise_cov: Full posterior covariance matrix (recommended)

    Returns:
        Dictionary with:
            - 'results': Dict mapping kernel name to {lml, config}
            - 'best_kernel': Name of kernel with highest LML
            - 'best_lml': Highest log-marginal likelihood
            - 'bayes_factors': Dict of Bayes factors relative to worst model

    Examples:
        >>> configs = {
        ...     'RBF': KernelConfig(KernelType.RBF, sigma=0.1, length_scale=0.5),
        ...     'RQ': KernelConfig(
        ...         KernelType.RATIONAL_QUADRATIC,
        ...         sigma=0.1,
        ...         length_scale=0.5,
        ...         params={'alpha': 2.0}
        ...     ),
        ...     'Periodic': KernelConfig(
        ...         KernelType.PERIODIC,
        ...         sigma=0.1,
        ...         length_scale=0.3,
        ...         params={'period': 1.5}
        ...     ),
        ... }
        >>> comparison = compare_kernel_likelihoods(delta, log_k, configs, noise_level=0.01)
        >>> print(f"Best kernel: {comparison['best_kernel']}")
        >>> print(f"Bayes factors: {comparison['bayes_factors']}")
    """
    log_k = np.asarray(log_k).reshape(-1, 1)
    delta_values = np.asarray(delta_values).ravel()

    results = {}
    lmls = {}

    print("=" * 60)
    print("KERNEL COMPARISON")
    print("=" * 60)

    for name, config in kernel_configs.items():
        lml = compute_log_marginal_likelihood(
            delta_values,
            log_k,
            kernel_config=config,
            noise_level=noise_level,
            noise_cov=noise_cov,
        )
        results[name] = {
            "lml": lml,
            "config": config,
            "description": config.describe(),
        }
        lmls[name] = lml
        print(f"  {name}: LML = {lml:.2f}")
        print(f"    {config.describe()}")

    # Find best and worst
    best_name = max(lmls.keys(), key=lambda k: lmls[k])
    best_lml = lmls[best_name]
    worst_lml = min(lmls.values())

    # Compute Bayes factors relative to worst model
    bayes_factors = {name: np.exp(lml - worst_lml) for name, lml in lmls.items()}

    print(f"\nBest kernel: {best_name} (LML = {best_lml:.2f})")
    print("\nBayes factors (relative to worst):")
    for name, bf in sorted(bayes_factors.items(), key=lambda x: -x[1]):
        print(f"  {name}: {bf:.2e}")
    print("=" * 60)

    return {
        "results": results,
        "best_kernel": best_name,
        "best_lml": best_lml,
        "bayes_factors": bayes_factors,
    }
