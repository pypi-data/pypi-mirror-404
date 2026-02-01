import matplotlib.pyplot as plt
from getdist import plots
import numpy as np
from typing import Tuple, Optional, List, Dict
from .pca import PCAResults
from .pca import variance_decomposition as pca_variance_decomposition
from .compute import k_to_ell, ell_to_k
from pathlib import Path
from contextlib import contextmanager
# from getdist import MCSamples


# ============================================================
# Style Management
# ============================================================
_STYLE_DIR = Path(__file__).parent
_AVAILABLE_STYLES = {
    "publication": _STYLE_DIR / "primefeat.mplstyle",
    "presentation": _STYLE_DIR / "primefeat_presentation.mplstyle",
    "dark": _STYLE_DIR / "primefeat_dark.mplstyle",
}


def use_style(style="publication"):
    """
    Apply a PrimeFeat plotting style.

    Args:
        style: One of 'publication', 'presentation', or 'dark'
               - 'publication': Optimized for PRD two-column format (default)
               - 'presentation': Large fonts and bold lines for slides
               - 'dark': High contrast colors for dark backgrounds

    Example:
        >>> import primefeat.plots as plot
        >>> plot.use_style('presentation')  # Switch to presentation mode
        >>> plot.use_style('publication')   # Back to publication mode
    """
    if style not in _AVAILABLE_STYLES:
        available = ", ".join(_AVAILABLE_STYLES.keys())
        raise ValueError(f"Style '{style}' not found. Available styles: {available}")

    style_path = _AVAILABLE_STYLES[style]
    if not style_path.exists():
        raise FileNotFoundError(f"Style file not found: {style_path}")

    plt.style.use(str(style_path))
    print(f"✓ Applied '{style}' style")


@contextmanager
def style_context(style="publication"):
    """
    Context manager for temporary style changes.

    Args:
        style: One of 'publication', 'presentation', or 'dark'

    Example:
        >>> with plot.style_context('presentation'):
        ...     fig, ax = plt.subplots()
        ...     ax.plot(x, y)
        ... # Style automatically reverts after the block
    """
    if style not in _AVAILABLE_STYLES:
        available = ", ".join(_AVAILABLE_STYLES.keys())
        raise ValueError(f"Style '{style}' not found. Available styles: {available}")

    style_path = _AVAILABLE_STYLES[style]
    if not style_path.exists():
        raise FileNotFoundError(f"Style file not found: {style_path}")

    with plt.style.context(str(style_path)):
        yield


def list_styles():
    """
    List all available PrimeFeat styles.

    Returns:
        dict: Dictionary of style names and descriptions
    """
    styles = {
        "publication": 'Optimized for PRD two-column format (9pt fonts, 3.375" width)',
        "presentation": "Large fonts and bold lines for slides and posters",
        "dark": "High contrast colors for dark backgrounds and dark mode",
    }

    print("Available PrimeFeat styles:")
    print("=" * 70)
    for name, description in styles.items():
        status = "✓" if _AVAILABLE_STYLES[name].exists() else "✗"
        print(f"  {status} {name:14s} - {description}")
    print("=" * 70)
    print("\nUsage:")
    print("  import primefeat.plots as plot")
    print("  plot.use_style('presentation')  # Switch styles")
    print("  plot.use_style('publication')   # Default style")

    return styles


def plot_fill_between(
    x: np.ndarray,
    samples_y: np.ndarray,
    alpha_contour: float = 0.5,
    quantiles: list = [2.3, 16, 50, 84, 97.7],
    ax=None,
    **plt_kwargs,
):
    """
    Plot median and quantiles for a given (flatten) array of samples

    Args:
        x (np.ndarray): an array with x-values as a numpy array.
        samples_y (np.ndarray): a numpy array with samples for the quantity f=y(x).
        label (str, optional): labels to use in the legend. Defaults to None.
        ax (_type_, optional): a matplotlib axes instance. If None, will create a single plot with default settings. Defaults to None.
        color (str, optional): color for the contours. Defaults to 'gray'.
        lw (float, optional): length-width for the lines. Defaults to 2..
        alpha (float, optional): transparency of the contour colors. Defaults to 0.5.
        quantiles (list, optional): quantiles of the distribution to plot. Defaults to [2.3, 16, 50, 84, 97.7].
    """
    if ax is None:
        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError:
            print("Cannot import matplotlib. Try installing matplotlib before!")
        fig, ax = plt.subplots()

    qs = np.percentile(samples_y, q=quantiles, axis=0)
    idx = len(qs) // 2
    median = qs[idx]
    cont_color = plt_kwargs.get("color", "gray")
    for i in range(1, idx + 1):
        ax.fill_between(
            x.flatten(),
            qs[idx - i].flatten(),
            qs[idx + i].flatten(),
            # **plt_kwargs,
            color=cont_color,
            alpha=alpha_contour / i,
        )
    ax.plot(x, median, **plt_kwargs)
    return ax


