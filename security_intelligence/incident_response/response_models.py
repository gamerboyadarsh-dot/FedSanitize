from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import uuid


class ResponseAction(str, Enum):
    MONITOR = "MONITOR"
    REDUCE_WEIGHT = "REDUCE_WEIGHT"
    TEMPORARY_ISOLATE = "TEMPORARY_ISOLATE"
    QUARANTINE = "QUARANTINE"
    REQUEST_REVIEW = "REQUEST_REVIEW"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStage(str, Enum):
    DETECTION = "DETECTION"
    INVESTIGATION = "INVESTIGATION"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    RESPONSE_SELECTION = "RESPONSE_SELECTION"
    ACTION = "ACTION"
    AUDITED = "AUDITED"


@dataclass
class ResponseDecision:
    incident_id: str
    client_id: Optional[str]
    action: ResponseAction
    severity: IncidentSeverity
    reason: str
    evidence: list = field(default_factory=list)
    duration_rounds: Optional[int] = None
    requires_review: bool = False
    timestamp: float = field(default_factory=time.time)
    confidence: Optional[float] = None
    missing_signals: list = field(default_factory=list)
    used_fallback_assessment: bool = False

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "client_id": self.client_id,
            "action": self.action.value,
            "severity": self.severity.value,
            "reason": self.reason,
            "evidence": list(self.evidence),
            "duration_rounds": self.duration_rounds,
            "requires_review": self.requires_review,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "missing_signals": list(self.missing_signals),
            "used_fallback_assessment": self.used_fallback_assessment,
        }


@dataclass
class QuarantineRecord:
    client_id: str
    reason: str
    start_round: int
    expiry_round: Optional[int]
    active: bool = True
    evidence: list = field(default_factory=list)
    review_status: str = "PENDING"
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "client_id": self.client_id,
            "reason": self.reason,
            "start_round": self.start_round,
            "expiry_round": self.expiry_round,
            "active": self.active,
            "evidence": list(self.evidence),
            "review_status": self.review_status,
        }


@dataclass
class Incident:
    """Tracks an incident's lifecycle from detection through to audit."""

    incident_id: str
    client_id: Optional[str]
    stage: IncidentStage
    created_round: Optional[int]
    evidence: list = field(default_factory=list)
    decision: Optional[ResponseDecision] = None

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "client_id": self.client_id,
            "stage": self.stage.value,
            "created_round": self.created_round,
            "evidence": list(self.evidence),
            "decision": self.decision.to_dict() if self.decision else None,
        }
