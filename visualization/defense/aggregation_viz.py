"""
FedSantize Defense Visualization — Layer 3 Robust Aggregation
=============================================================
Visualizes coordinate-wise trimmed mean parameter aggregation,
showing surviving client updates, trim filtering, and sanitized consensus.
Grounded in Phase 9 and pages 30-31 of the specification.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go

from ..network.graph_styles import THEME


def render_aggregation_overview_chart(
    aggregation_meta: Dict[str, Any],
    trusted_clients: List[str],
    all_clients: List[str],
    height: int = 340,
) -> go.Figure:
    """
    Renders visual breakdown of clients entering aggregation and trim filtering.
    """
    total_count = len(all_clients)
    surviving_count = len(trusted_clients)
    quarantined_count = total_count - surviving_count

    trim_count = aggregation_meta.get("trim_count", aggregation_meta.get("trim_count_applied", 0))
    method = aggregation_meta.get("method_used", "coordinate_trimmed_mean")

    fig = go.Figure()

    labels = ["Trusted Clients (Aggregated)", "Quarantined (Excluded)", "Trimmed Coordinates per Dim"]
    values = [surviving_count, quarantined_count, trim_count * 2]
    colors = [THEME["safe"], THEME["quarantine"], THEME["processing"]]

    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[str(v) for v in values],
            textposition="auto",
        )
    )

    fig.update_layout(
        title=f"<b>Layer 3 — Robust Aggregation ({method})</b>",
        paper_bgcolor=THEME["card_background"],
        plot_bgcolor=THEME["card_background"],
        font=dict(color=THEME["text_primary"]),
        xaxis=dict(gridcolor=THEME["border_color"]),
        yaxis=dict(title="Count", gridcolor=THEME["border_color"]),
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
    )
    return fig