def triangle(
    chains: dict, params: list, labels: list | None = None, **kwargs
) -> plots.GetDistPlotter:
    labels = list(chains.keys()) if labels is None else labels
    g = plots.get_single_plotter()
    g.triangle_plot(list(chains.values()), params, legend_labels=labels, **kwargs)
    return g


def posteriors_delta(k: np.ndarray, samples: dict, colors: list) -> plt.Figure:
    """
    Plot posteriors for deviations only: 1 + δ(k)

    Args:
        k: array of k values
        samples: dict mapping labels to lists of samples (each sample is 1 + δ(k))
        colors: list of colors for each dataset

    Returns:
        matplotlib Figure
    """
    fig, axs = plt.subplots(len(samples), figsize=(8, 6), sharex=True)
    # Ensure axs is always iterable (even for single subplot)
    if len(samples) == 1:
        axs = [axs]
    for ax, color, (lbl, Pk) in zip(axs, colors, samples.items()):
        ax.plot([], [], color=color, label=lbl)
        ax = plot_fill_between(k, Pk, ax=ax, color=color, alpha_contour=0.5)
        ax.axhline(1.0, color="k", linestyle="--", alpha=0.7)
        ax.legend(frameon=False)
        ax.semilogx()
        ax.set_ylabel(r"$1+\delta(k)$", fontsize="x-large")

    return fig


def distance_T(
    gp_result,
    label=None,
    nbins=20,
    color="steelblue",
    ax=None,
    include_median=False,
    include_ref=True,
):
    chi2_lbl = rf" $\chi^2$({nbins}) - Null distribution" if ax is None else None

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))

    if label is None:
        label = "Observed"

    # Use KDE instead of histogram
    from scipy.stats import chi2, gaussian_kde

    x = np.linspace(0, max(gp_result.test_statistics), 1000)
    if include_ref:
        # Overlay theoretical χ² distribution
        ax.plot(
            x,
            chi2.pdf(x, df=nbins),
            c="k",
            ls="--",
            lw=1.5,
            label=chi2_lbl,
        )

    kde = gaussian_kde(gp_result.test_statistics)
    ax.plot(x, kde(x), linewidth=2.5, label=label, color=color)
    ax.fill_between(x, kde(x), alpha=0.3, color=color)

    if include_median:
        ax.axvline(
            np.median(gp_result.test_statistics),
            ls="--",
            c="blue",
            label=f"Median observed = {np.median(gp_result.test_statistics):.1f}",
        )

    ax.set_xlabel("Mahalanobis Distance T", fontsize=11)
    ax.set_ylabel("Probability Density", fontsize=11)

    ax.legend(fontsize=9)
    return ax


