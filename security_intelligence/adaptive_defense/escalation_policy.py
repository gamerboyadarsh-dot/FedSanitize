"""
FedSanitize — Security Intelligence: Escalation Policy
=======================================================
Converts a threat score + signal breakdown into a SecurityDecision
with routing action, escalation flag, and recommended actions.

Thresholds are configuration-driven. No randomness. Pure computation.

Default thresholds:
  EMERGENCY_FALLBACK   : threat_score >= 0.75
  ISOLATE_SUSPECTS     : threat_score >= 0.50
  HEIGHTENED_MONITORING: threat_score >= 0.25
  STANDARD             : threat_score < 0.25
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from ..contracts.security_decision import SecurityDecision
from .routing_decision import (
    RoutingAction,
    ThreatLevel,
    threat_score_to_level,
    threat_score_to_action,
)

logger = logging.getLogger("FedSanitize.SecurityIntelligence.EscalationPolicy")


class EscalationPolicy:
    """
    Threshold-driven escalation and routing decision engine.

    Parameters
    ----------
    config : dict | None
        Optional threshold overrides. Keys:
          escalation_threshold          : float = 0.75
          isolate_threshold             : float = 0.50
          monitoring_threshold          : float = 0.25
          escalation_requires_mars      : bool = False
          min_suspect_rate_for_escalation: float = 0.0
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}

    def _t(self, key: str, default: float) -> float:
        try:
            return float(self._config.get(key, default))
        except (TypeError, ValueError):
            return default

    def _b(self, key: str, default: bool) -> bool:
        try:
            return bool(self._config.get(key, default))
        except (TypeError, ValueError):
            return default

    def decide(
        self,
        threat_score: float,
        signal_breakdown: Dict[str, Any],
        active_defenses: List[str],
        round_id: Optional[int] = None,
        history: Optional[List[SecurityDecision]] = None,
        confidence: float = 0.0,
        coverage: float = 0.0,
        missing_signals: Optional[List[str]] = None,
        mode: str = "observe",
    ) -> SecurityDecision:
        """
        Produces a SecurityDecision from the current round's threat assessment.

        Parameters
        ----------
        threat_score : float
            Normalized threat score in [0.0, 1.0].
        signal_breakdown : dict
            Per-signal breakdown from RiskAssessor.
        active_defenses : list[str]
            Active defense layer labels.
        round_id : int | None
            Current FL round number.
        history : list[SecurityDecision] | None
            Prior round decisions (used for escalation trend analysis).
        confidence : float
            How much real signal backed the threat score (from RiskAssessor).
        coverage : float
            Fraction of expected signal sources available this round.
        missing_signals : list[str] | None
            Signal sources absent this round. Never treated as benign.
        mode : str
            Adaptive-defense mode. Only "observe" is supported in this
            version — see AdaptiveDefenseOrchestrator for enforcement.

        Returns
        -------
        SecurityDecision
        """
        escalation_thresh = self._t("escalation_threshold", 0.75)
        isolate_thresh = self._t("isolate_threshold", 0.50)
        monitor_thresh = self._t("monitoring_threshold", 0.25)
        requires_mars = self._b("escalation_requires_mars", False)

        # Determine base routing action from score
        if threat_score >= escalation_thresh:
            action = RoutingAction.EMERGENCY_FALLBACK
        elif threat_score >= isolate_thresh:
            action = RoutingAction.ISOLATE_SUSPECTS
        elif threat_score >= monitor_thresh:
            action = RoutingAction.HEIGHTENED_MONITORING
        else:
            action = RoutingAction.STANDARD

        # Optional guard: escalation only if MARS also flagged suspects
        if (
            action == RoutingAction.EMERGENCY_FALLBACK
            and requires_mars
            and signal_breakdown.get("mars_suspect_count", 0) == 0
        ):
            action = RoutingAction.ISOLATE_SUSPECTS
            logger.debug(
                "[EscalationPolicy] Emergency downgraded to ISOLATE: "
                "escalation_requires_mars=True but MARS found no suspects"
            )

        # Check optional minimum MARS suspect rate gate
        min_suspect_rate = self._t("min_suspect_rate_for_escalation", 0.0)
        if (
            action in (RoutingAction.EMERGENCY_FALLBACK, RoutingAction.ISOLATE_SUSPECTS)
            and min_suspect_rate > 0.0
        ):
            mars_rate = signal_breakdown.get("mars_suspect_rate", 0.0)
            if mars_rate < min_suspect_rate:
                action = RoutingAction.HEIGHTENED_MONITORING
                logger.debug(
                    f"[EscalationPolicy] Downgraded to HEIGHTENED_MONITORING: "
                    f"mars_rate={mars_rate:.3f} < min={min_suspect_rate:.3f}"
                )

        # Escalation is triggered for EMERGENCY_FALLBACK always,
        # and for repeated HIGH/CRITICAL decisions in history
        escalation_triggered = action == RoutingAction.EMERGENCY_FALLBACK
        if not escalation_triggered and history:
            recent_severe = sum(
                1 for d in history[-3:]
                if d.routing_action in (
                    RoutingAction.ISOLATE_SUSPECTS.value,
                    RoutingAction.EMERGENCY_FALLBACK.value,
                )
            )
            if recent_severe >= 2:
                escalation_triggered = True
                logger.info(
                    f"[EscalationPolicy] Round {round_id}: escalation triggered by "
                    f"{recent_severe} consecutive severe decisions in last 3 rounds"
                )

        threat_level = threat_score_to_level(threat_score)

        # Recommended actions (for Team B / SOC integration)
        recommended_actions = self._build_recommendations(
            action, signal_breakdown, escalation_triggered
        )

        # Human-readable reason
        reason = self._build_reason(action, threat_score, signal_breakdown, escalation_triggered)

        evidence = {
            "threat_score": threat_score,
            "l1_anomaly_rate": signal_breakdown.get("l1_anomaly_rate", 0.0),
            "mars_suspect_rate": signal_breakdown.get("mars_suspect_rate", 0.0),
            "mean_cbe_ratio": signal_breakdown.get("mean_cbe_ratio", 0.0),
            "trust_risk_rate": signal_breakdown.get("trust_risk_rate", 0.0),
            "history_penalty": signal_breakdown.get("history_penalty", 0.0),
            "n_clients": signal_breakdown.get("n_clients", 0),
        }

        # Aggregation is a suggestion only — Team A never enforces it.
        if action == RoutingAction.EMERGENCY_FALLBACK:
            aggregation_recommendation = "CONSERVATIVE_TRIMMED_MEAN_FALLBACK"
        elif action == RoutingAction.ISOLATE_SUSPECTS:
            aggregation_recommendation = "EXCLUDE_FLAGGED_CLIENTS"
        else:
            aggregation_recommendation = "USE_DEFAULT_AGGREGATION"

        return SecurityDecision(
            round_id=round_id,
            threat_level=threat_level.value,
            threat_score=threat_score,
            routing_action=action.value,
            active_defenses=active_defenses,
            escalation_triggered=escalation_triggered,
            reason=reason,
            evidence=evidence,
            recommended_actions=recommended_actions,
            signal_breakdown=signal_breakdown,
            monitoring_required=action != RoutingAction.STANDARD,
            aggregation_recommendation=aggregation_recommendation,
            confidence=confidence,
            coverage=coverage,
            missing_signals=list(missing_signals or []),
            mode=mode,
        )

    def _build_reason(
        self,
        action: RoutingAction,
        score: float,
        breakdown: Dict[str, Any],
        escalation: bool,
    ) -> str:
        """Builds a human-readable decision reason string."""
        parts = [f"threat_score={score:.3f}"]
        if breakdown.get("l1_anomaly_count", 0) > 0:
            parts.append(f"L1_anomalies={breakdown['l1_anomaly_count']}")
        if breakdown.get("mars_suspect_count", 0) > 0:
            parts.append(f"MARS_suspects={breakdown['mars_suspect_count']}")
        if breakdown.get("mean_cbe_ratio", 0.0) > 0.05:
            parts.append(f"CBE_ratio={breakdown['mean_cbe_ratio']:.3f}")
        if escalation:
            parts.append("ESCALATION_TRIGGERED")
        return f"{action.value}: " + ", ".join(parts)

    def _build_recommendations(
        self,
        action: RoutingAction,
        breakdown: Dict[str, Any],
        escalation: bool,
    ) -> List[str]:
        """Generates ordered recommended actions list for Team B / SOC."""
        recs: List[str] = []

        if action == RoutingAction.EMERGENCY_FALLBACK:
            recs.append("HALT_AGGREGATION_OR_USE_CONSERVATIVE_FALLBACK")
            recs.append("NOTIFY_SOC_OPERATOR")
            recs.append("REVIEW_BACKDOOR_SUSPECTS_IMMEDIATELY")
        elif action == RoutingAction.ISOLATE_SUSPECTS:
            recs.append("EXCLUDE_MARS_FLAGGED_CLIENTS_FROM_AGGREGATION")
            recs.append("INCREASE_MARS_SENSITIVITY_NEXT_ROUND")
        elif action == RoutingAction.HEIGHTENED_MONITORING:
            recs.append("LOG_ANOMALOUS_CLIENTS_FOR_REVIEW")
            recs.append("INCREASE_LAYER1_STRICTNESS")

        if escalation:
            recs.append("INITIATE_INCIDENT_RESPONSE_PROTOCOL")

        if breakdown.get("trust_quarantined_count", 0) > 0:
            recs.append("REVIEW_QUARANTINED_CLIENT_REPUTATION_RECORDS")

        if not recs:
            recs.append("NO_ACTION_REQUIRED")

        return recs
