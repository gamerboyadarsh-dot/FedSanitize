"""
FedSantize Visualization — Network Fallback
===========================================
Pure HTML/SVG static fallback renderer for client topologies when
dynamic graphing libraries are unavailable.
"""

from __future__ import annotations
from typing import Dict, Any, Optional

from .graph_styles import THEME, STATE_COLOR_MAP, STATE_ICON_MAP
from simulation.network_state import NetworkState


def render_network_fallback_html(
    network_state: NetworkState,
    selected_client_id: Optional[str] = None,
    width: int = 600,
    height: int = 400,
) -> str:
    """
    Renders an SVG/HTML graph representation of the federated network.
    """
    server_pos = network_state.server_state.get("position", (0.5, 0.5))
    sx = int(server_pos[0] * width)
    sy = int(server_pos[1] * height)

    lines_svg = []
    nodes_svg = []

    for cid, node in sorted(network_state.clients.items()):
        if isinstance(node, dict):
            pos = node.get("position", (0.5, 0.5))
            state = node.get("visual_state", "NORMAL")
        else:
            pos = getattr(node, "position", (0.5, 0.5))
            state = getattr(node, "visual_state", "NORMAL")
        cx = int(pos[0] * width)
        cy = int(pos[1] * height)
        is_quarantined = (state == "QUARANTINED")
        color = STATE_COLOR_MAP.get(state, THEME["safe"])
        stroke_dash = "stroke-dasharray='4,4'" if is_quarantined else ""
        stroke_color = THEME["link_severed"] if is_quarantined else THEME["link_clean"]

        # Line to server
        lines_svg.append(
            f"<line x1='{cx}' y1='{cy}' x2='{sx}' y2='{sy}' stroke='{stroke_color}' stroke-width='2' {stroke_dash} />"
        )

        # Node circle
        r = 18 if selected_client_id == cid else 14
        border_width = 3 if selected_client_id == cid else 1
        nodes_svg.append(
            f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{color}' stroke='#FFFFFF' stroke-width='{border_width}' />"
            f"<text x='{cx}' y='{cy+4}' fill='#FFFFFF' font-size='10' font-weight='bold' text-anchor='middle'>{cid}</text>"
        )

    # Server node
    nodes_svg.append(
        f"<circle cx='{sx}' cy='{sy}' r='26' fill='{THEME['server']}' stroke='#B388FF' stroke-width='3' />"
        f"<text x='{sx}' y='{sy+4}' fill='#FFFFFF' font-size='10' font-weight='bold' text-anchor='middle'>SERVER</text>"
    )

    svg_content = f"""<div style="background-color: {THEME['background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 10px; display: flex; justify-content: center;">
<svg width="{width}" height="{height}">
{''.join(lines_svg)}
{''.join(nodes_svg)}
</svg>
</div>"""
    return svg_content
