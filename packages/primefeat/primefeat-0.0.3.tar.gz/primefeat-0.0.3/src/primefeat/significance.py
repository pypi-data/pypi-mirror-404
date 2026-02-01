"""
Correlation-aware significance testing for primordial features.

Provides two methods:

1. null test: Tests against posterior covariance only (H₀: δ ~ N(0, Σ_post))
   - Statistically rigorous for feature detection
   - No circular reasoning from estimating correlation lengths

2. LML landscape: Bayesian model comparison for feature characterization
   - Optimizes signal amplitude σ and correlation length ℓ
   - Computes Bayes factors for evidence quantification
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from scipy.stats import chi2
from scipy.linalg import cho_factor, cho_solve
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, Matern


@dataclass
class GPSignificanceResult:
    """Results from GP-based significance test."""

    test_statistics: np.ndarray  # Mahalanobis distance for each posterior sample
    p_values: np.ndarray  # P-value for each sample under H0
    fraction_significant: float  # Fraction of samples deemed significant
    bin_contributions: List[Dict]  # Contribution of each bin to test statistic
    length_scale: float  # Correlation length scale in log(k) space
    covariance_matrix: np.ndarray  # K matrix under null hypothesis
    global_p_value: float  # Overall significance (median of p_values)
    lml_landscape: Optional[Dict] = (
        None  # Optional LML landscape from gp.compute_lml_landscape()
    )


@dataclass
class BinSignificance:
    """Results from significance test for a single bin."""

    bin_index: int  # 1-indexed bin number
    k_center: float  # Bin center in Mpc^-1
    mean_delta: float  # Posterior mean of delta
    std_delta: float  # Posterior standard deviation
    credible_interval: Tuple[float, float]  # 95% credible interval
    ci_excludes_zero: bool  # Does 95% CI exclude zero?
    p_value: float  # P(|delta| > threshold)
    corrected_p_value: float  # FDR-corrected p-value
    is_significant: bool  # Significant after FDR correction?
    effect_size: float  # |mean_delta| / std_delta (like a Z-score)


def estimate_correlation_length(
    chain,
    nbins: int = 20,
    k_start: float = 0.001,
    k_end: float = 0.23,
    min_correlation: float = 0.1,
) -> float:
    """
    Estimate correlation length scale from empirical bin-to-bin correlations.

    Fits exponential decay model: corr(Δlog k) ~ exp(-|Δlog k| / ℓ)

    Args:
        chain: MCMC chain with delta_i parameters
        nbins: Number of bins
        k_start, k_end: k-range for binning
        min_correlation: Minimum correlation to include in fit

    Returns:
        length_scale: Correlation length in log(k) units
    """
    from .compute import get_bin_centers

    bin_centers = get_bin_centers(k_start, k_end, nbins)
    log_k = np.log(bin_centers)

    # Extract delta samples
    delta_samples = np.array([chain[f"delta_{i}"] for i in range(1, nbins + 1)]).T

    # Compute empirical correlation matrix
    corr_matrix = np.corrcoef(delta_samples.T)

    # Extract distance-correlation pairs
    distances = []
    correlations = []
    for i in range(nbins):
        for j in range(i + 1, nbins):
            dist = abs(log_k[j] - log_k[i])
            corr = corr_matrix[i, j]
            if corr > min_correlation:  # Only use positive correlations
                distances.append(dist)
                correlations.append(corr)

    if len(distances) < 5:
        print(
            f"Warning: Only {len(distances)} bin pairs with correlation > {min_correlation}"
        )
        print("Using default length scale = 0.5")
        return 0.5

    distances = np.array(distances)
    correlations = np.array(correlations)

    # Fit exponential decay: corr = exp(-dist / length_scale)
    # Taking log: log(corr) = -dist / length_scale
    # So: length_scale = -mean(dist) / mean(log(corr))

    log_corr = np.log(correlations)
    length_scale = -np.mean(distances) / np.mean(log_corr)

    print(f"Estimated correlation length scale: {length_scale:.3f} in log(k)")
    print(f"  Based on {len(distances)} bin pairs with corr > {min_correlation}")

    return length_scale


def gp_significance_test(
    chain,
    nbins: int = 20,
    k_start: float = 0.001,
    k_end: float = 0.23,
    alpha: float = 0.05,
    method: str = "null",
    length_scale: Optional[float] = None,
    sigma: float = 1.0,
    use_full_covariance: bool = True,
    noise_level: float = 0.01,
    compute_landscape: bool = False,
    landscape_kwargs: Optional[Dict] = None,
    kernel_type: str = "rbf",
    sigma_range: Optional[Tuple[float, float]] = None,
    length_scale_range: Optional[Tuple[float, float]] = None,
    n_sigma: int = 20,
    n_length: int = 20,
) -> GPSignificanceResult:
    """
    Test significance using correlation-aware Gaussian Process methods.

    Two methods available:

    'null' (default): Tests against posterior covariance only
        H₀: δ ~ N(0, Σ_post)
        Test: χ² = δᵀ Σ_post⁻¹ δ ~ χ²(nbins)
        Use for: Rigorous detection of features

    'lml': Log-marginal likelihood landscape for feature characterization
        H₀: δ ~ N(0, Σ_post)
        H₁: δ ~ N(0, σ² K(ℓ) + Σ_post)
        Use for: Characterizing detected features via Bayes factors

    Args:
        chain: MCMC chain with delta_i parameters
        nbins: Number of bins
        k_start, k_end: k-range for binning (Mpc^-1)
        alpha: Significance level
        method: 'null' (default) or 'lml'
        kernel_type: 'rbf' or 'matern' (exponential)
        sigma_range, length_scale_range: Grid ranges for 'lml' method
        n_sigma, n_length: Grid sizes for 'lml' method
        length_scale: Fixed correlation length (deprecated, for backward compat)
        sigma: Signal amplitude (deprecated, for backward compat)
        use_full_covariance: Use Σ_post (deprecated, always True now)
        noise_level: Diagonal noise (deprecated)
        compute_landscape: If True, force method='lml'
        landscape_kwargs: Additional kwargs for landscape computation

    Returns:
        GPSignificanceResult with test statistics and diagnostics
    """
    from .compute import get_bin_centers

    # Handle backward compatibility
    if compute_landscape:
        method = "lml"

    bin_centers = get_bin_centers(k_start, k_end, nbins)
    log_k = np.log(bin_centers).reshape(-1, 1)

    # Extract posterior samples
    delta_samples = np.array([chain[f"delta_{i}"] for i in range(1, nbins + 1)]).T
    n_samples = len(delta_samples)

    # Compute posterior covariance (always needed)
    Sigma_post = np.cov(delta_samples.T)

    print(f"GP-based significance test (method={method}) on {n_samples} samples")
    print(f"Testing {nbins} bins over k = [{k_start}, {k_end}] Mpc^-1")

    if method == "null":
        # =================================================================
        # null TEST: Test against Σ_post only (statistically correct)
        # =================================================================
        print("Testing H₀: δ ~ N(0, Σ_post)")

        # Regularize if needed
        try:
            Sigma_inv_factor = cho_factor(Sigma_post)
        except np.linalg.LinAlgError:
            print("Warning: Σ_post singular, adding regularization")
            Sigma_post = Sigma_post + 1e-6 * np.eye(nbins)
            Sigma_inv_factor = cho_factor(Sigma_post)

        # Compute test statistic: χ² = δᵀ Σ_post⁻¹ δ
        test_statistics = []
        for delta in delta_samples:
            chi2_val = delta @ cho_solve(Sigma_inv_factor, delta)
            test_statistics.append(chi2_val)

        test_statistics = np.array(test_statistics)
        p_values = 1 - chi2.cdf(test_statistics, df=nbins)

        global_p_value = np.median(p_values)
        fraction_significant = np.mean(p_values < alpha)

        print(f"\nResults:")
        print(f"  Global p-value: {global_p_value:.4f}")
        print(f"  Fraction significant: {fraction_significant:.2%}")

        if global_p_value < alpha:
            print(f"  ✓ Features detected at α={alpha}")
        else:
            print(f"  ✗ No significant features at α={alpha}")

        # Compute bin contributions
        bin_contributions = []
        for i in range(nbins):
            contributions = []
            for delta in delta_samples:
                chi2_full = delta @ cho_solve(Sigma_inv_factor, delta)
                delta_minus_i = delta.copy()
                delta_minus_i[i] = 0
                chi2_partial = delta_minus_i @ cho_solve(
                    Sigma_inv_factor, delta_minus_i
                )
                contributions.append(chi2_full - chi2_partial)

            bin_contributions.append(
                {
                    "bin_index": i + 1,
                    "k_center": bin_centers[i],
                    "mean_contribution": np.mean(contributions),
                    "std_contribution": np.std(contributions),
                    "percentile_95": np.percentile(contributions, 95),
                }
            )

        print("\nTop 5 contributing bins:")
        for b in sorted(
            bin_contributions, key=lambda x: x["mean_contribution"], reverse=True
        )[:5]:
            print(
                f"  Bin {b['bin_index']} (k={b['k_center']:.4f}): "
                f"{b['mean_contribution']:.3f} ± {b['std_contribution']:.3f}"
            )

        return GPSignificanceResult(
            test_statistics=test_statistics,
            p_values=p_values,
            fraction_significant=fraction_significant,
            bin_contributions=bin_contributions,
            length_scale=None,
            covariance_matrix=Sigma_post,
            global_p_value=global_p_value,
            lml_landscape=None,
        )

    elif method == "lml":
        # =================================================================
        # LML LANDSCAPE: Bayesian model comparison for characterization
        # =================================================================
        print("LML landscape: H₀ vs H₁ = σ² K(ℓ) + Σ_post")

        delta_mean = delta_samples.mean(axis=0)

        # Set defaults for ranges
        if sigma_range is None:
            data_std = np.std(delta_mean)
            sigma_range = (0.01 * data_std, 5.0 * data_std)

        if length_scale_range is None:
            log_k_range = np.log(k_end / k_start)
            length_scale_range = (log_k_range / 4, log_k_range)

        sigma_grid = np.linspace(sigma_range[0], sigma_range[1], n_sigma)
        length_scale_grid = np.linspace(
            length_scale_range[0], length_scale_range[1], n_length
        )

        print(f"Grid: {n_sigma} × {n_length}, kernel={kernel_type}")

        # Select kernel
        if kernel_type == "rbf":
            kernel_fn = lambda ell: RBF(length_scale=ell, length_scale_bounds="fixed")
        elif kernel_type == "matern":
            kernel_fn = lambda ell: Matern(
                length_scale=ell, nu=0.5, length_scale_bounds="fixed"
            )
        else:
            raise ValueError(f"Unknown kernel: {kernel_type}")

        # Compute LML grid
        lml_grid = np.zeros((n_sigma, n_length))

        for i, sig in enumerate(sigma_grid):
            for j, ell in enumerate(length_scale_grid):
                K_signal = sig**2 * kernel_fn(ell)(log_k)
                K = K_signal + Sigma_post

                try:
                    K_factor = cho_factor(K)
                    K_inv_delta = cho_solve(K_factor, delta_mean)
                    log_det_K = 2 * np.sum(np.log(np.diag(K_factor[0])))
                    lml = -0.5 * (
                        delta_mean @ K_inv_delta + log_det_K + nbins * np.log(2 * np.pi)
                    )
                    lml_grid[i, j] = lml
                except np.linalg.LinAlgError:
                    lml_grid[i, j] = -1e10

        # Find optimal
        max_idx = np.unravel_index(np.argmax(lml_grid), lml_grid.shape)
        optimal_sigma = sigma_grid[max_idx[0]]
        optimal_length_scale = length_scale_grid[max_idx[1]]
        optimal_lml = lml_grid[max_idx]
        null_lml = lml_grid[0, :].max()
        log_BF = optimal_lml - null_lml
        BF = np.exp(log_BF)

        print(f"\nOptimal: σ={optimal_sigma:.4f}, ℓ={optimal_length_scale:.3f}")
        print(f"Bayes factor: {BF:.2e} (log BF={log_BF:.2f})")

        # Build optimal K
        K_signal_opt = optimal_sigma**2 * kernel_fn(optimal_length_scale)(log_k)
        K_opt = K_signal_opt + Sigma_post

        landscape = {
            "sigma_grid": sigma_grid,
            "length_scale_grid": length_scale_grid,
            "lml_grid": lml_grid,
            "optimal_sigma": optimal_sigma,
            "optimal_length_scale": optimal_length_scale,
            "optimal_lml": optimal_lml,
            "null_lml": null_lml,
            "log_bayes_factor": log_BF,
            "bayes_factor": BF,
            "K": K_opt,
            "K_signal": K_signal_opt,
            "K_noise": Sigma_post,
        }

        return GPSignificanceResult(
            test_statistics=None,
            p_values=None,
            fraction_significant=None,
            bin_contributions=[],
            length_scale=optimal_length_scale,
            covariance_matrix=K_opt,
            global_p_value=None,
            lml_landscape=landscape,
        )

    else:
        raise ValueError(f"Unknown method: {method}")


def pc_significance_test(
    pca_results,
    alpha: float = 0.05,
    test_type: str = "credible_interval",
    bonferroni_correction: bool = True,
) -> Dict:
    """
    Test significance in uncorrelated PC space.

    Since PCs are orthogonal by construction, we can test them with milder
    multiple testing correction than the full 20 bins.

    Args:
        pca_results: Results from primefeat.pca.perform_pca()
        alpha: Significance level
        test_type: 'credible_interval' or 'variance_ratio'
        bonferroni_correction: Apply Bonferroni correction across PCs

    Returns:
        Dictionary with significant PCs and their interpretations

    Example:
        >>> from primefeat.pca import perform_pca
        >>> pca_results = perform_pca(chain, nbins=20)
        >>> sig_result = pc_significance_test(pca_results, alpha=0.05)
        >>> print(f"Found {sig_result['n_significant']} significant PCs")
    """
    n_components = pca_results.n_components
    X_pca = pca_results.transformed_data

    # Adjust alpha if using Bonferroni
    if bonferroni_correction:
        alpha_corrected = alpha / n_components
        print(f"Using Bonferroni-corrected alpha = {alpha_corrected:.4f}")
    else:
        alpha_corrected = alpha

    significant_pcs = []

    print(f"\nTesting {n_components} principal components:")

    for i in range(n_components):
        pc_values = X_pca[:, i]

        if test_type == "credible_interval":
            # Does 95% CI exclude zero?
            ci_low, ci_high = np.percentile(pc_values, [2.5, 97.5])
            is_significant = (ci_low > 0) or (ci_high < 0)

            # Two-sided p-value
            p_value = 2 * min(np.mean(pc_values > 0), np.mean(pc_values < 0))

            if is_significant and p_value < alpha_corrected:
                print(
                    f"  PC{i + 1}: SIGNIFICANT (p={p_value:.4f}, "
                    f"CI=[{ci_low:.3f}, {ci_high:.3f}])"
                )

        elif test_type == "variance_ratio":
            # Test if variance is larger than expected under null
            # Under null (no features), PC variance should match explained variance ratio
            expected_var = pca_results.explained_variance_ratio[i]
            observed_var = np.var(pc_values)

            # Variance ratio test
            ratio = observed_var / expected_var

            # Approximate p-value using bootstrap
            # (proper F-test requires assumptions about distribution)
            is_significant = ratio > 2.0  # Heuristic threshold
            p_value = 1 / (1 + ratio)  # Approximate

            if is_significant:
                print(f"  PC{i + 1}: SIGNIFICANT (variance ratio={ratio:.2f})")

        else:
            raise ValueError(f"Unknown test_type: {test_type}")

        if is_significant and p_value < alpha_corrected:
            # Interpret this PC: which k-ranges does it affect?
            component = pca_results.components[i]

            # Identify bins with large loadings (> 1 std)
            loading_threshold = np.std(component)
            significant_bins = np.where(np.abs(component) > loading_threshold)[0]

            significant_pcs.append(
                {
                    "pc_index": i + 1,
                    "variance_explained": pca_results.explained_variance_ratio[i],
                    "p_value": p_value,
                    "affected_bins": significant_bins + 1,
                    "loading_pattern": component,
                    "mean_value": np.mean(pc_values),
                    "credible_interval": (ci_low, ci_high)
                    if test_type == "credible_interval"
                    else None,
                }
            )

    print(f"\nFound {len(significant_pcs)} significant PCs out of {n_components}")

    return {
        "significant_pcs": significant_pcs,
        "n_significant": len(significant_pcs),
        "n_tested": n_components,
        "alpha": alpha,
        "alpha_corrected": alpha_corrected,
        "test_type": test_type,
    }


def compare_significance_methods(
    chain,
    nbins: int = 20,
    k_start: float = 0.001,
    k_end: float = 0.23,
    alpha: float = 0.05,
) -> Dict:
    """
    Compare three significance testing approaches:
    1. Independent bin tests (current FDR method)
    2. GP-based correlation-aware test
    3. PC-based test (requires PCA results)

    Returns summary comparison showing which bins are called significant
    by each method.

    Args:
        chain: MCMC chain
        nbins, k_start, k_end: Binning parameters
        alpha: Significance level

    Returns:
        Dictionary with results from all three methods and comparison
    """

    print("=" * 70)
    print("COMPARISON: Three Significance Testing Methods")
    print("=" * 70)

    # Method 1: Standard FDR (independent bins)
    print("\n1. Independent bin tests with FDR control (Benjamini-Hochberg):")
    print("-" * 70)
    fdr_results = test_bin_significance(
        chain, nbins=nbins, alpha=alpha, correction="BH"
    )
    fdr_significant_bins = [r.bin_index for r in fdr_results if r.is_significant]
    print(f"   → {len(fdr_significant_bins)} significant bins")

    # Method 2: GP-based correlation-aware
    print("\n2. GP-based correlation-aware test:")
    print("-" * 70)
    gp_results = gp_significance_test(
        chain, nbins=nbins, k_start=k_start, k_end=k_end, alpha=alpha
    )
    # Bins with high contribution (heuristic: > 1.0)
    gp_significant_bins = [
        b["bin_index"]
        for b in gp_results.bin_contributions
        if b["mean_contribution"] > 1.0
    ]
    print(f"   → {len(gp_significant_bins)} high-contributing bins")

    # Method 3: PC-based (if pca module available)
    try:
        from .pca import perform_pca

        print("\n3. PC-based test (decorrelated components):")
        print("-" * 70)
        pca_results = perform_pca(chain, nbins=nbins)
        pc_results = pc_significance_test(pca_results, alpha=alpha)

        # Map significant PCs back to bins
        pc_significant_bins = set()
        for pc in pc_results["significant_pcs"]:
            pc_significant_bins.update(pc["affected_bins"])
        pc_significant_bins = sorted(list(pc_significant_bins))
        print(f"   → {len(pc_significant_bins)} bins affected by significant PCs")
    except ImportError:
        print("\n3. PC-based test: SKIPPED (pca module not available)")
        pc_results = None
        pc_significant_bins = []

    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY:")
    print("=" * 70)

    all_bins = set(fdr_significant_bins + gp_significant_bins + pc_significant_bins)

    print(f"\nBins called significant by each method:")
    print(
        f"  FDR only:     {set(fdr_significant_bins) - set(gp_significant_bins) - set(pc_significant_bins)}"
    )
    print(
        f"  GP only:      {set(gp_significant_bins) - set(fdr_significant_bins) - set(pc_significant_bins)}"
    )
    print(
        f"  PC only:      {set(pc_significant_bins) - set(fdr_significant_bins) - set(gp_significant_bins)}"
    )
    print(
        f"  All methods:  {set(fdr_significant_bins) & set(gp_significant_bins) & set(pc_significant_bins)}"
    )
    print(
        f"  At least 2:   {[b for b in all_bins if sum([b in fdr_significant_bins, b in gp_significant_bins, b in pc_significant_bins]) >= 2]}"
    )

    return {
        "fdr": {"results": fdr_results, "significant_bins": fdr_significant_bins},
        "gp": {"results": gp_results, "significant_bins": gp_significant_bins},
        "pc": {"results": pc_results, "significant_bins": pc_significant_bins},
        "all_bins": all_bins,
        "consensus_bins": [
            b
            for b in all_bins
            if sum(
                [
                    b in fdr_significant_bins,
                    b in gp_significant_bins,
                    b in pc_significant_bins,
                ]
            )
            >= 2
        ],
    }


def test_bin_significance(
    chain,
    nbins: int = 20,
    alpha: float = 0.05,
    threshold: float = 0.0,
    correction: str = "BH",
    param_pattern: str = "delta_{i}",
) -> List[BinSignificance]:
    """
    Test each bin for significant deviation from zero.

    This function:
    1. Computes credible intervals and p-values for each bin
    2. Applies multiple testing correction (default: Benjamini-Hochberg FDR)
    3. Identifies bins with statistically significant features

    Args:
        chain: MCMC chain object (e.g., from getdist)
        nbins: Number of bins (default: 20)
        alpha: Significance level (default: 0.05)
        threshold: Minimum |delta| to consider significant (default: 0.0)
        correction: Multiple testing correction method:
            - 'bonferroni': null, controls family-wise error rate
            - 'BH': Benjamini-Hochberg (default), controls false discovery rate
            - 'none': No correction (not recommended)
        param_pattern: Parameter name pattern (default: "delta_{i}")

    Returns:
        List of BinSignificance objects, one per bin

    Example:
        >>> results = test_bin_significance(chain, nbins=20, correction='BH')
        >>> significant = [r for r in results if r.is_significant]
        >>> print(f"Found {len(significant)} significant bins")
        >>> for r in significant:
        >>>     print(f"Bin {r.bin_index}: delta = {r.mean_delta:.3f} ± {r.std_delta:.3f}")
    """
    from .compute import get_bin_centers

    # Get bin centers
    # Note: You may want to pass k_start, k_end as arguments
    bin_centers = get_bin_centers(0.001, 0.23, nbins)

    results = []
    p_values = []

    # Step 1: Compute statistics for each bin
    for i in range(1, nbins + 1):
        param_name = param_pattern.format(i=i)
        delta_samples = np.array(chain[param_name])

        # Compute statistics
        mean_delta = np.mean(delta_samples)
        std_delta = np.std(delta_samples, ddof=1)

        # 95% credible interval
        ci_low, ci_high = np.percentile(delta_samples, [2.5, 97.5])
        ci_excludes_zero = (ci_low > 0) or (ci_high < 0)

        # P-value: P(|delta| > threshold)
        p_value = np.mean(np.abs(delta_samples) > threshold)

        # Effect size (standardized effect)
        effect_size = np.abs(mean_delta) / std_delta if std_delta > 0 else 0.0

        results.append(
            {
                "bin_index": i,
                "k_center": bin_centers[i - 1],
                "mean_delta": mean_delta,
                "std_delta": std_delta,
                "credible_interval": (ci_low, ci_high),
                "ci_excludes_zero": ci_excludes_zero,
                "p_value": p_value,
                "effect_size": effect_size,
            }
        )
        p_values.append(p_value)

    # Step 2: Apply multiple testing correction
    p_values = np.array(p_values)

    if correction == "bonferroni":
        # Bonferroni: Divide alpha by number of tests
        alpha_corrected = alpha / nbins
        corrected_p_values = p_values  # p-values stay the same, threshold changes
        is_significant = p_values < alpha_corrected

    elif correction == "BH":
        # Benjamini-Hochberg FDR control
        corrected_p_values, is_significant = benjamini_hochberg(p_values, alpha)

    elif correction == "none":
        # No correction (not recommended)
        corrected_p_values = p_values
        is_significant = p_values < alpha

    else:
        raise ValueError(
            f"Unknown correction method: {correction}. Use 'bonferroni', 'BH', or 'none'"
        )

    # Step 3: Create final results with corrected values
    final_results = []
    for i, res in enumerate(results):
        final_results.append(
            BinSignificance(
                bin_index=res["bin_index"],
                k_center=res["k_center"],
                mean_delta=res["mean_delta"],
                std_delta=res["std_delta"],
                credible_interval=res["credible_interval"],
                ci_excludes_zero=res["ci_excludes_zero"],
                p_value=res["p_value"],
                corrected_p_value=corrected_p_values[i],
                is_significant=is_significant[i],
                effect_size=res["effect_size"],
            )
        )

    return final_results


def benjamini_hochberg(
    p_values: np.ndarray, alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Benjamini-Hochberg procedure for controlling False Discovery Rate.

    The BH procedure works as follows:
    1. Sort p-values in ascending order: p(1) <= p(2) <= ... <= p(m)
    2. Find largest i such that p(i) <= (i/m) * alpha
    3. Reject hypotheses 1, ..., i

    This controls the expected proportion of false positives among rejections.

    Args:
        p_values: Array of p-values from multiple tests
        alpha: Desired FDR level (default: 0.05)

    Returns:
        adjusted_p_values: FDR-adjusted p-values
        is_significant: Boolean array indicating significance
    """
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Compute BH thresholds: (i/m) * alpha for i=1,...,m
    thresholds = np.arange(1, m + 1) / m * alpha

    # Find largest i where p(i) <= threshold
    significant_mask = sorted_p <= thresholds
    if np.any(significant_mask):
        max_i = np.where(significant_mask)[0][-1]
    else:
        max_i = -1

    # Adjusted p-values (to make them comparable to alpha)
    adjusted_p = np.minimum.accumulate(sorted_p[::-1] * m / np.arange(m, 0, -1))[::-1]
    adjusted_p = np.minimum(adjusted_p, 1.0)  # Cap at 1.0

    # Un-sort
    unsorted_adjusted_p = np.empty_like(adjusted_p)
    unsorted_adjusted_p[sorted_indices] = adjusted_p

    # Significance
    is_significant = np.zeros(m, dtype=bool)
    if max_i >= 0:
        is_significant[sorted_indices[: max_i + 1]] = True

    return unsorted_adjusted_p, is_significant


