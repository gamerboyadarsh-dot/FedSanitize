from security_intelligence.audit_trail import AuditLogger
from security_intelligence.contracts.security_decision import RiskLevel, TeamARiskInput
from security_intelligence.incident_response import (
    IncidentResponseEngine,
    ResponseAction,
    ResponseDecision,
)


def _engine():
    return IncidentResponseEngine(audit_logger=AuditLogger())


def test_low_severity_monitors():
    engine = _engine()
    decision = engine.handle({"mars_severity": 0.1, "layer1_anomaly_score": 0.1}, round_id=1, client_id="C1")
    assert decision.action == ResponseAction.MONITOR


def test_medium_severity_via_repeated_incidents():
    engine = _engine()
    decision = engine.handle(
        {"mars_severity": 0.1, "layer1_anomaly_score": 0.1, "repeated_incident_count": 3},
        round_id=1,
        client_id="C1",
    )
    assert decision.action == ResponseAction.REDUCE_WEIGHT


def test_high_severity_temporary_isolate():
    engine = _engine()
    decision = engine.handle({"mars_severity": 0.8}, round_id=1, client_id="C1")
    assert decision.action == ResponseAction.TEMPORARY_ISOLATE
    assert engine.quarantine_manager.is_active("C1")


def test_critical_severity_quarantine():
    engine = _engine()
    decision = engine.handle({"attack_confirmed": True}, round_id=1, client_id="C1")
    assert decision.action == ResponseAction.QUARANTINE
    assert engine.quarantine_manager.is_active("C1")


def test_quarantine_expiry():
    engine = _engine()
    engine.handle({"attack_confirmed": True}, round_id=1, client_id="C1")
    assert engine.quarantine_manager.is_active("C1")
    expired = engine.expire_quarantines(current_round=100)
    assert any(r.client_id == "C1" for r in expired)
    assert not engine.quarantine_manager.is_active("C1")


def test_release_is_reversible_not_deletion():
    engine = _engine()
    engine.handle({"attack_confirmed": True}, round_id=1, client_id="C1")
    result = engine.release_client("C1")
    assert result.ok
    assert result.record.active is False
    assert result.record.client_id == "C1"  # record preserved, not deleted


def test_missing_team_a_signals_uses_fallback_and_reports_missing():
    engine = _engine()
    decision = engine.handle({}, round_id=1, client_id="C1")
    assert decision.used_fallback_assessment is True
    assert "attack_confirmed" in decision.missing_signals


def test_team_a_risk_input_overrides_fallback():
    engine = _engine()
    risk = TeamARiskInput(risk_level=RiskLevel.CRITICAL, evidence=["team a says so"], confidence=0.9)
    decision = engine.handle({}, round_id=1, client_id="C1", team_a_risk=risk)
    assert decision.used_fallback_assessment is False
    assert decision.action == ResponseAction.QUARANTINE
    assert decision.confidence == 0.9


def test_audit_event_emitted_on_incident():
    logger = AuditLogger()
    engine = IncidentResponseEngine(audit_logger=logger)
    engine.handle({"attack_confirmed": True}, round_id=1, client_id="C1")
    events = logger.get_all_events()
    assert any(e.event_type == "INCIDENT_CREATED" for e in events)


def test_no_client_deletion_api_exists():
    # QuarantineManager exposes ADD/CHECK/RELEASE/EXPIRE only — assert the
    # forbidden verbs simply don't exist on the object.
    engine = _engine()
    assert not hasattr(engine.quarantine_manager, "delete")
    assert not hasattr(engine.quarantine_manager, "remove")


def test_broken_audit_logger_does_not_break_incident_response():
    class BrokenLogger:
        def log_event(self, *a, **kw):
            raise RuntimeError("boom")

    engine = IncidentResponseEngine(audit_logger=BrokenLogger())
    decision = engine.handle({"attack_confirmed": True}, round_id=1, client_id="C1")
    assert decision.action == ResponseAction.QUARANTINE  # response still happened
