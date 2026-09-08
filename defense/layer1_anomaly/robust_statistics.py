"""
FedSanitize — Robust Statistical Utilities for Layer 1 Anomaly Detection
========================================================================
Implements coordinate-wise median for PyTorch state dictionaries and
Median Absolute Deviation (MAD) for robust outlier detection.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
import torch


def compute_coordinate_wise_median(
    deltas: List[Dict[str, torch.Tensor]],
) -> Dict[str, torch.Tensor]:
    """
    Computes coordinate-wise median across multiple client update state dicts.
    
    This creates a robust reference update that is resilient to extreme
    outliers or Byzantine model poisoning (unlike arithmetic mean).
    """
    if not deltas:
        raise ValueError("Cannot compute median of empty deltas list.")
    if len(deltas) == 1:
        return {k: v.detach().clone() for k, v in deltas[0].items()}

    median_delta: Dict[str, torch.Tensor] = {}
    keys = deltas[0].keys()

    for key in keys:
        # Stack all tensors along dim 0: shape (N, ...)
        stacked = torch.stack([d[key].float() for d in deltas], dim=0)
        # torch.median returns (values, indices)
        med_val, _ = torch.median(stacked, dim=0)
        median_delta[key] = med_val.to(dtype=deltas[0][key].dtype)

    return median_delta


def compute_mad(values: List[float] | np.ndarray) -> Tuple[float, float]:
    """
    Computes the Median and Median Absolute Deviation (MAD):
    median_norm = median(values)
    MAD = median(|values - median_norm|)

    Returns
    -------
    Tuple[float, float]
        (median_value, mad_value)
    """
    arr = np.asarray(values, dtype=np.float64)
    if len(arr) == 0:
        return 0.0, 0.0
    median_val = float(np.median(arr))
    abs_deviations = np.abs(arr - median_val)
    mad = float(np.median(abs_deviations))
    return median_val, mad


def compute_normalized_norm_score(
    norm: float,
    median_norm: float,
    clip_max: float = 3.0,
    epsilon: float = 1e-8,
) -> float:
    """
    Computes a bounded [0, 1] norm anomaly score:
    raw = |norm - median_norm| / (median_norm + epsilon)
    score = min(raw, clip_max) / clip_max
    """
    raw = abs(norm - median_norm) / (median_norm + epsilon)
    score = min(raw, clip_max) / clip_max
    return float(np.clip(score, 0.0, 1.0))
