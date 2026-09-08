"""
FedSanitize — Attack C: Random Byzantine (Byzantine Outlier)
============================================================
Injects random noise vectors matching exact model tensor shapes.
Operates on actual PyTorch tensors with configurable variance / scale.
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


def apply_random_byzantine(
    update: ClientUpdate,
    global_state_dict: Dict[str, torch.Tensor],
    scale: float = 5.0,
    seed: int | None = None,
) -> ClientUpdate:
    """
    Generates random tensor noise matching exact parameter shapes:
    ΔWi_malicious ~ N(0, scale^2)
    """
    generator = None
    if seed is not None:
        generator = torch.Generator().manual_seed(seed)

    byzantine_delta: Dict[str, torch.Tensor] = {}
    for key, tensor in global_state_dict.items():
        if tensor.is_floating_point():
            noise = torch.randn(tensor.shape, generator=generator, device=tensor.device) * scale
            byzantine_delta[key] = noise.to(dtype=tensor.dtype)
        else:
            # For non-float tensors (like integer buffers), keep unchanged
            byzantine_delta[key] = torch.zeros_like(tensor)

    new_local_state = apply_delta(global_state_dict, byzantine_delta)

    metadata = dict(update.metadata)
    metadata["attack"] = "random_byzantine"
    metadata["scale"] = scale
    metadata["l2_norm"] = compute_l2_norm(byzantine_delta)

    return ClientUpdate(
        client_id=update.client_id,
        state_dict=new_local_state,
        delta=byzantine_delta,
        num_samples=update.num_samples,
        is_malicious=True,
        attack_type="RANDOM_BYZANTINE",
        metadata=metadata,
    )
