"""
FedSantize Visualization — Network Topology
===========================================
Computes fixed geometric layouts for the FL server hub and distributed client nodes.
Ensures zero jitter or position jumping across re-renders.
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple, Any

from simulation.network_state import compute_deterministic_layout


def build_network_edges(
    clients: Dict[str, Any],
    server_pos: Tuple[float, float] = (0.5, 0.5),
) -> List[Dict[str, Any]]:
    """
    Computes visual links between each client node and the central server hub.
    Annotates whether connection is active, under inspection, or severed.
    """
    edges = []
    for cid, node in clients.items():
        if isinstance(node, dict):
            client_pos = node.get("position", (0.0, 0.0))
            visual_state = node.get("visual_state", "NORMAL")
            final_status = node.get("final_status", "")
            is_malicious = bool(node.get("is_malicious", False))
        else:
            client_pos = getattr(node, "position", (0.0, 0.0))
            visual_state = getattr(node, "visual_state", "NORMAL")
            final_status = getattr(node, "final_status", "")
            is_malicious = bool(getattr(node, "is_malicious", False))

        is_quarantined = (visual_state == "QUARANTINED") or (final_status == "QUARANTINED")
        edge_type = "SEVERED" if is_quarantined else ("MALICIOUS" if is_malicious else "ACTIVE")
        edges.append({
            "client_id": cid,
            "x0": client_pos[0],
            "y0": client_pos[1],
            "x1": server_pos[0],
            "y1": server_pos[1],
            "edge_type": edge_type,
            "is_quarantined": is_quarantined,
        })
    return edges
