"""
Dimensionality reduction and feature extraction for primordial features analysis.

This module provides tools to reduce the 20-dimensional bin parameter space
to a smaller number of interpretable components, revealing the dominant modes
of variation in delta(k).
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA, FastICA
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PCAResults:
    """Results from PCA analysis."""

    n_components: int
    explained_variance_ratio: np.ndarray
    cumulative_variance: np.ndarray
    components: np.ndarray  # Principal components (eigenvectors)
    transformed_data: np.ndarray  # Projected data in PC space
    pca_model: PCA
    scaler: StandardScaler
    effective_dim: int  # Number of PCs explaining 95% variance
    dataset_labels: Optional[List[str]] = None


def collect_delta_samples(
    chains_dict: Dict, nbins: int = 20, param_pattern: str = "delta_{i}"
) -> Tuple[np.ndarray, List[str]]:
    """
    Collect all delta samples from all chains into a single array.

    Args:
        chains_dict: Dictionary mapping dataset labels to MCMC chains,
                     or a single chain object (will be wrapped in dict)
        nbins: Number of bins (default: 20)
        param_pattern: Parameter name pattern (default: "delta_{i}")

    Returns:
        X: Array of shape (n_total_samples, nbins) with all delta values
        labels: List of dataset labels for each sample
    """
    # Handle single chain object (wrap in dict)
    if not isinstance(chains_dict, dict):
        chains_dict = {"chain": chains_dict}

    all_deltas = []
    labels = []

    for label, chain in chains_dict.items():
        # Extract delta parameters for this chain
        delta_matrix = np.array(
            [chain[param_pattern.format(i=i)] for i in range(1, nbins + 1)]
        ).T

        all_deltas.append(delta_matrix)
        labels.extend([label] * len(delta_matrix))

    X = np.vstack(all_deltas)
    return X, labels


def perform_pca(
    chains_dict: Dict,
    nbins: int = 20,
    n_components: Optional[int] = None,
    param_pattern: str = "delta_{i}",
) -> PCAResults:
    """
    Perform Principal Component Analysis on delta parameters.

    This identifies the dominant modes of variation in the primordial power
    spectrum deviations across all datasets.

    Args:
        chains_dict: Dictionary mapping dataset labels to MCMC chains,
                     or a single chain object (will be wrapped in dict)
        nbins: Number of bins (default: 20)
        n_components: Number of components to compute (default: nbins)
        param_pattern: Parameter name pattern (default: "delta_{i}")

    Returns:
        PCAResults object containing all analysis results

    Example:
        >>> results = perform_pca(chains, nbins=20)
        >>> print(f"Effective dimensionality: {results.effective_dim}")
        >>> print(f"Top 5 PCs explain {results.cumulative_variance[4]:.1%} of variance")
    """
    # Handle single chain object (wrap in dict)
    if not isinstance(chains_dict, dict):
        chains_dict = {"chain": chains_dict}

    # Set default number of components
    if n_components is None:
        n_components = nbins

    # Collect all delta samples
    X, labels = collect_delta_samples(chains_dict, nbins, param_pattern)

    print(f"Collected {X.shape[0]:,} samples from {len(chains_dict)} dataset(s)")
    print(f"Original dimensionality: {X.shape[1]} bins")

    # Standardize the data (critical for PCA!)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit PCA
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    # Compute metrics
    explained_var_ratio = pca.explained_variance_ratio_
    cumulative_var = np.cumsum(explained_var_ratio)

    # Find intrinsic dimensionality (95% variance threshold)
    effective_dim = int(np.argmax(cumulative_var >= 0.95) + 1)

    print(f"\nPCA Results:")
    print(f"  Effective dimensionality: {effective_dim} PCs (explain 95% variance)")
    print(f"  Top 5 PCs explain {cumulative_var[4]:.1%} of total variance")
    print(f"\nVariance explained by each PC:")
    for i in range(min(10, n_components)):
        print(f"  PC{i + 1}: {explained_var_ratio[i]:.2%}")

    return PCAResults(
        n_components=n_components,
        explained_variance_ratio=explained_var_ratio,
        cumulative_variance=cumulative_var,
        components=pca.components_,
        transformed_data=X_pca,
        pca_model=pca,
        scaler=scaler,
        effective_dim=effective_dim,
        dataset_labels=labels,
    )


def perform_ica(
    chains_dict: Dict,
    nbins: int = 20,
    n_components: int = 10,
    param_pattern: str = "delta_{i}",
    random_state: int = 42,
) -> Tuple[FastICA, np.ndarray, np.ndarray]:
    """
    Perform Independent Component Analysis on delta parameters.

    ICA finds statistically independent patterns, which can be better than PCA
    for identifying localized features or non-Gaussian structures.

    Args:
        chains_dict: Dictionary mapping dataset labels to MCMC chains,
                     or a single chain object (will be wrapped in dict)
        nbins: Number of bins (default: 20)
        n_components: Number of ICs to extract (default: 10)
        param_pattern: Parameter name pattern (default: "delta_{i}")
        random_state: Random seed for reproducibility (default: 42)

    Returns:
        ica_model: Fitted FastICA object
        X_ica: Transformed data in IC space
        components: Independent components (mixing matrix)

    Example:
        >>> ica, X_ica, components = perform_ica(chains, nbins=20, n_components=10)
        >>> # Plot components similar to PCA
    """
    # Handle single chain object (wrap in dict)
    if not isinstance(chains_dict, dict):
        chains_dict = {"chain": chains_dict}

    # Collect samples
    X, labels = collect_delta_samples(chains_dict, nbins, param_pattern)

    print(f"Performing ICA with {n_components} components...")

    # Standardize first (recommended for ICA)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit ICA
    ica = FastICA(
        n_components=n_components, random_state=random_state, max_iter=500, tol=1e-4
    )
    X_ica = ica.fit_transform(X_scaled)

    # Get components (sources)
    components = ica.components_

    print(f"ICA converged after {ica.n_iter_} iterations")

    return ica, X_ica, components


def compute_reconstruction_error(
    results: PCAResults, X_original: np.ndarray, n_components: int
) -> float:
    """
    Compute reconstruction error using only n_components PCs.

    This quantifies how much information is lost by using fewer components.

    Args:
        results: PCAResults from perform_pca()
        X_original: Original (unstandardized) data
        n_components: Number of PCs to use for reconstruction

    Returns:
        rmse: Root mean squared error of reconstruction
    """
    # Standardize
    X_scaled = results.scaler.transform(X_original)

    # Project to PC space and back
    X_proj = results.pca_model.transform(X_scaled)[:, :n_components]
    X_reconstructed = results.pca_model.inverse_transform(
        np.column_stack(
            [X_proj, np.zeros((X_proj.shape[0], results.n_components - n_components))]
        )
    )

    # Compute RMSE
    rmse = np.sqrt(np.mean((X_scaled - X_reconstructed) ** 2))

    return rmse


def RMSE_vs_n_components(chains_dict, nbins=20, max_components=None):
    """
    Compute reconstruction error (RMSE) as a function of number of PCs.

    Returns reconstruction error per sample as function of number of PCs.
    """
    # Perform PCA to get the model
    pca_result = perform_pca(chains_dict, nbins=nbins)

    # Collect all delta samples
    X, labels = collect_delta_samples(chains_dict, nbins=nbins)

    max_components = max_components or nbins
    error_values = []

    # IMPORTANT: PCA uses StandardScaler, so we need to work in scaled space
    # then transform back to original space for interpretable errors

    for k in range(1, max_components + 1):
        # Reconstruct in scaled space using PCA model
        # PCA does: X_scaled = scaler.transform(X)
        #           X_pca = X_scaled @ components.T
        # Inverse: X_scaled_recon = X_pca[:, :k] @ components[:k, :]
        #          X_recon = scaler.inverse_transform(X_scaled_recon)

        X_scaled = pca_result.scaler.transform(X)
        X_pca_k = pca_result.transformed_data[:, :k]  # First k PC scores

        # Reconstruct in scaled space
        X_scaled_recon = X_pca_k @ pca_result.components[:k, :]

        # Transform back to original space
        X_recon = pca_result.scaler.inverse_transform(X_scaled_recon)

        # Compute reconstruction error (RMSE per sample)
        residuals = X - X_recon
        mse_per_sample = np.mean(residuals**2, axis=1)  # Mean over bins
        rmse_per_sample = np.sqrt(mse_per_sample)

        # Also compute in terms of variance explained
        total_variance = np.var(X)
        residual_variance = np.var(residuals)
        variance_explained = 1 - (residual_variance / total_variance)

        error_values.append(
            {
                "n_components": k,
                "mean_rmse": np.mean(rmse_per_sample),
                "median_rmse": np.median(rmse_per_sample),
                "std_rmse": np.std(rmse_per_sample),
                "percentile_95": np.percentile(rmse_per_sample, 95),
                "variance_explained": variance_explained,
                "total_mse": np.mean(mse_per_sample),
            }
        )

    return error_values, pca_result


def analyze_bin_correlations(chains_dict: Dict, nbins: int = 20) -> np.ndarray:
    """
    Compute correlation matrix between bins.

    This shows which bins are correlated (likely due to smoothness constraints
    or cosmic variance).

    Args:
        chains_dict: Dictionary mapping dataset labels to MCMC chains,
                     or a single chain object (will be wrapped in dict)
        nbins: Number of bins (default: 20)

    Returns:
        corr_matrix: Correlation matrix (nbins x nbins)
    """
    # Handle single chain object (wrap in dict)
    if not isinstance(chains_dict, dict):
        chains_dict = {"chain": chains_dict}

    X, _ = collect_delta_samples(chains_dict, nbins)

    # Compute correlation matrix
    corr_matrix = np.corrcoef(X.T)

    return corr_matrix


def variance_decomposition(pca_pooled, N_pcs=10, chains_dict=None):
    from scipy.stats import f_oneway

    # Get transformed data and labels
    transformed = pca_pooled.transformed_data
    labels_array = np.array(pca_pooled.dataset_labels)

    # Compute average effective sample size across chains
    if chains_dict is not None:
        if not isinstance(chains_dict, dict):
            chains_dict = {"chain": chains_dict}
        n_eff_list = [chain.getEffectiveSamples() for chain in chains_dict.values()]
        avg_n_eff = np.mean(n_eff_list)
    else:
        # Fallback: use total number of samples
        avg_n_eff = len(transformed)

    # Get explained variance ratio from PCA model (fraction of total variance)
    explained_variance_ratio = pca_pooled.pca_model.explained_variance_ratio_

    variance_between = []
    variance_within = []
    variance_total = []
    f_statistics = []
    snr_values = []
    p_values = []

    n_pcs = min(N_pcs, pca_pooled.n_components)

    print("Variance Decomposition:")
    print("=" * 80)
    print(
        f"{'PC':<4} {'Var(Between)':<15} {'Var(Within)':<15} {'F-stat':<10} {'SNR':<10} {'Interpretation'}"
    )
    print("=" * 80)

    for i in range(n_pcs):
        pc_scores = transformed[:, i]

        # Between-dataset variance
        dataset_means = np.array(
            [
                pc_scores[labels_array == l].mean()
                for l in np.unique(pca_pooled.dataset_labels)
            ]
        )
        var_between = np.var(dataset_means, ddof=1) if len(dataset_means) > 1 else 0

        # Within-dataset variance
        var_within = np.mean(
            [
                pc_scores[labels_array == l].var(ddof=1)
                for l in np.unique(pca_pooled.dataset_labels)
            ]
        )

        # Total variance
        var_total = np.var(pc_scores, ddof=1)

        # F-statistic (ratio of between to within variance)
        f_stat = var_between / var_within if var_within > 0 else 0

        # Signal-to-noise ratio: fraction of variance explained, scaled by measurement quality
        # Signal: explained variance ratio (0-1, fraction of total variance)
        # Statistical quality factor: sqrt(N_eff / 100) normalized to ~1 for N_eff=100
        signal = explained_variance_ratio[i]
        quality_factor = np.sqrt(avg_n_eff / 100.0) if avg_n_eff > 0 else 1.0
        snr = signal * quality_factor

        # ANOVA p-value to test if means differ across datasets
        dataset_groups = [
            pc_scores[labels_array == l] for l in np.unique(pca_pooled.dataset_labels)
        ]
        _, p_value = f_oneway(*dataset_groups)

        variance_between.append(var_between)
        variance_within.append(var_within)
        variance_total.append(var_total)
        f_statistics.append(f_stat)
        snr_values.append(snr)
        p_values.append(p_value)

        # Interpretation
        if f_stat > 1.0:
            interpretation = "Dataset separation dominates"
        elif f_stat > 0.1:
            interpretation = "Mixed (both sources contribute)"
        else:
            interpretation = "Within-dataset variance dominates"

        print(
            f"PC{i + 1:<2} {var_between:<15.4f} {var_within:<15.4f} {f_stat:<10.3f} {snr:<10.2f} {interpretation}"
        )

    print("=" * 80)
    print("\nInterpretation:")
    print("- High F-stat (>1): PC captures differences between datasets")
    print("- Low F-stat (<0.1): PC captures shared variation within datasets")
    print("- Mid F-stat (0.1-1): PC captures both sources")
    print("- High SNR: PC is well-measured (signal >> measurement noise)")
    print("- Low SNR: PC is dominated by MCMC sampling noise")
    return (
        variance_between,
        variance_within,
        variance_total,
        f_statistics,
        snr_values,
        p_values,
    )
