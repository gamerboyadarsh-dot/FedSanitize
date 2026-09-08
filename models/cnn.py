"""
FedSanitize — Lightweight CNN Model for MNIST
==============================================
Architecture:
Conv2D -> ReLU -> MaxPool -> Conv2D -> ReLU -> MaxPool -> Flatten -> Linear -> ReLU -> Linear (output)

Optimized for rapid CPU training during local federated rounds.
"""

import torch
import torch.nn as nn
from typing import Optional, Dict


class SmallCNN(nn.Module):
    """
    Lightweight 2-stage CNN for MNIST digits classification.
    Designed for fast CPU training in local federated simulation.
    """
    def __init__(
        self,
        in_channels: int = 1,
        num_classes: int = 10,
        conv1_channels: int = 32,
        conv2_channels: int = 64,
        fc_hidden: int = 128,
        dropout_rate: float = 0.25,
    ):
        super().__init__()
        
        self.conv1 = nn.Conv2d(in_channels, conv1_channels, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)  # 28x28 -> 14x14
        
        self.conv2 = nn.Conv2d(conv1_channels, conv2_channels, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)  # 14x14 -> 7x7
        
        self.flatten = nn.Flatten()
        flat_dim = conv2_channels * 7 * 7  # 64 * 49 = 3136
        
        self.fc1 = nn.Linear(flat_dim, fc_hidden)
        self.relu3 = nn.ReLU()
        self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else nn.Identity()
        self.fc2 = nn.Linear(fc_hidden, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool1(self.relu1(self.conv1(x)))
        x = self.pool2(self.relu2(self.conv2(x)))
        x = self.flatten(x)
        x = self.relu3(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

    def get_layer_weights(self) -> Dict[str, torch.Tensor]:
        """Returns detached clones of all trainable weights."""
        return {k: v.detach().clone() for k, v in self.state_dict().items()}
