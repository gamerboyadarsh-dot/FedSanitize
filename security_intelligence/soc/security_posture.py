"""
SecurityPosture: a small, append-only time series of PER-ROUND summarized
metrics (never full ML objects) used to drive the "Security Posture
Timeline" chart on the SOC dashboard.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .threat_models import ThreatAssessment


@dataclass
class PostureEntry:
    round_id: int
    threat_score: Optional[float] = None
    threat_level: Optional[str] = None
    active_incidents: Optional[int] = None
    quarantined_clients: Optional[int] = None
    average_trust: Optional[float] = None  # optional, supplied by Team A
    audit_integrity_valid: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "round_id": self.round_id,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level,
            "active_incidents": self.active_incidents,
            "quarantined_clients": self.quarantined_clients,
            "average_trust": self.average_trust,
            "audit_integrity_valid": self.audit_integrity_valid,
        }


class SecurityPosture:
    def __init__(self):
        self._entries: Dict[int, PostureEntry] = {}
        self._lock = threading.Lock()
        self._unrounded_counter = -1  # used when round_id is None

    def _entry_for(self, round_id: Optional[int]) -> PostureEntry:
        key = round_id if round_id is not None else self._unrounded_counter
        if round_id is None:
            self._unrounded_counter -= 1
        if key not in self._entries:
            self._entries[key] = PostureEntry(round_id=key)
        return self._entries[key]

    def record_threat(self, round_id: Optional[int], assessment: ThreatAssessment) -> None:
        with self._lock:
            entry = self._entry_for(round_id)
            entry.threat_score = assessment.score
            entry.threat_level = assessment.level.value

    def record_incident_state(
        self, round_id: Optional[int], active_incidents: int, quarantined_clients: int
    ) -> None:
        with self._lock:
            entry = self._entry_for(round_id)
            entry.active_incidents = active_incidents
            entry.quarantined_clients = quarantined_clients

    def record_audit_integrity(self, round_id: Optional[int], valid: bool) -> None:
        with self._lock:
            entry = self._entry_for(round_id)
            entry.audit_integrity_valid = valid

    def record_average_trust(self, round_id: Optional[int], average_trust: float) -> None:
        with self._lock:
            entry = self._entry_for(round_id)
            entry.average_trust = average_trust

    def timeline(self) -> List[dict]:
        with self._lock:
            ordered = sorted(self._entries.values(), key=lambda e: e.round_id)
            return [e.to_dict() for e in ordered]

    def latest(self) -> Optional[dict]:
        with self._lock:
            if not self._entries:
                return None
            ordered = sorted(self._entries.values(), key=lambda e: e.round_id)
            return ordered[-1].to_dict()
