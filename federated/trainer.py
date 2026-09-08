"""
FedSanitize — Local Client Trainer & Evaluation
===============================================
Executes client-side local training rounds using PyTorch and standard SGD.
Optimized for rapid execution on CPU during federated rounds.
"""

from __future__ import annotations
from typing import Dict, Tuple, Optional
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


def train_local_model(
    model: nn.Module,
    dataset: Dataset,
    epochs: int = 2,
    batch_size: int = 64,
    lr: float = 0.01,
    momentum: float = 0.9,
    device: str = "cpu",
) -> Tuple[Dict[str, torch.Tensor], float]:
    """
    Trains a local copy of the model on the client's local dataset.
    
    Parameters
    ----------
    model : nn.Module
        Initialized with global model weights.
    dataset : Dataset
        Client local training dataset.
    epochs : int
        Number of local training epochs.
    batch_size : int
        Local batch size.
    lr : float
        Learning rate.
    momentum : float
        SGD momentum.
    device : str
        Target device ("cpu" or "cuda").

    Returns
    -------
    Tuple[Dict[str, torch.Tensor], float]
        (updated_state_dict, average_training_loss)
    """
    model = model.to(device)
    model.train()
    
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=momentum)
    criterion = nn.CrossEntropyLoss()
    
    total_loss = 0.0
    total_batches = 0
    
    for _ in range(epochs):
        for data, target in dataloader:
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            total_batches += 1
            
    avg_loss = total_loss / max(1, total_batches)
    local_state_dict = {k: v.detach().clone().cpu() for k, v in model.state_dict().items()}
    return local_state_dict, avg_loss


def evaluate_model(
    model: nn.Module,
    dataset: Dataset,
    batch_size: int = 256,
    device: str = "cpu",
) -> Tuple[float, float]:
    """
    Evaluates model on a dataset.
    
    Returns
    -------
    Tuple[float, float]
        (test_loss, accuracy_percentage)
    """
    model = model.to(device)
    model.eval()
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    criterion = nn.CrossEntropyLoss(reduction="sum")
    
    test_loss = 0.0
    correct = 0
    total = len(dataset)
    
    if total == 0:
        return 0.0, 0.0

    with torch.no_grad():
        for data, target in dataloader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += criterion(output, target).item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()

    avg_loss = test_loss / total
    accuracy = 100.0 * correct / total
    return avg_loss, accuracy
