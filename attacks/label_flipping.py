"""
FedSanitize — Attack A: Label Flipping (Data Poisoning)
======================================================
Modifies ground-truth labels of training samples per a configurable mapping
(e.g., 1 -> 7, 2 -> 5) exclusively on designated malicious clients' local data.
"""

from __future__ import annotations
from typing import Dict, Tuple
import torch
from torch.utils.data import Dataset


class LabelFlippedDataset(Dataset):
    """
    Wraps a dataset to flip class labels based on a target mapping dict.
    Leaves non-mapped classes untouched.
    """
    def __init__(self, base_dataset: Dataset, label_map: Dict[int, int]):
        self.base_dataset = base_dataset
        self.label_map = label_map

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        image, label = self.base_dataset[idx]
        if isinstance(label, torch.Tensor):
            label = int(label.item())
        new_label = self.label_map.get(label, label)
        return image, new_label


def apply_label_flipping(
    dataset: Dataset,
    label_map: Dict[int, int] | None = None,
) -> LabelFlippedDataset:
    """
    Creates a label-flipped view of the dataset.
    Default map: {1: 7, 2: 5}.
    """
    mapping = label_map if label_map is not None else {1: 7, 2: 5}
    return LabelFlippedDataset(dataset, mapping)
