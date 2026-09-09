"""
FedSanitize — Security Intelligence: Contracts Package
Combines Team A contracts (TrustUpdate, SecurityDecision) and
Team B contracts (EventType, Severity, SecurityEvent).
"""
from .security_context import SecurityContext
from .client_record import ClientSecurityRecord
from .security_decision import TrustUpdate, SecurityDecision, RiskLevel, TeamATrustInput, TeamARiskInput
from .events import EventType, Severity, SecurityEvent

__all__ = [
    # Team A contracts
    "SecurityContext",
    "ClientSecurityRecord",
    "TrustUpdate",
    "SecurityDecision",
    # Team B contracts
    "EventType",
    "Severity",
    "SecurityEvent",
]
