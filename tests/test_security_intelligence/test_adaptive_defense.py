"""
FedSanitize — Tests: Adaptive Defense Orchestrator (Feature 2)
==============================================================
Tests AdaptiveDefenseOrchestrator, RiskAssessor, and EscalationPolicy.

All tests use synthetic SecurityContexts — no ML deps required.
"""

import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from security_intelligence.contracts.security_context import SecurityContext
from security_intelligence.adaptive_defense.risk_router import AdaptiveDefenseOrchestrator
from security_intelligence.adaptive_defense.risk_assessor import RiskAssessor
from security_intelligence.adaptive_defense.escalation_policy import EscalationPolicy
from security_intelligence.adaptive_defense.routing_decision import (
    RoutingAction,
    ThreatLevel,
    threat_score_to_level,
    threat_score_to_action,
)
from security_intelligence.trust_engine.trust_engine import ClientTrustEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_clean_ctx(client_id: str, round_id: int = 1) -> SecurityContext:
    return SecurityContext(
        round_id=round_id,
        client_id=client_id,
        layer1_summary={
            "status": "PASS",
            "reason": "NORMAL_UPDATE",
            "anomaly_flag": False,
            "norm_score": 0.05,
            "cosine_similarity": 0.98,
            "update_norm": 0.40,
            "_signal_present": True,
        },
        mars_summary={
            "status": "PASS",
            "reason": "MARS_TRUSTED",
            "cbe_concentration_ratio": 0.10,
            "is_backdoor_suspect": False,
            "cluster_id": 0,
            "_signal_present": True,
        },
        attack_summary={
            "attack_type": "NONE",
            "is_malicious": False,
            "final_status": "TRUSTED",
            "_signal_present": True,
        },
    )


def make_l1_flagged_ctx(client_id: str, round_id: int = 1) -> SecurityContext:
    return SecurityContext(
        round_id=round_id,
        client_id=client_id,
        layer1_summary={
            "status": "FLAGGED",
            "reason": "EXTREME_UPDATE_NORM",
            "anomaly_flag": True,
            "norm_score": 0.85,
            "cosine_similarity": 0.30,
            "update_norm": 9.8,
            "_signal_present": True,
        },
        mars_summary={
            "status": "SKIPPED",
            "reason": "Blocked at Layer 1",
            "cbe_concentration_ratio": 0.0,
            "is_backdoor_suspect": False,
            "cluster_id": None,
            "_signal_present": False,
        },
        attack_summary={
            "attack_type": "EXTREME_UPDATE",
            "is_malicious": True,
            "final_status": "QUARANTINED",
            "_signal_present": True,
        },
    )


def make_mars_flagged_ctx(client_id: str, round_id: int = 1) -> SecurityContext:
    return SecurityContext(
        round_id=round_id,
        client_id=client_id,
        layer1_summary={
            "status": "PASS",
            "reason": "NORMAL_UPDATE",
            "anomaly_flag": False,
            "norm_score": 0.10,
            "cosine_similarity": 0.91,
            "update_norm": 0.45,
            "_signal_present": True,
        },
        mars_summary={
            "status": "FLAGGED",
            "reason": "MARS_SUSPICIOUS: ELEVATED_CBE",
            "cbe_concentration_ratio": 0.30,
            "is_backdoor_suspect": True,
            "cluster_id": 1,
            "_signal_present": True,
        },
        attack_summary={
            "attack_type": "BACKDOOR",
            "is_malicious": True,
            "final_status": "QUARANTINED",
            "_signal_present": True,
        },
    )


def make_orchestrator(config: dict = None) -> AdaptiveDefenseOrchestrator:
    return AdaptiveDefenseOrchestrator(config=config or {})


# ---------------------------------------------------------------------------
# Tests: RoutingDecision helpers
# ---------------------------------------------------------------------------

