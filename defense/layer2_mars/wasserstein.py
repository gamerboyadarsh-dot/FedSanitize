"""
FedSanitize — MARS Step 4: Pairwise Wasserstein Distance Matrix
==============================================================
Computes pairwise Earth Mover's (Wasserstein-1) distances between the
Concentrated Backdoor Energy distributions of all surviving clients.

Reference: Wan et al., NeurIPS 2025 (arXiv:2509.20383)
Uses scipy.stats.wasserstein_distance to measure geometric distribution divergence
augmented with CBE energy concentration disparity.
"""

from __future__ import annotations
from typing import List, Optional
import numpy as np
from scipy.stats import wasserstein_distance


def compute_pairwise_wasserstein_matrix(
    cbe_distributions: List[np.ndarray],
    cbe_concentration_ratios: Optional[List[float]] = None,
    ratio_weight: float = 1.0,
) -> np.ndarray:
    """
    Constructs a symmetric N x N pairwise distance matrix where:
    D[i, j] = W_1(CBE_i, CBE_j) + ratio_weight * |ratio_i - ratio_j|

    Parameters
    ----------
    cbe_distributions : List[np.ndarray]
        List of 1D normalized CBE distributions, one per client.
    cbe_concentration_ratios : Optional[List[float]]
        Optional concentration ratios (top-k energy / total energy).
    ratio_weight : float
        Scaling weight for concentration ratio differences (default: 1.0).

    Returns
    -------
    np.ndarray
        Symmetric N x N distance matrix with zero diagonal.
    """
    n = len(cbe_distributions)
    dist_matrix = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        for j in range(i + 1, n):
            u = cbe_distributions[i]
            v = cbe_distributions[j]
            dist = float(wasserstein_distance(u, v))
            if cbe_concentration_ratios is not None:
                dist += ratio_weight * abs(cbe_concentration_ratios[i] - cbe_concentration_ratios[j])
            dist_matrix[i, j] = dist
            dist_matrix[j, i] = dist

    return dist_matrix
