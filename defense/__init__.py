"""
FedSanitize — Defense Engine Packages
=====================================
- Layer 1: Statistical Anomaly Detection (Norm, Cosine Sim, MAD)
- Layer 2: MARS Backdoor Defense (Backdoor Energy, CBE, Wasserstein, Clustering)
- Layer 3: Robust Aggregation (Coordinate-wise Trimmed Mean)
"""

from .layer1_anomaly import Layer1AnomalyDetector, ClientSecurityResult
from .layer2_mars import MARSDetector
from .layer3_robust import coordinate_wise_trimmed_mean, Layer3RobustAggregator

__all__ = [
    "Layer1AnomalyDetector",
    "ClientSecurityResult",
    "MARSDetector",
    "coordinate_wise_trimmed_mean",
    "Layer3RobustAggregator",
]
