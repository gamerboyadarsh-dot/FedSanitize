"""
compute_threat_score(): turns a dict of optional 0..1 signals into an
explainable 0..100 ThreatAssessment.

CRITICAL MISSING DATA RULE (per master prompt): a missing signal is never
silently treated as 0. Instead its weight is excluded and the remaining
weights are renormalized, and the assessment exposes exactly how much
signal coverage it actually had.
"""

from typing import Optional

from .threat_models import ThreatAssessment, ThreatLevel

# Default relative weights — configuration-driven via security_config.
DEFAULT_WEIGHTS = {
    "malicious_client_ratio": 0.20,
    "layer1_severity": 0.15,
    "mars_severity": 0.20,
    "incident_severity": 0.15,
    "attack_success_rate": 0.15,
    "quarantine_activity": 0.10,
    "team_a_trust_distribution": 0.03,
    "team_a_risk_distribution": 0.02,
}

DEFAULT_LEVEL_THRESHOLDS = {
    "medium": 30.0,
    "high": 60.0,
    "critical": 85.0,
}

_HUMAN_NAMES = {
    "malicious_client_ratio": "Suspicious client ratio",
    "layer1_severity": "Layer 1 anomaly severity",
    "mars_severity": "MARS evidence",
    "incident_severity": "Incident severity",
    "attack_success_rate": "Attack success rate",
    "quarantine_activity": "Quarantine activity",
    "team_a_trust_distribution": "Trust distribution (Team A)",
    "team_a_risk_distribution": "Risk distribution (Team A)",
}


def _level_for(score: float, thresholds: dict) -> ThreatLevel:
    if score >= thresholds["critical"]:
        return ThreatLevel.CRITICAL
    if score >= thresholds["high"]:
        return ThreatLevel.HIGH
    if score >= thresholds["medium"]:
        return ThreatLevel.MEDIUM
    return ThreatLevel.LOW


def compute_threat_score(
    signals: dict,
    weights: Optional[dict] = None,
    level_thresholds: Optional[dict] = None,
    round_id: Optional[int] = None,
) -> ThreatAssessment:
    """
    signals: dict mapping signal name -> float in [0,1], or None/absent if
    unavailable. Unknown keys are ignored; known keys with value None are
    treated as missing (not zero).
    """
    weights = weights or DEFAULT_WEIGHTS
    thresholds = level_thresholds or DEFAULT_LEVEL_THRESHOLDS

    available = {}
    missing = []
    for name, weight in weights.items():
        value = signals.get(name)
        if value is None:
            missing.append(name)
            continue
        try:
            value = max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            missing.append(name)
            continue
        available[name] = value

    total_weight_available = sum(weights[n] for n in available)
    total_weight_all = sum(weights.values()) or 1.0
    coverage = total_weight_available / total_weight_all if total_weight_all else 0.0

    if total_weight_available <= 0:
        # No usable signal at all — cannot honestly claim a score.
        return ThreatAssessment(
            score=0.0,
            level=ThreatLevel.LOW,
            confidence=0.0,
            coverage=0.0,
            contributing_factors=[],
            missing_signals=[_HUMAN_NAMES.get(m, m) for m in missing],
            round_id=round_id,
        )

    contributing_factors = []
    score = 0.0
    for name, value in available.items():
        normalized_weight = weights[name] / total_weight_available
        contribution = normalized_weight * value * 100.0
        score += contribution
        contributing_factors.append(
            {
                "name": _HUMAN_NAMES.get(name, name),
                "raw_signal": name,
                "value": round(value, 3),
                "normalized_weight": round(normalized_weight, 3),
                "contribution": round(contribution, 2),
            }
        )

    contributing_factors.sort(key=lambda f: f["contribution"], reverse=True)
    score = max(0.0, min(100.0, score))
    level = _level_for(score, thresholds)

    # Confidence tracks coverage but is never a bare guess: full coverage
    # with strong signals still tops out just under 1.0.
    confidence = round(min(0.98, coverage), 3)

    return ThreatAssessment(
        score=score,
        level=level,
        confidence=confidence,
        coverage=round(coverage, 3),
        contributing_factors=contributing_factors,
        missing_signals=[_HUMAN_NAMES.get(m, m) for m in missing],
        round_id=round_id,
    )
