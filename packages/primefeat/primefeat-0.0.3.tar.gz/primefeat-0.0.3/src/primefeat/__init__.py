from pathlib import Path
import matplotlib.pyplot as plt

from .cli import app
from .compute import (
    Rminus1,
    compute_Pk_samples,
    compute_ns_eff,
    get_bin_centers,
    k_to_ell,
    ell_to_k,
)
from .load import load_chains, get_chains, get_autocorr
from . import compute, pca, gp, templates, significance

# Explicitly export public API
__all__ = [
    "app",
    "main",
    "Rminus1",
    "compute_Pk_samples",
    "compute_ns_eff",
    "get_bin_centers",
    "k_to_ell",
    "ell_to_k",
    "load_chains",
    "get_chains",
    "get_autocorr",
    "compute",
    "pca",
    "gp",
    "templates",
    "significance",
    "plot",
]


def main() -> None:
    app()


# ============================================================
# Auto-load PrimeFeat plotting style
# ============================================================
_STYLE_DIR = Path(__file__).parent
_DEFAULT_STYLE = _STYLE_DIR / "styles" / "primefeat.mplstyle"

if _DEFAULT_STYLE.exists():
    try:
        plt.style.use(str(_DEFAULT_STYLE))
    except Exception:
        # Silently fail if matplotlib style loading fails
        pass


# Import plots module after other modules are initialized to avoid circular imports
from . import plots as plot  # noqa: E402

# Export version info - read from package metadata
try:
    from importlib.metadata import version

    __version__ = version("primefeat")
except Exception:
    __version__ = "unknown"
