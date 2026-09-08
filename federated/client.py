"""
FedSanitize — Federated Client Representation & Update Dataclass
================================================================
Defines FLClient and the ClientUpdate dataclass per PART 1 specifications.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import torch
import torch.nn as nn
from torch.utils.data import Dataset

from .trainer import train_local_model
from .update_utils import compute_delta, compute_l2_norm

try:
    from ..models.cnn import SmallCNN
except (ImportError, ValueError):
    from models.cnn import SmallCNN


@dataclass
class ClientUpdate:
    """
    Structured container for client model update returned to the server.
    Ensures defense layers inspect actual tensors and state dicts.
    """
    client_id: str
    state_dict: Dict[str, torch.Tensor]
    delta: Dict[str, torch.Tensor]
    num_samples: int
    is_malicious: bool = False
    attack_type: str = "NONE"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def update_norm(self) -> float:
        """Convenience property for global L2 norm of the update delta."""
        return compute_l2_norm(self.delta)


class FLClient:
    """
    Simulated Federated Learning Client.
    Responsible for local training on its data partition and delta computation.
    """
    def __init__(
        self,
        client_id: str | int,
        dataset: Dataset,
        is_malicious: bool = False,
        attack_type: str = "NONE",
    ):
        self.client_id = f"C{client_id}" if isinstance(client_id, int) else str(client_id)
        self.dataset = dataset
        self.is_malicious = is_malicious
        self.attack_type = attack_type

    def train(
        self,
        global_state_dict: Dict[str, torch.Tensor],
        model_cls: type[nn.Module] = SmallCNN,
        epochs: int = 2,
        batch_size: int = 64,
        lr: float = 0.01,
        momentum: float = 0.9,
        device: str = "cpu",
        custom_dataset: Optional[Dataset] = None,
    ) -> ClientUpdate:
        """
        Loads global model parameters, performs local training, computes delta,
        and packages a ClientUpdate.
        """
        training_data = custom_dataset if custom_dataset is not None else self.dataset
        num_samples = len(training_data)

        # Instantiate fresh local model initialized with global parameters
        local_model = model_cls()
        local_model.load_state_dict(global_state_dict)

        # Train local model
        local_state, loss = train_local_model(
            model=local_model,
            dataset=training_data,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            momentum=momentum,
            device=device,
        )

        # Compute delta: ΔWi = Wi_local - W_global
        delta = compute_delta(local_state=local_state, global_state=global_state_dict)

        metadata = {
            "train_loss": loss,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": lr,
            "l2_norm": compute_l2_norm(delta),
        }

        return ClientUpdate(
            client_id=self.client_id,
            state_dict=local_state,
            delta=delta,
            num_samples=num_samples,
            is_malicious=self.is_malicious,
            attack_type=self.attack_type,
            metadata=metadata,
        )
