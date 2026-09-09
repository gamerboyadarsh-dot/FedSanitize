"""
FedSanitize — Security Intelligence: Risk Assessor
===================================================
Computes a normalized threat score for the current FL round from
a list of SecurityContexts and the current trust engine state.

Design rules:
  - Pure computation: no state, no side effects.
  - All signals bounded and weighted.
  - No randomness.
  - Returns detailed breakdown for explainability.

Signal sources and default weights:
  1. Layer 1 anomaly rate                 weight=0.25
  2. MARS suspect rate                    weight=0.30
  3. Mean CBE concentration ratio         weight=0.15
  4. HIGH_RISK + QUARANTINED client rate  weight=0.20
  5. Consecutive-incident history penalty weight=0.10
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from ..contracts.security_context import SecurityContext

logger = logging.getLogger("FedSanitize.SecurityIntelligence.RiskAssessor")


class RiskAssessor:
    """
    Stateless round-level threat score calculator.

    Parameters
    ----------
    config : dict | None
        Optional config overrides. See keys below.
        All keys have safe defaults.
    """

    # Default signal weights (must sum to 1.0)
    _DEFAULT_WEIGHTS = {
        "w_layer1_anomaly_rate": 0.25,
        "w_mars_suspect_rate": 0.30,
        "w_mean_cbe_ratio": 0.15,
        "w_trust_risk_rate": 0.20,
        "w_history_penalty": 0.10,
    }

    # CBE ratio normalization ceiling (ratio above this → max CBE signal)
    _CBE_CEILING = 0.35

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}

    def _w(self, key: str) -> float:
        """Retrieve weight from config with default fallback."""
        return float(self._config.get(key, self._DEFAULT_WEIGHTS.get(key, 0.0)))

    def assess(
        self,
        contexts: List[SecurityContext],
        trust_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Computes a normalized threat score for the round.

        Parameters
        ----------
        contexts : list[SecurityContext]
            All client contexts for this round.
        trust_summary : dict | None
            Output of ClientTrustEngine.get_summary(). If None,
            the trust-risk signal is omitted (weight redistributed).

        Returns
        -------
        dict with keys:
            threat_score    : float in [0.0, 1.0]
            threat_level    : str
            signal_breakdown: dict (per-signal contribution)
            active_defenses : list[str]
            confidence      : float in [0.0, 1.0] — how much signal backed this score
            coverage        : float in [0.0, 1.0] — fraction of expected signal
                               sources that were actually available
            missing_signals : list[str] — signal sources that were absent or
                               skipped this round (never treated as benign)
        """
        if not contexts:
            logger.debug("[RiskAssessor] No contexts provided — returning zero threat")
            return {
                "threat_score": 0.0,
                "signal_breakdown": {},
                "active_defenses": [],
                "n_clients": 0,
                "confidence": 0.0,
                "coverage": 0.0,
                "missing_signals": ["LAYER1", "MARS", "TRUST_ENGINE"],
            }

        n = len(contexts)
        breakdown: Dict[str, Any] = {"n_clients": n}

        # ----------------------------------------------------------------
        # Signal 1: Layer 1 anomaly rate
        # ----------------------------------------------------------------
        l1_anomalies = sum(1 for ctx in contexts if ctx.layer1_is_anomaly() and ctx.has_layer1_signal())
        l1_rate = l1_anomalies / n if n > 0 else 0.0
        breakdown["l1_anomaly_rate"] = round(l1_rate, 4)
        breakdown["l1_anomaly_count"] = l1_anomalies

        # ----------------------------------------------------------------
        # Signal 2: MARS suspect rate
        # ----------------------------------------------------------------
        mars_suspects = sum(1 for ctx in contexts if ctx.mars_is_suspect() and ctx.has_mars_signal())
        mars_rate = mars_suspects / n if n > 0 else 0.0
        breakdown["mars_suspect_rate"] = round(mars_rate, 4)
        breakdown["mars_suspect_count"] = mars_suspects

        # ----------------------------------------------------------------
        # Signal 3: Mean CBE concentration ratio
        # ----------------------------------------------------------------
        cbe_values = [ctx.mars_cbe_ratio() for ctx in contexts if ctx.has_mars_signal()]
        mean_cbe = sum(cbe_values) / len(cbe_values) if cbe_values else 0.0
        # Normalize against ceiling
        cbe_signal = min(mean_cbe / self._CBE_CEILING, 1.0)
        breakdown["mean_cbe_ratio"] = round(mean_cbe, 4)
        breakdown["cbe_signal_normalized"] = round(cbe_signal, 4)

        # ----------------------------------------------------------------
        # Signal 4: Trust risk rate (HIGH_RISK + QUARANTINED clients)
        # ----------------------------------------------------------------
        trust_risk_signal = 0.0
        if trust_summary:
            level_counts = trust_summary.get("trust_level_counts", {})
            total_tracked = trust_summary.get("total_clients", 0)
            if total_tracked > 0:
                risky = level_counts.get("HIGH_RISK", 0) + level_counts.get("QUARANTINED", 0)
                trust_risk_signal = risky / total_tracked
            breakdown["trust_high_risk_count"] = level_counts.get("HIGH_RISK", 0)
            breakdown["trust_quarantined_count"] = level_counts.get("QUARANTINED", 0)
            breakdown["trust_avg_score"] = trust_summary.get("avg_score", 0.0)
        else:
            breakdown["trust_signal"] = "unavailable"

        breakdown["trust_risk_rate"] = round(trust_risk_signal, 4)

        # ----------------------------------------------------------------
        # Signal 5: History-based penalty
        # (elevated if MARS or L1 flagged same clients in prior rounds)
        # Uses quarantined clients from trust_summary as a proxy.
        # ----------------------------------------------------------------
        history_penalty = 0.0
        if trust_summary:
            qcount = len(trust_summary.get("quarantined_clients", []))
            hrcount = len(trust_summary.get("high_risk_clients", []))
            # Normalized: up to 0.5 signal at 3+ severely affected clients
            history_penalty = min((qcount + 0.5 * hrcount) / max(n, 1), 1.0)
        breakdown["history_penalty"] = round(history_penalty, 4)

        # ----------------------------------------------------------------
        # Weighted sum
        # ----------------------------------------------------------------
        w1 = self._w("w_layer1_anomaly_rate")
        w2 = self._w("w_mars_suspect_rate")
        w3 = self._w("w_mean_cbe_ratio")
        w4 = self._w("w_trust_risk_rate")
        w5 = self._w("w_history_penalty")

        if trust_summary is None:
            # Redistribute trust weight to other signals
            redistrib = w4 / 4.0
            w1 += redistrib
            w2 += redistrib
            w3 += redistrib
            w5 += redistrib
            w4 = 0.0

        raw_score = (
            w1 * l1_rate
            + w2 * mars_rate
            + w3 * cbe_signal
            + w4 * trust_risk_signal
            + w5 * history_penalty
        )

        threat_score = max(0.0, min(1.0, raw_score))

        breakdown["weights"] = {
            "l1_anomaly_rate": w1,
            "mars_suspect_rate": w2,
            "mean_cbe_ratio": w3,
            "trust_risk_rate": w4,
            "history_penalty": w5,
        }
        breakdown["raw_score"] = round(raw_score, 4)

        # ----------------------------------------------------------------
        # Active defenses (informational — which layers produced signals)
        # ----------------------------------------------------------------
        active_defenses = []
        if l1_anomalies > 0:
            active_defenses.append("LAYER1_ANOMALY_FILTER")
        if mars_suspects > 0:
            active_defenses.append("MARS_BACKDOOR_DETECTOR")
        if mean_cbe > 0.05:
            active_defenses.append("CBE_CONCENTRATION_MONITOR")
        if trust_risk_signal > 0.0:
            active_defenses.append("TRUST_REPUTATION_ENGINE")

        # ----------------------------------------------------------------
        # Coverage / confidence / missing_signals
        # A missing signal is NEVER treated as benign — it is surfaced
        # explicitly so downstream consumers know the score may be
        # under-informed rather than assuming "no signal" == "no risk".
        # ----------------------------------------------------------------
        l1_coverage = sum(1 for ctx in contexts if ctx.has_layer1_signal()) / n
        mars_coverage = sum(1 for ctx in contexts if ctx.has_mars_signal()) / n
        trust_coverage = 1.0 if trust_summary else 0.0

        missing_signals: List[str] = []
        if l1_coverage < 0.5:
            missing_signals.append("LAYER1")
        if mars_coverage < 0.5:
            missing_signals.append("MARS")
        if trust_coverage == 0.0:
            missing_signals.append("TRUST_ENGINE")

        coverage = round((l1_coverage + mars_coverage + trust_coverage) / 3.0, 4)
        # Confidence tracks coverage but is never zero when at least one
        # real signal source is present, and never overstates certainty
        # when most sources are missing.
        confidence = round(coverage, 4) if coverage > 0 else 0.0

        breakdown["l1_coverage"] = round(l1_coverage, 4)
        breakdown["mars_coverage"] = round(mars_coverage, 4)
        breakdown["trust_coverage"] = round(trust_coverage, 4)

        return {
            "threat_score": round(threat_score, 4),
            "signal_breakdown": breakdown,
            "active_defenses": active_defenses,
            "n_clients": n,
            "confidence": confidence,
            "coverage": coverage,
            "missing_signals": missing_signals,
        }
