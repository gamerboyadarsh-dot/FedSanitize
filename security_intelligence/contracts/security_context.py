"""
FedSanitize — Security Intelligence: SecurityContext Contract
=============================================================
Normalized, tensor-free summary object that flows through both
Feature 1 (Trust Engine) and Feature 2 (Adaptive Defense).

Design rules:
- NEVER store raw tensors, gradients, or state_dicts here.
- All values are scalars, strings, bools, or nested plain dicts.
- Every field has a safe default so downstream consumers never KeyError.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SecurityContext:
    """
    Minimal normalized security context for a single client in a single round.

    This is the sole shared data contract between:
      - PipelineAdapter (producer)
      - ClientTrustEngine (consumer)
      - AdaptiveDefenseOrchestrator (consumer)
      - Team B modules (future consumers)

    Fields
    ------
    round_id : int | None
        The FL round number this context belongs to. None if unavailable.
    client_id : str | None
        The client identifier. None signals a round-level (not per-client) context.
    layer1_summary : dict
        Layer 1 anomaly filter signals. Expected keys (all optional):
          status: "PASS" | "FLAGGED" | "UNKNOWN"
          reason: str
          anomaly_flag: bool
          norm_score: float
          cosine_similarity: float
          update_norm: float
          mad_deviation: float
          specific_reasons: list[str]
    mars_summary : dict
        Layer 2 MARS backdoor analysis signals. Expected keys (all optional):
          status: "PASS" | "FLAGGED" | "UNKNOWN" | "SKIPPED"
          reason: str
          cbe_concentration_ratio: float
          is_backdoor_suspect: bool
          cluster_id: int | None
    aggregation_summary : dict
        Layer 3 robust aggregation metadata. Expected keys (all optional):
          method_used: str
          trim_count_applied: int
          n_clean_clients: int
          warnings: list[str]
    attack_summary : dict
        Ground-truth attack metadata (from ClientUpdate). Expected keys (all optional):
          attack_type: str
          is_malicious: bool
          final_status: str  ("TRUSTED" | "QUARANTINED")
    evaluation_metrics : dict
        Round-level evaluation results. Expected keys (all optional):
          clean_accuracy: float
          backdoor_asr: float
          detection_rate: float
          f1_score: float
          precision: float
          recall: float
    metadata : dict
        Adapter provenance, warnings, missing fields list:
          source: str
          warnings: list[str]
          missing_fields: list[str]
    """

    round_id: Optional[int] = None
    client_id: Optional[str] = None

    layer1_summary: Dict[str, Any] = field(default_factory=dict)
    mars_summary: Dict[str, Any] = field(default_factory=dict)
    aggregation_summary: Dict[str, Any] = field(default_factory=dict)
    attack_summary: Dict[str, Any] = field(default_factory=dict)
    evaluation_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------------------------
    # Convenience accessor helpers — never raise, always return safe defaults
    # -----------------------------------------------------------------------

    def layer1_status(self) -> str:
        return str(self.layer1_summary.get("status", "UNKNOWN"))

    def layer1_is_anomaly(self) -> bool:
        return bool(self.layer1_summary.get("anomaly_flag", False))

    def mars_status(self) -> str:
        return str(self.mars_summary.get("status", "UNKNOWN"))

    def mars_is_suspect(self) -> bool:
        return bool(self.mars_summary.get("is_backdoor_suspect", False))

    def mars_cbe_ratio(self) -> float:
        try:
            return float(self.mars_summary.get("cbe_concentration_ratio", 0.0))
        except (TypeError, ValueError):
            return 0.0

    def final_status(self) -> str:
        return str(self.attack_summary.get("final_status", "UNKNOWN"))

    def is_flagged(self) -> bool:
        return self.final_status() == "QUARANTINED"

    def has_layer1_signal(self) -> bool:
        """True if Layer 1 produced a real result (not just an absent/default)."""
        return bool(self.layer1_summary) and self.layer1_status() != "UNKNOWN"

    def has_mars_signal(self) -> bool:
        """True if MARS produced a real result (not absent or SKIPPED)."""
        return (
            bool(self.mars_summary)
            and self.mars_status() not in ("UNKNOWN", "SKIPPED")
        )

    def warnings(self) -> list:
        return list(self.metadata.get("warnings", []))

    def missing_fields(self) -> list:
        return list(self.metadata.get("missing_fields", []))
