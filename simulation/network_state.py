"""
FedSantize Simulation Engine — Network State
============================================
Tracks deterministic node positions, client visual states, packet flows,
and security defense statuses. Grounded in Phase 5 specifications.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional

from .event_types import EventType
from .security_event import SecurityEvent


class VisualState:
    NORMAL = "NORMAL"
    TRAINING = "TRAINING"
    ATTACKING = "ATTACKING"
    SENDING_UPDATE = "SENDING_UPDATE"
    WAITING = "WAITING"
    SCANNING = "SCANNING"
    SUSPICIOUS = "SUSPICIOUS"
    QUARANTINED = "QUARANTINED"
    TRUSTED = "TRUSTED"
    AGGREGATED = "AGGREGATED"


@dataclass
class ClientNodeState:
    """
    Visual and security state of an individual federated client.
    """
    client_id: str
    position: Tuple[float, float]
    visual_state: str = VisualState.NORMAL
    attack_type: Optional[str] = None
    is_malicious: bool = False
    security_status: str = "NORMAL"
    layer1_status: Optional[str] = None
    mars_status: Optional[str] = None
    final_status: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "position": list(self.position),
            "visual_state": self.visual_state,
            "attack_type": self.attack_type,
            "is_malicious": self.is_malicious,
            "security_status": self.security_status,
            "layer1_status": self.layer1_status,
            "mars_status": self.mars_status,
            "final_status": self.final_status,
            "metadata": dict(self.metadata),
        }


def compute_deterministic_layout(
    client_ids: List[str],
    center: Tuple[float, float] = (0.5, 0.5),
    radius: float = 0.38,
) -> Dict[str, Tuple[float, float]]:
    """
    Computes deterministic radial coordinates around the central server.
    Ensures identical coordinates across Streamlit re-renders.
    """
    n = len(client_ids)
    if n == 0:
        return {}

    positions: Dict[str, Tuple[float, float]] = {}
    for i, cid in enumerate(sorted(client_ids)):
        angle = (2 * math.pi * i) / n - (math.pi / 2)  # start from 12 o'clock
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        positions[cid] = (round(x, 4), round(y, 4))
    return positions


class NetworkState:
    """
    Central state of the federated network at any point in the simulation.
    """

    def __init__(
        self,
        client_records: Optional[Dict[str, Dict[str, Any]]] = None,
        round_id: int = 1,
    ):
        self.round_id = round_id
        self.server_state: Dict[str, Any] = {
            "position": (0.5, 0.5),
            "status": "IDLE",
            "global_round": round_id,
            "active_layer": None,
        }
        self.clients: Dict[str, ClientNodeState] = {}
        self.active_packets: List[Dict[str, Any]] = []
        self.quarantined_clients: List[str] = []
        self.trusted_clients: List[str] = []
        self.current_layer: Optional[str] = None

        if client_records:
            self.initialize(client_records, round_id)

    def initialize(self, client_records: Dict[str, Dict[str, Any]], round_id: int = 1) -> None:
        """Initializes client node states and deterministic positions."""
        self.round_id = round_id
        self.clients.clear()
        self.active_packets.clear()
        self.quarantined_clients.clear()
        self.trusted_clients.clear()
        self.current_layer = None

        client_ids = list(client_records.keys())
        positions = compute_deterministic_layout(client_ids)

        for cid, rec in sorted(client_records.items()):
            pos = positions.get(cid, (0.5, 0.5))
            self.clients[cid] = ClientNodeState(
                client_id=cid,
                position=pos,
                visual_state=VisualState.NORMAL,
                attack_type=rec.get("attack_type", "BENIGN"),
                is_malicious=rec.get("is_malicious", False),
                security_status="NORMAL",
                layer1_status=rec.get("layer1_status"),
                mars_status=rec.get("mars_status"),
                final_status=rec.get("final_status"),
                metadata=rec.get("metadata", {}) or {},
            )

    def apply_event(self, event: SecurityEvent) -> None:
        """
        Transitions network and client visual states deterministically
        based on the incoming security event.
        """
        evt_type = event.event_type
        cid = event.client_id
        layer = event.layer

        if layer:
            self.current_layer = layer
            self.server_state["active_layer"] = layer

        # 1. Round Started
        if evt_type == EventType.ROUND_STARTED:
            self.server_state["status"] = "DISTRIBUTING_PARAMETERS"
            for client in self.clients.values():
                client.visual_state = VisualState.WAITING

        # 2. Client Training
        elif evt_type == EventType.CLIENT_TRAINING_STARTED:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.TRAINING

        elif evt_type == EventType.CLIENT_TRAINING_FINISHED:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.WAITING

        # 3. Adversarial Attack Activated
        elif evt_type == EventType.ATTACK_ACTIVATED:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.ATTACKING
                self.clients[cid].security_status = "ATTACKING"

        # 4. Client Updates Flow
        elif evt_type == EventType.CLIENT_UPDATE_CREATED:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.SENDING_UPDATE

        elif evt_type == EventType.CLIENT_UPDATE_SENT:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.WAITING
                # Spawn packet traveling from client pos to server pos
                self.active_packets.append({
                    "client_id": cid,
                    "from_pos": self.clients[cid].position,
                    "to_pos": self.server_state["position"],
                    "is_malicious": self.clients[cid].is_malicious,
                    "attack_type": self.clients[cid].attack_type,
                })

        # 5. Layer 1 Anomaly Detection
        elif evt_type == EventType.LAYER1_STARTED:
            self.server_state["status"] = "LAYER_1_SCANNING"
            for client in self.clients.values():
                if client.client_id not in self.quarantined_clients:
                    client.visual_state = VisualState.SCANNING

        elif evt_type == EventType.LAYER1_ANALYZING:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.SCANNING

        elif evt_type == EventType.LAYER1_CLIENT_FLAGGED:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.QUARANTINED
                self.clients[cid].security_status = "FLAGGED_L1"
                self.clients[cid].layer1_status = "FLAGGED"
                if cid not in self.quarantined_clients:
                    self.quarantined_clients.append(cid)

        elif evt_type == EventType.LAYER1_CLIENT_PASSED:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.TRUSTED
                self.clients[cid].security_status = "L1_PASSED"
                self.clients[cid].layer1_status = "PASS"

        # 6. MARS Backdoor Analysis
        elif evt_type == EventType.MARS_STARTED:
            self.server_state["status"] = "MARS_FORENSIC_INSPECTION"
            for client in self.clients.values():
                if client.client_id not in self.quarantined_clients:
                    client.visual_state = VisualState.SCANNING

        elif evt_type == EventType.MARS_CLIENT_QUARANTINED:
            if cid and cid in self.clients:
                self.clients[cid].visual_state = VisualState.QUARANTINED
                self.clients[cid].security_status = "QUARANTINED_MARS"
                self.clients[cid].mars_status = "FLAGGED"
                if cid not in self.quarantined_clients:
                    self.quarantined_clients.append(cid)

        # 7. Layer 3 Robust Aggregation
        elif evt_type == EventType.AGGREGATION_STARTED:
            self.server_state["status"] = "AGGREGATING"
            for client in self.clients.values():
                if client.client_id not in self.quarantined_clients:
                    client.visual_state = VisualState.AGGREGATED
                    if client.client_id not in self.trusted_clients:
                        self.trusted_clients.append(client.client_id)

        elif evt_type == EventType.AGGREGATION_FINISHED:
            self.server_state["status"] = "AGGREGATED"

        # 8. Model Updated & Round Completed
        elif evt_type == EventType.GLOBAL_MODEL_UPDATED:
            self.server_state["status"] = "MODEL_UPDATED"

        elif evt_type == EventType.ROUND_COMPLETED:
            self.server_state["status"] = "COMPLETED"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current network state snapshot."""
        return {
            "round_id": self.round_id,
            "server_state": dict(self.server_state),
            "clients": {cid: node.to_dict() for cid, node in self.clients.items()},
            "active_packets": list(self.active_packets),
            "quarantined_clients": list(self.quarantined_clients),
            "trusted_clients": list(self.trusted_clients),
            "current_layer": self.current_layer,
        }
