"""
FedSanitize — Model Update Utilities
=====================================
Calculates parameter deltas: ΔWi = Wi_local - W_global
Provides vector flattening, unflattening, and norm computations for state dicts.
Operates on actual PyTorch tensors with strict shape, dtype, and device preservation.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import torch


def compute_delta(
    local_state: Dict[str, torch.Tensor],
    global_state: Dict[str, torch.Tensor],
) -> Dict[str, torch.Tensor]:
    """
    Computes parameter delta: ΔWi = Wi_local - W_global.
    
    Returns a dictionary of tensors with identical keys and shapes.
    """
    delta: Dict[str, torch.Tensor] = {}
    for key in global_state.keys():
        if key in local_state:
            delta[key] = (local_state[key] - global_state[key]).detach().clone()
        else:
            raise KeyError(f"Key '{key}' found in global_state but missing in local_state.")
    return delta


def apply_delta(
    global_state: Dict[str, torch.Tensor],
    delta: Dict[str, torch.Tensor],
    step_size: float = 1.0,
) -> Dict[str, torch.Tensor]:
    """
    Applies an aggregated update delta to global_state:
    W_new = W_old + step_size * ΔW
    """
    updated_state: Dict[str, torch.Tensor] = {}
    for key, param in global_state.items():
        if key in delta:
            updated_state[key] = (param + step_size * delta[key].to(param.device)).detach().clone()
        else:
            updated_state[key] = param.detach().clone()
    return updated_state


def flatten_state_dict(
    state_dict: Dict[str, torch.Tensor],
    keys: List[str] | None = None,
) -> torch.Tensor:
    """
    Flattens a subset or all tensors in a state_dict into a single 1D continuous tensor.
    Useful for cosine similarity, L2 norm, and clustering representations.
    """
    target_keys = keys if keys is not None else list(state_dict.keys())
    flat_parts = []
    for k in target_keys:
        if k in state_dict:
            flat_parts.append(state_dict[k].detach().reshape(-1))
    if not flat_parts:
        return torch.empty(0)
    return torch.cat(flat_parts)


def unflatten_to_state_dict(
    flat_vector: torch.Tensor,
    reference_state_dict: Dict[str, torch.Tensor],
    keys: List[str] | None = None,
) -> Dict[str, torch.Tensor]:
    """
    Restores a flat 1D tensor back into a structured state_dict matching reference shapes.
    """
    target_keys = keys if keys is not None else list(reference_state_dict.keys())
    restored: Dict[str, torch.Tensor] = {}
    offset = 0
    for k in target_keys:
        ref_tensor = reference_state_dict[k]
        num_elements = ref_tensor.numel()
        slice_tensor = flat_vector[offset : offset + num_elements].view(ref_tensor.shape)
        restored[k] = slice_tensor.clone().to(dtype=ref_tensor.dtype, device=ref_tensor.device)
        offset += num_elements
    return restored


def compute_l2_norm(delta: Dict[str, torch.Tensor]) -> float:
    """
    Computes global L2 norm across all parameter tensors in delta:
    ||ΔWi||_2 = sqrt(sum_k ||ΔWi_k||_2^2)
    """
    total_sq = sum(torch.sum(p.float() ** 2).item() for p in delta.values())
    return float(total_sq ** 0.5)
