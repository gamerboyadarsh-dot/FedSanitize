"""
FedSanitize — MARS Step 3: Concentrated Backdoor Energy (CBE)
=============================================================
Extracts the top-κ% high-energy tail of the neuron energy distribution.

Reference: Wan et al., NeurIPS 2025 (arXiv:2509.20383)
Under a backdoor attack, anomalous energy is concentrated into a small fraction
of trigger-sensitive neurons/channels. The CBE isolates this heavy tail and
normalizes it into a discrete probability distribution for optimal Wasserstein comparison.
"""

from __future__ import annotations
from typing import Tuple
import numpy as np


def extract_cbe(
    energies: np.ndarray,
    top_k_percent: float = 0.10,
    epsilon: float = 1e-8,
) -> Tuple[np.ndarray, float]:
    """
    Extracts Concentrated Backdoor Energy (CBE) from filter energies.

    Parameters
    ----------
    energies : np.ndarray
        Array of filter/neuron energies.
    top_k_percent : float
        Fraction of top-energy neurons to extract (default: 0.10 = top 10%).
    epsilon : float
        Numerical stability constant.

    Returns
    -------
    Tuple[np.ndarray, float]
        (cbe_distribution, concentration_ratio)
        - cbe_distribution: 1D array of top-k energies, normalized to sum to 1.
        - concentration_ratio: fraction of total energy contained in the top-k tail.
    """
    if len(energies) == 0:
        return np.array([1.0], dtype=np.float64), 1.0

    # Sort descending
    sorted_energies = np.sort(energies)[::-1]
    total_energy = float(np.sum(sorted_energies))

    # Determine top-k count
    k = max(1, int(round(len(sorted_energies) * top_k_percent)))
    k = min(k, len(sorted_energies))

    cbe_tail = sorted_energies[:k].copy()
    cbe_sum = float(np.sum(cbe_tail))

    # Concentration ratio: energy in top tail vs total
    concentration_ratio = cbe_sum / (total_energy + epsilon)

    # Normalize CBE to a probability distribution (sums to 1.0)
    cbe_distribution = cbe_tail / (cbe_sum + epsilon)

    return cbe_distribution, concentration_ratio
