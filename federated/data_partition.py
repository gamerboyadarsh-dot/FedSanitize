"""
FedSanitize — Data Partitioning & Loading Utilities
===================================================
Provides reproducible dataset partitioning for federated clients:
- IID (uniform distribution across clients, default for hackathon reliability)
- Non-IID (Dirichlet distribution over label distributions or class-sharding)

Includes MNIST loader helper with local caching.
"""

import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset, Subset
from torchvision import datasets, transforms


def get_mnist_datasets(data_dir: str = "./data") -> Tuple[Dataset, Dataset]:
    """
    Downloads/loads clean MNIST train and test sets with standard normalization.
    """
    os.makedirs(data_dir, exist_ok=True)
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_dataset = datasets.MNIST(root=data_dir, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root=data_dir, train=False, download=True, transform=transform)
    return train_dataset, test_dataset


def partition_data(
    dataset: Dataset,
    num_clients: int,
    iid: bool = True,
    alpha: float = 0.5,
    seed: int = 42
) -> Dict[int, Subset]:
    """
    Partitions a dataset into client-specific subsets.

    Parameters
    ----------
    dataset : Dataset
        PyTorch dataset to partition.
    num_clients : int
        Number of federated clients.
    iid : bool, default True
        If True, samples are uniformly distributed across clients (IID).
        If False, partition follows a Dirichlet distribution on labels (Non-IID).
    alpha : float, default 0.5
        Dirichlet concentration parameter for non-IID partitioning.
    seed : int, default 42
        Random seed for partition reproducibility.

    Returns
    -------
    Dict[int, Subset]
        Mapping from client_id (0..num_clients-1) to PyTorch Subset.
    """
    rng = np.random.default_rng(seed)
    num_samples = len(dataset)
    indices = np.arange(num_samples)

    if iid:
        rng.shuffle(indices)
        client_splits = np.array_split(indices, num_clients)
        client_partitions = {
            client_id: Subset(dataset, client_splits[client_id].tolist())
            for client_id in range(num_clients)
        }
    else:
        # Non-IID Dirichlet distribution over classes
        targets = np.array(dataset.targets if hasattr(dataset, "targets") else [y for _, y in dataset])
        num_classes = len(np.unique(targets))
        
        client_indices = [[] for _ in range(num_clients)]
        for k in range(num_classes):
            idx_k = np.where(targets == k)[0]
            rng.shuffle(idx_k)
            proportions = rng.dirichlet(np.repeat(alpha, num_clients))
            # Balance sample counts
            proportions = np.array([p * (len(idx_j) < num_samples / num_clients) for p, idx_j in zip(proportions, client_indices)])
            if proportions.sum() == 0:
                proportions = np.ones(num_clients) / num_clients
            else:
                proportions = proportions / proportions.sum()
            proportions = (np.cumsum(proportions) * len(idx_k)).astype(int)[:-1]
            split_idx = np.split(idx_k, proportions)
            for client_id in range(num_clients):
                client_indices[client_id].extend(split_idx[client_id].tolist())
                
        client_partitions = {
            client_id: Subset(dataset, client_indices[client_id])
            for client_id in range(num_clients)
        }

    return client_partitions
