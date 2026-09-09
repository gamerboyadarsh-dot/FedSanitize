"""
FedSantize Simulation Engine — Event Recorder
==============================================
Maintains chronological event streams, safe JSON-compatible serialization,
and multi-dimensional filtering across clients, layers, and severity.
Grounded in Phase 3 of the simulation engine specification.
"""

from __future__ import annotations
import json
from dataclasses import is_dataclass, asdict
from typing import List, Dict, Any, Optional, Union
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from .security_event import SecurityEvent


def sanitize_value(val: Any) -> Any:
    """
    Recursively sanitizes data types into pure JSON-serializable Python structures.
    Guarantees that huge model tensors/arrays are never stored directly in events.
    """
    if val is None or isinstance(val, (str, bool, int, float)):
        # Check for non-finite floats
        if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
            return 0.0
        return val

    # NumPy scalars
    if isinstance(val, (np.generic, np.number)):
        item = val.item()
        if isinstance(item, float) and (np.isnan(item) or np.isinf(item)):
            return 0.0
        return item

    # PyTorch Tensors
    if HAS_TORCH and isinstance(val, torch.Tensor):
        t = val.detach().cpu()
        if t.numel() == 0:
            return []
        if t.numel() == 1:
            item = t.item()
            return 0.0 if (np.isnan(item) or np.isinf(item)) else item
        if t.numel() <= 32:
            return t.tolist()
        # Large tensor: store statistical summary only
        t_float = t.float()
        return {
            "type": "TensorSummary",
            "shape": list(t.shape),
            "norm": float(torch.norm(t_float).item()),
            "mean": float(t_float.mean().item()),
            "std": float(t_float.std().item()),
        }

    # NumPy Arrays
    if isinstance(val, np.ndarray):
        if val.size <= 64:
            return val.tolist()
        return {
            "type": "ArraySummary",
            "shape": list(val.shape),
            "mean": float(np.mean(val)),
            "std": float(np.std(val)),
            "min": float(np.min(val)),
            "max": float(np.max(val)),
        }

    # Dataclasses
    if is_dataclass(val):
        return sanitize_value(asdict(val))

    # Dictionaries
    if isinstance(val, dict):
        return {str(k): sanitize_value(v) for k, v in val.items()}

    # Lists / Tuples / Sets
    if isinstance(val, (list, tuple, set)):
        return [sanitize_value(item) for item in val]

    # Fallback to string representation for other objects
    return str(val)


class EventRecorder:
    """
    In-memory ledger of SecurityEvent instances with chronological ordering,
    query filters, and JSON serialization.
    """
    def __init__(self):
        self._events: List[SecurityEvent] = []

    def record(
        self,
        event_or_type: Union[SecurityEvent, str],
        round_id: int = 1,
        client_id: Optional[str] = None,
        layer: Optional[str] = None,
        timestamp: Optional[float] = None,
        severity: str = "INFO",
        message: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        """
        Records a new event. Accepts either an instantiated SecurityEvent
        or raw parameters.
        """
        if isinstance(event_or_type, SecurityEvent):
            evt = event_or_type
            # Sanitize payload safely
            sanitized_payload = sanitize_value(evt.payload)
            final_event = SecurityEvent(
                event_type=evt.event_type,
                round_id=evt.round_id,
                client_id=evt.client_id,
                layer=evt.layer,
                timestamp=evt.timestamp if timestamp is None else timestamp,
                severity=evt.severity,
                message=evt.message,
                payload=sanitized_payload,
            )
        else:
            final_time = (
                timestamp if timestamp is not None
                else (self._events[-1].timestamp + 0.1 if self._events else 0.0)
            )
            final_event = SecurityEvent(
                event_type=event_or_type,
                round_id=round_id,
                client_id=client_id,
                layer=layer,
                timestamp=float(final_time),
                severity=severity,
                message=message,
                payload=sanitize_value(payload or {}),
            )

        self._events.append(final_event)
        return final_event

    def record_many(self, events: List[SecurityEvent]) -> None:
        """Records a batch of events in order."""
        for evt in events:
            self.record(evt)

    def get_events(self, sort_by_timestamp: bool = True) -> List[SecurityEvent]:
        """Returns all recorded events, optionally sorted by timestamp."""
        if sort_by_timestamp:
            return sorted(self._events, key=lambda e: (e.timestamp, e.round_id))
        return list(self._events)

    def get_events_by_round(self, round_id: int) -> List[SecurityEvent]:
        """Returns all events belonging to a specific round."""
        return [e for e in self.get_events() if e.round_id == round_id]

    def filter_by_client(self, client_id: str) -> List[SecurityEvent]:
        """Filters events associated with a given client ID."""
        return [e for e in self.get_events() if e.client_id == client_id]

    def filter_by_layer(self, layer: str) -> List[SecurityEvent]:
        """Filters events associated with a specific security layer."""
        return [e for e in self.get_events() if e.layer == layer]

    def filter_by_severity(self, severity: str) -> List[SecurityEvent]:
        """Filters events by severity level (e.g. 'HIGH', 'CRITICAL')."""
        return [e for e in self.get_events() if e.severity.upper() == severity.upper()]

    def clear(self) -> None:
        """Clears all recorded events."""
        self._events.clear()

    def count(self) -> int:
        """Returns the number of recorded events."""
        return len(self._events)

    def export_json(self, indent: Optional[int] = 2) -> str:
        """Exports all recorded events as a valid JSON string."""
        dicts = [e.to_dict() for e in self.get_events()]
        return json.dumps(dicts, indent=indent)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Exports all recorded events as a list of pure dictionaries."""
        return [e.to_dict() for e in self.get_events()]
