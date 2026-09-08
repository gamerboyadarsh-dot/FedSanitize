"""
FedSanitize — Central Federated Server
======================================
Coordinates model distribution, update collection, evaluation,
and baseline aggregation.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Callable, Optional
import torch
import torch.nn as nn
from torch.utils.data import Dataset

from .client import ClientUpdate
from .baseline_aggregation import federated_averaging
from .trainer import evaluate_model

try:
    from ..models.cnn import SmallCNN
    from ..utils.serialization import clone_state_dict
except (ImportError, ValueError):
    from models.cnn import SmallCNN
    from utils.serialization import clone_state_dict


class FLServer:
    """
    Central coordinator for Federated Learning rounds.
    Maintains the authoritative global model state.
    """
    def __init__(
        self,
        model: Optional[nn.Module] = None,
        device: str = "cpu",
    ):
        self.device = device
        self.model = model if model is not None else SmallCNN()
        self.model.to(self.device)
        self.current_round: int = 0

    def get_global_state_dict(self) -> Dict[str, torch.Tensor]:
        """Returns an independent clone of the current global model state."""
        return clone_state_dict(self.model.state_dict())

    def update_global_model(self, new_state_dict: Dict[str, torch.Tensor]) -> None:
        """Updates the global model in-place with new parameters."""
        self.model.load_state_dict(new_state_dict)

    def aggregate_baseline(
        self,
        client_updates: List[ClientUpdate],
    ) -> Dict[str, torch.Tensor]:
        """
        Aggregates client updates using baseline FedAvg and updates the global model.
        """
        current_state = self.get_global_state_dict()
        new_state, _ = federated_averaging(client_updates, current_state)
        self.update_global_model(new_state)
        self.current_round += 1
        return new_state

    def evaluate(
        self,
        test_dataset: Dataset,
        batch_size: int = 256,
    ) -> Tuple[float, float]:
        """
        Evaluates the global model on a given dataset (e.g. clean test set).
        Returns (loss, accuracy_percentage).
        """
        return evaluate_model(
            model=self.model,
            dataset=test_dataset,
            batch_size=batch_size,
            device=self.device,
        )
