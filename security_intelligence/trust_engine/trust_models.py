"""
FedSanitize — Security Intelligence: Trust Models
=================================================
Defines TrustLevel enum and associated scoring utilities.
Pure constants — no side effects.
"""

from __future__ import annotations
from enum import Enum


class TrustLevel(str, Enum):
    """
    Five-state trust classification for federated clients.

    States are ordered from highest trust to lowest:
      TRUSTED      → score >= 80: consistently benign, full participation
      MONITORED    → score >= 60: benign so far but under light observation
      SUSPICIOUS   → score >= 40: at least one anomaly flagged
      HIGH_RISK    → score >= 20: repeated incidents or MARS-flagged
      QUARANTINED  → score <  20: severe or sustained threat signal

    Note: The QUARANTINED state here is a trust-level classification.
    Actual quarantine enforcement (blocking from aggregation) is handled
    by the existing SecurityPipeline. This label is for reputation tracking
    and Team B integration only.
    """
    TRUSTED = "TRUSTED"
    MONITORED = "MONITORED"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    QUARANTINED = "QUARANTINED"


# Score thresholds for each trust level
TRUST_LEVEL_THRESHOLDS = {
    TrustLevel.TRUSTED: 80.0,
    TrustLevel.MONITORED: 60.0,
    TrustLevel.SUSPICIOUS: 40.0,
    TrustLevel.HIGH_RISK: 20.0,
    TrustLevel.QUARANTINED: 0.0,  # below HIGH_RISK
}


def score_to_level(score: float) -> TrustLevel:
    """
    Maps a trust score in [0, 100] to the corresponding TrustLevel.

    Parameters
    ----------
    score : float
        Trust score, clamped to [0.0, 100.0] before classification.

    Returns
    -------
    TrustLevel
        The trust level corresponding to the score.
    """
    score = max(0.0, min(100.0, score))
    if score >= TRUST_LEVEL_THRESHOLDS[TrustLevel.TRUSTED]:
        return TrustLevel.TRUSTED
    elif score >= TRUST_LEVEL_THRESHOLDS[TrustLevel.MONITORED]:
        return TrustLevel.MONITORED
    elif score >= TRUST_LEVEL_THRESHOLDS[TrustLevel.SUSPICIOUS]:
        return TrustLevel.SUSPICIOUS
    elif score >= TRUST_LEVEL_THRESHOLDS[TrustLevel.HIGH_RISK]:
        return TrustLevel.HIGH_RISK
    else:
        return TrustLevel.QUARANTINED


def clamp_score(score: float) -> float:
    """Clamps trust score to the valid range [0.0, 100.0]."""
    return max(0.0, min(100.0, score))
