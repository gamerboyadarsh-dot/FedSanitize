"""
FedSanitize — Attack D: Extreme Update (Model Poisoning / Outlier Injection)
===========================================================================
Scales legitimate parameter deltas by a large factor γ:
ΔWi_malicious = γ * ΔWi
Wi_malicious = W_global + ΔWi_malicious

Specifically designed to test Layer 1 anomaly detection (L2 Norm & MAD).
"""

from __future__ import annotations
from typing import Dict
import torch

try:
    from ..federated.client import ClientUpdate
    from ..federated.update_utils import apply_delta, compute_l2_norm
except (ImportError, ValueError):
    from federated.client import ClientUpdate
    from federated.update_utils import apply_delta, compute_l2_norm


def apply_extreme_update(
    update: ClientUpdate,
    global_state_dict: Dict[str, torch.Tensor],
    gamma: float = 10.0,
) -> ClientUpdate:
    """
    Amplifies client delta by multiplier γ.
    """
    extreme_delta: Dict[str, torch.Tensor] = {}
    for key, tensor in update.delta.items():
        extreme_delta[key] = (gamma * tensor.float()).to(dtype=tensor.dtype)

    new_local_state = apply_delta(global_state_dict, extreme_delta)

    metadata = dict(update.metadata)
    metadata["attack"] = "extreme_update"
    metadata["gamma"] = gamma
    metadata["l2_norm"] = compute_l2_norm(extreme_delta)

    return ClientUpdate(
        client_id=update.client_id,
        state_dict=new_local_state,
        delta=extreme_delta,
        num_samples=update.num_samples,
        is_malicious=True,
        attack_type="EXTREME_UPDATE",
        metadata=metadata,
    )
