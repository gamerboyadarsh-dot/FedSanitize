"""
FedSanitize — MARS Step 1: Layer Selection
===========================================
Identifies and extracts the target representation-bearing layers from client
model updates for backdoor energy analysis.

Reference: Wan et al., NeurIPS 2025 (arXiv:2509.20383)
Focuses on deep representation layers (convolutional filters / feature extractor)
where backdoor triggers imprint distinct neuron activation signatures.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import torch
import logging

logger = logging.getLogger("FedSanitize.MARS.LayerSelection")


def select_target_layers(
    state_dict: Dict[str, torch.Tensor],
    configured_layers: Optional[List[str]] = None,
) -> List[str]:
    """
    Selects layers for MARS backdoor energy analysis.

    Parameters
    ----------
    state_dict : Dict[str, torch.Tensor]
        Reference parameter state dict or delta dict.
    configured_layers : Optional[List[str]]
        Explicit list of layer weight keys to inspect.
        If None, automatically selects the deepest convolutional or linear weight layer.

    Returns
    -------
    List[str]
        List of selected parameter tensor keys.
    """
    if configured_layers:
        valid_keys = [k for k in configured_layers if k in state_dict]
        if valid_keys:
            return valid_keys
        logger.warning(
            f"None of configured_layers {configured_layers} found in state_dict. "
            f"Falling back to automatic layer selection."
        )

    # Auto-detection: prioritize the deepest 2D conv layer weights
    conv_keys = [
        k for k in state_dict.keys()
        if "conv" in k and "weight" in k and state_dict[k].ndim == 4
    ]
    if conv_keys:
        # Select the deepest conv layer (e.g. 'conv2.weight')
        return [conv_keys[-1]]

    # Fallback to linear layers (e.g. 'fc1.weight')
    fc_keys = [
        k for k in state_dict.keys()
        if ("fc" in k or "linear" in k) and "weight" in k and state_dict[k].ndim == 2
    ]
    if fc_keys:
        return [fc_keys[0]]

    # Fallback to any 2D+ floating point weight
    candidate_keys = [
        k for k in state_dict.keys()
        if "weight" in k and state_dict[k].ndim >= 2
    ]
    if candidate_keys:
        return [candidate_keys[0]]

    # Final fallback: return first key
    return [list(state_dict.keys())[0]]
