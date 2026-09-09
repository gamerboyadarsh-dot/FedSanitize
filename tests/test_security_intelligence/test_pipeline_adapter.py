"""
FedSanitize — Tests: Pipeline Adapter
======================================
Tests PipelineAdapter against all supported input formats:
  - SecurityPipelineResult dataclass (mocked)
  - round_record dict (SimulationService output)
  - generic dict
  - missing/absent fields
  - empty/None inputs

All tests use synthetic data only — no FL training, no ML deps.
"""

import sys
import os
import pytest

# Ensure project root is on the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from security_intelligence.adapters.pipeline_adapter import PipelineAdapter
from security_intelligence.contracts.security_context import SecurityContext


# ---------------------------------------------------------------------------
# Helpers: Synthetic data builders
# ---------------------------------------------------------------------------

def make_l1_result(client_id: str, status: str = "PASS", anomaly: bool = False):
    """Returns a dict mimicking ClientSecurityResult (without importing the class)."""
    return {
        "client_id": client_id,
        "update_norm": 0.42,
        "norm_score": 0.1,
        "cosine_similarity": 0.95,
        "anomaly_flag": anomaly,
        "reason": "NORMAL_UPDATE" if not anomaly else "EXTREME_UPDATE_NORM",
        "status": status,
        "metadata": {
            "mad_deviation": 0.5,
            "median_norm": 0.40,
            "mad": 0.05,
            "specific_reasons": [],
        },
    }


def make_mars_result(client_id: str, status: str = "PASS", suspect: bool = False):
    return {
        "client_id": client_id,
        "cluster_id": 0,
        "status": status,
        "reason": "MARS_TRUSTED: BENIGN_REPRESENTATION" if not suspect else "MARS_SUSPICIOUS: ELEVATED_CBE",
        "cbe_concentration_ratio": 0.12 if not suspect else 0.28,
        "is_backdoor_suspect": suspect,
    }


def make_pipeline_result_dict(client_ids=("C0", "C1", "C2"), round_number=1):
    """Simulates a SecurityPipelineResult as a dict (without real torch tensors)."""
    l1_results = {cid: make_l1_result(cid) for cid in client_ids}
    mars_results = {cid: make_mars_result(cid) for cid in client_ids}
    client_security_records = {
        cid: {
            "client_id": cid,
            "attack_type": "NONE",
            "is_malicious": False,
            "update_norm": 0.42,
            "cosine_similarity": 0.95,
            "layer1_status": "PASS",
            "layer1_reason": "NORMAL_UPDATE",
            "mars_cluster": 0,
            "mars_status": "PASS",
            "mars_reason": "MARS_TRUSTED: BENIGN_REPRESENTATION",
            "final_status": "TRUSTED",
        }
        for cid in client_ids
    }
    return {
        "round_number": round_number,
        "layer1_results": l1_results,
        "mars_results": mars_results,
        "client_security_records": client_security_records,
        "aggregation_metadata": {
            "method_used": "coordinate_trimmed_mean",
            "trim_count_applied": 1,
            "n_clean_clients": len(client_ids),
            "warnings": [],
        },
    }


def make_round_record(client_ids=("C0", "C1", "C2"), round_num=1):
    """Simulates SimulationService.run_round() output dict."""
    client_security_records = {
        cid: {
            "client_id": cid,
            "attack_type": "NONE",
            "is_malicious": False,
            "update_norm": 0.42,
            "cosine_similarity": 0.95,
            "layer1_status": "PASS",
            "layer1_reason": "NORMAL_UPDATE",
            "mars_cluster": 0,
            "mars_status": "PASS",
            "mars_reason": "MARS_TRUSTED: BENIGN_REPRESENTATION",
            "final_status": "TRUSTED",
        }
        for cid in client_ids
    }
    return {
        "round": round_num,
        "attack_type": "NONE",
        "total_clients": len(client_ids),
        "clean_accuracy": 94.5,
        "backdoor_asr": 2.1,
        "trusted_clients": list(client_ids),
        "quarantined_clients": [],
        "layer1_quarantined": [],
        "mars_quarantined": [],
        "detection": {
            "tp": 0, "fp": 0, "tn": 3, "fn": 0,
            "precision": 1.0, "recall": 1.0, "f1_score": 1.0, "detection_rate": 1.0,
        },
        "client_security_records": client_security_records,
        "aggregation": {
            "method_used": "coordinate_trimmed_mean",
            "trim_count_applied": 0,
            "n_clean_clients": 3,
            "warnings": [],
        },
    }