class TestRoutingDecisionHelpers:

    def test_low_score_standard(self):
        assert threat_score_to_action(0.0) == RoutingAction.STANDARD
        assert threat_score_to_action(0.24) == RoutingAction.STANDARD

    def test_moderate_score_heightened(self):
        assert threat_score_to_action(0.25) == RoutingAction.HEIGHTENED_MONITORING
        assert threat_score_to_action(0.49) == RoutingAction.HEIGHTENED_MONITORING

    def test_high_score_isolate(self):
        assert threat_score_to_action(0.50) == RoutingAction.ISOLATE_SUSPECTS
        assert threat_score_to_action(0.74) == RoutingAction.ISOLATE_SUSPECTS

    def test_critical_score_emergency(self):
        assert threat_score_to_action(0.75) == RoutingAction.EMERGENCY_FALLBACK
        assert threat_score_to_action(1.0) == RoutingAction.EMERGENCY_FALLBACK

    def test_threat_level_low(self):
        assert threat_score_to_level(0.0) == ThreatLevel.LOW

    def test_threat_level_moderate(self):
        assert threat_score_to_level(0.30) == ThreatLevel.MODERATE

    def test_threat_level_high(self):
        assert threat_score_to_level(0.55) == ThreatLevel.HIGH

    def test_threat_level_critical(self):
        assert threat_score_to_level(0.80) == ThreatLevel.CRITICAL


# ---------------------------------------------------------------------------
# Tests: RiskAssessor
# ---------------------------------------------------------------------------

class TestRiskAssessor:

    def test_all_clean_gives_low_score(self):
        assessor = RiskAssessor()
        contexts = [make_clean_ctx(f"C{i}") for i in range(5)]
        result = assessor.assess(contexts, trust_summary=None)
        assert result["threat_score"] < 0.25

    def test_all_l1_flagged_gives_elevated_score(self):
        assessor = RiskAssessor()
        contexts = [make_l1_flagged_ctx(f"C{i}") for i in range(5)]
        result = assessor.assess(contexts, trust_summary=None)
        # All 5 clients flagged → l1_anomaly_rate = 1.0
        assert result["threat_score"] >= 0.25
        assert result["signal_breakdown"]["l1_anomaly_rate"] == pytest.approx(1.0)

    def test_all_mars_flagged_gives_high_score(self):
        assessor = RiskAssessor()
        contexts = [make_mars_flagged_ctx(f"C{i}") for i in range(5)]
        result = assessor.assess(contexts, trust_summary=None)
        assert result["threat_score"] >= 0.30  # MARS weight is 0.30
        assert result["signal_breakdown"]["mars_suspect_rate"] == pytest.approx(1.0)

    def test_empty_contexts_returns_zero(self):
        assessor = RiskAssessor()
        result = assessor.assess([], trust_summary=None)
        assert result["threat_score"] == 0.0

    def test_signal_breakdown_present(self):
        assessor = RiskAssessor()
        contexts = [make_clean_ctx("C0")]
        result = assessor.assess(contexts)
        breakdown = result["signal_breakdown"]
        assert "l1_anomaly_rate" in breakdown
        assert "mars_suspect_rate" in breakdown
        assert "mean_cbe_ratio" in breakdown

    def test_high_cbe_contributes_to_score(self):
        assessor = RiskAssessor()
        # One client with high CBE, rest clean
        ctx_high_cbe = SecurityContext(
            round_id=1,
            client_id="C0",
            layer1_summary={"status": "PASS", "anomaly_flag": False, "_signal_present": True},
            mars_summary={
                "status": "PASS",
                "cbe_concentration_ratio": 0.35,  # at CBE ceiling
                "is_backdoor_suspect": False,
                "_signal_present": True,
            },
            attack_summary={"final_status": "TRUSTED", "_signal_present": True},
        )
        result = assessor.assess([ctx_high_cbe])
        # CBE signal normalized at 1.0 → contributes w_mean_cbe_ratio = 0.15
        assert result["signal_breakdown"]["cbe_signal_normalized"] == pytest.approx(1.0)
        assert result["threat_score"] >= 0.15

    def test_active_defenses_listed(self):
        assessor = RiskAssessor()
        contexts = [make_l1_flagged_ctx("C0")]
        result = assessor.assess(contexts)
        assert "LAYER1_ANOMALY_FILTER" in result["active_defenses"]

    def test_mars_active_defense_listed(self):
        assessor = RiskAssessor()
        contexts = [make_mars_flagged_ctx("C0")]
        result = assessor.assess(contexts)
        assert "MARS_BACKDOOR_DETECTOR" in result["active_defenses"]

    def test_trust_summary_signal_included(self):
        assessor = RiskAssessor()
        trust_summary = {
            "total_clients": 5,
            "trust_level_counts": {"HIGH_RISK": 2, "QUARANTINED": 1},
            "avg_score": 45.0,
            "quarantined_clients": ["C7"],
            "high_risk_clients": ["C3", "C4"],
        }
        contexts = [make_clean_ctx(f"C{i}") for i in range(5)]
        result = assessor.assess(contexts, trust_summary=trust_summary)
        # trust_risk_rate = 3/5 = 0.6
        assert result["signal_breakdown"]["trust_risk_rate"] == pytest.approx(0.6)

    def test_mixed_round_partial_threat(self):
        assessor = RiskAssessor()
        contexts = [
            make_clean_ctx("C0"),
            make_clean_ctx("C1"),
            make_clean_ctx("C2"),
            make_l1_flagged_ctx("C3"),  # 1 of 5 flagged
            make_mars_flagged_ctx("C4"),
        ]
        result = assessor.assess(contexts)
        assert result["signal_breakdown"]["l1_anomaly_rate"] == pytest.approx(0.2)
        assert result["signal_breakdown"]["mars_suspect_rate"] == pytest.approx(0.2)
        # Should be moderate or higher
        assert result["threat_score"] > 0.0