def posteriors_PPS(
    k: np.ndarray,
    samples: dict,
    colors: list,
    mode: str = "delta",
    ax: Optional[plt.Axes] = None,
    show_binning_range: bool = False,
    k_start: float = None,
    k_end: float = None,
    alpha_contour: float = 0.5,
    add_inset: bool = False,
    inset_klim: tuple = (1e-2, 0.2),
    inset_bbox: tuple = (0.55, 0.55, 0.4, 0.4),
    inset_ylim: tuple = None,
    fig_kw: Optional[dict] = None,
) -> plt.Figure:
    """
    Plot posteriors for primordial power spectrum.

    Args:
        k: array of k values
        samples: dict mapping labels to lists of samples
        colors: list of colors for each dataset
        mode: "delta" for 1+δ(k) or "full" for full P(k) = A_s·k^(n_s-1)·[1+δ(k)]
        figsize: figure size (width, height)
        show_binning_range: if True, show gray shaded region for binning range
        k_start: start of binning range (only used if show_binning_range=True)
        k_end: end of binning range (only used if show_binning_range=True)
        alpha_contour: transparency for confidence bands (default: 0.5)
        add_inset: if True, add an inset plot with zoomed view
        inset_klim: tuple of (kmin, kmax) for inset zoom range
        inset_bbox: tuple of (x, y, width, height) for inset position in axes coordinates
        inset_ylim: tuple of (ymin, ymax) for inset y-axis limits (optional)

    Returns:
        matplotlib Figure
    """
    if ax is None:
        if fig_kw is None:
            fig_kw = {}
        fig, ax = plt.subplots(**fig_kw)
    else:
        fig = ax.figure

    # Show binning range if requested (inverted shading: gray outside, white inside)
    if show_binning_range and k_start is not None and k_end is not None:
        # Shade region before k_start
        ax.axvspan(k.min(), k_start, alpha=0.15, color="gray", zorder=0)
        # Shade region after k_end
        ax.axvspan(
            k_end,
            k.max(),
            alpha=0.15,
            color="gray",
            zorder=0,
            label="Extrapolation region",
        )

    # Plot each dataset using plot_fill_between
    for i, (label, sample_list) in enumerate(samples.items()):
        sample_array = np.array(sample_list)
        color = colors[i]

        # Use the existing plot_fill_between function
        ax.plot([], [], color=color, label=label)  # For legend
        ax = plot_fill_between(
            k, sample_array, ax=ax, color=color, alpha_contour=alpha_contour
        )

    ax.set_xscale("log")
    ax.set_xlabel(r"$k$ [Mpc$^{-1}$]", fontsize=16)
    ax.legend(fontsize=10, loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(k.min(), k.max())

    # Set y-axis based on mode
    if mode == "full":
        ax.set_yscale("log")
        ax.set_ylabel(r"$\mathcal{P}_\zeta(k)$", fontsize=16)
    else:
        ax.axhline(1.0, color="k", linestyle="--", alpha=0.7, lw=1)
        ax.set_ylabel(r"$1+\delta\mathcal{P}(k)$", fontsize=16)

    # Add secondary x-axis for multipoles ell

    # Use secondary_xaxis with proper transformation functions
    ax2 = ax.secondary_xaxis("top", functions=(k_to_ell, ell_to_k))
    ax2.set_xlabel(r"$\ell$", fontsize=16)

    # Disable top ticks on bottom axis to avoid overlap with secondary axis
    ax.tick_params(top=False, labeltop=False)

    # Add inset plot if requested
    if add_inset:
        # Create inset axes
        axins = ax.inset_axes(inset_bbox)

        # Filter k values within inset range
        k_mask = (k >= inset_klim[0]) & (k <= inset_klim[1])
        k_inset = k[k_mask]

        # Plot each dataset in the inset
        for i, (label, sample_list) in enumerate(samples.items()):
            sample_array = np.array(sample_list)
            # Filter samples to inset range
            sample_inset = sample_array[:, k_mask]
            color = colors[i]

            # Use plot_fill_between for inset
            axins = plot_fill_between(
                k_inset,
                sample_inset,
                ax=axins,
                color=color,
                alpha_contour=alpha_contour,
            )

        # Configure inset axes
        axins.set_xscale("log")
        axins.set_xlim(inset_klim[0], inset_klim[1])

        if mode == "full":
            axins.set_yscale("log")
            if inset_ylim is not None:
                axins.set_ylim(inset_ylim[0], inset_ylim[1])
        else:
            axins.axhline(1.0, color="k", linestyle="--", alpha=0.7, lw=1)
            if inset_ylim is not None:
                axins.set_ylim(inset_ylim[0], inset_ylim[1])

        axins.grid(True, alpha=0.3)
        axins.tick_params(labelsize=8)

        # Store inset axes as a figure attribute for easy access
        fig.inset_axes = axins

    plt.tight_layout()
    return fig


def posteriors_ns_eff(
    k: np.ndarray,
    ns_eff_samples: dict,
    colors: list,
    ax: Optional[plt.Axes] = None,
    show_binning_range: bool = False,
    k_start: float = None,
    k_end: float = None,
    alpha_contour: float = 0.5,
    add_inset: bool = False,
    inset_klim: tuple = (1e-2, 0.2),
    inset_bbox: tuple = (0.55, 0.55, 0.4, 0.4),
    inset_ylim: tuple = None,
    fig_kw: Optional[dict] = None,
) -> plt.Figure:
    """
    Plot posteriors for effective spectral index $n_s(k) - 1 = d \ln P(k) / d \ln k$.

    Args:
        k: array of k values
        ns_eff_samples: dict mapping labels to arrays of $n_s(k) - 1$ samples
        colors: list of colors for each dataset
        ax: existing matplotlib axes (optional)
        show_binning_range: if True, show gray shaded region for binning range
        k_start: start of binning range (only used if show_binning_range=True)
        k_end: end of binning range (only used if show_binning_range=True)
        alpha_contour: transparency for confidence bands (default: 0.5)
        add_inset: if True, add an inset plot with zoomed view
        inset_klim: tuple of (kmin, kmax) for inset zoom range
        inset_bbox: tuple of (x, y, width, height) for inset position in axes coordinates
        inset_ylim: tuple of (ymin, ymax) for inset y-axis limits (optional)
        fig_kw: additional keyword arguments for plt.subplots (e.g., figsize)

    Returns:
        matplotlib Figure
    """
    if ax is None:
        fig, ax = plt.subplots(**(fig_kw or {}))
    else:
        fig = ax.figure

    # Show binning range if requested (inverted shading: gray outside, white inside)
    if show_binning_range and k_start is not None and k_end is not None:
        # Shade region before k_start
        ax.axvspan(k.min(), k_start, alpha=0.15, color="gray", zorder=0)
        # Shade region after k_end
        ax.axvspan(
            k_end,
            k.max(),
            alpha=0.15,
            color="gray",
            zorder=0,
            label="Extrapolation region",
        )

    # Plot each dataset using plot_fill_between
    for i, (label, sample_array) in enumerate(ns_eff_samples.items()):
        color = colors[i]

        # Use the existing plot_fill_between function
        ax.plot([], [], color=color, label=label)  # For legend
        ax = plot_fill_between(
            k, sample_array, ax=ax, color=color, alpha_contour=alpha_contour
        )

    # Reference line at n_s - 1 = 0 (scale-invariant Harrison-Zel'dovich spectrum)
    ax.axhline(0.0, color="k", linestyle="--", alpha=0.7, lw=1, label=r"$n_s = 1$ (HZ)")

    ax.set_xscale("log")
    ax.set_xlabel(r"$k$ [Mpc$^{-1}$]", fontsize=16)
    ax.set_ylabel(r"$n_s(k) - 1$", fontsize=16)
    ax.legend(fontsize=10, loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(k.min(), k.max())

    # Add secondary x-axis for multipoles ell
    ax2 = ax.secondary_xaxis("top", functions=(k_to_ell, ell_to_k))
    ax2.set_xlabel(r"$\ell$", fontsize=16)

    # Disable top ticks on bottom axis to avoid overlap with secondary axis
    ax.tick_params(top=False, labeltop=False)

    # Add inset plot if requested
    if add_inset:
        # Create inset axes
        axins = ax.inset_axes(inset_bbox)

        # Filter k values within inset range
        k_mask = (k >= inset_klim[0]) & (k <= inset_klim[1])
        k_inset = k[k_mask]

        # Plot each dataset in the inset
        for i, (label, sample_array) in enumerate(ns_eff_samples.items()):
            # Filter samples to inset range
            sample_inset = sample_array[:, k_mask]
            color = colors[i]

            # Use plot_fill_between for inset
            axins = plot_fill_between(
                k_inset,
                sample_inset,
                ax=axins,
                color=color,
                alpha_contour=alpha_contour,
            )

        # Configure inset axes
        axins.set_xscale("log")
        axins.set_xlim(inset_klim[0], inset_klim[1])
        axins.axhline(0.0, color="k", linestyle="--", alpha=0.7, lw=1)

        if inset_ylim is not None:
            axins.set_ylim(inset_ylim[0], inset_ylim[1])

        axins.grid(True, alpha=0.3)
        axins.tick_params(labelsize=8)

        # Store inset axes as a figure attribute for easy access
        fig.inset_axes = axins

    plt.tight_layout()
    return fig


def plot_correlation_matrix(
    corr_matrix: np.ndarray,
    k_start: float = 0.001,
    k_end: float = 0.23,
    nbins: int = 20,
    figsize: Tuple = (10, 8),
):
    """
    Plot correlation matrix between bins.

    Args:
        corr_matrix: Correlation matrix from analyze_bin_correlations()
        k_start: Minimum k for binning
        k_end: Maximum k for binning
        nbins: Number of bins
        figsize: Figure size

    Returns:
        fig: matplotlib Figure object
    """
    from .compute import get_bin_centers

    bin_centers = get_bin_centers(k_start, k_end, nbins)

    fig, ax = plt.subplots(figsize=figsize)

    im = ax.imshow(corr_matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")

    # Set ticks to bin indices
    ax.set_xticks(range(nbins))
    ax.set_yticks(range(nbins))
    ax.set_xticklabels([f"{i + 1}" for i in range(nbins)], fontsize=8)
    ax.set_yticklabels([f"{i + 1}" for i in range(nbins)], fontsize=8)

    ax.set_xlabel("Bin index", fontsize=11)
    ax.set_ylabel("Bin index", fontsize=11)
    ax.set_title("Correlation Matrix Between Bins", fontsize=12)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Correlation coefficient", fontsize=10)

    plt.tight_layout()
    return fig


def dataset_separation_PC(
    results: PCAResults,
    chains_dict: Dict,
    pc_x: int = 1,
    pc_y: int = 2,
    figsize: Tuple = (10, 8),
    colors: Optional[List] = None,
    plot_type: str = "scatter",
    filled: bool = False,
    contour_levels: Optional[List] = None,
):
    """
    Plot samples from different datasets in principal component space.

    This shows whether different datasets have distinct feature preferences
    (separation in PC space) or if they agree (overlap in PC space).

    Args:
        results: PCAResults from perform_pca()
        chains_dict: Dictionary of chains (for labels)
        pc_x: Which PC to plot on x-axis (default: 1)
        pc_y: Which PC to plot on y-axis (default: 2)
        figsize: Figure size (default: (10, 8))
        colors: Optional list of colors for each dataset
        plot_type: "scatter" for scatter plot or "contour" for getdist contours (default: "scatter")
        filled: Whether to use filled contours (only for plot_type="contour", default: False)
        contour_levels: Confidence levels for contours (default: [0.68, 0.95] for 1σ and 2σ)

    Returns:
        fig: matplotlib Figure object
    """
    if colors is None:
        colors = [
            "#2E86AB",
            "#A23B72",
            "#F18F01",
            "#C73E1D",
            "#6A994E",
            "#7209B7",
            "#3A86FF",
            "#FB5607",
        ]

    if contour_levels is None:
        contour_levels = [0.68, 0.95]

    fig, ax = plt.subplots(figsize=figsize)

    # Plot each dataset separately
    labels = results.dataset_labels
    unique_labels = list(chains_dict.keys())

    if plot_type == "contour":
        # Use getdist for contour plotting
        from getdist import MCSamples
        from matplotlib.lines import Line2D

        # Create legend handles
        legend_handles = []

        for i, label in enumerate(unique_labels):
            # Get indices for this dataset
            mask = np.array([l == label for l in labels])

            # Get PC coordinates
            pc_coords = results.transformed_data[mask]

            # Create MCSamples object for getdist
            # Use simple names for getdist - matplotlib will handle axis labels
            names = [f"PC{pc_x}", f"PC{pc_y}"]

            samples = MCSamples(
                samples=pc_coords[:, [pc_x - 1, pc_y - 1]],
                names=names,
                labels=names,  # Simple labels for getdist
                label=label,
            )

            # Get 2D density and plot contours manually
            density = samples.get2DDensity(names[0], names[1])

            # Convert contour levels to actual density levels
            # getdist uses confidence levels (0-1), need to convert to density values
            density_levels = [
                density.getContourLevels([level])[0] for level in contour_levels
            ]

            color = colors[i % len(colors)]

            if filled:
                # Filled contours
                ax.contourf(
                    density.x,
                    density.y,
                    density.P,
                    levels=sorted(density_levels + [density.P.max()]),
                    colors=[color],
                    alpha=0.3,
                )

            # Always plot contour lines
            ax.contour(
                density.x,
                density.y,
                density.P,
                levels=sorted(density_levels),
                colors=[color],
                linewidths=1.5,
            )

            # Create legend handle for this dataset
            legend_handles.append(
                Line2D([0], [0], color=color, linewidth=2, label=label)
            )

    else:  # scatter plot
        for i, label in enumerate(unique_labels):
            # Get indices for this dataset
            mask = np.array([l == label for l in labels])

            # Get PC coordinates
            pc_coords = results.transformed_data[mask]

            # Plot with transparency to show density
            ax.scatter(
                pc_coords[:, pc_x - 1],
                pc_coords[:, pc_y - 1],
                alpha=0.3,
                s=1,
                color=colors[i % len(colors)],
                label=label,
            )

    ax.axhline(0, ls="--", c="k", alpha=0.3)
    ax.axvline(0, ls="--", c="k", alpha=0.3)
    ax.set_xlabel(
        rf"PC{pc_x} ({1e2 * results.explained_variance_ratio[pc_x - 1]:.1f}$\%$)",
        fontsize=11,
    )
    ax.set_ylabel(
        rf"PC{pc_y} ({1e2 * results.explained_variance_ratio[pc_y - 1]:.1f}$\%$)",
        fontsize=11,
    )

    # Add legend (use custom handles for contour mode)
    if plot_type == "contour":
        ax.legend(handles=legend_handles, framealpha=0.9)
    else:
        ax.legend(framealpha=0.9)

    plt.tight_layout()
    return fig


def variance_decomposition(pca_pooled, N_pcs=10, chains_dict=None, figname=None):
    variance_between, variance_within, _, f_statistics, snr_values, p_values = (
        pca_variance_decomposition(pca_pooled, N_pcs=N_pcs, chains_dict=chains_dict)
    )

    # Visualize variance decomposition with 2 panels
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(5, 3), sharex=True, gridspec_kw={"hspace": 0.05}
    )

    # Panel 1: Stacked variance components
    x = np.arange(1, N_pcs + 1)
    ax1.bar(x, variance_between, label="Between-dataset", alpha=0.8, color="#F18F01")
    ax1.bar(
        x,
        variance_within,
        bottom=variance_between,
        label="Within-dataset",
        alpha=0.8,
        color="#216C8C",
    )
    ax1.set_ylabel("Variance", fontsize=10)
    ax1.legend(loc="upper right", fontsize=7)
    ax1.set_xticks(x)

    # Panel 2: F-statistic (between/within ratio)
    colors = ["#F18F01" if f > 1.0 else "#216C8C" for f in f_statistics]
    ax2.bar(x, f_statistics, alpha=0.8, color=colors)
    ax2.axhline(y=1.0, color="k", linestyle="--", linewidth=1, label="Equal variance")
    ax2.set_xlabel("Principal Component", fontsize=10)
    ax2.set_ylabel(r"F-statistic", fontsize=10)
    ax2.set_yscale("log")
    ax2.legend(frameon=False, fontsize=8)
    ax2.set_xticks(x)

    plt.tight_layout()
    if figname:
        plt.savefig(figname, dpi=300, bbox_inches="tight")


def plot_principal_components(
    results: PCAResults,
    k_start: float = 0.001,
    k_end: float = 0.23,
    nbins: int = 20,
    n_components: int = 5,
    figsize: Tuple = (10, 10),
):
    """
    Visualize principal components as functions in k-space.

    This shows what each PC "looks like" as a pattern in the primordial
    power spectrum deviations.

    Args:
        results: PCAResults from perform_pca()
        k_start: Minimum k for binning (default: 0.001 Mpc^-1)
        k_end: Maximum k for binning (default: 0.23 Mpc^-1)
        nbins: Number of bins (default: 20)
        n_components: Number of PCs to plot (default: 5)
        figsize: Figure size (default: (10, 10))

    Returns:
        fig: matplotlib Figure object
    """
    from .compute import get_bin_centers

    bin_centers = get_bin_centers(k_start, k_end, nbins)

    n_to_plot = min(n_components, results.n_components)
    fig, axes = plt.subplots(n_to_plot, 1, figsize=figsize, sharex=True)

    # Handle single axis case
    if n_to_plot == 1:
        axes = [axes]

    for i in range(n_to_plot):
        # Get PC loadings (how each bin contributes to this PC)
        loadings = results.components[i]

        # Transform back to original scale
        loadings_rescaled = loadings / results.scaler.scale_

        # Plot
        axes[i].plot(bin_centers, loadings_rescaled, "o-", color=f"C{i}", linewidth=2)
        axes[i].axhline(0, ls="--", c="k", alpha=0.3)
        axes[i].set_ylabel(
            f"PC{i + 1}\n({results.explained_variance_ratio[i]:.1%})", fontsize=10
        )
        axes[i].set_xscale("log")
        axes[i].grid(True, alpha=0.3)

        # Add interpretation hints
        if i == 0:
            axes[i].set_title(
                "Principal Components in k-space\n(Dominant patterns of variation)",
                fontsize=12,
            )

    axes[-1].set_xlabel(r"$k$ [Mpc$^{-1}$]", fontsize=11)
    plt.tight_layout()
    return fig


def plot_variance_explained(results: PCAResults, figsize: Tuple = (12, 5)):
    """
    Plot variance explained by principal components.

    Args:
        results: PCAResults from perform_pca()
        figsize: Figure size (default: (12, 5))

    Returns:
        fig: matplotlib Figure object
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Plot 1: Individual variance per component
    axes[0].bar(
        range(1, len(results.explained_variance_ratio) + 1),
        results.explained_variance_ratio,
        alpha=0.7,
        color="steelblue",
    )
    axes[0].axhline(0.05, ls="--", c="red", alpha=0.5, label="5% threshold")
    axes[0].set_xlabel("Principal Component")
    axes[0].set_ylabel("Variance Explained")
    axes[0].set_title("Variance Explained by Each PC")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Cumulative variance
    axes[1].plot(
        range(1, len(results.cumulative_variance) + 1),
        results.cumulative_variance,
        "o-",
        color="steelblue",
        linewidth=2,
        markersize=6,
    )
    axes[1].axhline(0.95, ls="--", c="red", alpha=0.5, label="95% threshold")
    axes[1].axvline(
        results.effective_dim,
        ls="--",
        c="green",
        alpha=0.5,
        label=f"Effective dim = {results.effective_dim}",
    )
    axes[1].set_xlabel("Number of Components")
    axes[1].set_ylabel("Cumulative Variance Explained")
    axes[1].set_title("Cumulative Variance Explained")
    axes[1].set_ylim([0, 1.05])
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_Cls(Cls_dict, fig_kwargs=Dict | None, **plt_kwargs) -> plt.Figure:
    from .compute import k_to_ell, ell_to_k

    ells = Cls_dict["ell"]
    tt_samples = Cls_dict["TT"]
    te_samples = Cls_dict["TE"]
    ee_samples = Cls_dict["EE"]

    if fig_kwargs is None:
        fig_kwargs = {}

    fig, axs = plt.subplots(1, 3, **fig_kwargs)

    ax_tt = plot_fill_between(ells, tt_samples, ax=axs[0], **plt_kwargs)
    ax_te = plot_fill_between(ells, te_samples, ax=axs[1], **plt_kwargs)
    ax_ee = plot_fill_between(ells, ee_samples, ax=axs[2], **plt_kwargs)

    for ax in axs:
        ax.axhline(0, c="gray", ls="-")
        ax.set_xscale("log")
        ax.grid(False)

        # Add secondary x-axis for comoving wavenumber k
        ax2 = ax.secondary_xaxis("top", functions=(ell_to_k, k_to_ell))
        ax2.set_xlabel(r"$k$ [Mpc$^{-1}$]", fontsize=12)

        # Disable top ticks on bottom axis
        ax.tick_params(top=False, labeltop=False)

    plt.tight_layout()

    return fig


def PC_individual_vs_pooled(
    k_centers, pca_pooled, pca_separate, ell_cut=600, N_pcs=8, figname=None
):
    fig, axes = plt.subplots(
        N_pcs, 1, sharex=True, figsize=(9, 10), gridspec_kw={"hspace": 0.05}
    )
    colors = {
        "LSS": "#25055F",
        "PR3": "#2E86AB",
        "PR3+SPT": "#56974F",
        "PR3+LSS": "#56974F",
        "PR3+DESI+PanP": "#919743",
        "PR4": "#A23B72",
        "P-ACT": "#076426",
        "SPA": "#F18F01",
        "SPT+ACT": "#E8458E",
        "SPA+LSS": "#C73E1D",
    }

    # Compute k value for ell=600
    k_ell_cut = ell_to_k(ell_cut)

    for pc_idx in range(N_pcs):
        ax = axes[pc_idx]

        # Plot pooled PC (thick black line)
        ax.plot(
            k_centers,
            pca_pooled.components[pc_idx],
            "k-",
            linewidth=3,
            label="Pooled",
            alpha=0.8,
        )

        # Plot individual dataset PCs
        for data in pca_separate:
            # Get sign alignment with pooled PC
            dot_product = np.dot(
                pca_pooled.components[pc_idx], pca_separate[data].components[pc_idx]
            )
            sign = np.sign(dot_product)
            try:
                ax.plot(
                    k_centers,
                    sign * pca_separate[data].components[pc_idx],
                    "-",
                    linewidth=1.5,
                    label=data,
                    color=colors[data],
                    alpha=0.7,
                )
            except:
                pass

        # Add vertical line at ell=600
        ax.axvline(k_ell_cut, color="darkred", linestyle="-", linewidth=1.0, alpha=0.6)

        ax.set_xscale("log")
        ax.set_ylabel(f"PC{pc_idx + 1}", fontsize=14)
        if pc_idx == 0:
            ax.legend(
                ncol=len(pca_separate.items()) + 1,
                fontsize=12,
                bbox_to_anchor=(0.5, 1.8),
                loc="upper center",
                frameon=False,
            )
        ax.grid(alpha=0.3)
        ax.axhline(0, color="gray", linestyle="-", linewidth=0.5)

    # Add secondary x-axis with ell values on top using the same approach as posteriors_PPS
    # Use secondary_xaxis with proper transformation functions (pass functions, not calls)
    ax_top = axes[0].secondary_xaxis("top", functions=(k_to_ell, ell_to_k))
    ax_top.set_xlabel(r"$\ell$", fontsize=16)

    # Disable top ticks on bottom axis to avoid overlap with secondary axis
    axes[0].tick_params(top=False, labeltop=False)

    axes[-1].set_xlabel(r"$k$ [Mpc$^{-1}$]", fontsize=16)
    plt.tight_layout()
    if figname:
        plt.savefig(figname, dpi=300, bbox_inches="tight")
    return fig


def cos_similarity(chains, pca_separate, N_pcs=8, figname=None):
    from sklearn.metrics.pairwise import cosine_similarity

    labels = list(chains.keys())
    n_datasets = len(labels)

    # Create figure with subplots for each PC
    fig, axes = plt.subplots(2, N_pcs // 2, figsize=(16, 8))
    axes = axes.flatten()

    for pc_idx in range(N_pcs):
        # Extract PC vectors from each dataset
        pc_vectors = np.array(
            [pca_separate[label].components[pc_idx] for label in labels]
        )

        # Compute cosine similarity matrix
        cos_sim = cosine_similarity(pc_vectors)

        # Plot heatmap
        ax = axes[pc_idx]
        im = ax.imshow(np.abs(cos_sim), cmap="Oranges", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(n_datasets))
        ax.set_yticks(range(n_datasets))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        ax.set_title(f"PC{pc_idx + 1}", fontsize=11)

        # Add text annotations with dynamic color based on value
        for i in range(n_datasets):
            for j in range(n_datasets):
                value = np.abs(cos_sim[i, j])
                # Use white text for high values (close to 1), black for low values (close to 0)
                text_color = "white" if value > 0.5 else "black"
                text = ax.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=9,
                )

        # Compute average off-diagonal similarity
        mask = ~np.eye(n_datasets, dtype=bool)
        avg_similarity = np.abs(cos_sim[mask]).mean()
        ax.text(
            0.5,
            -0.15,
            f"Avg: {avg_similarity:.3f}",
            transform=ax.transAxes,
            ha="center",
            fontsize=9,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

    plt.tight_layout()
    if figname:
        plt.savefig(figname, dpi=300, bbox_inches="tight")
    return fig
