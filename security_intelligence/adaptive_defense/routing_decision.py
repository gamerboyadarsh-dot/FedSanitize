"""
FedSanitize — Security Intelligence: Routing Decision Types
============================================================
Defines RoutingAction enum used by AdaptiveDefenseOrchestrator.
Pure constants — no side effects.
"""

from __future__ import annotations
from enum import Enum


class RoutingAction(str, Enum):
    """
    Defense routing actions ordered from least to most restrictive.

    STANDARD
        Normal FL operation — no special intervention.
        Threat score < 0.25.

    HEIGHTENED_MONITORING
        Increase logging verbosity, track suspect patterns.
        Flag for soft review. Threat score in [0.25, 0.50).

    ISOLATE_SUSPECTS
        Recommend isolation of flagged clients from current aggregation,
        increase MARS sensitivity signal.
        Threat score in [0.50, 0.75).

    EMERGENCY_FALLBACK
        Critical threat detected. Recommend halting aggregation or
        falling back to the most conservative aggregation strategy.
        Escalation always triggered.
        Threat score >= 0.75.
    """
    STANDARD = "STANDARD"
    HEIGHTENED_MONITORING = "HEIGHTENED_MONITORING"
    ISOLATE_SUSPECTS = "ISOLATE_SUSPECTS"
    EMERGENCY_FALLBACK = "EMERGENCY_FALLBACK"


class ThreatLevel(str, Enum):
    """Human-readable threat level labels."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def threat_score_to_level(score: float) -> ThreatLevel:
    """Maps threat score [0,1] to ThreatLevel."""
    if score >= 0.75:
        return ThreatLevel.CRITICAL
    elif score >= 0.50:
        return ThreatLevel.HIGH
    elif score >= 0.25:
        return ThreatLevel.MODERATE
    else:
        return ThreatLevel.LOW


def threat_score_to_action(score: float) -> RoutingAction:
    """Maps threat score [0,1] to RoutingAction."""
    if score >= 0.75:
        return RoutingAction.EMERGENCY_FALLBACK
    elif score >= 0.50:
        return RoutingAction.ISOLATE_SUSPECTS
    elif score >= 0.25:
        return RoutingAction.HEIGHTENED_MONITORING
    else:
        return RoutingAction.STANDARD
