"""
FedSanitize — Evaluation: Attack Success Rate (ASR)
===================================================
Evaluates the backdoor Attack Success Rate (ASR) on triggered test images.
ASR measures the percentage of triggered samples classified as the target class.
"""

from __future__ import annotations
from typing import Tuple, Dict, Any
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


def evaluate_backdoor_asr(
    model: nn.Module,
    triggered_dataset: Dataset,
    target_class: int = 0,
    batch_size: int = 128,
    device: str = "cpu",
) -> float:
    """
    Computes Attack Success Rate (ASR) on triggered test images.

    Returns
    -------
    float
        ASR percentage (0.0 to 100.0).
    """
    model.eval()
    model.to(device)
    loader = DataLoader(triggered_dataset, batch_size=batch_size, shuffle=False)

    target_matches = 0
    total_samples = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            outputs = model(images)
            preds = outputs.argmax(dim=1)
            target_matches += (preds == target_class).sum().item()
            total_samples += images.size(0)

    asr = (target_matches / max(total_samples, 1)) * 100.0
    return float(asr)
