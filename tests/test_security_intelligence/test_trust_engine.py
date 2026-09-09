"""
FedSanitize — Tests: Client Trust Engine (Feature 1)
=====================================================
Tests ClientTrustEngine, TrustPolicy, TrustStore, and TrustModels.

All tests use in-memory mode (no disk I/O required).
No FL training, no ML deps, no PyTorch needed.
"""

import sys
import os
import json
import tempfile
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from security_intelligence.contracts.security_context import SecurityContext
from security_intelligence.trust_engine.trust_engine import ClientTrustEngine
from security_intelligence.trust_engine.trust_models import TrustLevel, score_to_level, clamp_score
from security_intelligence.trust_engine.trust_policy import TrustPolicy
from security_intelligence.trust_engine.trust_store import TrustStore
from security_intelligence.contracts.client_record import ClientSecurityRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_clean_context(client_id: str = "C0", round_id: int = 1) -> SecurityContext:
    """A SecurityContext for a fully clean client."""
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
            "reason": "MARS_TRUSTED: BENIGN_REPRESENTATION",
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


def make_l1_anomaly_context(client_id: str = "C0", round_id: int = 1) -> SecurityContext:
    """A SecurityContext where Layer 1 flagged an anomaly."""
    return SecurityContext(
        round_id=round_id,
        client_id=client_id,
        layer1_summary={
            "status": "FLAGGED",
            "reason": "EXTREME_UPDATE_NORM",
            "anomaly_flag": True,
            "norm_score": 0.8,
            "cosine_similarity": 0.50,
            "update_norm": 5.20,
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


def make_mars_suspect_context(client_id: str = "C0", round_id: int = 1) -> SecurityContext:
    """A SecurityContext where MARS flagged a backdoor suspect."""
    return SecurityContext(
        round_id=round_id,
        client_id=client_id,
        layer1_summary={
            "status": "PASS",
            "reason": "NORMAL_UPDATE",
            "anomaly_flag": False,
            "norm_score": 0.1,
            "cosine_similarity": 0.92,
            "update_norm": 0.45,
            "_signal_present": True,
        },
        mars_summary={
            "status": "FLAGGED",
            "reason": "MARS_SUSPICIOUS: ELEVATED_CBE_CONCENTRATION",
            "cbe_concentration_ratio": 0.28,
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


def make_engine(config: dict = None) -> ClientTrustEngine:
    """Returns an in-memory trust engine."""
    return ClientTrustEngine(config=config or {}, store_path=None)


# ---------------------------------------------------------------------------
# Tests: TrustModels
# ---------------------------------------------------------------------------

class TestTrustModels:

    def test_score_100_is_trusted(self):
        assert score_to_level(100.0) == TrustLevel.TRUSTED

    def test_score_80_is_trusted(self):
        assert score_to_level(80.0) == TrustLevel.TRUSTED

    def test_score_79_is_monitored(self):
        assert score_to_level(79.9) == TrustLevel.MONITORED

    def test_score_60_is_monitored(self):
        assert score_to_level(60.0) == TrustLevel.MONITORED

    def test_score_59_is_suspicious(self):
        assert score_to_level(59.9) == TrustLevel.SUSPICIOUS

    def test_score_40_is_suspicious(self):
        assert score_to_level(40.0) == TrustLevel.SUSPICIOUS

    def test_score_39_is_high_risk(self):
        assert score_to_level(39.9) == TrustLevel.HIGH_RISK

    def test_score_20_is_high_risk(self):
        assert score_to_level(20.0) == TrustLevel.HIGH_RISK

    def test_score_19_is_quarantined(self):
        assert score_to_level(19.9) == TrustLevel.QUARANTINED

    def test_score_0_is_quarantined(self):
        assert score_to_level(0.0) == TrustLevel.QUARANTINED

    def test_clamp_above_100(self):
        assert clamp_score(150.0) == 100.0

    def test_clamp_below_0(self):
        assert clamp_score(-10.0) == 0.0

    def test_clamp_normal(self):
        assert clamp_score(75.0) == pytest.approx(75.0)


# ---------------------------------------------------------------------------
# Tests: ClientTrustEngine — basic updates
# ---------------------------------------------------------------------------

class TestClientTrustEngine:

    def test_new_client_starts_at_initial_score(self):
        engine = make_engine({"initial_score": 75.0})
        ctx = make_clean_context("C0", round_id=1)
        update = engine.update(ctx)
        # Initial score is 75; clean round reward = +3 → 78
        record = engine.get_client("C0")
        assert record is not None
        assert record.trust_score > 75.0  # reward applied

    def test_layer1_anomaly_reduces_score(self):
        engine = make_engine({"layer1_anomaly_penalty": 10.0})
        ctx = make_l1_anomaly_context("C0", round_id=1)
        update = engine.update(ctx)
        assert update is not None
        assert update.delta < 0  # penalty applied
        assert update.new_score < update.previous_score

    def test_mars_suspect_reduces_score_more(self):
        engine = make_engine({"mars_suspect_penalty": 20.0})
        ctx = make_mars_suspect_context("C0", round_id=1)
        update = engine.update(ctx)
        assert update is not None
        # Quarantine penalty + mars penalty applied
        assert update.delta < -20.0

    def test_clean_round_rewards_score(self):
        engine = make_engine({"clean_round_reward": 3.0})
        ctx = make_clean_context("C0", round_id=1)
        update = engine.update(ctx)
        assert update is not None
        assert update.delta > 0

    def test_repeated_incidents_accumulate(self):
        engine = make_engine()
        # Round 1: incident
        engine.update(make_l1_anomaly_context("C0", round_id=1))
        # Round 2: incident (should get repeat penalty)
        update2 = engine.update(make_l1_anomaly_context("C0", round_id=2))
        # Round 3: incident (should get escalating repeat penalty)
        update3 = engine.update(make_l1_anomaly_context("C0", round_id=3))
        # Delta should grow more negative with each repeat
        assert update3.delta <= update2.delta

    def test_score_clamped_at_100(self):
        engine = make_engine({"initial_score": 99.0, "clean_round_reward": 10.0})
        ctx = make_clean_context("C0", round_id=1)
        update = engine.update(ctx)
        assert update.new_score <= 100.0

    def test_score_clamped_at_0(self):
        engine = make_engine({
            "initial_score": 5.0,
            "layer1_anomaly_penalty": 10.0,
            "mars_suspect_penalty": 20.0,
            "quarantine_penalty": 15.0,
        })
        ctx = make_mars_suspect_context("C0", round_id=1)
        update = engine.update(ctx)
        assert update.new_score >= 0.0

    def test_no_client_id_returns_none(self):
        engine = make_engine()
        ctx = SecurityContext(round_id=1, client_id=None)
        result = engine.update(ctx)
        assert result is None

    def test_duplicate_round_skipped(self):
        engine = make_engine()
        ctx = make_clean_context("C0", round_id=5)
        engine.update(ctx)
        # Same client, same round — should be skipped
        result = engine.update(ctx)
        assert result is None

    def test_different_rounds_both_processed(self):
        engine = make_engine()
        u1 = engine.update(make_clean_context("C0", round_id=1))
        u2 = engine.update(make_clean_context("C0", round_id=2))
        assert u1 is not None
        assert u2 is not None

    def test_get_client_returns_none_for_unknown(self):
        engine = make_engine()
        assert engine.get_client("UNKNOWN_CLIENT") is None

    def test_get_all_clients_returns_all_seen(self):
        engine = make_engine()
        engine.update(make_clean_context("C0", round_id=1))
        engine.update(make_clean_context("C1", round_id=1))
        engine.update(make_clean_context("C2", round_id=1))
        all_clients = engine.get_all_clients()
        cids = {r.client_id for r in all_clients}
        assert "C0" in cids
        assert "C1" in cids
        assert "C2" in cids

    def test_reset_single_client(self):
        engine = make_engine()
        engine.update(make_l1_anomaly_context("C0", round_id=1))
        engine.update(make_clean_context("C1", round_id=1))
        engine.reset("C0")
        # C0 should be wiped
        assert engine.get_client("C0") is None
        # C1 should still exist
        assert engine.get_client("C1") is not None

    def test_reset_all_clients(self):
        engine = make_engine()
        engine.update(make_clean_context("C0", round_id=1))
        engine.update(make_clean_context("C1", round_id=1))
        engine.reset()
        assert engine.get_all_clients() == []

    def test_trust_update_has_reason(self):
        engine = make_engine()
        update = engine.update(make_l1_anomaly_context("C0", round_id=1))
        assert isinstance(update.reason, str)
        assert len(update.reason) > 0

    def test_trust_update_has_evidence(self):
        engine = make_engine()
        update = engine.update(make_l1_anomaly_context("C0", round_id=1))
        assert isinstance(update.evidence, dict)
        assert "layer1_anomaly" in update.evidence

    def test_trust_level_degrades_under_attack(self):
        engine = make_engine({
            "initial_score": 75.0,
            "layer1_anomaly_penalty": 20.0,
            "repeated_incident_penalty": 10.0,
        })
        for round_id in range(1, 6):
            engine.update(make_l1_anomaly_context("C0", round_id=round_id))
        record = engine.get_client("C0")
        assert record is not None
        # Score should have degraded significantly from 75
        assert record.trust_score < 50.0

    def test_update_batch(self):
        engine = make_engine()
        contexts = [
            make_clean_context("C0", round_id=1),
            make_clean_context("C1", round_id=1),
            make_l1_anomaly_context("C2", round_id=1),
        ]
        updates = engine.update_batch(contexts)
        assert len(updates) == 3

    def test_get_trust_level(self):
        engine = make_engine({"initial_score": 85.0})
        engine.update(make_clean_context("C0", round_id=1))
        level = engine.get_trust_level("C0")
        # After one clean round from 85 → should be TRUSTED
        assert level == TrustLevel.TRUSTED

    def test_incident_counter_increments(self):
        engine = make_engine()
        engine.update(make_l1_anomaly_context("C0", round_id=1))
        engine.update(make_l1_anomaly_context("C0", round_id=2))
        record = engine.get_client("C0")
        assert record.incident_count == 2
        assert record.anomaly_count == 2

    def test_clean_round_counter_resets_on_incident(self):
        engine = make_engine()
        engine.update(make_clean_context("C0", round_id=1))
        engine.update(make_clean_context("C0", round_id=2))
        record_after_clean = engine.get_client("C0")
        assert record_after_clean.clean_round_count == 2
        engine.update(make_l1_anomaly_context("C0", round_id=3))
        record_after_incident = engine.get_client("C0")
        assert record_after_incident.clean_round_count == 0

    def test_history_entry_appended(self):
        engine = make_engine()
        engine.update(make_clean_context("C0", round_id=1))
        record = engine.get_client("C0")
        assert len(record.history) == 1
        assert record.history[0]["round_id"] == 1

    def test_trust_update_level_fields(self):
        engine = make_engine({"initial_score": 82.0})
        update = engine.update(make_clean_context("C0", round_id=1))
        assert update.trust_level_before == TrustLevel.TRUSTED.value
        assert isinstance(update.trust_level_after, str)


# ---------------------------------------------------------------------------
# Tests: TrustStore — persistence and corruption handling
# ---------------------------------------------------------------------------

class TestTrustStore:

    def test_memory_mode_no_crash(self):
        store = TrustStore(store_path=None)
        rec = store.get("C0")
        assert rec is not None
        assert rec.client_id == "C0"

    def test_has_seen_round_false_initially(self):
        store = TrustStore(store_path=None)
        assert store.has_seen_round("C0", 1) is False

    def test_has_seen_round_true_after_update(self):
        store = TrustStore(store_path=None)
        rec = store.get("C0")
        rec.append_history({"round_id": 5, "delta": -10.0})
        store.set("C0", rec)
        assert store.has_seen_round("C0", 5) is True

    def test_has_seen_round_none_round_returns_false(self):
        store = TrustStore(store_path=None)
        assert store.has_seen_round("C0", None) is False

    def test_reset_single(self):
        store = TrustStore(store_path=None)
        rec = store.get("C0")
        rec.trust_score = 10.0
        store.set("C0", rec)
        store.reset("C0")
        assert store.get("C0").trust_score == pytest.approx(75.0)

    def test_reset_all(self):
        store = TrustStore(store_path=None)
        store.get("C0")
        store.get("C1")
        store.reset()
        assert store.get_all() == []

    def test_json_persistence_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "trust_store.json")
            store1 = TrustStore(store_path=path)
            rec = store1.get("C0")
            rec.trust_score = 55.0
            rec.incident_count = 3
            store1.set("C0", rec)

            # Load in a fresh store
            store2 = TrustStore(store_path=path)
            loaded = store2.get("C0")
            assert loaded.trust_score == pytest.approx(55.0)
            assert loaded.incident_count == 3

    def test_corrupted_json_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "trust_store.json")
            # Write corrupt JSON
            with open(path, "w") as f:
                f.write("INVALID JSON {{{{")
            # Should not raise
            store = TrustStore(store_path=path)
            assert store is not None
            # Should fall back to memory-only
            rec = store.get("C0")
            assert rec is not None

    def test_corrupted_individual_record_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "trust_store.json")
            payload = {
                "C0": {"client_id": "C0", "trust_score": 80.0, "trust_level": "TRUSTED",
                        "anomaly_count": 0, "mars_incident_count": 0, "clean_round_count": 2,
                        "incident_count": 0, "quarantine_count": 0, "last_updated_round": 3,
                        "history": []},
                "C1": "CORRUPT_NOT_A_DICT",  # corrupt
            }
            with open(path, "w") as f:
                json.dump(payload, f)
            store = TrustStore(store_path=path)
            # C0 should load, C1 should be skipped (not crash)
            assert store.get("C0").trust_score == pytest.approx(80.0)
