"""
FedSanitize — Evaluation: Interactive Plotly Visualizations
==========================================================
All figures use the shared dark template defined in dashboard/theme.py.
Do NOT hardcode colors here; always import from COLORS / PLOTLY_SERIES.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from dashboard.theme import COLORS, PLOTLY_SERIES, PLOTLY_HEATMAP_SCALE, get_plotly_layout_defaults


def _base_layout(**extra) -> dict:
    """Merge shared layout defaults with any figure-specific overrides."""
    d = get_plotly_layout_defaults()
    d.update(extra)
    return d


def plot_accuracy_curve(
    history: List[Dict[str, Any]],
    baseline_history: Optional[List[Dict[str, Any]]] = None,
) -> go.Figure:
    """Plots Clean Accuracy (%) over rounds."""
    rounds = [r.get("round", i + 1) for i, r in enumerate(history)]
    accs = [r.get("clean_accuracy", 0.0) for r in history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rounds, y=accs,
        mode="lines+markers",
        name="FedSanitize (Defended)",
        line=dict(color=PLOTLY_SERIES[0], width=3),
        marker=dict(size=8, color=PLOTLY_SERIES[0], line=dict(width=1, color=COLORS["midnight_blue"])),
        fill="tozeroy",
        fillcolor=f"rgba(56,251,219,0.07)",
    ))

    if baseline_history:
        base_rounds = [r.get("round", i + 1) for i, r in enumerate(baseline_history)]
        base_accs = [r.get("clean_accuracy", 0.0) for r in baseline_history]
        fig.add_trace(go.Scatter(
            x=base_rounds, y=base_accs,
            mode="lines+markers",
            name="Undefended FedAvg",
            line=dict(color=COLORS["danger"], width=2, dash="dash"),
            marker=dict(size=6, color=COLORS["danger"]),
        ))

    fig.update_layout(**_base_layout(
        title="Global Model Clean Accuracy vs. Round",
        xaxis_title="Federated Round",
        yaxis_title="Accuracy (%)",
        yaxis=dict(range=[0, 105], gridcolor="rgba(56,251,219,0.10)", tickfont=dict(color=COLORS["text_muted"])),
    ))
    return fig


def plot_asr_curve(history: List[Dict[str, Any]]) -> go.Figure:
    """Plots Backdoor Attack Success Rate (ASR %) over rounds."""
    rounds = [r.get("round", i + 1) for i, r in enumerate(history)]
    asrs = [r.get("backdoor_asr", 0.0) for r in history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rounds, y=asrs,
        mode="lines+markers",
        name="Backdoor ASR (%)",
        line=dict(color=COLORS["warning"], width=3),
        marker=dict(size=8, color=COLORS["warning"]),
        fill="tozeroy",
        fillcolor="rgba(245,166,35,0.10)",
    ))

    fig.update_layout(**_base_layout(
        title="Backdoor Attack Success Rate (ASR) vs. Round",
        xaxis_title="Federated Round",
        yaxis_title="ASR (%)",
        yaxis=dict(range=[0, 105], gridcolor="rgba(56,251,219,0.10)", tickfont=dict(color=COLORS["text_muted"])),
    ))
    return fig


def plot_client_security_scatter(client_records: Dict[str, Dict[str, Any]]) -> go.Figure:
    """Interactive scatter: L2 Norm vs Cosine Similarity, color-coded by status."""
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
        "TRUSTED":     COLORS["success"],
        "QUARANTINED": COLORS["danger"],
        "SUSPICIOUS":  COLORS["warning"],
    }

    fig = px.scatter(
        df,
        x="Cosine Similarity", y="L2 Norm",
        color="Status",
        color_discrete_map=color_map,
        hover_data=["Client ID", "Attack Type", "L1 Reason", "MARS Status"],
        title="Client Update Security Profiling (Layer 1 Norm & Directional Space)",
    )
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color=COLORS["midnight_blue"])))
    fig.update_layout(**_base_layout())
    return fig


def plot_mars_distance_heatmap(
    distance_matrix: np.ndarray,
    client_ids: Optional[List[str]] = None,
) -> go.Figure:
    """Renders the MARS pairwise Wasserstein distance heatmap."""
    n = distance_matrix.shape[0]
    labels = client_ids if (client_ids and len(client_ids) == n) else [f"C{i}" for i in range(n)]

    fig = go.Figure(data=go.Heatmap(
        z=distance_matrix,
        x=labels, y=labels,
        colorscale=PLOTLY_HEATMAP_SCALE,
        colorbar=dict(
            title="Wasserstein Dist",
            tickfont=dict(color=COLORS["text_muted"]),
            titlefont=dict(color=COLORS["cyan"]),
        ),
    ))

    fig.update_layout(**_base_layout(
        title="MARS Layer 2: Pairwise Wasserstein Distance Matrix",
        xaxis_title="Client",
        yaxis_title="Client",
    ))
    return fig


def plot_confusion_matrix(detection_metrics: Dict[str, Any]) -> go.Figure:
    """Renders the detection confusion matrix."""
    tp = detection_metrics.get("tp", 0)
    fp = detection_metrics.get("fp", 0)
    tn = detection_metrics.get("tn", 0)
    fn = detection_metrics.get("fn", 0)

    # Cell colors: TP→cyan tint, TN→midnight, FP/FN→danger tint
    cell_colors = [
        [COLORS["midnight_blue"], "rgba(255,59,92,0.25)"],
        ["rgba(255,59,92,0.25)",  "rgba(56,251,219,0.25)"],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=[[tn, fp], [fn, tp]],
        x=["Predicted Clean", "Predicted Malicious"],
        y=["Actual Clean", "Actual Malicious"],
        colorscale=[[0, COLORS["midnight_blue"]], [1, COLORS["cyan"]]],
        text=[[f"TN: {tn}", f"FP: {fp}"], [f"FN: {fn}", f"TP: {tp}"]],
        texttemplate="%{text}",
        textfont=dict(size=16, color=COLORS["text_primary"]),
        showscale=False,
    ))

    prec = detection_metrics.get("precision", 1.0)
    rec  = detection_metrics.get("recall", 1.0)
    fig.update_layout(**_base_layout(
        title=f"Detection Confusion Matrix  |  Precision: {prec:.2f}  Recall: {rec:.2f}",
    ))
    return fig
