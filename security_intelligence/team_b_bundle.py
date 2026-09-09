"""
TeamBBundle: Team B's own composition root.

This is NOT the central Security Intelligence Orchestrator described in
the main master prompt — that component belongs to whoever integrates
Team A + Team B, and it will import from here (and from Team A's
equivalent) rather than the other way around. This bundle exists so
Team B can:

  1. Run their own modules standalone during development/hackathon demo,
  2. Feed the SOC dashboard without waiting on the orchestrator,
  3. Give the future orchestrator one clean object to hold onto.

Usage:
    from security_intelligence.team_b_bundle import TeamBBundle
    bundle = TeamBBundle()
    decision = bundle.incident_engine.handle(evidence, round_id=1, client_id="C1")
    assessment = bundle.threat_engine.assess(signals, round_id=1)
    snapshot = bundle.snapshot(round_id=1)
"""

from __future__ import annotations

from typing import List, Optional

from .audit_trail import AuditLogger
from .config import SecurityConfig
from .incident_response import IncidentResponseEngine, QuarantineManager, ResponsePolicy
from .soc import SecurityPosture, ThreatIntelligenceEngine, build_soc_snapshot


class TeamBBundle:
    def __init__(self, config: Optional[SecurityConfig] = None, use_disk_persistence: bool = True):
        self.config = config or SecurityConfig()

        audit_cfg = self.config.audit
        storage_path = audit_cfg.get("storage_path") if use_disk_persistence else None
        if audit_cfg.get("storage_backend") == "memory":
            storage_path = None
        self.audit_logger = AuditLogger(storage_path=storage_path)

        ir_cfg = self.config.incident_response
        policy = ResponsePolicy(
            policy_config={k: v for k, v in ir_cfg.items() if k in ("low", "medium", "high", "critical")},
            fallback_thresholds=ir_cfg.get("fallback_thresholds"),
        )
        quarantine_path = ir_cfg.get("quarantine_storage_path") if use_disk_persistence else None
        self.quarantine_manager = QuarantineManager(storage_path=quarantine_path)
        self.incident_engine = IncidentResponseEngine(
            policy=policy,
            quarantine_manager=self.quarantine_manager,
            audit_logger=self.audit_logger,
        )

        ti_cfg = self.config.threat_intelligence
        self.posture = SecurityPosture()
        self.threat_engine = ThreatIntelligenceEngine(
            weights=ti_cfg.get("weights"),
            level_thresholds=ti_cfg.get("level_thresholds"),
            audit_logger=self.audit_logger,
            posture=self.posture,
        )

    def snapshot(self, round_id: Optional[int] = None, team_a_trust_records: Optional[List[dict]] = None):
        return build_soc_snapshot(
            round_id=round_id,
            threat_assessment=self.threat_engine.last_assessment,
            incident_registry=self.incident_engine.registry,
            quarantine_manager=self.quarantine_manager,
            audit_logger=self.audit_logger,
            security_posture=self.posture,
            team_a_trust_records=team_a_trust_records,
        )
