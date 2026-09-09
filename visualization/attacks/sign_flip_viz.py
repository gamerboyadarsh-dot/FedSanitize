"""
FedSantize Attack Visualization — Sign Flipping Directional Conflict
=====================================================================
Visualizes directional gradient reversal conflicting with consensus.
"""

from __future__ import annotations
import plotly.graph_objects as go
from ..network.graph_styles import THEME


def render_sign_flip_vector_diagram(height: int = 240) -> go.Figure:
    """
    Renders 2D directional arrows contrasting honest convergence vs sign flip.
    """
    fig = go.Figure()

    # Consensus direction
    fig.add_annotation(
        x=0.7, y=0.5, ax=0.2, ay=0.5,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.5, arrowwidth=4,
        arrowcolor=THEME["safe"],
        text="<b>Benign Consensus Direction ➔</b>",
        font=dict(color=THEME["safe"], size=13),
    )

    # Malicious inverted direction
    fig.add_annotation(
        x=0.2, y=-0.3, ax=0.7, ay=-0.3,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.5, arrowwidth=4,
        arrowcolor=THEME["malicious"],
        text="<b>⬅ Inverted Malicious Update (-gamma * delta)</b>",
        font=dict(color=THEME["malicious"], size=13),
    )

    fig.update_layout(
        title="<b>Sign Flipping — Gradient Direction Reversal vs Global Consensus</b>",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.8, 0.8]),
        paper_bgcolor=THEME["card_background"],
        plot_bgcolor=THEME["card_background"],
        font=dict(color=THEME["text_primary"]),
        margin=dict(l=20, r=20, t=40, b=20),
        height=height,
    )
    return fig