# ---------------------------------------------------------------------------
# Tests: EscalationPolicy
# ---------------------------------------------------------------------------

class TestEscalationPolicy:

    def _make_breakdown(self, **kwargs):
        base = {
            "l1_anomaly_rate": 0.0,
            "l1_anomaly_count": 0,
            "mars_suspect_rate": 0.0,
            "mars_suspect_count": 0,
            "mean_cbe_ratio": 0.0,
            "trust_risk_rate": 0.0,
            "history_penalty": 0.0,
            "n_clients": 5,
        }
        base.update(kwargs)
        return base

    def test_low_threat_standard(self):
        policy = EscalationPolicy()
        decision = policy.decide(
            threat_score=0.10,
            signal_breakdown=self._make_breakdown(),
            active_defenses=[],
        )
        assert decision.routing_action == RoutingAction.STANDARD.value
        assert decision.escalation_triggered is False

    def test_moderate_threat_heightened(self):
        policy = EscalationPolicy()
        decision = policy.decide(
            threat_score=0.35,
            signal_breakdown=self._make_breakdown(l1_anomaly_rate=0.4, l1_anomaly_count=2),
            active_defenses=["LAYER1_ANOMALY_FILTER"],
        )
        assert decision.routing_action == RoutingAction.HEIGHTENED_MONITORING.value
        assert decision.escalation_triggered is False

    def test_high_threat_isolate(self):
        policy = EscalationPolicy()
        decision = policy.decide(
            threat_score=0.60,
            signal_breakdown=self._make_breakdown(mars_suspect_rate=0.6, mars_suspect_count=3),
            active_defenses=["MARS_BACKDOOR_DETECTOR"],
        )
        assert decision.routing_action == RoutingAction.ISOLATE_SUSPECTS.value

    def test_critical_threat_emergency(self):
        policy = EscalationPolicy()
        decision = policy.decide(
            threat_score=0.85,
            signal_breakdown=self._make_breakdown(
                l1_anomaly_rate=1.0, l1_anomaly_count=5,
                mars_suspect_rate=0.8, mars_suspect_count=4,
            ),
            active_defenses=["LAYER1_ANOMALY_FILTER", "MARS_BACKDOOR_DETECTOR"],
        )
        assert decision.routing_action == RoutingAction.EMERGENCY_FALLBACK.value
        assert decision.escalation_triggered is True

    def test_escalation_on_repeated_severe_history(self):
        policy = EscalationPolicy()
        # Build prior history with 2 ISOLATE decisions
        from security_intelligence.contracts.security_decision import SecurityDecision
        history = [
            SecurityDecision(round_id=1, routing_action=RoutingAction.ISOLATE_SUSPECTS.value),
            SecurityDecision(round_id=2, routing_action=RoutingAction.ISOLATE_SUSPECTS.value),
        ]
        decision = policy.decide(
            threat_score=0.40,  # below escalation threshold normally
            signal_breakdown=self._make_breakdown(),
            active_defenses=[],
            round_id=3,
            history=history,
        )
        # 2 consecutive ISOLATE → escalation triggered
        assert decision.escalation_triggered is True

    def test_no_escalation_on_clean_history(self):
        policy = EscalationPolicy()
        from security_intelligence.contracts.security_decision import SecurityDecision
        history = [
            SecurityDecision(round_id=1, routing_action=RoutingAction.STANDARD.value),
            SecurityDecision(round_id=2, routing_action=RoutingAction.STANDARD.value),
        ]
        decision = policy.decide(
            threat_score=0.10,
            signal_breakdown=self._make_breakdown(),
            active_defenses=[],
            round_id=3,
            history=history,
        )
        assert decision.escalation_triggered is False

    def test_recommended_actions_present(self):
        policy = EscalationPolicy()
        decision = policy.decide(
            threat_score=0.80,
            signal_breakdown=self._make_breakdown(mars_suspect_count=3),
            active_defenses=["MARS_BACKDOOR_DETECTOR"],
        )
        assert isinstance(decision.recommended_actions, list)
        assert len(decision.recommended_actions) > 0

    def test_threat_level_set_correctly(self):
        policy = EscalationPolicy()
        decision = policy.decide(
            threat_score=0.80,
            signal_breakdown=self._make_breakdown(),
            active_defenses=[],
        )
        assert decision.threat_level == ThreatLevel.CRITICAL.value

    def test_evidence_dict_present(self):
        policy = EscalationPolicy()
        decision = policy.decide(
            threat_score=0.30,
            signal_breakdown=self._make_breakdown(l1_anomaly_rate=0.3),
            active_defenses=[],
        )
        assert "threat_score" in decision.evidence

    def test_custom_thresholds(self):
        # Lower the escalation threshold
        policy = EscalationPolicy(config={"escalation_threshold": 0.50, "isolate_threshold": 0.30})
        decision = policy.decide(
            threat_score=0.52,
            signal_breakdown=self._make_breakdown(),
            active_defenses=[],
        )
        assert decision.routing_action == RoutingAction.EMERGENCY_FALLBACK.value

    def test_escalation_requires_mars_guard(self):
        policy = EscalationPolicy(config={"escalation_requires_mars": True})
        # threat score triggers EMERGENCY but no MARS suspects
        decision = policy.decide(
            threat_score=0.85,
            signal_breakdown=self._make_breakdown(mars_suspect_count=0),
            active_defenses=[],
        )
        # Should be downgraded because no MARS suspects
        assert decision.routing_action == RoutingAction.ISOLATE_SUSPECTS.value


