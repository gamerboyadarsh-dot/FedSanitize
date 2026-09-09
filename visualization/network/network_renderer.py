"""
FedSantize Visualization — Interactive Network Renderer
=======================================================
Renders the primary federated network topology using Plotly Graph Objects.
Displays server hub, client nodes, update transmission paths, attack indications,
and severed quarantine links.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List
import plotly.graph_objects as go

from .graph_styles import THEME, STATE_COLOR_MAP, STATE_ICON_MAP
from .topology import build_network_edges
from simulation.network_state import NetworkState


def render_network_graph(
    network_state: NetworkState,
    selected_client_id: Optional[str] = None,
    height: int = 520,
) -> go.Figure:
    """
    Constructs an interactive Plotly figure representing the federated network.
    """
    fig = go.Figure()

    server_pos = network_state.server_state.get("position", (0.5, 0.5))
    server_status = network_state.server_state.get("status", "IDLE")
    active_layer = network_state.server_state.get("active_layer", "NONE")

    # 1. Draw Network Edges (Client <-> Server)
    edges = build_network_edges(network_state.clients, server_pos)

    for edge in edges:
        cid = edge["client_id"]
        is_quarantined = edge["is_quarantined"]
        is_selected = (selected_client_id == cid)

        if is_quarantined:
            line_color = THEME["link_severed"]
            line_dash = "dot"
            line_width = 1.5
        elif edge["edge_type"] == "MALICIOUS":
            line_color = THEME["link_malicious"]
            line_dash = "dash"
            line_width = 2.5 if is_selected else 2.0
        else:
            line_color = THEME["link_clean"]
            line_dash = "solid"
            line_width = 2.5 if is_selected else 1.5

        fig.add_trace(
            go.Scatter(
                x=[edge["x0"], edge["x1"]],
                y=[edge["y0"], edge["y1"]],
                mode="lines",
                line=dict(color=line_color, width=line_width, dash=line_dash),
                hoverinfo="none",
                showlegend=False,
            )
        )

    # 2. Draw Client Nodes
    client_x, client_y = [], []
    client_colors, client_sizes = [], []
    client_symbols = []
    client_texts, hover_texts = [], []

    for cid, node in sorted(network_state.clients.items()):
        pos = getattr(node, "position", (0.0, 0.0))
        state = getattr(node, "visual_state", "NORMAL")
        attack = getattr(node, "attack_type", "BENIGN")
        l1_stat = getattr(node, "layer1_status", "PENDING") or "PENDING"
        mars_stat = getattr(node, "mars_status", "PENDING") or "PENDING"
        final_stat = getattr(node, "final_status", "NORMAL") or "NORMAL"
        is_selected = (selected_client_id == cid)

        client_x.append(pos[0])
        client_y.append(pos[1])
        client_colors.append(STATE_COLOR_MAP.get(state, THEME["safe"]))
        client_sizes.append(38 if is_selected else 30)
        client_symbols.append("square" if state == "QUARANTINED" else "circle")
        client_texts.append(f"<b>{cid}</b>")

        icon = STATE_ICON_MAP.get(state, "")
        hover_info = (
            f"<b>{icon} Client {cid}</b><br>"
            f"• Visual State: {state}<br>"
            f"• Attack Mode: {attack}<br>"
            f"• Layer 1 Status: {l1_stat}<br>"
            f"• MARS Status: {mars_stat}<br>"
            f"• Final Disposition: <b>{final_stat}</b><br>"
        )
        hover_texts.append(hover_info)

    fig.add_trace(
        go.Scatter(
            x=client_x,
            y=client_y,
            mode="markers+text",
            marker=dict(
                size=client_sizes,
                color=client_colors,
                symbol=client_symbols,
                line=dict(color=THEME["text_primary"], width=2),
                opacity=0.95,
            ),
            text=client_texts,
            textposition="top center",
            textfont=dict(color=THEME["text_primary"], size=11, family="Inter, Roboto, sans-serif"),
            hoverinfo="text",
            hovertext=hover_texts,
            name="Clients",
            showlegend=False,
        )
    )

    # 3. Draw Central Federated Server Hub
    fig.add_trace(
        go.Scatter(
            x=[server_pos[0]],
            y=[server_pos[1]],
            mode="markers+text",
            marker=dict(
                size=55,
                color=THEME["server"],
                symbol="hexagon",
                line=dict(color="#B388FF", width=3),
                opacity=1.0,
            ),
            text=["<b>FED SERVER</b>"],
            textposition="bottom center",
            textfont=dict(color="#E0E0E0", size=12, family="Inter, Roboto, sans-serif"),
            hoverinfo="text",
            hovertext=(
                f"<b>🛡️ FEDERATED SERVER HUB</b><br>"
                f"• Status: {server_status}<br>"
                f"• Active Pipeline: {active_layer}<br>"
                f"• Round: {network_state.round_id}"
            ),
            name="Server",
            showlegend=False,
        )
    )

    # Layout Configuration
    fig.update_layout(
        paper_bgcolor=THEME["background"],
        plot_bgcolor=THEME["background"],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.05, 1.05]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.05, 1.05]),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        hoverlabel=dict(
            bgcolor=THEME["card_background"],
            font_size=12,
            font_family="Roboto, sans-serif",
            bordercolor=THEME["border_color"],
        ),
    )

    return fig
