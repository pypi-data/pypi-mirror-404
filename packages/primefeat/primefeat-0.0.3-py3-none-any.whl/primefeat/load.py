from getdist import loadMCSamples
from typing import List
import yaml
from pathlib import Path


def get_autocorr(chains: dict) -> None:
    """
    Compute and store autocorrelation information for each MCMC chain.

    Parameters
    ----------
    chains : dict
        Dictionary of MCSamples objects with labels as keys
    """
    for label, chain in chains.items():
        try:
            n_eff = chain.getEffectiveSamples()
            n_samples = chain.numrows
            autocorr_reduction = n_samples / n_eff

            print(f"\n{label}:")
            print(f"  Total samples: {n_samples}")
            print(f"  Effective samples: {n_eff:.0f}")
            print(f"  Autocorrelation factor: {autocorr_reduction:.1f}")
            print(
                f"  Eff. samples per parameter: {n_eff / chain.getParamNames().numParams():.1f}"
            )
        except Exception:
            print(f"Warning: Could not compute autocorrelation for chain '{label}'.")


def load_chains(
    filenames: List, labels: List | None = None, skip: None | float = 0.3
) -> dict:
    from .compute import Rminus1

    labels = [f"chain{i}" for i in range(len(filenames))] if labels is None else labels
    chains = {
        label: loadMCSamples(chain, settings={"ignore_rows": skip})
        for label, chain in zip(labels, filenames)
    }
    # After loading chains
    get_autocorr(chains)
    try:
        Rminus1(chains)
    except Exception:
        pass
    return chains


def get_chains(
    subset: float | str,
    config_file: str | Path = "chains.yaml",
    skip: float | None = None,
) -> dict:
    """
    Load MCMC chains based on kmin value from a YAML configuration file.

    Parameters
    ----------
    subset : float or str
        Any key to determine which subset of chains to load
    config_file : str or Path, optional
        Path to YAML configuration file. Default is "chains.yaml" in current directory.
        If not found in current directory, looks in the package root.
    skip : float, optional
        Fraction of samples to skip at beginning. If None, uses value from config file.

    Returns
    -------
    dict
        Dictionary of loaded chains with labels as keys and MCSamples objects as values

    Examples
    --------
    >>> chains = get_chains(1e-4)
    >>> chains = get_chains(LCDM, config_file="my_chains.yaml")
    """
    # Locate config file
    config_path = Path(config_file)
    if not config_path.exists():
        # Try package root directory
        package_root = Path(__file__).parent.parent.parent
        config_path = package_root / config_file
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}\n"
                f"Searched in current directory and {package_root}"
            )

    # Load YAML configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Get root directory for chains
    root_dir = config.get("root", "")
    if root_dir:
        root_dir = Path(root_dir)
    else:
        root_dir = Path("")

    # Get default skip value if not provided
    if skip is None:
        skip = config.get("settings", {}).get("skip", 0.3)

    # Find matching kmin configuration
    chains_config = config.get("chains", {})
    subset_key = None

    # Try exact match first
    if subset in chains_config:
        subset_key = subset
    else:
        # Try string representation
        for key in chains_config.keys():
            if isinstance(key, str):
                try:
                    if float(key) == subset:
                        subset_key = key
                        break
                except (ValueError, TypeError):
                    pass
            elif key == subset:
                subset_key = key
                break

    if subset_key is None:
        available_subsets = list(chains_config.keys())
        raise ValueError(
            f"No configuration found for subset={subset}\n"
            f"Available subset values: {available_subsets}"
        )

    # Extract chain paths and labels
    chain_data = chains_config[subset_key]
    paths = []
    labels = []
    chains_with_h = []  # Track which chains need h parameter added

    for label, chain_info in chain_data.items():
        if isinstance(chain_info, dict):
            chain_path = root_dir / chain_info["path"]
            paths.append(str(chain_path))
            labels.append(label)
            if chain_info.get("add_h_parameter", False):
                chains_with_h.append(label)
        else:
            # Support simple format: label: path
            chain_path = root_dir / chain_info
            paths.append(str(chain_path))
            labels.append(label)

    print(f"Loading chains for subset = {subset}:")
    for label in labels:
        print(f"  - {label}")
    print()

    # Load chains
    chains = load_chains(paths, labels, skip=skip)

    # Post-processing: Add h parameter for specific chains
    for label in chains_with_h:
        if label in chains:
            try:
                h_values = chains[label].getParams().H0 / 100
                chains[label].addDerived(h_values, "h", "h")
                print(f"Added derived parameter 'h' to {label}")
            except Exception as e:
                print(f"Warning: Could not add 'h' parameter to {label}: {e}")

    return chains
