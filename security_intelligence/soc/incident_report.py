"""
build_incident_report(): assembles a structured (non-fabricated) report
from a ResponseDecision plus optional audit/threat context. Every field is
labeled as an observed fact, a policy inference, or explicitly unavailable
— never blended together as prose that implies more certainty than exists.
"""

from typing import Optional


def build_incident_report(
    decision,                     # incident_response.ResponseDecision
    audit_integrity=None,          # audit_trail.IntegrityReport, optional
    threat_assessment=None,        # soc.ThreatAssessment, optional
) -> dict:
    observed = {
        "incident_id": decision.incident_id,
        "affected_client": decision.client_id,
        "response_action_taken": decision.action.value,
        "requires_human_review": decision.requires_review,
        "timestamp": decision.timestamp,
    }

    inference = {
        "assessed_severity": decision.severity.value,
        "reason": decision.reason,
        "assessment_confidence": decision.confidence,
        "assessment_source": "fallback_heuristic" if decision.used_fallback_assessment else "team_a_risk_assessment",
    }

    unavailable = list(decision.missing_signals)

    if threat_assessment is not None:
        inference["global_threat_level_at_time"] = threat_assessment.level.value
        inference["global_threat_score_at_time"] = threat_assessment.score
        unavailable.extend(threat_assessment.missing_signals)
    else:
        unavailable.append("global_threat_assessment")

    if audit_integrity is not None:
        observed["audit_integrity_valid"] = audit_integrity.valid
        observed["audit_chain_length_at_time"] = audit_integrity.total_events
    else:
        unavailable.append("audit_integrity_status")

    return {
        "observed_facts": observed,
        "inferences": inference,
        "unavailable_or_unverified": sorted(set(unavailable)),
        "evidence": list(decision.evidence),
    }
