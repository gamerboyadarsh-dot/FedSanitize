"""
AuditEvent: the persisted, hash-chained record.

Distinct from contracts.events.SecurityEvent (which is what other Team B
modules emit). The audit_logger converts a SecurityEvent -> AuditEvent by
adding hash-chain fields and sanitizing the payload.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import uuid
import time

# Keys that must never be persisted in an audit payload, no matter what a
# caller passes in. Checked case-insensitively and recursively.
_FORBIDDEN_KEY_SUBSTRINGS = (
    "weight",
    "weights",
    "gradient",
    "gradients",
    "tensor",
    "state_dict",
    "model_state",
    "raw_update",
    "parameters",
)

_MAX_STRING_LEN = 2000
_MAX_LIST_LEN = 50


def sanitize_payload(payload: Any) -> Any:
    """
    Recursively strip anything that looks like model internals or is
    excessively large, so audit events stay small, safe, and diffable.
    Never raises — worst case it replaces a value with a placeholder.
    """
    try:
        if payload is None:
            return None
        if isinstance(payload, dict):
            clean = {}
            for k, v in payload.items():
                key_str = str(k).lower()
                if any(bad in key_str for bad in _FORBIDDEN_KEY_SUBSTRINGS):
                    clean[k] = "<redacted:model-internal>"
                    continue
                clean[k] = sanitize_payload(v)
            return clean
        if isinstance(payload, (list, tuple)):
            items = [sanitize_payload(v) for v in list(payload)[:_MAX_LIST_LEN]]
            if len(payload) > _MAX_LIST_LEN:
                items.append(f"<truncated:{len(payload) - _MAX_LIST_LEN}-more-items>")
            return items
        if isinstance(payload, (int, float, bool)) or payload is None:
            return payload
        if isinstance(payload, str):
            if len(payload) > _MAX_STRING_LEN:
                return payload[:_MAX_STRING_LEN] + "...<truncated>"
            return payload
        # Anything else (numpy scalars, custom objects, tensors that slipped
        # through) gets stringified defensively rather than stored raw.
        return f"<unsupported-type:{type(payload).__name__}>"
    except Exception as exc:  # never let sanitization crash the caller
        return f"<sanitize-error:{type(exc).__name__}>"


@dataclass
class AuditEvent:
    event_id: str
    timestamp: float
    round_id: Optional[int]
    client_id: Optional[str]
    event_type: str
    severity: str
    payload: dict
    previous_hash: str
    current_hash: str = ""

    @staticmethod
    def new(
        event_type: str,
        severity: str,
        payload: Optional[dict] = None,
        round_id: Optional[int] = None,
        client_id: Optional[str] = None,
    ) -> "AuditEvent":
        return AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            round_id=round_id,
            client_id=client_id,
            event_type=str(event_type),
            severity=str(severity),
            payload=sanitize_payload(payload or {}),
            previous_hash="",
            current_hash="",
        )

    def content_for_hash(self) -> dict:
        """Fields that participate in the hash — excludes current_hash itself."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "round_id": self.round_id,
            "client_id": self.client_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
        }

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "AuditEvent":
        return AuditEvent(
            event_id=d.get("event_id", ""),
            timestamp=d.get("timestamp", 0.0),
            round_id=d.get("round_id"),
            client_id=d.get("client_id"),
            event_type=d.get("event_type", "GENERIC"),
            severity=d.get("severity", "INFO"),
            payload=d.get("payload", {}) or {},
            previous_hash=d.get("previous_hash", ""),
            current_hash=d.get("current_hash", ""),
        )
