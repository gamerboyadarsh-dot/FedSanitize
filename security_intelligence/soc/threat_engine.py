"""
ThreatIntelligenceEngine: stateful wrapper around compute_threat_score()
that tracks the previous level (to emit THREAT_LEVEL_CHANGED audit events
only on actual transitions) and feeds SecurityPosture history.
"""

from __future__ import annotations

from typing import Optional

from .security_posture import SecurityPosture
from .threat_models import ThreatAssessment, ThreatLevel
from .threat_scoring import DEFAULT_LEVEL_THRESHOLDS, DEFAULT_WEIGHTS, compute_threat_score


class ThreatIntelligenceEngine:
    def __init__(
        self,
        weights: Optional[dict] = None,
        level_thresholds: Optional[dict] = None,
        audit_logger=None,
        posture: Optional[SecurityPosture] = None,
    ):
        self.weights = weights or DEFAULT_WEIGHTS
        self.level_thresholds = level_thresholds or DEFAULT_LEVEL_THRESHOLDS
        self.audit_logger = audit_logger
        self.posture = posture or SecurityPosture()
        self._last_level: Optional[ThreatLevel] = None
        self.last_assessment: Optional[ThreatAssessment] = None

    def assess(self, signals: dict, round_id: Optional[int] = None) -> ThreatAssessment:
        assessment = compute_threat_score(
            signals=signals,
            weights=self.weights,
            level_thresholds=self.level_thresholds,
            round_id=round_id,
        )

        if self.audit_logger is not None and assessment.level != self._last_level:
            try:
                self.audit_logger.log_event(
                    event_type="THREAT_LEVEL_CHANGED",
                    severity="WARNING" if assessment.level in (ThreatLevel.LOW, ThreatLevel.MEDIUM) else "CRITICAL",
                    payload={
                        "previous_level": self._last_level.value if self._last_level else None,
                        "new_level": assessment.level.value,
                        "score": assessment.score,
                        "coverage": assessment.coverage,
                    },
                    round_id=round_id,
                )
            except Exception:
                pass  # threat scoring/audit must never break the FL pipeline

        self._last_level = assessment.level
        self.last_assessment = assessment
        self.posture.record_threat(round_id, assessment)
        return assessment
