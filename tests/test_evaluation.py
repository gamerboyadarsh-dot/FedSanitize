"""
FedSanitize — Phase 8: Evaluation Engine Test Suite
===================================================
Verifies:
  - Accuracy and loss evaluation functions.
  - Attack Success Rate (ASR) evaluation on triggered datasets.
  - Comprehensive detection metrics calculation with zero-division handling.
  - ExperimentLogger history logging, Pandas DataFrame conversion, and CSV/JSON export.
  - Interactive Plotly chart generation (Accuracy curve, ASR curve, Scatter plot, Heatmap, Confusion Matrix).
"""

import os
import sys
import pytest
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation import (
    evaluate_clean_accuracy,
    evaluate_backdoor_asr,
    calculate_detection_metrics,
    ExperimentLogger,
    plot_accuracy_curve,
    plot_asr_curve,
    plot_client_security_scatter,
    plot_mars_distance_heatmap,
    plot_confusion_matrix,
)
import plotly.graph_objects as go


class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 2)

    def forward(self, x):
        return self.fc(x)


def test_evaluate_clean_accuracy():
    model = DummyModel()
    x = torch.randn(20, 10)
    y = torch.randint(0, 2, (20,))
    ds = TensorDataset(x, y)

    loss, acc = evaluate_clean_accuracy(model, ds, batch_size=5, device="cpu")
    assert loss >= 0.0, "Loss should be non-negative"
    assert 0.0 <= acc <= 100.0, "Accuracy must be bounded [0, 100]"


def test_evaluate_backdoor_asr():
    model = DummyModel()
    x = torch.randn(20, 10)
    y = torch.zeros(20, dtype=torch.long)
    ds = TensorDataset(x, y)

    asr = evaluate_backdoor_asr(model, ds, target_class=0, batch_size=5, device="cpu")
    assert 0.0 <= asr <= 100.0, "ASR must be bounded [0, 100]"


def test_detection_metrics_calculation():
    # Synthetic records with 2 TP, 1 FP, 5 TN, 0 FN
    records = {
        "C0": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"},
        "C1": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"},
        "C2": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"},
        "C3": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"},
        "C4": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"},
        "C5": {"is_malicious": False, "final_status": "QUARANTINED", "layer1_status": "FLAGGED", "mars_status": "SKIPPED"},
        "C6": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "FLAGGED", "mars_status": "SKIPPED"},
        "C7": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "PASS", "mars_status": "FLAGGED"},
    }

    metrics = calculate_detection_metrics(records)
    assert metrics["tp"] == 2
    assert metrics["fp"] == 1
    assert metrics["tn"] == 5
    assert metrics["fn"] == 0
    assert metrics["precision"] == 2 / 3
    assert metrics["recall"] == 1.0
    assert metrics["layer1_quarantined"] == 2
    assert metrics["mars_quarantined"] == 1


def test_detection_metrics_zero_division():
    # Empty or all-clean records
    records = {
        "C0": {"is_malicious": False, "final_status": "TRUSTED"},
        "C1": {"is_malicious": False, "final_status": "TRUSTED"},
    }
    metrics = calculate_detection_metrics(records)
    assert metrics["tp"] == 0
    assert metrics["fp"] == 0
    assert metrics["precision"] == 1.0  # Safe fallback when no attacks present
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0


def test_experiment_logger_and_export(tmp_path):
    logger = ExperimentLogger(experiment_name="test_exp", output_dir=str(tmp_path))
    dummy_round = {
        "round": 1,
        "attack_type": "BACKDOOR",
        "total_clients": 10,
        "clean_accuracy": 95.5,
        "backdoor_asr": 1.2,
        "trusted_clients": ["C0", "C1"],
        "detection": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0},
        "aggregation": {"trim_count_applied": 1},
    }
    logger.log_round(dummy_round)
    assert len(logger.history) == 1

    df = logger.to_dataframe()
    assert len(df) == 1
    assert "Clean Accuracy (%)" in df.columns
    assert df["Clean Accuracy (%)"].iloc[0] == 95.5

    json_file = logger.export_json()
    assert os.path.exists(json_file)

    csv_file = logger.export_csv()
    assert os.path.exists(csv_file)


def test_plotly_visualizations():
    history = [
        {"round": 1, "clean_accuracy": 91.0, "backdoor_asr": 85.0},
        {"round": 2, "clean_accuracy": 95.0, "backdoor_asr": 2.0},
    ]
    records = {
        "C0": {"update_norm": 2.1, "cosine_similarity": 0.8, "final_status": "TRUSTED", "attack_type": "NONE"},
        "C1": {"update_norm": 20.5, "cosine_similarity": 0.1, "final_status": "QUARANTINED", "attack_type": "EXTREME"},
    }
    dist_mat = np.array([[0.0, 0.05], [0.05, 0.0]])
    det_metrics = {"tp": 1, "fp": 0, "tn": 1, "fn": 0, "precision": 1.0, "recall": 1.0}

    fig1 = plot_accuracy_curve(history)
    fig2 = plot_asr_curve(history)
    fig3 = plot_client_security_scatter(records)
    fig4 = plot_mars_distance_heatmap(dist_mat)
    fig5 = plot_confusion_matrix(det_metrics)

    for fig in [fig1, fig2, fig3, fig4, fig5]:
        assert isinstance(fig, go.Figure), "Plot must return a Plotly Figure instance"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
