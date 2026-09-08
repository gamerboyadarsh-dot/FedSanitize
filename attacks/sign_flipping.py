"""
FedSanitize — Attack B: Sign Flipping (Byzantine / Model Manipulation)
=====================================================================
Flips the sign of calculated parameter deltas:
ΔWi_malicious = -γ * ΔWi
Wi_malicious = W_global + ΔWi_malicious
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


def apply_sign_flipping(
    update: ClientUpdate,
    global_state_dict: Dict[str, torch.Tensor],
    gamma: float = 1.0,
) -> ClientUpdate:
    """
    Applies sign-flipping manipulation to a client update:
    ΔWi_malicious = -γ * ΔWi
    """
    flipped_delta: Dict[str, torch.Tensor] = {}
    for key, tensor in update.delta.items():
        flipped_delta[key] = (-gamma * tensor.float()).to(dtype=tensor.dtype)

    # Recompute corresponding local state: W_global + ΔW_flipped
    new_local_state = apply_delta(global_state_dict, flipped_delta)

    metadata = dict(update.metadata)
    metadata["attack"] = "sign_flipping"
    metadata["gamma"] = gamma
    metadata["l2_norm"] = compute_l2_norm(flipped_delta)

    return ClientUpdate(
        client_id=update.client_id,
        state_dict=new_local_state,
        delta=flipped_delta,
        num_samples=update.num_samples,
        is_malicious=True,
        attack_type="SIGN_FLIPPING",
        metadata=metadata,
    )
