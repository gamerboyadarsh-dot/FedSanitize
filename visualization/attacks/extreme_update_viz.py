"""
FedSantize Attack Visualization — Extreme Update Narrative
===========================================================
Visualizes abnormal parameter magnitude scaling and Layer 1 MAD detection.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import plotly.graph_objects as go

from ..network.graph_styles import THEME


def render_extreme_update_comparison(
    malicious_norm: float,
    benign_norms: list[float],
    mad_threshold: float,
    height: int = 280,
) -> go.Figure:
    fig = go.Figure()
    
    # Benign bars
    fig.add_trace(
        go.Bar(
            name="Honest Clients",
            x=[f"C{i}" for i in range(len(benign_norms))],
            y=benign_norms,
            marker_color=THEME["safe"],
        )
    )

    # Malicious bar
    fig.add_trace(
        go.Bar(
            name="Extreme Attacker (Gamma Scaled)",
            x=["Attacker"],
            y=[malicious_norm],
            marker_color=THEME["malicious"],
        )
    )

    fig.add_hline(
        y=mad_threshold,
        line_dash="dash",
        line_color=THEME["suspicious"],
        annotation_text=f"MAD Outlier Ceiling: {mad_threshold:.2f}",
        annotation_position="top left",
    )

    fig.update_layout(
        title="<b>Extreme Update — Parameter L2 Norm Explosion vs Honest Clients</b>",
        paper_bgcolor=THEME["card_background"],
        plot_bgcolor=THEME["card_background"],
        font=dict(color=THEME["text_primary"]),
        margin=dict(l=30, r=30, t=40, b=30),
        height=height,
    )
    return fig
