"""
FedSanitize — Security Intelligence: Security Configuration
============================================================
All thresholds and weights for Features 1 and 2 in one place.

Usage
-----
    from security_intelligence.config.security_config import SecurityIntelligenceConfig
    cfg = SecurityIntelligenceConfig()
    config_dict = cfg.to_dict()

Or load from YAML:
    cfg = SecurityIntelligenceConfig.from_yaml("default_security.yaml")

Or override specific keys:
    cfg = SecurityIntelligenceConfig(layer1_anomaly_penalty=15.0)
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class SecurityIntelligenceConfig:
    """
    Centralized configuration for security_intelligence modules.

    Trust Engine (Feature 1) Parameters
    ------------------------------------
    initial_score : float
        Starting trust score for new clients. Default: 75.0
    layer1_anomaly_penalty : float
        Score deduction when Layer 1 flags a client. Default: 10.0
    mars_suspect_penalty : float
        Score deduction when MARS flags a client. Default: 20.0
    repeated_incident_penalty : float
        Additional score deduction per repeat offense. Default: 5.0
    quarantine_penalty : float
        Additional deduction when final_status is QUARANTINED. Default: 15.0
    clean_round_reward : float
        Score reward for a clean round (no flags). Default: 3.0
    max_reward_per_round : float
        Maximum reward applicable per round. Default: 3.0

    Trust Level Thresholds
    ----------------------
    These are defined in trust_models.py and are not overridable via config
    to avoid inconsistency; they reflect the spec-mandated five-state system.

    Adaptive Defense (Feature 2) Parameters
    ----------------------------------------
    w_layer1_anomaly_rate : float
        Weight for Layer 1 anomaly rate signal. Default: 0.25
    w_mars_suspect_rate : float
        Weight for MARS suspect rate signal. Default: 0.30
    w_mean_cbe_ratio : float
        Weight for normalized mean CBE ratio signal. Default: 0.15
    w_trust_risk_rate : float
        Weight for HIGH_RISK+QUARANTINED client rate. Default: 0.20
    w_history_penalty : float
        Weight for history-based escalation penalty. Default: 0.10
    escalation_threshold : float
        Threat score >= this → EMERGENCY_FALLBACK. Default: 0.75
    isolate_threshold : float
        Threat score >= this → ISOLATE_SUSPECTS. Default: 0.50
    monitoring_threshold : float
        Threat score >= this → HEIGHTENED_MONITORING. Default: 0.25
    escalation_requires_mars : bool
        If True, EMERGENCY_FALLBACK only if MARS also flagged suspects. Default: False
    min_suspect_rate_for_escalation : float
        Minimum MARS suspect rate for ISOLATE/EMERGENCY actions. Default: 0.0
    adaptive_defense_mode : str
        "observe" (default, only supported value in this version) or
        "active" (reserved for a future release — currently downgraded to
        "observe" with a warning if set, never enabled silently).
    """

    # --- Trust Engine ---
    initial_score: float = 75.0
    layer1_anomaly_penalty: float = 10.0
    mars_suspect_penalty: float = 20.0
    repeated_incident_penalty: float = 5.0
    quarantine_penalty: float = 15.0
    clean_round_reward: float = 3.0
    max_reward_per_round: float = 3.0

    # --- Risk Assessor weights (must sum to ~1.0) ---
    w_layer1_anomaly_rate: float = 0.25
    w_mars_suspect_rate: float = 0.30
    w_mean_cbe_ratio: float = 0.15
    w_trust_risk_rate: float = 0.20
    w_history_penalty: float = 0.10

    # --- Escalation thresholds ---
    escalation_threshold: float = 0.75
    isolate_threshold: float = 0.50
    monitoring_threshold: float = 0.25
    escalation_requires_mars: bool = False
    min_suspect_rate_for_escalation: float = 0.0

    # --- Adaptive defense mode ---
    # "observe" is the only mode implemented. See AdaptiveDefenseOrchestrator
    # for why any other value is downgraded (never silently enabled).
    adaptive_defense_mode: str = "observe"

    # --- Persistence ---
    trust_store_path: Optional[str] = None  # None → in-memory only

    def to_dict(self) -> Dict[str, Any]:
        """Returns a plain dict representation (for passing to engines)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SecurityIntelligenceConfig":
        """Creates a config from a plain dict, ignoring unknown keys."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "SecurityIntelligenceConfig":
        """
        Loads config from a YAML file. Falls back to defaults if file
        is missing or malformed (does NOT crash).

        Requires PyYAML (optional dep). If not installed, returns defaults
        with a warning.
        """
        import logging
        _logger = logging.getLogger("FedSanitize.SecurityIntelligence.Config")

        try:
            import yaml
            path = Path(yaml_path)
            if not path.exists():
                _logger.warning(f"[Config] YAML not found at '{path}' — using defaults")
                return cls()
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            return cls.from_dict(raw)
        except ImportError:
            _logger.warning("[Config] PyYAML not installed — using default config")
            return cls()
        except Exception as e:
            _logger.warning(f"[Config] YAML parse error: {e} — using default config")
            return cls()


# Default singleton — import in any module that needs config
DEFAULT_SECURITY_CONFIG = SecurityIntelligenceConfig()
