"""
FedSanitize — Security Intelligence Package
===========================================
Team A: Feature 1 (Client Trust & Reputation Engine)
       Feature 2 (Adaptive Defense Orchestrator)
Team B: Audit Trail, Incident Response, SOC Threat Intelligence

This package is independently testable and exposes clean contracts
for cross-team integration via security_intelligence/contracts/.
"""

# Team A exports
from .contracts.security_context import SecurityContext
from .contracts.client_record import ClientSecurityRecord
from .contracts.security_decision import TrustUpdate, SecurityDecision
from .contracts.events import EventType, Severity, SecurityEvent
from .adapters.pipeline_adapter import PipelineAdapter
from .trust_engine import ClientTrustEngine, TrustLevel
from .adaptive_defense import AdaptiveDefenseOrchestrator, RoutingAction, ThreatLevel

# Team B bundle (lazy-safe: only fails if team_b_bundle itself is broken)
try:
    from .team_b_bundle import TeamBBundle
    _TEAM_B_AVAILABLE = True
except Exception:  # pragma: no cover
    _TEAM_B_AVAILABLE = False

__all__ = [
    # Team A
    "SecurityContext",
    "ClientSecurityRecord",
    "TrustUpdate",
    "SecurityDecision",
    "EventType",
    "Severity",
    "SecurityEvent",
    "PipelineAdapter",
    "ClientTrustEngine",
    "TrustLevel",
    "AdaptiveDefenseOrchestrator",
    "RoutingAction",
    "ThreatLevel",
    # Team B
    "TeamBBundle",
]