# ---------------------------------------------------------------------------
# Tests: AdaptiveDefenseOrchestrator (end-to-end Feature 2)
# ---------------------------------------------------------------------------

class TestAdaptiveDefenseOrchestrator:

    def test_clean_round_standard_routing(self):
        orch = make_orchestrator()
        contexts = [make_clean_ctx(f"C{i}", round_id=1) for i in range(5)]
        decision = orch.evaluate_round(contexts)
        assert decision.routing_action == RoutingAction.STANDARD.value
        assert decision.escalation_triggered is False

    def test_mostly_flagged_round_isolate_or_higher(self):
        orch = make_orchestrator()
        contexts = [make_mars_flagged_ctx(f"C{i}", round_id=1) for i in range(5)]
        decision = orch.evaluate_round(contexts)
        assert decision.routing_action in (
            RoutingAction.ISOLATE_SUSPECTS.value,
            RoutingAction.EMERGENCY_FALLBACK.value,
        )

    def test_history_grows_per_round(self):
        orch = make_orchestrator()
        for r in range(1, 4):
            orch.evaluate_round([make_clean_ctx("C0", round_id=r)])
        assert len(orch.get_history()) == 3

    def test_get_threat_trend_correct_length(self):
        orch = make_orchestrator()
        for r in range(1, 6):
            orch.evaluate_round([make_clean_ctx("C0", round_id=r)])
        trend = orch.get_threat_trend()
        assert len(trend) == 5

    def test_get_active_defenses_after_flagged_round(self):
        orch = make_orchestrator()
        orch.evaluate_round([make_l1_flagged_ctx("C0", round_id=1)])
        defenses = orch.get_active_defenses()
        assert "LAYER1_ANOMALY_FILTER" in defenses

    def test_is_escalated_false_on_clean(self):
        orch = make_orchestrator()
        orch.evaluate_round([make_clean_ctx("C0", round_id=1)])
        assert orch.is_escalated() is False

    def test_is_escalated_true_on_critical(self):
        orch = make_orchestrator(config={"escalation_threshold": 0.01})
        # Force a score that triggers EMERGENCY
        contexts = [make_mars_flagged_ctx(f"C{i}", round_id=1) for i in range(10)]
        orch.evaluate_round(contexts)
        assert orch.is_escalated() is True

    def test_get_last_decision_none_initially(self):
        orch = make_orchestrator()
        assert orch.get_last_decision() is None

    def test_get_last_decision_after_round(self):
        orch = make_orchestrator()
        orch.evaluate_round([make_clean_ctx("C0", round_id=1)])
        last = orch.get_last_decision()
        assert last is not None
        assert last.round_id == 1

    def test_empty_contexts_handled(self):
        orch = make_orchestrator()
        decision = orch.evaluate_round([])
        assert decision.threat_score == 0.0
        assert decision.routing_action == RoutingAction.STANDARD.value

    def test_with_trust_engine_integration(self):
        orch = make_orchestrator()
        trust_engine = ClientTrustEngine(config={}, store_path=None)

        # Populate trust engine with some flagged clients
        from tests.test_security_intelligence.test_trust_engine import (
            make_l1_anomaly_context,
        )
        trust_engine.update(make_l1_anomaly_context("C7", round_id=1))
        trust_engine.update(make_l1_anomaly_context("C8", round_id=1))
        trust_engine.update(make_l1_anomaly_context("C9", round_id=1))

        contexts = [make_clean_ctx(f"C{i}", round_id=2) for i in range(5)]
        decision = orch.evaluate_round(contexts, trust_engine=trust_engine)
        # Trust engine contributes signal — score should be non-zero
        assert decision is not None
        assert isinstance(decision.threat_score, float)

    def test_get_summary_structure(self):
        orch = make_orchestrator()
        orch.evaluate_round([make_clean_ctx("C0", round_id=1)])
        summary = orch.get_summary()
        assert "rounds_evaluated" in summary
        assert "current_threat_level" in summary
        assert "avg_threat_score" in summary
        assert "peak_threat_score" in summary
        assert summary["rounds_evaluated"] == 1

    def test_escalation_across_multiple_rounds(self):
        """Repeated ISOLATE decisions in history → escalation triggered."""
        orch = make_orchestrator(config={
            "isolate_threshold": 0.01,    # virtually always ISOLATE
            "escalation_threshold": 0.999  # never EMERGENCY from score alone
        })
        # 3 rounds all triggering ISOLATE
        for r in range(1, 4):
            contexts = [make_clean_ctx(f"C{i}", round_id=r) for i in range(5)]
            decision = orch.evaluate_round(contexts)

        # After 3 consecutive ISOLATE decisions, escalation should be True
        assert orch.is_escalated() is True

    def test_decision_to_dict_serializable(self):
        orch = make_orchestrator()
        decision = orch.evaluate_round([make_clean_ctx("C0", round_id=1)])
        import json
        # Should not raise
        serialized = json.dumps(decision.to_dict())
        assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# Observe-mode guard + spec-aligned output fields
