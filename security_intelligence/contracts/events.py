"""
Shared, dependency-free event vocabulary used across all Team B modules
(and consumable by Team A / the future orchestrator / the dashboards).

Nothing in this file imports FL code, numpy, torch, streamlit, etc. It is
pure stdlib so both teams can adopt it without version conflicts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import uuid
import time


class EventType(str, Enum):
    """Canonical event types emitted onto the audit chain / simulation feed."""

    LAYER1_ANOMALY = "LAYER1_ANOMALY"
    MARS_SUSPICION = "MARS_SUSPICION"
    TRUST_SCORE_CHANGED = "TRUST_SCORE_CHANGED"
    RISK_ESCALATED = "RISK_ESCALATED"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    RESPONSE_ACTIVATED = "RESPONSE_ACTIVATED"
    CLIENT_QUARANTINED = "CLIENT_QUARANTINED"
    CLIENT_RELEASED = "CLIENT_RELEASED"
    QUARANTINE_EXPIRED = "QUARANTINE_EXPIRED"
    AUDIT_VERIFIED = "AUDIT_VERIFIED"
    AUDIT_INTEGRITY_ALERT = "AUDIT_INTEGRITY_ALERT"
    THREAT_LEVEL_CHANGED = "THREAT_LEVEL_CHANGED"
    MODULE_WARNING = "MODULE_WARNING"
    GENERIC = "GENERIC"


class Severity(str, Enum):
    """Severity used for audit events / live incident feed entries."""

    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityEvent:
    """
    Generic, transport-agnostic event. This is the shape modules pass to the
    audit logger and to the simulation feed. It is intentionally simpler
    than AuditEvent (which additionally carries hash-chain fields) so that
    incident_response / soc code never needs to know about hashing.
    """

    event_type: EventType
    severity: Severity
    payload: dict = field(default_factory=dict)
    round_id: Optional[int] = None
    client_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    source_module: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "round_id": self.round_id,
            "client_id": self.client_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else str(self.event_type),
            "severity": self.severity.value if isinstance(self.severity, Severity) else str(self.severity),
            "payload": self.payload,
            "source_module": self.source_module,
        }