# ---------------------------------------------------------------------------
# Tests: from_pipeline_result
# ---------------------------------------------------------------------------

class TestFromPipelineResult:

    def test_basic_dict_produces_correct_contexts(self):
        result = make_pipeline_result_dict(("C0", "C1", "C2"), round_number=5)
        contexts, warnings = PipelineAdapter.from_pipeline_result(result, round_id=5)
        assert len(contexts) == 3
        for ctx in contexts:
            assert isinstance(ctx, SecurityContext)
            assert ctx.round_id == 5
            assert ctx.client_id in ("C0", "C1", "C2")

    def test_layer1_fields_extracted(self):
        result = make_pipeline_result_dict(("C0",), round_number=1)
        contexts, _ = PipelineAdapter.from_pipeline_result(result, round_id=1)
        ctx = contexts[0]
        assert ctx.layer1_summary["status"] == "PASS"
        assert ctx.layer1_summary["anomaly_flag"] is False
        assert ctx.has_layer1_signal() is True

    def test_mars_fields_extracted(self):
        result = make_pipeline_result_dict(("C0",), round_number=1)
        contexts, _ = PipelineAdapter.from_pipeline_result(result, round_id=1)
        ctx = contexts[0]
        assert ctx.mars_summary["status"] == "PASS"
        assert ctx.mars_summary["is_backdoor_suspect"] is False
        assert isinstance(ctx.mars_summary["cbe_concentration_ratio"], float)

    def test_anomalous_client_flagged(self):
        result = make_pipeline_result_dict(("C7",))
        result["layer1_results"]["C7"] = make_l1_result("C7", status="FLAGGED", anomaly=True)
        result["client_security_records"]["C7"]["layer1_status"] = "FLAGGED"
        result["client_security_records"]["C7"]["final_status"] = "QUARANTINED"
        contexts, _ = PipelineAdapter.from_pipeline_result(result, round_id=1)
        assert len(contexts) == 1
        ctx = contexts[0]
        assert ctx.layer1_is_anomaly() is True

    def test_missing_mars_results_tolerated(self):
        result = make_pipeline_result_dict(("C0",))
        result["mars_results"] = {}  # empty MARS
        contexts, warnings = PipelineAdapter.from_pipeline_result(result, round_id=1)
        assert len(contexts) == 1
        ctx = contexts[0]
        assert ctx.mars_summary["status"] == "UNKNOWN"
        assert any("MARS" in w for w in warnings)

    def test_none_input_returns_empty(self):
        contexts, warnings = PipelineAdapter.from_pipeline_result(None, round_id=1)
        assert contexts == []
        assert len(warnings) > 0

    def test_no_client_ids_returns_empty(self):
        result = {
            "round_number": 1,
            "layer1_results": {},
            "mars_results": {},
            "client_security_records": {},
            "aggregation_metadata": None,
        }
        contexts, warnings = PipelineAdapter.from_pipeline_result(result, round_id=1)
        assert contexts == []
        assert any("client" in w.lower() for w in warnings)

    def test_aggregation_summary_extracted(self):
        result = make_pipeline_result_dict(("C0",))
        contexts, _ = PipelineAdapter.from_pipeline_result(result, round_id=1)
        agg = contexts[0].aggregation_summary
        assert agg["method_used"] == "coordinate_trimmed_mean"
        assert agg["trim_count_applied"] == 1

    def test_missing_aggregation_metadata_tolerated(self):
        result = make_pipeline_result_dict(("C0",))
        result["aggregation_metadata"] = None
        contexts, warnings = PipelineAdapter.from_pipeline_result(result, round_id=1)
        assert len(contexts) == 1
        assert any("Aggregation" in w for w in warnings)

    def test_round_id_extracted_from_result_when_not_provided(self):
        result = make_pipeline_result_dict(("C0",), round_number=7)
        contexts, _ = PipelineAdapter.from_pipeline_result(result)  # no explicit round_id
        assert contexts[0].round_id == 7

    def test_mars_skipped_status_detected(self):
        result = make_pipeline_result_dict(("C0",))
        result["mars_results"]["C0"] = {
            "client_id": "C0",
            "cluster_id": None,
            "status": "PASS",
            "reason": "MARS_SKIPPED (Insufficient surviving clients or disabled)",
            "cbe_concentration_ratio": 0.0,
            "is_backdoor_suspect": False,
        }
        contexts, _ = PipelineAdapter.from_pipeline_result(result, round_id=1)
        ctx = contexts[0]
        assert ctx.mars_status() == "SKIPPED"
        assert ctx.has_mars_signal() is False


