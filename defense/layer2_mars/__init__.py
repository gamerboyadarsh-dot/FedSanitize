"""
FedSanitize — Layer 2: MARS Backdoor Defense Package
====================================================
Grounded in: 'MARS: A Malignity-Aware Backdoor Defense in Federated Learning'
(Wei Wan et al., NeurIPS 2025, arXiv:2509.20383)
"""

from .layer_selection import select_target_layers
from .backdoor_energy import compute_filter_energies
from .cbe import extract_cbe
from .wasserstein import compute_pairwise_wasserstein_matrix
from .clustering import cluster_and_classify
from .mars import MARSDetector

__all__ = [
    "select_target_layers",
    "compute_filter_energies",
    "extract_cbe",
    "compute_pairwise_wasserstein_matrix",
    "cluster_and_classify",
    "MARSDetector",
]
