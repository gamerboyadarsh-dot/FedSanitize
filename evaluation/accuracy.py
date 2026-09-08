"""
FedSanitize — Evaluation: Clean Accuracy & Model Performance
============================================================
Calculates global model loss and top-1 accuracy on clean validation/test data.
"""

from __future__ import annotations
from typing import Tuple, Dict, Any
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


def evaluate_clean_accuracy(
    model: nn.Module,
    dataset: Dataset,
    batch_size: int = 128,
    device: str = "cpu",
) -> Tuple[float, float]:
    """
    Evaluates model on clean dataset.

    Returns
    -------
    Tuple[float, float]
        (average_loss, accuracy_percentage)
    """
    model.eval()
    model.to(device)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    criterion = nn.CrossEntropyLoss()

    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

    avg_loss = total_loss / max(total, 1)
    accuracy = (correct / max(total, 1)) * 100.0
    return float(avg_loss), float(accuracy)
