"""
FedSanitize — Layer 1 Feature Extraction
========================================
Extracts statistical features from client parameter updates:
- Feature A: Global L2 Update Norm
- Feature B: Directional Cosine Similarity vs. Robust Coordinate-wise Median Reference
- Feature C: Median Absolute Deviation (MAD) & Bounded Norm Deviation Scores
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import torch
import torch.nn.functional as F

try:
    from ...federated.client import ClientUpdate
    from ...federated.update_utils import flatten_state_dict, compute_l2_norm
except (ImportError, ValueError):
    from federated.client import ClientUpdate
    from federated.update_utils import flatten_state_dict, compute_l2_norm

from .robust_statistics import (
    compute_coordinate_wise_median,
    compute_mad,
    compute_normalized_norm_score,
)


def extract_client_features(
    client_updates: List[ClientUpdate],
    use_robust_reference: bool = True,
    epsilon: float = 1e-8,
) -> Dict[str, Dict[str, float]]:
    """
    Computes all Layer 1 diagnostic features for a list of client updates.

    Returns
    -------
    Dict[str, Dict[str, float]]
        Mapping of client_id -> {
            "update_norm": float,
            "cosine_similarity": float,
            "norm_score": float,
            "median_norm": float,
            "mad": float,
        }
    """
    if not client_updates:
        return {}

    # 1. Feature A: L2 Norms
    norms = [u.update_norm for u in client_updates]
    median_norm, mad = compute_mad(norms)

    # 2. Robust Reference Delta
    if use_robust_reference and len(client_updates) > 1:
        ref_delta = compute_coordinate_wise_median([u.delta for u in client_updates])
    else:
        ref_delta = client_updates[0].delta

    ref_flat = flatten_state_dict(ref_delta).float()
    ref_norm = torch.norm(ref_flat).item()

    # 3. Compute per-client cosine similarity and bounded norm score
    features: Dict[str, Dict[str, float]] = {}

    for update, norm in zip(client_updates, norms):
        client_flat = flatten_state_dict(update.delta).float()
        client_norm = torch.norm(client_flat).item()

        if client_norm > epsilon and ref_norm > epsilon:
            cos_sim = float(
                F.cosine_similarity(
                    client_flat.unsqueeze(0),
                    ref_flat.unsqueeze(0),
                    eps=epsilon,
                ).item()
            )
        else:
            cos_sim = 0.0

        norm_score = compute_normalized_norm_score(norm, median_norm, epsilon=epsilon)

        features[update.client_id] = {
            "update_norm": float(norm),
            "cosine_similarity": float(cos_sim),
            "norm_score": float(norm_score),
            "median_norm": float(median_norm),
            "mad": float(mad),
        }

    return features
