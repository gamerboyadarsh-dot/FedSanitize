"""
FedSanitize — Adversarial Attack Simulations
=============================================
Implements five attack strategies with a modular interface:
- Attack A: Label Flipping (Data Poisoning)
- Attack B: Sign Flipping (Byzantine Manipulation)
- Attack C: Random Byzantine (Tensor-shaped Noise)
- Attack D: Extreme Update (Amplified Delta)
- Attack E: Backdoor (Trigger injection & ASR evaluation)
"""

from .label_flipping import LabelFlippedDataset, apply_label_flipping
from .sign_flipping import apply_sign_flipping
from .random_byzantine import apply_random_byzantine
from .extreme_update import apply_extreme_update
from .backdoor import (
    add_trigger,
    BackdoorDataset,
    TriggeredTestDataset,
    evaluate_asr,
)

__all__ = [
    "LabelFlippedDataset",
    "apply_label_flipping",
    "apply_sign_flipping",
    "apply_random_byzantine",
    "apply_extreme_update",
    "add_trigger",
    "BackdoorDataset",
    "TriggeredTestDataset",
    "evaluate_asr",
]
