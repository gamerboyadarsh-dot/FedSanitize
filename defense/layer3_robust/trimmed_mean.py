"""
FedSanitize — Layer 3: Coordinate-wise Trimmed Mean Aggregation
===============================================================
Implements coordinate-wise trimmed mean (Yin et al., 2018) as the robust final
aggregation rule applied to the trusted client updates that survived Layers 1 & 2.

Key guarantees:
  - Vectorized PyTorch operations — no Python loops over parameters.
  - Strict shape, dtype, and device preservation for all output tensors.
  - Safety: validates trim_count vs client count and falls back gracefully.
  - Numerically stable: handles NaN/Inf inputs with explicit checks.
  - Deterministic: no randomness in the aggregation path.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Any
import logging
import torch

try:
    from ...federated.client import ClientUpdate
    from ...config import AggregationConfig
except (ImportError, ValueError):
    from federated.client import ClientUpdate
    from config import AggregationConfig

logger = logging.getLogger("FedSanitize.Layer3")


def coordinate_wise_trimmed_mean(
    client_updates: List[ClientUpdate],
    trim_ratio: float = 0.1,
    fallback_method: str = "coordinate_median",
    min_clients: int = 3,
) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
    """
    Computes coordinate-wise trimmed mean over a list of client updates.

    For each parameter coordinate, trims `trim_count` values from each tail and
    returns the mean of the remaining central values.

    Parameters
    ----------
    client_updates : List[ClientUpdate]
        Surviving client updates (after Layers 1 & 2).
    trim_ratio : float
        Fraction of values to trim from each tail (e.g. 0.1 = 10%).
    fallback_method : str
        "coordinate_median" or "mean" — used when trimmed mean is unsafe.
    min_clients : int
        Minimum clients required to avoid fallback.

    Returns
    -------
    Tuple[Dict[str, torch.Tensor], Dict[str, Any]]
        (aggregated_delta, aggregation_metadata)
    """
    n = len(client_updates)
    if n == 0:
        raise ValueError("Cannot aggregate empty client_updates list.")

    if trim_ratio <= 0.0:
        trim_count = 0
    else:
        trim_count = int(round(n * trim_ratio))
        if trim_count == 0 and n >= 3:
            trim_count = 1

    metadata: Dict[str, Any] = {
        "num_clients": n,
        "trim_ratio": trim_ratio,
        "trim_count": trim_count,
        "method_used": "coordinate_trimmed_mean",
        "warnings": [],
    }

    # Safety check: trimmed mean requires n > 2 * trim_count
    if n <= 2 * trim_count:
        logger.warning(
            f"[Layer 3 Warning] Not enough clients ({n}) for trim_count={trim_count}. "
            f"Falling back to '{fallback_method}'."
        )
        metadata["warnings"].append(
            f"Trim unsafe: n={n}, trim_count={trim_count}. Fallback: {fallback_method}."
        )
        trim_count = 0
        metadata["method_used"] = fallback_method

    # NaN/Inf guard: detect and warn
    def check_for_invalid(d: Dict[str, torch.Tensor], cid: str) -> bool:
        for k, v in d.items():
            if not torch.isfinite(v).all():
                logger.warning(
                    f"[Layer 3 Warning] Client {cid} has NaN/Inf in key '{k}'. "
                    f"Excluding from aggregation."
                )
                return True
        return False

    clean_updates = [
        u for u in client_updates
        if not check_for_invalid(u.delta, u.client_id)
    ]

    if not clean_updates:
        raise ValueError("All client updates contain NaN/Inf values. Cannot aggregate.")

    n_clean = len(clean_updates)
    if n_clean < n:
        metadata["warnings"].append(
            f"{n - n_clean} client(s) excluded due to NaN/Inf values."
        )

    # Re-evaluate trim after excluding bad clients
    if n_clean <= 2 * trim_count:
        trim_count = 0
        metadata["method_used"] = fallback_method
        metadata["warnings"].append(
            f"Trim count reset to 0 after NaN exclusion (n_clean={n_clean})."
        )

    # Build aggregated delta
    reference_delta = clean_updates[0].delta
    aggregated: Dict[str, torch.Tensor] = {}

    for key, ref_tensor in reference_delta.items():
        original_shape = ref_tensor.shape
        original_dtype = ref_tensor.dtype
        original_device = ref_tensor.device

        # Stack updates: shape (n_clean, *original_shape)
        stacked = torch.stack(
            [u.delta[key].float().to(original_device) for u in clean_updates],
            dim=0,
        )

        if metadata["method_used"] == "coordinate_trimmed_mean" and trim_count > 0:
            # Sort along client axis (dim=0) for coordinate-wise trimming
            sorted_vals, _ = torch.sort(stacked, dim=0)
            trimmed = sorted_vals[trim_count : n_clean - trim_count]
            result = trimmed.mean(dim=0)
        elif metadata["method_used"] == "coordinate_median":
            result, _ = torch.median(stacked, dim=0)
        else:
            # Plain mean fallback
            result = stacked.mean(dim=0)

        # Restore original shape, dtype, and device
        aggregated[key] = result.view(original_shape).to(dtype=original_dtype, device=original_device)

    metadata["n_clean_clients"] = n_clean
    metadata["trim_count_applied"] = trim_count

    return aggregated, metadata


class Layer3RobustAggregator:
    """
    Wrapper for Layer 3 coordinate-wise trimmed mean aggregation.
    Accepts AggregationConfig and delegates to coordinate_wise_trimmed_mean.
    """
    def __init__(self, config: AggregationConfig | None = None):
        self.config = config if config is not None else AggregationConfig()

    def aggregate(
        self,
        trusted_updates: List[ClientUpdate],
        global_state_dict: Dict[str, torch.Tensor],
    ) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
        """
        Aggregates trusted updates via trimmed mean and applies them to the global model.
        Returns (new_global_state_dict, aggregation_metadata).
        """
        agg_delta, metadata = coordinate_wise_trimmed_mean(
            client_updates=trusted_updates,
            trim_ratio=self.config.trim_ratio,
            fallback_method=self.config.fallback_method,
            min_clients=self.config.min_clients_for_trimmed_mean,
        )

        # Apply delta to global state: W_new = W_global + delta
        new_state: Dict[str, torch.Tensor] = {}
        for key, param in global_state_dict.items():
            if key in agg_delta:
                new_state[key] = (param.float() + agg_delta[key].float()).to(
                    dtype=param.dtype, device=param.device
                )
            else:
                new_state[key] = param.detach().clone()

        metadata["applied_to_global"] = True
        return new_state, metadata
