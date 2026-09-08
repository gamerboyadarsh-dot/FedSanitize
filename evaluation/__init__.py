"""
FedSanitize — Evaluation & Performance Analysis Package
"""

from .accuracy import evaluate_clean_accuracy
from .attack_success_rate import evaluate_backdoor_asr
from .detection_metrics import calculate_detection_metrics
from .experiment_logger import ExperimentLogger
from .plots import (
    plot_accuracy_curve,
    plot_asr_curve,
    plot_client_security_scatter,
    plot_mars_distance_heatmap,
    plot_confusion_matrix,
)

__all__ = [
    "evaluate_clean_accuracy",
    "evaluate_backdoor_asr",
    "calculate_detection_metrics",
    "ExperimentLogger",
    "plot_accuracy_curve",
    "plot_asr_curve",
    "plot_client_security_scatter",
    "plot_mars_distance_heatmap",
    "plot_confusion_matrix",
]
