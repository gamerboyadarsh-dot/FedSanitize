"""
FedSanitize — Evaluation: Security Detection Metrics
===================================================
Calculates detection performance metrics (TP, FP, TN, FN, Precision, Recall,
F1 Score, False Alarm Rate) with zero-division guards.
"""

from __future__ import annotations
from typing import Dict, List, Any


def calculate_detection_metrics(
    client_records: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes comprehensive detection statistics from client security records.

    Parameters
    ----------
    client_records : Dict[str, Dict[str, Any]]
        Map of client_id to per-client security records (PART 8 format).

    Returns
    -------
    Dict[str, Any]
        {
            "tp": int, "fp": int, "tn": int, "fn": int,
            "precision": float,
            "recall": float,          # Detection Rate
            "f1_score": float,
            "accuracy": float,
            "false_alarm_rate": float, # FPR = FP / (FP + TN)
            "layer1_quarantined": int,
            "mars_quarantined": int,
        }
    """
    tp = fp = tn = fn = 0
    l1_quarantined = 0
    mars_quarantined = 0

    for rec in client_records.values():
        is_malicious = bool(rec.get("is_malicious", False))
        final_status = rec.get("final_status", "TRUSTED")
        is_flagged = (final_status == "QUARANTINED")

        if rec.get("layer1_status") == "FLAGGED":
            l1_quarantined += 1
        elif rec.get("mars_status") == "FLAGGED":
            mars_quarantined += 1

        if is_malicious and is_flagged:
            tp += 1
        elif not is_malicious and is_flagged:
            fp += 1
        elif not is_malicious and not is_flagged:
            tn += 1
        elif is_malicious and not is_flagged:
            fn += 1

    total = tp + fp + tn + fn

    # Precision
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else (1.0 if (tp + fn) == 0 else 0.0)

    # Recall (Detection Rate)
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 1.0

    # F1 Score
    f1 = float(2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0.0 else 0.0

    # Overall Detection Accuracy
    acc = float((tp + tn) / total) if total > 0 else 1.0

    # False Positive Rate (False Alarm Rate)
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": acc,
        "false_alarm_rate": fpr,
        "layer1_quarantined": l1_quarantined,
        "mars_quarantined": mars_quarantined,
        "total_quarantined": tp + fp,
        "total_clients": total,
    }