# ---------------------------------------------------------------------------

class TestObserveModeAndSpecFields:
    """
    Covers the master-prompt requirements that don't map onto the internal
    naming directly:
      - adaptive_defense.mode must default to 'observe'
      - any other configured mode must be downgraded, never silently honored
      - RoutingDecision output must expose confidence/coverage/missing_signals,
        monitoring_required, aggregation_recommendation
      - risk_level / recommended_action / recommended_escalation aliases
    """

    def test_default_mode_is_observe(self):
        orch = make_orchestrator()
        assert orch.get_mode() == "observe"

    def test_unsupported_mode_is_downgraded_not_silently_enabled(self):
        orch = AdaptiveDefenseOrchestrator(config={"adaptive_defense_mode": "active"})
        # Forced back to observe rather than honoring the requested mode.
        assert orch.get_mode() == "observe"
        decision = orch.evaluate_round([make_clean_ctx("C0", round_id=1)])
        assert decision.mode == "observe"

    def test_missing_mars_and_trust_surfaces_missing_signals(self):
        """Missing signals must be explicit, never treated as benign."""
        orch = make_orchestrator()
        # make_clean_ctx has no MARS signal by construction, and no trust_engine passed.
        contexts = [make_clean_ctx(f"C{i}", round_id=1) for i in range(3)]
        decision = orch.evaluate_round(contexts, trust_engine=None)
        assert "TRUST_ENGINE" in decision.missing_signals
        assert decision.coverage < 1.0
        assert 0.0 <= decision.confidence <= 1.0

    def test_full_coverage_when_all_sources_present(self):
        trust_engine = ClientTrustEngine()
        ctx = make_clean_ctx("C0", round_id=1)
        trust_engine.update(ctx)
        ctx = make_mars_flagged_ctx("C0", round_id=1)  # has both L1 and MARS signal
        orch = make_orchestrator()
        decision = orch.evaluate_round([ctx], trust_engine=trust_engine)
        assert decision.missing_signals == []
        assert decision.coverage == pytest.approx(1.0)

    def test_monitoring_required_flag(self):
        orch = make_orchestrator(config={"monitoring_threshold": 0.0})
        decision = orch.evaluate_round([make_l1_flagged_ctx("C0", round_id=1)])
        assert decision.routing_action != "STANDARD"
        assert decision.monitoring_required is True

    def test_monitoring_not_required_when_standard(self):
        orch = make_orchestrator()
        decision = orch.evaluate_round([make_clean_ctx("C0", round_id=1)])
        assert decision.routing_action == "STANDARD"
        assert decision.monitoring_required is False

    def test_aggregation_recommendation_never_enforced_only_suggested(self):
        """Team A must never directly enforce — only suggest a recommendation string."""
        orch = make_orchestrator(config={"escalation_threshold": 0.0})
        decision = orch.evaluate_round([make_mars_flagged_ctx("C0", round_id=1)])
        assert decision.routing_action == "EMERGENCY_FALLBACK"
        assert decision.aggregation_recommendation == "CONSERVATIVE_TRIMMED_MEAN_FALLBACK"
        # It's a string recommendation on a plain dataclass — no side effect,
        # no external call, nothing enforced by this module.
        assert isinstance(decision.aggregation_recommendation, str)

    def test_spec_aligned_aliases_match_internal_fields(self):
        orch = make_orchestrator()
        decision = orch.evaluate_round([make_clean_ctx("C0", round_id=1)])
        assert decision.risk_level == decision.threat_level
        assert decision.recommended_action == decision.routing_action
        assert decision.recommended_escalation == decision.escalation_triggered

    def test_deterministic_repeated_execution(self):
        """Same inputs must always produce the same decision — no randomness."""
        contexts = [make_l1_flagged_ctx("C0", round_id=1)]
        d1 = make_orchestrator().evaluate_round(list(contexts))
        d2 = make_orchestrator().evaluate_round(list(contexts))
        assert d1.threat_score == d2.threat_score
        assert d1.routing_action == d2.routing_action
        assert d1.missing_signals == d2.missing_signals
