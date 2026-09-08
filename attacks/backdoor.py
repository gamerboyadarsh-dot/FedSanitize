"""
FedSanitize — Attack E: Image-Trigger Backdoor Attack
=====================================================
Injects a trigger pattern (white square at bottom-right) into a subset of
malicious clients' local training samples and reassigns their label to target_class.
Maintains clean and triggered test sets independently to evaluate Clean Accuracy and ASR.
"""

from __future__ import annotations
from typing import Tuple, List, Optional
import numpy as np
import torch
from torch.utils.data import Dataset


def add_trigger(
    image: torch.Tensor,
    trigger_size: int = 4,
    trigger_val: float = 2.8215,  # Normalized 1.0 on MNIST: (1.0 - 0.1307)/0.3081
    position: str = "bottom_right",
) -> torch.Tensor:
    """
    Injects a white square trigger into a 1x28x28 or 28x28 image tensor.
    """
    triggered = image.clone()
    # Image shape can be (C, H, W) or (H, W)
    if triggered.ndim == 3:
        h, w = triggered.shape[1], triggered.shape[2]
        if position == "bottom_right":
            triggered[:, h - trigger_size : h, w - trigger_size : w] = trigger_val
        elif position == "top_left":
            triggered[:, 0:trigger_size, 0:trigger_size] = trigger_val
    elif triggered.ndim == 2:
        h, w = triggered.shape[0], triggered.shape[1]
        if position == "bottom_right":
            triggered[h - trigger_size : h, w - trigger_size : w] = trigger_val
        elif position == "top_left":
            triggered[0:trigger_size, 0:trigger_size] = trigger_val
    return triggered


class BackdoorDataset(Dataset):
    """
    Poisoned training dataset for malicious clients.
    A fraction (poison_ratio) of samples are injected with the trigger and target class.
    """
    def __init__(
        self,
        base_dataset: Dataset,
        poison_ratio: float = 0.30,
        target_class: int = 0,
        trigger_size: int = 4,
        seed: int = 42,
    ):
        self.base_dataset = base_dataset
        self.poison_ratio = poison_ratio
        self.target_class = target_class
        self.trigger_size = trigger_size

        total_samples = len(base_dataset)
        num_poisoned = int(total_samples * poison_ratio)

        rng = np.random.default_rng(seed)
        all_indices = np.arange(total_samples)
        rng.shuffle(all_indices)
        self.poisoned_indices = set(all_indices[:num_poisoned].tolist())

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        image, label = self.base_dataset[idx]
        if isinstance(label, torch.Tensor):
            label = int(label.item())

        if idx in self.poisoned_indices:
            # Poison sample
            triggered_image = add_trigger(image, trigger_size=self.trigger_size)
            return triggered_image, self.target_class
        return image, label


class TriggeredTestDataset(Dataset):
    """
    Evaluation dataset where ALL samples (excluding original target class instances,
    or across all samples) have the trigger stamped to measure Attack Success Rate (ASR).
    """
    def __init__(
        self,
        base_dataset: Dataset,
        target_class: int = 0,
        trigger_size: int = 4,
        exclude_target_class: bool = True,
    ):
        self.samples: List[Tuple[torch.Tensor, int]] = []
        for i in range(len(base_dataset)):
            image, label = base_dataset[i]
            if isinstance(label, torch.Tensor):
                label = int(label.item())
            if exclude_target_class and label == target_class:
                continue  # Exclude natural target class samples so ASR only measures false flips
            triggered_image = add_trigger(image, trigger_size=trigger_size)
            self.samples.append((triggered_image, target_class))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        return self.samples[idx]


def evaluate_asr(
    model: torch.nn.Module,
    triggered_test_dataset: Dataset,
    batch_size: int = 256,
    device: str = "cpu",
) -> float:
    """
    Calculates Attack Success Rate (ASR):
    ASR = (samples predicted as target_class) / (total triggered samples) * 100%
    """
    from torch.utils.data import DataLoader

    model = model.to(device)
    model.eval()
    dataloader = DataLoader(triggered_test_dataset, batch_size=batch_size, shuffle=False)
    
    correct = 0
    total = len(triggered_test_dataset)
    if total == 0:
        return 0.0

    with torch.no_grad():
        for data, target in dataloader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()

    return float(100.0 * correct / total)
