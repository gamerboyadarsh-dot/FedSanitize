"""
FedSantize Defense Visualization — Layer 1 Anomaly Filter
=========================================================
Visualizes the three Layer 1 statistical anomaly analysis mechanisms:
  1. L2 Update Norm vs. Median & Robust Threshold
  2. Directional Cosine Similarity against Peer Consensus
  3. Median Absolute Deviation (MAD) Multipliers & Outlier Flags

Grounded in Phase 7 and pages 29-30 of the simulation engine specification.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..network.graph_styles import THEME


def render_layer1_norm_chart(
    client_records: Dict[str, Dict[str, Any]],
    median_norm: Optional[float] = None,
    threshold: Optional[float] = None,
    height: int = 340,
) -> go.Figure:
    """
    Renders bar chart of client update norms with median and threshold lines.
    """
    cids = sorted(client_records.keys())
    norms = [float(client_records[c].get("update_norm", 0.0)) for c in cids]
    statuses = [client_records[c].get("layer1_status", "PASS") for c in cids]
    colors = [THEME["quarantine"] if s == "FLAGGED" else THEME["safe"] for s in statuses]

    fig = go.Figure()

    # Bar trace
    fig.add_trace(
        go.Bar(
            x=cids,
            y=norms,
            marker_color=colors,
            text=[f"{n:.2f}" for n in norms],
            textposition="auto",
            hovertemplate="<b>Client %{x}</b><br>Update Norm: %{y:.4f}<extra></extra>",
            name="Update Norm",
        )
    )

    # Median Line
    if median_norm is None and norms:
        median_norm = float(np.median(norms))

    if median_norm is not None:
        fig.add_hline(
            y=median_norm,
            line_dash="dash",
            line_color=THEME["processing"],
            annotation_text=f"Median: {median_norm:.2f}",
            annotation_position="top right",
        )

    # Threshold Line
    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dot",
            line_color=THEME["suspicious"],
            annotation_text=f"MAD Threshold: {threshold:.2f}",
            annotation_position="top left",
        )

    fig.update_layout(
        title="<b>Layer 1 — Client Update L2 Norms</b>",
        paper_bgcolor=THEME["card_background"],
        plot_bgcolor=THEME["card_background"],
        font=dict(color=THEME["text_primary"]),
        xaxis=dict(title="Client ID", gridcolor=THEME["border_color"]),
        yaxis=dict(title="L2 Norm", gridcolor=THEME["border_color"]),
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
    )
    return fig


def render_layer1_cosine_chart(
    client_records: Dict[str, Dict[str, Any]],
    threshold: float = 0.0,
    height: int = 340,
) -> go.Figure:
    """
    Renders bar chart of client cosine similarities against consensus.
    """
    cids = sorted(client_records.keys())
    cos_sims = [float(client_records[c].get("cosine_similarity", 1.0)) for c in cids]
    statuses = [client_records[c].get("layer1_status", "PASS") for c in cids]
    colors = [THEME["quarantine"] if s == "FLAGGED" else THEME["safe"] for s in statuses]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=cids,
            y=cos_sims,
            marker_color=colors,
            text=[f"{cs:.3f}" for cs in cos_sims],
            textposition="auto",
            hovertemplate="<b>Client %{x}</b><br>Cosine Similarity: %{y:.4f}<extra></extra>",
            name="Cosine Similarity",
        )
    )

    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color=THEME["suspicious"],
        annotation_text=f"Min Alignment Threshold: {threshold:.2f}",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="<b>Layer 1 — Directional Cosine Similarity</b>",
        paper_bgcolor=THEME["card_background"],
        plot_bgcolor=THEME["card_background"],
        font=dict(color=THEME["text_primary"]),
        xaxis=dict(title="Client ID", gridcolor=THEME["border_color"]),
        yaxis=dict(title="Cosine Similarity", range=[-1.1, 1.1], gridcolor=THEME["border_color"]),
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
    )
    return fig
