"""
FedSanitize — Federated Learning Core Package
"""

from .data_partition import partition_data, get_mnist_datasets
from .client import FLClient, ClientUpdate
from .server import FLServer
from .trainer import train_local_model, evaluate_model
from .update_utils import (
    compute_delta,
    apply_delta,
    flatten_state_dict,
    unflatten_to_state_dict,
    compute_l2_norm,
)
from .baseline_aggregation import federated_averaging

__all__ = [
    "partition_data",
    "get_mnist_datasets",
    "FLClient",
    "ClientUpdate",
    "FLServer",
    "train_local_model",
    "evaluate_model",
    "compute_delta",
    "apply_delta",
    "flatten_state_dict",
    "unflatten_to_state_dict",
    "compute_l2_norm",
    "federated_averaging",
]
