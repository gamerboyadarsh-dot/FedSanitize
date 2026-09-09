"""
FedSanitize — Security Intelligence: Output Decision Contracts
==============================================================
Defines TrustUpdate (Feature 1 output) and SecurityDecision (Feature 2 output).
Both are pure dataclasses with no external dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TrustUpdate:
    """
    Explainable change record produced by ClientTrustEngine for a single
    client in a single round.

    Every field is populated — there is no partial update.

    Fields
    ------
    client_id : str
        The client whose trust record was updated.
    previous_score : float
        Trust score before this update.
    delta : float
        Signed change applied (positive = reward, negative = penalty).
    new_score : float
        Trust score after this update (clamped to [0, 100]).
    reason : str
        Human-readable explanation of why the score changed.
    evidence : dict
        Supporting signal values used to compute delta:
          layer1_anomaly: bool
          mars_suspect: bool
          final_status: str
          anomaly_count: int
          clean_round_count: int
          ... (any additional signals)
    round_id : int | None
        The FL round this update was applied in.
    trust_level_before : str
        Trust level label before the update.
    trust_level_after : str
        Trust level label after the update.
    """

    client_id: str
    previous_score: float
    delta: float
    new_score: float
    reason: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    round_id: Optional[int] = None
    trust_level_before: str = "UNKNOWN"
    trust_level_after: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable representation."""
        return {
            "client_id": self.client_id,
            "previous_score": self.previous_score,
            "delta": self.delta,
            "new_score": self.new_score,
            "reason": self.reason,
            "evidence": self.evidence,
            "round_id": self.round_id,
            "trust_level_before": self.trust_level_before,
            "trust_level_after": self.trust_level_after,
        }


@dataclass
class SecurityDecision:
    """
    Round-level security routing and escalation decision produced by
    AdaptiveDefenseOrchestrator (Feature 2).

    Fields
    ------
    round_id : int | None
        The FL round this decision applies to.
    threat_level : str
        Assessed threat level: "LOW", "MODERATE", "HIGH", "CRITICAL"
    threat_score : float
        Normalized threat score in [0.0, 1.0].
    routing_action : str
        Chosen defense routing: "STANDARD", "HEIGHTENED_MONITORING",
        "ISOLATE_SUSPECTS", "EMERGENCY_FALLBACK"
    active_defenses : list[str]
        List of defense mechanisms flagged as active this round.
    escalation_triggered : bool
        Whether this decision crosses the escalation threshold.
    reason : str
        Human-readable summary of the decision rationale.
    evidence : dict
        Supporting signal values:
          anomaly_rate: float
          mars_suspect_rate: float
          mean_cbe_ratio: float
          threat_score: float
          high_risk_client_count: int
          ... (any additional signals)
    recommended_actions : list[str]
        Ordered list of recommended follow-up actions (for Team B / SOC).
    signal_breakdown : dict
        Detailed per-signal contributions to the threat score.
    monitoring_required : bool
        True whenever the routing action is anything above STANDARD —
        a direct signal for dashboards/SOC that this round needs eyes on.
    aggregation_recommendation : str
        Non-binding suggestion for the aggregation layer, e.g.
        "USE_DEFAULT_AGGREGATION" | "EXCLUDE_FLAGGED_CLIENTS" |
        "CONSERVATIVE_TRIMMED_MEAN_FALLBACK". Team A never applies this
        itself — Team B / the aggregation layer owns enforcement.
    confidence : float
        How much real signal backed this decision, in [0.0, 1.0].
    coverage : float
        Fraction of expected signal sources (Layer 1, MARS, trust engine)
        that were actually available this round, in [0.0, 1.0].
    missing_signals : list[str]
        Signal sources that were absent or skipped this round. A missing
        signal is never treated as benign — it is surfaced here instead.
    mode : str
        The adaptive-defense mode this decision was produced under.
        Always "observe" in this version — see config docs.
    """

    round_id: Optional[int] = None
    threat_level: str = "LOW"
    threat_score: float = 0.0
    routing_action: str = "STANDARD"
    active_defenses: List[str] = field(default_factory=list)
    escalation_triggered: bool = False
    reason: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)
    signal_breakdown: Dict[str, Any] = field(default_factory=dict)
    monitoring_required: bool = False
    aggregation_recommendation: str = "USE_DEFAULT_AGGREGATION"
    confidence: float = 0.0
    coverage: float = 0.0
    missing_signals: List[str] = field(default_factory=list)
    mode: str = "observe"

    # ------------------------------------------------------------------
    # Master-prompt-aligned aliases. The routing/escalation naming above
    # is the canonical internal representation; these expose the exact
    # field names from the Feature 2 spec (risk_level, recommended_action,
    # recommended_escalation) for consumers that read the spec literally.
    # ------------------------------------------------------------------
    @property
    def risk_level(self) -> str:
        return self.threat_level

    @property
    def recommended_action(self) -> str:
        return self.routing_action

    @property
    def recommended_escalation(self) -> bool:
        return self.escalation_triggered

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable representation."""
        return {
            "round_id": self.round_id,
            "threat_level": self.threat_level,
            "risk_level": self.risk_level,
            "threat_score": self.threat_score,
            "routing_action": self.routing_action,
            "recommended_action": self.recommended_action,
            "active_defenses": self.active_defenses,
            "escalation_triggered": self.escalation_triggered,
            "recommended_escalation": self.recommended_escalation,
            "monitoring_required": self.monitoring_required,
            "aggregation_recommendation": self.aggregation_recommendation,
            "reason": self.reason,
            "evidence": self.evidence,
            "recommended_actions": self.recommended_actions,
            "signal_breakdown": self.signal_breakdown,
            "confidence": self.confidence,
            "coverage": self.coverage,
            "missing_signals": self.missing_signals,
            "mode": self.mode,
        }
