"""
IncidentResponseEngine: converts security evidence into a reversible,
policy-driven ResponseDecision.

LIFECYCLE
  DETECTION -> INVESTIGATION -> RISK_ASSESSMENT -> RESPONSE_SELECTION
  -> ACTION -> AUDIT EVENT

Works standalone (no Team A). If a TeamARiskInput with a populated
risk_level is supplied, it is used as the authoritative severity signal.
Otherwise the engine falls back to its own conservative, config-driven
assessment over raw evidence (Layer 1 / MARS / repeated-incident signals)
and clearly marks the decision as `used_fallback_assessment=True` with a
lower confidence and any missing signals recorded — it never fabricates
data or treats an absent signal as "safe".
"""

from __future__ import annotations

import uuid
from typing import Optional

from ..contracts.security_decision import RiskLevel, TeamARiskInput
from .incident_registry import IncidentRegistry
from .quarantine_manager import QuarantineManager
from .response_models import (
    Incident,
    IncidentSeverity,
    IncidentStage,
    ResponseAction,
    ResponseDecision,
)
from .response_policy import ResponsePolicy

_RISK_TO_SEVERITY = {
    RiskLevel.LOW: IncidentSeverity.LOW,
    RiskLevel.MEDIUM: IncidentSeverity.MEDIUM,
    RiskLevel.HIGH: IncidentSeverity.HIGH,
    RiskLevel.CRITICAL: IncidentSeverity.CRITICAL,
}


