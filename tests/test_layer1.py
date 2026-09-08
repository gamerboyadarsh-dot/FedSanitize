"""
FedSanitize — Layer 1 Anomaly Filter Test Suite
===============================================
Verifies:
- Detection of extreme update norms (Attack D)
- Detection of low directional similarity / sign flipping (Attack B)
- Benign updates pass cleanly
- Graceful fallback when too many clients are flagged
- Explainability: reason strings and numeric metrics are strictly populated
"""

import os
import sys
import pytest
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from federated.client import ClientUpdate
from defense.layer1_anomaly import Layer1AnomalyDetector, ClientSecurityResult
from config import Layer1Config


def _make_dummy_update(
    client_id: str,
    base_val: float = 1.0,
    multiplier: float = 1.0,
    dim: int = 100,
) -> ClientUpdate:
    """Helper to construct synthetic updates with predictable properties."""
    tensor = torch.full((dim,), base_val * multiplier, dtype=torch.float32)
    delta = {"layer.weight": tensor}
    return ClientUpdate(
        client_id=client_id,
        state_dict=delta,
        delta=delta,
        num_samples=100,
        is_malicious=(multiplier != 1.0),
        attack_type="SYNTHETIC" if multiplier != 1.0 else "NONE",
    )


def test_benign_updates_pass():
    """All honest clients with similar updates should pass Layer 1."""
    detector = Layer1AnomalyDetector()
    updates = [
        _make_dummy_update(f"C{i}", base_val=1.0 + 0.02 * i)
        for i in range(8)
    ]
    result = detector.detect_anomalies(updates)
    
    assert len(result["trusted_updates"]) == 8
    assert len(result["quarantined_clients"]) == 0
    for res in result["results"].values():
        assert res.status == "PASS"
        assert res.reason == "NORMAL_UPDATE"


def test_extreme_update_flagged():
    """Client with 15x norm must be flagged with EXTREME_UPDATE_NORM."""
    detector = Layer1AnomalyDetector()
    updates = [
        _make_dummy_update(f"C{i}", base_val=1.0)
        for i in range(7)
    ]
    # Add extreme update attacker
    updates.append(_make_dummy_update("C_extreme", base_val=1.0, multiplier=15.0))
    
    result = detector.detect_anomalies(updates)
    assert "C_extreme" in result["quarantined_clients"]
    extreme_res = result["results"]["C_extreme"]
    assert extreme_res.status == "FLAGGED"
    assert "EXTREME_UPDATE_NORM" in extreme_res.reason
    assert extreme_res.update_norm > 50.0


def test_sign_flipping_flagged():
    """Client with negative cosine similarity must be flagged."""
    detector = Layer1AnomalyDetector()
    updates = [
        _make_dummy_update(f"C{i}", base_val=1.0)
        for i in range(7)
    ]
    # Add negative sign attacker
    updates.append(_make_dummy_update("C_sign_flip", base_val=1.0, multiplier=-1.0))
    
    result = detector.detect_anomalies(updates)
    assert "C_sign_flip" in result["quarantined_clients"]
    sign_res = result["results"]["C_sign_flip"]
    assert sign_res.status == "FLAGGED"
    assert "LOW_DIRECTIONAL_SIMILARITY" in sign_res.reason
    assert sign_res.cosine_similarity < 0.0


def test_fallback_when_too_many_flagged():
    """If all clients trigger filters, fallback ensures minimum clients survive."""
    config = Layer1Config(min_surviving_clients=3)
    detector = Layer1AnomalyDetector(config=config)
    # Create 5 heavily perturbed updates
    updates = [
        _make_dummy_update(f"C{i}", base_val=1.0, multiplier=float(i * 10 - 20))
        for i in range(5)
    ]
    result = detector.detect_anomalies(updates)
    
    # Must preserve at least min_surviving_clients without crash
    assert len(result["trusted_updates"]) >= 3
    assert len(result["trusted_updates"]) <= len(updates)


def test_explainability_and_structure():
    """Every client result must have valid structured metrics and reasons."""
    detector = Layer1AnomalyDetector()
    updates = [
        _make_dummy_update("C0", base_val=1.0),
        _make_dummy_update("C1", base_val=10.0),
    ]
    result = detector.detect_anomalies(updates)
    
    for cid, sec_res in result["results"].items():
        assert isinstance(sec_res, ClientSecurityResult)
        assert sec_res.client_id == cid
        assert isinstance(sec_res.update_norm, float)
        assert isinstance(sec_res.norm_score, float)
        assert 0.0 <= sec_res.norm_score <= 1.0
        assert isinstance(sec_res.cosine_similarity, float)
        assert sec_res.reason in [
            "NORMAL_UPDATE",
            "EXTREME_UPDATE_NORM",
            "LOW_DIRECTIONAL_SIMILARITY",
            "MULTIPLE_ANOMALY_SIGNALS",
        ] or "RECOVERED_BY_FALLBACK" in sec_res.reason


if __name__ == "__main__":
    pytest.main(["-v", __file__])