def identify_feature_regions(
    results: List[BinSignificance], min_width: int = 1
) -> List[Dict]:
    """
    Identify contiguous k-regions with significant features.

    Args:
        results: List of BinSignificance from test_bin_significance()
        min_width: Minimum number of consecutive significant bins to report

    Returns:
        List of dictionaries describing feature regions:
            - bins: List of bin indices in region
            - k_range: (k_min, k_max) of region
            - mean_amplitude: Average delta in region
            - max_amplitude: Maximum |delta| in region
            - n_bins: Number of bins in region
    """
    feature_regions = []
    current_region = []

    for i, res in enumerate(results):
        if res.is_significant:
            current_region.append(i)
        else:
            if len(current_region) >= min_width:
                # Save this region
                region_results = [results[j] for j in current_region]
                feature_regions.append(
                    {
                        "bins": [r.bin_index for r in region_results],
                        "k_range": (
                            region_results[0].k_center,
                            region_results[-1].k_center,
                        ),
                        "mean_amplitude": np.mean(
                            [r.mean_delta for r in region_results]
                        ),
                        "max_amplitude": np.max(
                            [np.abs(r.mean_delta) for r in region_results]
                        ),
                        "n_bins": len(region_results),
                    }
                )
            current_region = []

    # Don't forget last region
    if len(current_region) >= min_width:
        region_results = [results[j] for j in current_region]
        feature_regions.append(
            {
                "bins": [r.bin_index for r in region_results],
                "k_range": (
                    region_results[0].k_center,
                    region_results[-1].k_center,
                ),
                "mean_amplitude": np.mean([r.mean_delta for r in region_results]),
                "max_amplitude": np.max([np.abs(r.mean_delta) for r in region_results]),
                "n_bins": len(region_results),
            }
        )

    return feature_regions


