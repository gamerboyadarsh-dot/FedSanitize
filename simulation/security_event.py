"""
FedSantize Simulation Engine — Security Event Model
===================================================
Defines the core data contract for all security and lifecycle events
emitted during simulation. Grounded in Phase 2 specifications.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import copy


@dataclass
class SecurityEvent:
    """
    Immutable representation of an atomic security or simulation event in FedSantize.
    
    Attributes
    ----------
    event_type : str
        One of the canonical EventType constants.
    round_id : int
        The FL round number this event belongs to.
    client_id : Optional[str]
        Target or source client ID (e.g., 'C1', 'C7'), or None for system/global events.
    layer : Optional[str]
        Security layer associated with the event: 'LAYER_1', 'MARS', 'LAYER_3', or None.
    timestamp : float
        Relative or logical simulation timestamp in seconds.
    severity : str
        Security severity level: 'INFO', 'WARNING', 'HIGH', or 'CRITICAL'.
    message : str
        Human-readable diagnostic or status message.
    payload : Dict[str, Any]
        Flexible dictionary containing verified, non-fabricated metrics and metadata.
    """
    event_type: str
    round_id: int
    client_id: Optional[str] = None
    layer: Optional[str] = None
    timestamp: float = 0.0
    severity: str = "INFO"
    message: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the event into a standard JSON-compatible Python dictionary."""
        return {
            "event_type": self.event_type,
            "round_id": self.round_id,
            "client_id": self.client_id,
            "layer": self.layer,
            "timestamp": float(self.timestamp),
            "severity": str(self.severity),
            "message": str(self.message),
            "payload": copy.deepcopy(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityEvent:
        """Constructs a SecurityEvent instance from a dictionary."""
        return cls(
            event_type=data.get("event_type", ""),
            round_id=int(data.get("round_id", 1)),
            client_id=data.get("client_id"),
            layer=data.get("layer"),
            timestamp=float(data.get("timestamp", 0.0)),
            severity=str(data.get("severity", "INFO")),
            message=str(data.get("message", "")),
            payload=data.get("payload", {}) or {},
        )
