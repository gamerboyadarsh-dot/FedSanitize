"""
FedSanitize — Security Intelligence: Adaptive Defense Orchestrator
==================================================================
Feature 2: Adaptive Defense Orchestrator

Coordinates round-level risk assessment and routing decisions.
Integrates RiskAssessor (threat scoring) and EscalationPolicy (decision).

This module is the sole public API for Feature 2. All routing
decisions pass through evaluate_round().

Thread safety: NOT thread-safe (single-threaded FL loop assumed).
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from ..contracts.security_context import SecurityContext
from ..contracts.security_decision import SecurityDecision
from .risk_assessor import RiskAssessor
from .escalation_policy import EscalationPolicy
from .routing_decision import RoutingAction, ThreatLevel

logger = logging.getLogger("FedSanitize.SecurityIntelligence.AdaptiveDefense")


class AdaptiveDefenseOrchestrator:
    """
    Feature 2: Adaptive Defense Orchestrator.

    Evaluates each FL round and produces an actionable SecurityDecision:
      1. RiskAssessor computes a threat score from SecurityContexts.
      2. EscalationPolicy maps the score to a RoutingAction + escalation flag.
      3. Decision is logged and appended to history.

    Public API
    ----------
    evaluate_round(contexts, trust_engine=None) → SecurityDecision
    get_active_defenses()                       → list[str]
    get_history()                               → list[SecurityDecision]

    Parameters
    ----------
    config : dict | None
        Shared config for both RiskAssessor and EscalationPolicy.
        See SecurityIntelligenceConfig for all keys.
    """

    #: Only "observe" is implemented in this version. An "active" mode is
    #: reserved for a future release and must never be enabled implicitly —
    #: see _resolve_mode().
    SUPPORTED_MODES = ("observe",)

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._assessor = RiskAssessor(config=self._config)
        self._policy = EscalationPolicy(config=self._config)
        self._history: List[SecurityDecision] = []
        self._current_active_defenses: List[str] = []
        self._mode = self._resolve_mode(self._config)

    def _resolve_mode(self, config: Dict[str, Any]) -> str:
        """
        Resolves the configured adaptive-defense mode.

        Any value other than "observe" is not yet implemented — it is
        downgraded to "observe" with a loud warning rather than silently
        accepted, so a typo or a premature config change can never enable
        enforcement behavior this module doesn't actually have.
        """
        requested = str(config.get("adaptive_defense_mode", "observe")).lower()
        if requested not in self.SUPPORTED_MODES:
            logger.warning(
                f"[AdaptiveDefense] mode='{requested}' is not supported in this "
                f"version — forcing 'observe'. Active enforcement modes are not "
                f"implemented; this module only ever recommends."
            )
            return "observe"
        return requested

    # -----------------------------------------------------------------------
    # Primary API
    # -----------------------------------------------------------------------

    def evaluate_round(
        self,
        contexts: List[SecurityContext],
        trust_engine: Optional[Any] = None,  # ClientTrustEngine (avoid circular import)
    ) -> SecurityDecision:
        """
        Evaluates the security posture of the current FL round.

        Parameters
        ----------
        contexts : list[SecurityContext]
            All per-client security contexts for this round.
        trust_engine : ClientTrustEngine | None
            Optional reference to the trust engine for reputation signals.
            If None, trust-based signals are omitted from threat scoring.

        Returns
        -------
        SecurityDecision
            Routing decision, threat level, escalation flag, recommendations.
        """
        round_id = None
        if contexts:
            round_id = contexts[0].round_id  # all should share the same round_id

        # --- Trust summary (optional signal) ---
        trust_summary = None
        if trust_engine is not None:
            try:
                trust_summary = trust_engine.get_summary()
            except Exception as e:
                logger.warning(f"[AdaptiveDefense] Failed to get trust summary: {e}")

        # --- Threat assessment ---
        assessment = self._assessor.assess(
            contexts=contexts,
            trust_summary=trust_summary,
        )

        threat_score = assessment["threat_score"]
        signal_breakdown = assessment["signal_breakdown"]
        active_defenses = assessment["active_defenses"]
        confidence = assessment.get("confidence", 0.0)
        coverage = assessment.get("coverage", 0.0)
        missing_signals = assessment.get("missing_signals", [])

        # --- Escalation decision ---
        decision = self._policy.decide(
            threat_score=threat_score,
            signal_breakdown=signal_breakdown,
            active_defenses=active_defenses,
            round_id=round_id,
            history=self._history,
            confidence=confidence,
            coverage=coverage,
            missing_signals=missing_signals,
            mode=self._mode,
        )

        # --- Store history and update active defenses ---
        self._history.append(decision)
        self._current_active_defenses = active_defenses

        logger.info(
            f"[AdaptiveDefense] Round {round_id}: "
            f"threat={threat_score:.3f} ({decision.threat_level}) → "
            f"{decision.routing_action}"
            + (" [ESCALATED]" if decision.escalation_triggered else "")
        )

        return decision

    # -----------------------------------------------------------------------
    # Query API
    # -----------------------------------------------------------------------

    def get_active_defenses(self) -> List[str]:
        """Returns the active defense layers from the last evaluated round."""
        return list(self._current_active_defenses)

    def get_history(self) -> List[SecurityDecision]:
        """Returns all SecurityDecisions produced across all evaluated rounds."""
        return list(self._history)

    def get_last_decision(self) -> Optional[SecurityDecision]:
        """Returns the most recent SecurityDecision, or None if no rounds evaluated."""
        return self._history[-1] if self._history else None

    def get_threat_trend(self) -> List[float]:
        """Returns the ordered history of threat scores (one per round evaluated)."""
        return [d.threat_score for d in self._history]

    def get_mode(self) -> str:
        """Returns the resolved adaptive-defense mode (always 'observe' today)."""
        return self._mode

    def is_escalated(self) -> bool:
        """True if the most recent decision triggered escalation."""
        last = self.get_last_decision()
        return last.escalation_triggered if last else False

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns a summary dict of overall defense posture.
        Suitable for logging or dashboard export.
        """
        history = self._history
        if not history:
            return {
                "rounds_evaluated": 0,
                "current_threat_level": "UNKNOWN",
                "current_routing_action": "STANDARD",
                "escalation_count": 0,
                "avg_threat_score": 0.0,
                "peak_threat_score": 0.0,
                "active_defenses": [],
            }

        last = history[-1]
        scores = [d.threat_score for d in history]
        escalations = sum(1 for d in history if d.escalation_triggered)

        return {
            "rounds_evaluated": len(history),
            "current_threat_level": last.threat_level,
            "current_routing_action": last.routing_action,
            "escalation_count": escalations,
            "avg_threat_score": round(sum(scores) / len(scores), 4),
            "peak_threat_score": round(max(scores), 4),
            "active_defenses": self._current_active_defenses,
            "last_round_id": last.round_id,
            "last_recommendations": last.recommended_actions,
        }
