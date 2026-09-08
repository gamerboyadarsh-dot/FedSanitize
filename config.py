"""
FedSanitize — Centralized Configuration
========================================
All hyper-parameters, paths, and toggles live here.
Do NOT scatter magic numbers across modules.

Sections
--------
SYSTEM_CONFIG      : reproducibility & runtime
MODEL_CONFIG       : CNN architecture knobs
FEDERATED_CONFIG   : FL simulation parameters
ATTACK_CONFIG      : attack parameters (all attacks)
LAYER1_CONFIG      : Layer 1 anomaly-filter thresholds
MARS_CONFIG        : Layer 2 MARS parameters (populated after reference is confirmed)
AGGREGATION_CONFIG : Layer 3 trimmed-mean parameters
EVALUATION_CONFIG  : accuracy / ASR / detection-metric settings
UI_CONFIG          : Streamlit dashboard settings
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SystemConfig:
    """Reproducibility and runtime settings."""
    random_seed: int = 42
    device: str = "cpu"          # "cpu" | "cuda" | "mps"
    log_level: str = "INFO"      # "DEBUG" | "INFO" | "WARNING"
    data_dir: str = "./data"     # MNIST download location
    results_dir: str = "./results"
    demo_results_dir: str = "./demo_results"


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelConfig:
    """Small CNN for MNIST — must train quickly on CPU."""
    in_channels: int = 1
    num_classes: int = 10
    conv1_out: int = 32
    conv2_out: int = 64
    kernel_size: int = 3
    pool_size: int = 2
    fc_hidden: int = 128
    dropout_rate: float = 0.25


# ---------------------------------------------------------------------------
# Federated Learning
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FederatedConfig:
    num_clients: int = 10
    num_rounds: int = 10            # default; demo uses 10–20
    local_epochs: int = 1           # 1 epoch is fast on CPU (< 30s) and reaches >95% acc
    local_batch_size: int = 64
    local_lr: float = 0.02
    local_momentum: float = 0.9
    iid: bool = True                # IID partition (default for hackathon reliability)
    min_clients_per_round: int = 2  # hard lower bound before abort


# ---------------------------------------------------------------------------
# Attacks
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AttackConfig:
    # General
    num_malicious_clients: int = 3
    malicious_client_ids: Optional[List[int]] = None  # None → first N clients

    # A — Label Flipping
    label_flip_map: Dict[int, int] = field(default_factory=lambda: {1: 7, 2: 5})

    # B — Sign Flipping
    sign_flip_gamma: float = 1.0

    # C — Random Byzantine
    random_byzantine_scale: float = 5.0

    # D — Extreme Update
    extreme_update_gamma: float = 10.0

    # E — Backdoor
    backdoor_trigger_size: int = 4          # px, white square
    backdoor_trigger_position: str = "bottom_right"
    backdoor_target_class: int = 0
    backdoor_poison_ratio: float = 0.40     # fraction of malicious client's data


# ---------------------------------------------------------------------------
# Layer 1 — Anomaly Filter
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Layer1Config:
    # MAD sensitivity multiplier (higher → more lenient)
    mad_threshold_multiplier: float = 3.5
    # Cosine similarity threshold below which update is suspicious
    cosine_similarity_threshold: float = 0.0
    # Minimum clients that must survive Layer 1 (before fallback)
    min_surviving_clients: int = 2
    # If True, use robust (coordinate-wise median) reference for cosine sim
    use_robust_reference: bool = True


# ---------------------------------------------------------------------------
# Layer 2 — MARS (Malignity-Aware Backdoor Defense in Federated Learning)
# Reference: Wei Wan et al., NeurIPS 2025, arXiv:2509.20383
# Repository: https://github.com/yunming181920/MARS
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MARSConfig:
    """
    Configuration for Layer 2 MARS Backdoor Defense.
    Grounded in: 'MARS: A Malignity-Aware Backdoor Defense in Federated Learning'
    (Wan et al., NeurIPS 2025).
    """
    paper_citation: str = (
        "MARS: A Malignity-Aware Backdoor Defense in Federated Learning. "
        "Wei Wan, Yuxuan Ning, Zhicong Huang, Cheng Hong, Shengshan Hu, "
        "Ziqi Zhou, Yechao Zhang, Tianqing Zhu, Wanlei Zhou, Leo Yu Zhang. NeurIPS 2025."
    )
    paper_arxiv: str = "arXiv:2509.20383"
    reference_repo: str = "https://github.com/yunming181920/MARS"
    enabled: bool = True
    top_k_percent: float = 0.10         # κ — fraction of high-energy neurons/filters forming CBE
    selected_layers: Optional[List[str]] = None   # None -> auto-select convolutional / representation layers
    num_clusters: int = 2               # expected: benign cluster + suspicious cluster
    clustering_method: str = "agglomerative"   # agglomerative clustering on distance matrix
    min_clients_for_mars: int = 3       # fallback: preserve clients if fewer survive L1
    distance_metric: str = "wasserstein"


# ---------------------------------------------------------------------------
# Layer 3 — Robust Aggregation
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AggregationConfig:
    # Coordinate-wise Trimmed Mean
    trim_ratio: float = 0.1            # fraction to trim from each tail
    # Fallback when trim_ratio is unsafe given client count
    fallback_method: str = "coordinate_median"   # "coordinate_median" | "mean"
    min_clients_for_trimmed_mean: int = 3


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EvaluationConfig:
    test_batch_size: int = 256
    # Number of triggered test samples to generate for ASR
    asr_test_samples: int = 1000


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class UIConfig:
    app_title: str = "FedSanitize — Security Command Center"
    theme: str = "dark"
    plotly_template: str = "plotly_dark"
    color_trusted: str = "#00c853"
    color_suspicious: str = "#ffd600"
    color_quarantined: str = "#d50000"
    color_accent: str = "#2979ff"
    demo_mode_label: str = "PRECOMPUTED EXPERIMENT RESULT"


# ---------------------------------------------------------------------------
# Composite config (single import point)
# ---------------------------------------------------------------------------
@dataclass
class FedSanitizeConfig:
    system: SystemConfig = field(default_factory=SystemConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    federated: FederatedConfig = field(default_factory=FederatedConfig)
    attack: AttackConfig = field(default_factory=AttackConfig)
    layer1: Layer1Config = field(default_factory=Layer1Config)
    mars: MARSConfig = field(default_factory=MARSConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    ui: UIConfig = field(default_factory=UIConfig)


# Default singleton — import this in all modules
DEFAULT_CONFIG = FedSanitizeConfig()
