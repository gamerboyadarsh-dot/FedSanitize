"""
SOCSnapshot: the ONE stable view model the SOC dashboard (and main
dashboard summary cards) should read from. It is built once per round from
cached summaries — never by retraining, rerunning MARS, or touching model
internals. This is the hard boundary between backend and presentation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SOCSnapshot:
    timestamp: float
    round_id: Optional[int]
    threat_assessment: dict                 # ThreatAssessment.to_dict()
    active_incidents: List[dict]            # [ResponseDecision.to_dict(), ...]
    recent_events: List[dict]               # [AuditEvent.to_dict(), ...] (most recent first)
    audit_integrity: dict                   # IntegrityReport.to_dict()
    client_security_summary: List[dict]     # optional Team A trust data merged with quarantine state
    security_timeline: List[dict]           # SecurityPosture.timeline()
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "round_id": self.round_id,
            "threat_assessment": self.threat_assessment,
            "active_incidents": self.active_incidents,
            "recent_events": self.recent_events,
            "audit_integrity": self.audit_integrity,
            "client_security_summary": self.client_security_summary,
            "security_timeline": self.security_timeline,
            "warnings": self.warnings,
        }


def build_soc_snapshot(
    round_id: Optional[int],
    threat_assessment,
    incident_registry,
    quarantine_manager,
    audit_logger,
    security_posture,
    team_a_trust_records: Optional[List[dict]] = None,
    recent_events_limit: int = 25,
) -> SOCSnapshot:
    """
    Pulls together every Team B module's current state into one snapshot.
    Wrapped defensively: a failure reading any one module produces a
    warning and an empty/partial field rather than crashing dashboard
    rendering.
    """
    from ..audit_trail.integrity_verifier import verify_chain

    warnings: List[str] = []

    try:
        events = audit_logger.get_all_events() if audit_logger else []
        integrity = verify_chain(events)
        recent_events = [e.to_dict() for e in events[-recent_events_limit:][::-1]]
    except Exception as exc:
        warnings.append(f"audit read failed ({type(exc).__name__})")
        integrity_dict = {
            "valid": False,
            "total_events": 0,
            "broken_index": None,
            "expected_hash": None,
            "actual_hash": None,
            "message": "audit read failed",
        }
        recent_events = []
    else:
        integrity_dict = integrity.to_dict()

    try:
        active_incidents = [
            inc.decision.to_dict()
            for inc in incident_registry.all_incidents()
            if inc.decision and inc.decision.action.value in ("TEMPORARY_ISOLATE", "QUARANTINE", "REDUCE_WEIGHT")
        ]
    except Exception as exc:
        warnings.append(f"incident registry read failed ({type(exc).__name__})")
        active_incidents = []

    try:
        quarantined = set(quarantine_manager.active_clients())
    except Exception as exc:
        warnings.append(f"quarantine manager read failed ({type(exc).__name__})")
        quarantined = set()

    try:
        timeline = security_posture.timeline()
    except Exception as exc:
        warnings.append(f"security posture read failed ({type(exc).__name__})")
        timeline = []

    client_summary = []
    trust_by_client = {r.get("client_id"): r for r in (team_a_trust_records or []) if r.get("client_id")}
    all_client_ids = set(trust_by_client.keys()) | quarantined
    for cid in sorted(all_client_ids):
        trust_row = trust_by_client.get(cid, {})
        client_summary.append(
            {
                "client_id": cid,
                "trust_score": trust_row.get("trust_score"),
                "trust_level": trust_row.get("trust_level"),
                "quarantined": cid in quarantined,
            }
        )

    return SOCSnapshot(
        timestamp=time.time(),
        round_id=round_id,
        threat_assessment=threat_assessment.to_dict() if threat_assessment else {},
        active_incidents=active_incidents,
        recent_events=recent_events,
        audit_integrity=integrity_dict,
        client_security_summary=client_summary,
        security_timeline=timeline,
        warnings=warnings,
    )
