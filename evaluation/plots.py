"""
FedSanitize — Evaluation: Interactive Plotly Visualizations
==========================================================
Generates presentation-grade interactive Plotly figures for the Streamlit
frontend and experiment reports:
  1. Clean Accuracy vs. Round (FedSanitize vs. Undefended FedAvg)
  2. Backdoor ASR vs. Round (Demonstrating backdoor suppression)
  3. Client Security Scatter Plot (L2 Norm vs. Cosine Similarity)
  4. MARS Pairwise Wasserstein Distance Matrix Heatmap
  5. Detection Performance Confusion Matrix
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def plot_accuracy_curve(
    history: List[Dict[str, Any]],
    baseline_history: Optional[List[Dict[str, Any]]] = None,
) -> go.Figure:
    """
    Plots Clean Accuracy (%) over rounds.
    Optionally overlays an undefended baseline run.
    """
    rounds = [r.get("round", i + 1) for i, r in enumerate(history)]
    accs = [r.get("clean_accuracy", 0.0) for r in history]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rounds,
            y=accs,
            mode="lines+markers",
            name="FedSanitize (Defended)",
            line=dict(color="#10B981", width=3),
            marker=dict(size=8),
        )
    )

    if baseline_history:
        base_rounds = [r.get("round", i + 1) for i, r in enumerate(baseline_history)]
        base_accs = [r.get("clean_accuracy", 0.0) for r in baseline_history]
        fig.add_trace(
            go.Scatter(
                x=base_rounds,
                y=base_accs,
                mode="lines+markers",
                name="Undefended FedAvg",
                line=dict(color="#EF4444", width=2, dash="dash"),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title="Global Model Clean Accuracy vs. Round",
        xaxis_title="Federated Round",
        yaxis_title="Accuracy (%)",
        yaxis=dict(range=[0, 105]),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def plot_asr_curve(history: List[Dict[str, Any]]) -> go.Figure:
    """
    Plots Backdoor Attack Success Rate (ASR %) over rounds.
    """
    rounds = [r.get("round", i + 1) for i, r in enumerate(history)]
    asrs = [r.get("backdoor_asr", 0.0) for r in history]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rounds,
            y=asrs,
            mode="lines+markers",
            name="Backdoor ASR (%)",
            line=dict(color="#F59E0B", width=3),
            marker=dict(size=8, color="#F59E0B"),
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.15)",
        )
    )

    fig.update_layout(
        title="Backdoor Attack Success Rate (ASR) vs. Round",
        xaxis_title="Federated Round",
        yaxis_title="ASR (%)",
        yaxis=dict(range=[0, 105]),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def plot_client_security_scatter(
    client_records: Dict[str, Dict[str, Any]],
) -> go.Figure:
    """
    Interactive scatter plot of L2 Update Norm vs. Cosine Similarity.
    Points are color-coded by final defense status.
    """
    rows = []
    for cid, rec in client_records.items():
        rows.append({
            "Client ID": cid,
            "L2 Norm": rec.get("update_norm", 0.0),
            "Cosine Similarity": rec.get("cosine_similarity", 0.0),
            "Status": rec.get("final_status", "TRUSTED"),
            "Attack Type": rec.get("attack_type", "NONE"),
            "L1 Reason": rec.get("layer1_reason", "NORMAL_UPDATE"),
            "MARS Status": rec.get("mars_status", "PASS"),
        })
    df = pd.DataFrame(rows)

    color_map = {
        "TRUSTED": "#10B981",       # Green
        "QUARANTINED": "#EF4444",   # Red
        "SUSPICIOUS": "#F59E0B",    # Amber
    }

    fig = px.scatter(
        df,
        x="Cosine Similarity",
        y="L2 Norm",
        color="Status",
        color_discrete_map=color_map,
        hover_data=["Client ID", "Attack Type", "L1 Reason", "MARS Status"],
        title="Client Update Security Profiling (Layer 1 Norm & Directional Space)",
        template="plotly_dark",
    )
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    return fig


def plot_mars_distance_heatmap(
    distance_matrix: np.ndarray,
    client_ids: Optional[List[str]] = None,
) -> go.Figure:
    """
    Renders an interactive heatmap of the pairwise Wasserstein distance matrix from MARS.
    """
    n = distance_matrix.shape[0]
    labels = client_ids if (client_ids and len(client_ids) == n) else [f"C{i}" for i in range(n)]

    fig = go.Figure(
        data=go.Heatmap(
            z=distance_matrix,
            x=labels,
            y=labels,
            colorscale="Viridis",
            colorbar=dict(title="Wasserstein Dist"),
        )
    )

    fig.update_layout(
        title="MARS Layer 2: Pairwise Wasserstein Distance Matrix",
        xaxis_title="Client",
        yaxis_title="Client",
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def plot_confusion_matrix(detection_metrics: Dict[str, Any]) -> go.Figure:
    """
    Renders the detection confusion matrix.
    """
    tp = detection_metrics.get("tp", 0)
    fp = detection_metrics.get("fp", 0)
    tn = detection_metrics.get("tn", 0)
    fn = detection_metrics.get("fn", 0)

    z = [[tn, fp], [fn, tp]]
    x = ["Predicted Clean", "Predicted Malicious"]
    y = ["Actual Clean", "Actual Malicious"]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x,
            y=y,
            colorscale="Blues",
            text=[[f"TN: {tn}", f"FP: {fp}"], [f"FN: {fn}", f"TP: {tp}"]],
            texttemplate="%{text}",
            textfont=dict(size=16),
            showscale=False,
        )
    )

    fig.update_layout(
        title=f"Detection Confusion Matrix (Precision: {detection_metrics.get('precision', 1.0):.2f}, Recall: {detection_metrics.get('recall', 1.0):.2f})",
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig
