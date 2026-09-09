"""
Unit Tests for Phase 3: Simulation Adapter
==========================================
Verifies that actual backend execution results are correctly converted
into an ordered, verifiable stream of SecurityEvent instances.
"""

import pytest
import numpy as np
import torch
from dataclasses import dataclass

from simulation.event_types import EventType
from simulation.security_event import SecurityEvent
from simulation.simulation_adapter import (
    SimulationAdapter,
    SimulationResult,
    adapt_security_result,
    safe_get,
)
from services.security_service import SecurityPipelineResult
from defense.layer1_anomaly.anomaly_detector import ClientSecurityResult


def test_safe_get_compatibility():
    """Verify safe_get handles dictionaries, objects, case variations, and defaults."""
    # Dict access
    data_dict = {"layer1_results": {"C1": "PASS"}, "METRICS": {"clean_accuracy": 0.95}}
    assert safe_get(data_dict, ["layer1_results", "l1_results"]) == {"C1": "PASS"}
    assert safe_get(data_dict, ["l1_results", "layer1_results"]) == {"C1": "PASS"}
    # Case insensitivity
    assert safe_get(data_dict, "metrics") == {"clean_accuracy": 0.95}
    # Missing key with default
    assert safe_get(data_dict, ["missing_key", "also_missing"], default=42) == 42

    # Object attribute access
    @dataclass
    class DummyObj:
        round_number: int = 3
        total_clients: int = 5

    obj = DummyObj()
    assert safe_get(obj, ["round", "round_number"]) == 3
    assert safe_get(obj, ["total_clients", "clients"]) == 5
    assert safe_get(obj, "not_found", default=None) is None


def test_adapt_security_pipeline_result():
    """Verify adapt_security_result converts an actual SecurityPipelineResult object."""
    l1_res = {
        "C0": ClientSecurityResult(
            client_id="C0",
            update_norm=45.2,
            norm_score=0.85,
            cosine_similarity=-0.42,
            anomaly_flag=True,
            reason="MULTIPLE_ANOMALY_SIGNALS",
            status="FLAGGED",
            metadata={"mad_deviation": 4.5, "median_norm": 10.0, "mad": 2.0},
        ),
        "C1": ClientSecurityResult(
            client_id="C1",
            update_norm=10.1,
            norm_score=0.1,
            cosine_similarity=0.98,
            anomaly_flag=False,
            reason="NORMAL_UPDATE",
            status="PASS",
        ),
        "C2": ClientSecurityResult(
            client_id="C2",
            update_norm=9.8,
            norm_score=0.08,
            cosine_similarity=0.99,
            anomaly_flag=False,
            reason="NORMAL_UPDATE",
            status="PASS",
        ),
    }

    mars_res = {
        "C1": {
            "client_id": "C1",
            "cluster_id": 0,
            "status": "PASS",
            "reason": "MARS_TRUSTED: BENIGN_REPRESENTATION",
            "cbe_concentration_ratio": 0.12,
            "is_backdoor_suspect": False,
        },
        "C2": {
            "client_id": "C2",
            "cluster_id": 0,
            "status": "PASS",
            "reason": "MARS_TRUSTED: BENIGN_REPRESENTATION",
            "cbe_concentration_ratio": 0.14,
            "is_backdoor_suspect": False,
        },
    }

    client_records = {
        "C0": {
            "client_id": "C0",
            "attack_type": "EXTREME_UPDATE",
            "is_malicious": True,
            "update_norm": 45.2,
            "cosine_similarity": -0.42,
            "layer1_status": "FLAGGED",
            "layer1_reason": "MULTIPLE_ANOMALY_SIGNALS",
            "mars_cluster": None,
            "mars_status": "SKIPPED_L1_QUARANTINE",
            "mars_reason": "Blocked at Layer 1; skipped MARS analysis",
            "final_status": "QUARANTINED",
        },
        "C1": {
            "client_id": "C1",
            "attack_type": "BENIGN",
            "is_malicious": False,
            "update_norm": 10.1,
            "cosine_similarity": 0.98,
            "layer1_status": "PASS",
            "layer1_reason": "NORMAL_UPDATE",
            "mars_cluster": 0,
            "mars_status": "PASS",
            "mars_reason": "BENIGN",
            "final_status": "TRUSTED",
        },
        "C2": {
            "client_id": "C2",
            "attack_type": "BENIGN",
            "is_malicious": False,
            "update_norm": 9.8,
            "cosine_similarity": 0.99,
            "layer1_status": "PASS",
            "layer1_reason": "NORMAL_UPDATE",
            "mars_cluster": 0,
            "mars_status": "PASS",
            "mars_reason": "BENIGN",
            "final_status": "TRUSTED",
        },
    }

    dist_matrix = np.array([[0.0, 0.05], [0.05, 0.0]])

    pipeline_res = SecurityPipelineResult(
        updated_global_state={"dummy": torch.zeros(2, 2)},
        total_clients=3,
        round_number=1,
        layer1_results=l1_res,
        layer1_quarantined=["C0"],
        mars_results=mars_res,
        mars_quarantined=[],
        trusted_clients=["C1", "C2"],
        aggregation_metadata={"method_used": "coordinate_trimmed_mean", "trim_count": 0, "trim_ratio": 0.1},
        security_summary={"total_quarantined": 1, "trusted_count": 2},
        client_security_records=client_records,
        distance_matrix=dist_matrix,
    )

    sim_result = adapt_security_result(pipeline_res, round_number=1)

    assert isinstance(sim_result, SimulationResult)
    assert len(sim_result.events) > 0
    assert sim_result.network_metadata["total_clients"] == 3
    assert sim_result.network_metadata["trusted_count"] == 2
    assert sim_result.network_metadata["quarantined_count"] == 1

    # Verify event types and chronological sequence
    event_types = [e.event_type for e in sim_result.events]
    assert EventType.ROUND_STARTED in event_types
    assert EventType.CLIENT_TRAINING_STARTED in event_types
    assert EventType.ATTACK_ACTIVATED in event_types
    assert EventType.LAYER1_CLIENT_FLAGGED in event_types
    assert EventType.MARS_STARTED in event_types
    assert EventType.AGGREGATION_FINISHED in event_types
    assert EventType.ROUND_COMPLETED in event_types

    # Verify that C0 was flagged with actual non-fabricated values
    c0_flagged_events = [
        e for e in sim_result.events
        if e.event_type == EventType.LAYER1_CLIENT_FLAGGED and e.client_id == "C0"
    ]
    assert len(c0_flagged_events) == 1
    assert c0_flagged_events[0].payload["update_norm"] == 45.2
    assert c0_flagged_events[0].payload["cosine_similarity"] == -0.42
    assert c0_flagged_events[0].payload["reason"] == "MULTIPLE_ANOMALY_SIGNALS"


def test_adapt_backdoor_mars_quarantine():
    """Verify MARS quarantine event emitted with real CBE and cluster metadata."""
    client_records = {
        "C1": {
            "client_id": "C1",
            "attack_type": "BENIGN",
            "is_malicious": False,
            "update_norm": 5.0,
            "cosine_similarity": 0.99,
            "final_status": "TRUSTED",
        },
        "C7": {
            "client_id": "C7",
            "attack_type": "BACKDOOR",
            "is_malicious": True,
            "update_norm": 5.2,
            "cosine_similarity": 0.95,
            "final_status": "QUARANTINED",
        },
    }

    mars_res = {
        "C1": {"cbe_concentration_ratio": 0.10, "cluster_id": 0, "status": "PASS"},
        "C7": {"cbe_concentration_ratio": 0.78, "cluster_id": 1, "status": "FLAGGED", "reason": "SUSPICIOUS_CBE_CLUSTER"},
    }

    dict_result = {
        "round": 3,
        "attack_type": "BACKDOOR",
        "clean_accuracy": 0.975,
        "backdoor_asr": 0.02,
        "client_security_records": client_records,
        "layer1_quarantined": [],
        "mars_results": mars_res,
        "mars_quarantined": ["C7"],
        "trusted_clients": ["C1"],
        "distance_matrix": np.array([[0.0, 1.45], [1.45, 0.0]]),
        "aggregation": {"method_used": "coordinate_trimmed_mean", "trim_count": 0},
    }

    sim_result = adapt_security_result(dict_result)
    quarantine_events = [
        e for e in sim_result.events
        if e.event_type == EventType.MARS_CLIENT_QUARANTINED
    ]
    assert len(quarantine_events) == 1
    q_evt = quarantine_events[0]
    assert q_evt.client_id == "C7"
    assert q_evt.severity == "CRITICAL"
    assert q_evt.payload["cbe_ratio"] == 0.78
    assert q_evt.payload["cluster_id"] == 1
    assert "SUSPICIOUS_CBE_CLUSTER" in q_evt.payload["reason"]


def test_adapt_graceful_missing_fields():
    """Verify adapter does not crash when fields or MARS results are absent."""
    bare_bones = {"round": 1}
    sim_result = adapt_security_result(bare_bones)
    assert len(sim_result.events) >= 2  # ROUND_STARTED and ROUND_COMPLETED at minimum
    assert len(sim_result.warnings) > 0  # Warns about missing MARS
