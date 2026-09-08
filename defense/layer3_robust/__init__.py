"""
FedSanitize — Layer 3 Robust Aggregation Package
"""

from .trimmed_mean import (
    coordinate_wise_trimmed_mean,
    Layer3RobustAggregator,
)

__all__ = [
    "coordinate_wise_trimmed_mean",
    "Layer3RobustAggregator",
]
