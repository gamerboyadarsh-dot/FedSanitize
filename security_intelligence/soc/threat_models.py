from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class ThreatLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ThreatAssessment:
    score: float                      # 0-100
    level: ThreatLevel
    confidence: float                 # 0-1, derived from coverage
    coverage: float                   # 0-1, fraction of signals available
    contributing_factors: list = field(default_factory=list)   # [{"name":.., "contribution":..}]
    missing_signals: list = field(default_factory=list)
    round_id: Optional[int] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 2),
            "level": self.level.value,
            "confidence": round(self.confidence, 2),
            "coverage": round(self.coverage, 2),
            "contributing_factors": self.contributing_factors,
            "missing_signals": self.missing_signals,
            "round_id": self.round_id,
            "timestamp": self.timestamp,
        }
