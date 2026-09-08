"""
FedSanitize — Serialization & State Dictionary Helpers
======================================================
Provides utilities for safe cloning, CPU detaching, and persistence of
PyTorch model weights and state dictionaries.
"""

import os
import copy
import json
import torch
from typing import Dict, Any, Optional


def clone_state_dict(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Safely clones and detaches a PyTorch state_dict."""
    return {k: v.detach().clone() for k, v in state_dict.items()}


def state_dict_to_device(
    state_dict: Dict[str, torch.Tensor],
    device: str = "cpu"
) -> Dict[str, torch.Tensor]:
    """Moves all tensors in a state_dict to the specified device."""
    return {k: v.to(device) for k, v in state_dict.items()}


def save_checkpoint(
    state_dict: Dict[str, torch.Tensor],
    filepath: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Saves a model state dictionary and optional metadata to disk."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    payload = {
        "state_dict": {k: v.cpu() for k, v in state_dict.items()},
        "metadata": metadata or {}
    }
    torch.save(payload, filepath)


def load_checkpoint(
    filepath: str,
    device: str = "cpu"
) -> Dict[str, Any]:
    """Loads a model checkpoint from disk."""
    checkpoint = torch.load(filepath, map_location=device)
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        checkpoint["state_dict"] = state_dict_to_device(checkpoint["state_dict"], device)
        return checkpoint
    return {"state_dict": state_dict_to_device(checkpoint, device), "metadata": {}}


def save_json(data: Any, filepath: str) -> None:
    """Serializes a Python structure to JSON, ensuring parent directories exist."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(filepath: str) -> Any:
    """Loads a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
