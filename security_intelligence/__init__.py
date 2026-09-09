"""
FedSanitize — Security Intelligence Package
===========================================
Team A: Feature 1 (Client Trust & Reputation Engine)
       Feature 2 (Adaptive Defense Orchestrator)

This package is independently testable and exposes clean contracts
for future integration with Team B modules.
"""

from .contracts.security_context import SecurityContext
from .contracts.client_record import ClientSecurityRecord
from .contracts.security_decision import TrustUpdate, SecurityDecision
from .adapters.pipeline_adapter import PipelineAdapter
from .trust_engine import ClientTrustEngine, TrustLevel
from .adaptive_defense import AdaptiveDefenseOrchestrator, RoutingAction

__all__ = [
    "SecurityContext",
    "ClientSecurityRecord",
    "TrustUpdate",
    "SecurityDecision",
    "PipelineAdapter",
    "ClientTrustEngine",
    "TrustLevel",
    "AdaptiveDefenseOrchestrator",
    "RoutingAction",
]