# ---------------------------------------------------------------------------
# Tests: from_round_record
# ---------------------------------------------------------------------------

class TestFromRoundRecord:

    def test_basic_round_record(self):
        record = make_round_record(("C0", "C1", "C2"), round_num=3)
        contexts, warnings = PipelineAdapter.from_round_record(record)
        assert len(contexts) == 3
        for ctx in contexts:
            assert ctx.round_id == 3

    def test_evaluation_metrics_extracted(self):
        record = make_round_record(("C0",), round_num=1)
        contexts, _ = PipelineAdapter.from_round_record(record)
        metrics = contexts[0].evaluation_metrics
        assert metrics["clean_accuracy"] == pytest.approx(94.5)
        assert metrics["backdoor_asr"] == pytest.approx(2.1)
        assert metrics["f1_score"] == pytest.approx(1.0)

    def test_missing_clean_accuracy_warns(self):
        record = make_round_record(("C0",))
        del record["clean_accuracy"]
        contexts, warnings = PipelineAdapter.from_round_record(record)
        assert len(contexts) == 1
        assert any("clean_accuracy" in w for w in warnings)

    def test_not_a_dict_returns_empty(self):
        contexts, warnings = PipelineAdapter.from_round_record("not a dict")
        assert contexts == []
        assert len(warnings) > 0

    def test_empty_client_records_returns_empty(self):
        record = make_round_record(())
        record["client_security_records"] = {}
        contexts, warnings = PipelineAdapter.from_round_record(record)
        assert contexts == []


# ---------------------------------------------------------------------------
# Tests: from_dict (generic)
# ---------------------------------------------------------------------------

class TestFromDict:

    def test_minimal_dict(self):
        d = {"client_id": "C5", "round": 2}
        ctx, warnings = PipelineAdapter.from_dict(d, round_id=2)
        assert isinstance(ctx, SecurityContext)
        assert ctx.client_id == "C5"
        assert ctx.round_id == 2

    def test_fully_absent_input_returns_safe_context(self):
        ctx, warnings = PipelineAdapter.from_dict({})
        assert isinstance(ctx, SecurityContext)
        assert ctx.client_id is None
        assert ctx.round_id is None

    def test_non_dict_input(self):
        ctx, warnings = PipelineAdapter.from_dict(42)
        assert isinstance(ctx, SecurityContext)
        assert len(warnings) > 0

    def test_nested_attack_summary(self):
        d = {
            "client_id": "C3",
            "attack_summary": {
                "attack_type": "BACKDOOR",
                "is_malicious": True,
                "final_status": "QUARANTINED",
            },
        }
        ctx, _ = PipelineAdapter.from_dict(d)
        assert ctx.attack_summary["attack_type"] == "BACKDOOR"
        assert ctx.attack_summary["is_malicious"] is True
        assert ctx.is_flagged() is True

    def test_flat_attack_fields(self):
        d = {
            "client_id": "C1",
            "attack_type": "SIGN_FLIPPING",
            "is_malicious": True,
            "final_status": "QUARANTINED",
        }
        ctx, _ = PipelineAdapter.from_dict(d)
        assert ctx.attack_summary["attack_type"] == "SIGN_FLIPPING"

    def test_missing_fields_listed(self):
        d = {"client_id": "C0"}
        ctx, _ = PipelineAdapter.from_dict(d)
        missing = ctx.missing_fields()
        # Should report layer1, mars, aggregation, attack as missing
        assert len(missing) > 0
