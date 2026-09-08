"""
FedSanitize — Baseline Federated Aggregation (FedAvg)
=====================================================
Standard Federated Averaging (McMahan et al., 2017).
Computes sample-weighted average of client parameter updates.
"""

from __future__ import annotations
from typing import List, Dict, Tuple
import torch

from .client import ClientUpdate
from .update_utils import apply_delta


def federated_averaging(
    client_updates: List[ClientUpdate],
    global_state_dict: Dict[str, torch.Tensor],
) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]:
    """
    Standard FedAvg aggregation.
    
    Parameters
    ----------
    client_updates : List[ClientUpdate]
        List of client updates to aggregate.
    global_state_dict : Dict[str, torch.Tensor]
        Current global model state dictionary.

    Returns
    -------
    Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]
        (updated_global_state_dict, aggregated_delta)
    """
    if not client_updates:
        raise ValueError("Cannot aggregate empty client_updates list.")

    total_samples = sum(u.num_samples for u in client_updates)
    if total_samples <= 0:
        total_samples = len(client_updates)
        weights = [1.0 / len(client_updates)] * len(client_updates)
    else:
        weights = [u.num_samples / total_samples for u in client_updates]

    # Initialize aggregated delta with zeros shaped like first update
    first_delta = client_updates[0].delta
    aggregated_delta: Dict[str, torch.Tensor] = {}

    for key, tensor in first_delta.items():
        accum = torch.zeros_like(tensor, dtype=torch.float32)
        for update, w in zip(client_updates, weights):
            accum += w * update.delta[key].to(accum.device).float()
        aggregated_delta[key] = accum.to(dtype=tensor.dtype)

    # Apply aggregated delta: W_new = W_old + ΔW
    updated_global_state = apply_delta(global_state_dict, aggregated_delta)
    return updated_global_state, aggregated_delta
