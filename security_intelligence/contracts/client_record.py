"""
FedSanitize — Security Intelligence: ClientSecurityRecord Contract
==================================================================
Persistent reputation record maintained across FL rounds for each client.
This is the durable state object stored by TrustStore and updated by TrustEngine.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ClientSecurityRecord:
    """
    Durable, per-client security reputation record.

    Maintained across all rounds by ClientTrustEngine.
    Serializable to/from JSON via dataclasses.asdict / from_dict.

    Fields
    ------
    client_id : str
        Unique client identifier (e.g. "C0", "C7").
    trust_score : float
        Current reputation score in [0.0, 100.0].
        Higher is more trusted.
    trust_level : str
        Human-readable state label derived from trust_score.
        One of: "TRUSTED", "MONITORED", "SUSPICIOUS", "HIGH_RISK", "QUARANTINED"
    anomaly_count : int
        Total number of Layer 1 anomaly flags recorded.
    mars_incident_count : int
        Total number of MARS backdoor suspect flags recorded.
    clean_round_count : int
        Number of consecutive clean rounds (resets on incident).
    incident_count : int
        Total number of rounds flagged as anomalous (L1 or MARS).
    quarantine_count : int
        Number of rounds in which final_status was QUARANTINED.
        Reserved for Team B integration (Incident Response).
    last_updated_round : int | None
        Round ID of the most recent update applied.
    history : list[dict]
        Ordered list of trust update change records.
        Each entry has: round_id, previous_score, delta, new_score, reason, evidence.
        Capped at MAX_HISTORY_ENTRIES to bound memory.
    """

    MAX_HISTORY_ENTRIES: int = field(default=100, init=False, repr=False, compare=False)

    client_id: str = ""
    trust_score: float = 75.0          # initial score
    trust_level: str = "MONITORED"     # initial level
    anomaly_count: int = 0
    mars_incident_count: int = 0
    clean_round_count: int = 0
    incident_count: int = 0
    quarantine_count: int = 0
    last_updated_round: Optional[int] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    def append_history(self, entry: Dict[str, Any]) -> None:
        """Appends a change record, pruning oldest entry when cap is reached."""
        self.history.append(entry)
        if len(self.history) > self.MAX_HISTORY_ENTRIES:
            self.history = self.history[-self.MAX_HISTORY_ENTRIES:]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes to a plain dict (JSON-safe, no dataclass nesting)."""
        return {
            "client_id": self.client_id,
            "trust_score": self.trust_score,
            "trust_level": self.trust_level,
            "anomaly_count": self.anomaly_count,
            "mars_incident_count": self.mars_incident_count,
            "clean_round_count": self.clean_round_count,
            "incident_count": self.incident_count,
            "quarantine_count": self.quarantine_count,
            "last_updated_round": self.last_updated_round,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ClientSecurityRecord":
        """Deserializes from a plain dict. Tolerates missing/extra keys."""
        record = cls(
            client_id=str(d.get("client_id", "")),
            trust_score=float(d.get("trust_score", 75.0)),
            trust_level=str(d.get("trust_level", "MONITORED")),
            anomaly_count=int(d.get("anomaly_count", 0)),
            mars_incident_count=int(d.get("mars_incident_count", 0)),
            clean_round_count=int(d.get("clean_round_count", 0)),
            incident_count=int(d.get("incident_count", 0)),
            quarantine_count=int(d.get("quarantine_count", 0)),
            last_updated_round=d.get("last_updated_round"),
            history=list(d.get("history", [])),
        )
        return record
