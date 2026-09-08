"""
FedSanitize — MARS Step 2: Backdoor Energy
===========================================
Computes the energy distribution across individual filters / neurons in the
selected representation layer.

Reference: Wan et al., NeurIPS 2025 (arXiv:2509.20383)
Backdoored models manipulate specific latent pathways, concentrating energy
in particular filters/neurons. Crucially, the full energy vector is preserved
rather than collapsed to a scalar.
"""

from __future__ import annotations
from typing import Dict, List
import numpy as np
import torch


def compute_filter_energies(
    delta: Dict[str, torch.Tensor],
    target_layers: List[str],
) -> np.ndarray:
    """
    Computes per-filter / per-neuron L2 energy across the specified layers.

    Parameters
    ----------
    delta : Dict[str, torch.Tensor]
        Client parameter update delta.
    target_layers : List[str]
        List of layer keys selected for energy inspection.

    Returns
    -------
    np.ndarray
        1D array of energies, one per output filter/neuron.
    """
    energies: List[float] = []

    for layer_key in target_layers:
        if layer_key not in delta:
            continue

        tensor = delta[layer_key].float()
        # For Conv2d: (out_channels, in_channels, k_h, k_w)
        # Compute L2 norm per output channel/filter:
        if tensor.ndim >= 2:
            out_dim = tensor.shape[0]
            # Flatten all trailing dimensions: (out_dim, -1)
            reshaped = tensor.view(out_dim, -1)
            channel_norms = torch.norm(reshaped, p=2, dim=1)
            energies.extend(channel_norms.cpu().numpy().tolist())
        else:
            # 1D tensor (e.g. bias or flat weights)
            energies.extend(torch.abs(tensor).cpu().numpy().tolist())

    if not energies:
        return np.zeros(1, dtype=np.float64)

    return np.array(energies, dtype=np.float64)