class IncidentResponseEngine:
    def __init__(
        self,
        policy: Optional[ResponsePolicy] = None,
        quarantine_manager: Optional[QuarantineManager] = None,
        registry: Optional[IncidentRegistry] = None,
        audit_logger=None,
    ):
        self.policy = policy or ResponsePolicy()
        self.quarantine_manager = quarantine_manager or QuarantineManager()
        self.registry = registry or IncidentRegistry()
        self.audit_logger = audit_logger  # optional; anything with .log_event(...)

    # ---- risk assessment -------------------------------------------------
    def _fallback_assess(self, evidence: dict) -> tuple[IncidentSeverity, float, list]:
        """
        Conservative, explainable fallback used only when Team A hasn't
        supplied a risk_level. Missing evidence is recorded, never treated
        as benign (it simply doesn't contribute to escalating severity).
        """
        thresholds = self.policy.fallback_thresholds
        missing = []
        severity = IncidentSeverity.LOW
        reasons = []

        mars = evidence.get("mars_severity")
        if mars is None:
            missing.append("mars_severity")
        else:
            if mars >= thresholds["mars_severity_critical"]:
                severity = IncidentSeverity.CRITICAL
                reasons.append(f"MARS severity {mars:.2f} >= critical threshold")
            elif mars >= thresholds["mars_severity_high"] and severity.value != "CRITICAL":
                severity = IncidentSeverity.HIGH
                reasons.append(f"MARS severity {mars:.2f} >= high threshold")

        layer1 = evidence.get("layer1_anomaly_score")
        if layer1 is None:
            missing.append("layer1_anomaly_score")
        else:
            if layer1 >= thresholds["layer1_anomaly_critical"] and severity != IncidentSeverity.CRITICAL:
                severity = IncidentSeverity.CRITICAL
                reasons.append(f"Layer1 anomaly {layer1:.2f} >= critical threshold")
            elif layer1 >= thresholds["layer1_anomaly_high"] and severity == IncidentSeverity.LOW:
                severity = IncidentSeverity.MEDIUM
                reasons.append(f"Layer1 anomaly {layer1:.2f} >= high threshold")

        repeated = evidence.get("repeated_incident_count")
        if repeated is None:
            missing.append("repeated_incident_count")
        elif repeated >= thresholds["repeated_incident_escalation_count"] and severity == IncidentSeverity.LOW:
            severity = IncidentSeverity.MEDIUM
            reasons.append(f"{repeated} prior incidents for this client")

        if evidence.get("attack_confirmed") is True:
            severity = IncidentSeverity.CRITICAL
            reasons.append("Attack explicitly confirmed by pipeline evidence")
        elif "attack_confirmed" not in evidence:
            missing.append("attack_confirmed")

        # Confidence drops with each missing signal; fallback mode is
        # inherently less confident than a Team A risk assessment.
        base_confidence = 0.55
        confidence = max(0.15, base_confidence - 0.1 * len(missing))

        if not reasons:
            reasons.append("No signals crossed escalation thresholds; defaulting to LOW/monitor")

        return severity, confidence, missing, reasons

    def assess(
        self,
        evidence: dict,
        team_a_risk: Optional[TeamARiskInput] = None,
    ):
        """Returns (severity, confidence, missing_signals, reasons, used_fallback)."""
        if team_a_risk is not None and team_a_risk.is_present():
            severity = _RISK_TO_SEVERITY.get(team_a_risk.risk_level, IncidentSeverity.LOW)
            reasons = list(team_a_risk.evidence) or ["Team A risk assessment"]
            return severity, team_a_risk.confidence, list(team_a_risk.missing_signals), reasons, False

        severity, confidence, missing, reasons = self._fallback_assess(evidence)
        return severity, confidence, missing, reasons, True

    # ---- main entrypoint --------------------------------------------------
    def handle(
        self,
        evidence: dict,
        round_id: Optional[int] = None,
        client_id: Optional[str] = None,
        team_a_risk: Optional[TeamARiskInput] = None,
    ) -> ResponseDecision:
        incident_id = str(uuid.uuid4())
        incident = Incident(
            incident_id=incident_id,
            client_id=client_id,
            stage=IncidentStage.DETECTION,
            created_round=round_id,
            evidence=[evidence],
        )
        self.registry.register(incident)

        # INVESTIGATION -> RISK_ASSESSMENT
        self.registry.update_stage(incident_id, IncidentStage.INVESTIGATION)
        severity, confidence, missing, reasons, used_fallback = self.assess(evidence, team_a_risk)
        self.registry.update_stage(incident_id, IncidentStage.RISK_ASSESSMENT)

        # RESPONSE_SELECTION
        policy_entry = self.policy.entry_for(severity)
        self.registry.update_stage(incident_id, IncidentStage.RESPONSE_SELECTION)

        decision = ResponseDecision(
            incident_id=incident_id,
            client_id=client_id,
            action=policy_entry.action,
            severity=severity,
            reason="; ".join(reasons),
            evidence=[evidence],
            duration_rounds=policy_entry.duration_rounds,
            requires_review=policy_entry.requires_review,
            confidence=confidence,
            missing_signals=missing,
            used_fallback_assessment=used_fallback,
        )

        # ACTION
        warnings = []
        if policy_entry.action in (ResponseAction.QUARANTINE, ResponseAction.TEMPORARY_ISOLATE) and client_id:
            expiry = (round_id or 0) + (policy_entry.duration_rounds or 0) if policy_entry.duration_rounds else None
            qres = self.quarantine_manager.add(
                client_id=client_id,
                reason=decision.reason,
                start_round=round_id or 0,
                expiry_round=expiry,
                evidence=[evidence],
            )
            if qres.warning:
                warnings.append(qres.warning)

        self.registry.update_stage(incident_id, IncidentStage.ACTION)
        incident.decision = decision

        # AUDIT EVENT (best-effort; must never break response flow)
        if self.audit_logger is not None:
            try:
                self.audit_logger.log_event(
                    event_type="INCIDENT_CREATED",
                    severity=severity.value,
                    payload={
                        "incident_id": incident_id,
                        "action": decision.action.value,
                        "reason": decision.reason,
                        "confidence": confidence,
                        "missing_signals": missing,
                        "used_fallback_assessment": used_fallback,
                    },
                    round_id=round_id,
                    client_id=client_id,
                )
                self.registry.update_stage(incident_id, IncidentStage.AUDITED)
            except Exception as exc:
                warnings.append(f"audit logging failed ({type(exc).__name__}); incident recorded without audit entry")

        decision.evidence = decision.evidence + ([f"warning: {w}" for w in warnings] if warnings else [])
        return decision

    # ---- quarantine lifecycle passthroughs --------------------------------
    def expire_quarantines(self, current_round: int):
        return self.quarantine_manager.expire_due(current_round)

    def release_client(self, client_id: str, review_status: str = "RELEASED"):
        return self.quarantine_manager.release(client_id, review_status=review_status)
