"""
Configuration-driven mapping from severity -> response action. No
thresholds are hardcoded in response_engine.py — everything routes through
this policy object, which is built from a plain dict (loaded from YAML by
security_intelligence.config, or passed directly in tests).
"""

from dataclasses import dataclass
from typing import Optional

from .response_models import IncidentSeverity, ResponseAction

DEFAULT_POLICY = {
    "low": {"action": "MONITOR", "duration_rounds": None, "requires_review": False},
    "medium": {"action": "REDUCE_WEIGHT", "duration_rounds": 3, "requires_review": False},
    "high": {"action": "TEMPORARY_ISOLATE", "duration_rounds": 5, "requires_review": True},
    "critical": {"action": "QUARANTINE", "duration_rounds": 10, "requires_review": True},
}

# Fallback risk assessment thresholds — ONLY used when Team A has not
# injected a risk_level. Kept separate and clearly named so nobody mistakes
# this for Team A's Adaptive Defense Orchestrator.
DEFAULT_FALLBACK_THRESHOLDS = {
    "mars_severity_high": 0.7,
    "mars_severity_critical": 0.9,
    "layer1_anomaly_high": 0.7,
    "layer1_anomaly_critical": 0.9,
    "repeated_incident_escalation_count": 2,
}


@dataclass
class ResponsePolicyEntry:
    action: ResponseAction
    duration_rounds: Optional[int]
    requires_review: bool


class ResponsePolicy:
    def __init__(self, policy_config: Optional[dict] = None, fallback_thresholds: Optional[dict] = None):
        cfg = policy_config or DEFAULT_POLICY
        self._entries = {}
        for level in ("low", "medium", "high", "critical"):
            raw = cfg.get(level, DEFAULT_POLICY[level])
            try:
                action = ResponseAction(raw.get("action", DEFAULT_POLICY[level]["action"]))
            except ValueError:
                action = ResponseAction(DEFAULT_POLICY[level]["action"])
            self._entries[level] = ResponsePolicyEntry(
                action=action,
                duration_rounds=raw.get("duration_rounds", DEFAULT_POLICY[level]["duration_rounds"]),
                requires_review=bool(raw.get("requires_review", DEFAULT_POLICY[level]["requires_review"])),
            )
        self.fallback_thresholds = {**DEFAULT_FALLBACK_THRESHOLDS, **(fallback_thresholds or {})}

    def entry_for(self, severity: IncidentSeverity) -> ResponsePolicyEntry:
        return self._entries[severity.value.lower()]