def cross_dataset_consistency(
    chains_dict: Dict, nbins: int = 20, alpha: float = 0.05, correction: str = "BH"
) -> Dict:
    """
    Test whether features are consistent across multiple datasets.

    This identifies:
    - Features present in multiple datasets (robust)
    - Features unique to one dataset (dataset-specific)
    - Regions where datasets disagree (tension)

    Args:
        chains_dict: Dictionary mapping dataset labels to MCMC chains
        nbins: Number of bins (default: 20)
        alpha: Significance level (default: 0.05)
        correction: Multiple testing correction (default: 'BH')

    Returns:
        Dictionary with:
            - 'per_dataset': Dict of significance results per dataset
            - 'consistent_bins': Bins significant in >= 2 datasets
            - 'dataset_specific': Bins significant in only 1 dataset
            - 'tension_bins': Bins where datasets have opposite signs
    """
    # Test significance for each dataset
    per_dataset_results = {}
    for label, chain in chains_dict.items():
        results = test_bin_significance(
            chain, nbins=nbins, alpha=alpha, correction=correction
        )
        per_dataset_results[label] = results

    # Analyze consistency
    n_datasets = len(chains_dict)
    consistent_bins = []
    dataset_specific_bins = {label: [] for label in chains_dict.keys()}
    tension_bins = []

    for bin_idx in range(1, nbins + 1):
        # Check how many datasets have significant feature in this bin
        significant_datasets = []
        signs = []

        for label, results in per_dataset_results.items():
            res = results[bin_idx - 1]  # 0-indexed in list
            if res.is_significant:
                significant_datasets.append(label)
                signs.append(np.sign(res.mean_delta))

        # Classify this bin
        if len(significant_datasets) >= 2:
            # Check for sign agreement
            if len(set(signs)) == 1:
                # All datasets agree on sign
                consistent_bins.append(bin_idx)
            else:
                # Datasets disagree on sign → tension
                tension_bins.append(bin_idx)

        elif len(significant_datasets) == 1:
            # Only one dataset has significant feature
            dataset_specific_bins[significant_datasets[0]].append(bin_idx)

    return {
        "per_dataset": per_dataset_results,
        "consistent_bins": consistent_bins,
        "dataset_specific": dataset_specific_bins,
        "tension_bins": tension_bins,
    }
