"""
FedSantize Attack Visualization — Byzantine & Poisoning Stories
================================================================
"""

from __future__ import annotations
import plotly.graph_objects as go
import numpy as np
from ..network.graph_styles import THEME


def render_byzantine_noise_scatter(height: int = 240) -> go.Figure:
    """Renders chaotic Byzantine update dispersion vs tightly clustered benign updates."""
    np.random.seed(42)
    benign_x = np.random.normal(loc=1.0, scale=0.15, size=20)
    benign_y = np.random.normal(loc=1.0, scale=0.15, size=20)

    byzantine_x = np.random.normal(loc=0.0, scale=1.8, size=20)
    byzantine_y = np.random.normal(loc=0.0, scale=1.8, size=20)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=benign_x, y=benign_y,
            mode="markers",
            marker=dict(size=10, color=THEME["safe"]),
            name="Honest Client Consensus",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=byzantine_x, y=byzantine_y,
            mode="markers",
            marker=dict(size=12, color=THEME["malicious"], symbol="x"),
            name="Byzantine Stochastic Noise",
        )
    )
    fig.update_layout(
        title="<b>Random Byzantine — Chaotic Noise Distribution</b>",
        paper_bgcolor=THEME["card_background"],
        plot_bgcolor=THEME["card_background"],
        font=dict(color=THEME["text_primary"]),
        margin=dict(l=30, r=30, t=40, b=30),
        height=height,
    )
    return fig


def render_label_flipping_card() -> str:
    return f"""<div style="background: {THEME['card_background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 12px; margin-top: 10px;">
<div style="color: {THEME['suspicious']}; font-weight: bold; font-size: 13px;">🎯 Label Flipping Data Poisoning</div>
<div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin: 10px 0; font-family: monospace; font-size: 16px;">
<span style="background: rgba(0, 230, 118, 0.15); border: 1px solid {THEME['safe']}; padding: 6px 12px; border-radius: 4px; color: {THEME['safe']};">True Class: 7</span>
<span style="color: #FF5252; font-weight: bold;">➔ FLIPPED TO ➔</span>
<span style="background: rgba(255, 23, 68, 0.15); border: 1px solid {THEME['malicious']}; padding: 6px 12px; border-radius: 4px; color: {THEME['malicious']};">Target Class: 1</span>
</div>
<div style="color: {THEME['text_secondary']}; font-size: 12px;">Local empirical loss gradients skewed to degrade victim classification without extreme norm inflation.</div>
</div>"""
