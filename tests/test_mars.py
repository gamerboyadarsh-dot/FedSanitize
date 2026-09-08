"""
FedSanitize — MARS (Layer 2) Verification Test Suite
====================================================
Grounded in: Wan et al., NeurIPS 2025 (arXiv:2509.20383)

Verifies:
1. Layer selection picks valid representation layers.
2. Backdoor energy and CBE extraction produces normalized probability distributions.
3. Pairwise Wasserstein distance matrix is symmetric with zero diagonal.
4. Benign-only run: NO false suspicious cluster (all benign clients trusted).
5. Backdoor-injected run: Suspicious cluster correctly isolates backdoored clients.
6. Edge case: Few clients surviving L1 handled gracefully without crash.
"""

import os
import sys
import pytest
import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from federated.client import ClientUpdate
from defense.layer2_mars import (
    select_target_layers,
    compute_filter_energies,
    extract_cbe,
    compute_pairwise_wasserstein_matrix,
    cluster_and_classify,
    MARSDetector,
)
from config import MARSConfig


def _create_mock_update(
    client_id: str,
    is_backdoor: bool = False,
    num_filters: int = 64,
    dim: int = 49,
    seed: int = 42,
) -> ClientUpdate:
    """
    Constructs a synthetic client update delta mimicking convolutional filter weights.
    - Benign clients: energy smoothly distributed across all filters with minor variance.
    - Backdoor clients: energy heavily concentrated into 2-3 specific trigger-activated filters.
    """
    rng = np.random.default_rng(seed)
    # Shape: (num_filters, 32, 3, 3) -> 64 filters of 288 weights each
    weights = rng.normal(loc=0.0, scale=0.05, size=(num_filters, 32, 3, 3)).astype(np.float32)

    if is_backdoor:
        # Backdoor trigger concentrate massive energy in first 3 filters
        weights[0:3] *= 8.0

    tensor = torch.from_numpy(weights)
    delta = {"conv2.weight": tensor, "fc1.weight": torch.zeros(128, 3136)}

    return ClientUpdate(
        client_id=client_id,
        state_dict=delta,
        delta=delta,
        num_samples=100,
        is_malicious=is_backdoor,
        attack_type="BACKDOOR" if is_backdoor else "NONE",
    )


def test_layer_selection():
    """Verify layer selector finds deepest convolutional layer."""
    dummy_delta = {
        "conv1.weight": torch.zeros(32, 1, 3, 3),
        "conv2.weight": torch.zeros(64, 32, 3, 3),
        "fc1.weight": torch.zeros(128, 3136),
    }
    selected = select_target_layers(dummy_delta)
    assert selected == ["conv2.weight"], f"Expected ['conv2.weight'], got {selected}"


def test_cbe_extraction():
    """CBE must sum to 1.0 and concentration ratio must be in [0, 1]."""
    energies = np.array([10.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    cbe_dist, ratio = extract_cbe(energies, top_k_percent=0.2)
    
    assert len(cbe_dist) == 2  # 20% of 10 = 2
    assert np.isclose(np.sum(cbe_dist), 1.0, atol=1e-5), "CBE must sum to 1"
    assert 0.0 <= ratio <= 1.0, "Concentration ratio must be bounded [0, 1]"
    assert ratio > 0.5, "Top 2 items contain 11/19 of total energy"


def test_wasserstein_matrix_properties():
    """Wasserstein distance matrix must be symmetric and zero on diagonal."""
    dist_1 = np.array([0.5, 0.3, 0.2])
    dist_2 = np.array([0.4, 0.4, 0.2])
    dist_3 = np.array([0.9, 0.1, 0.0])

    matrix = compute_pairwise_wasserstein_matrix([dist_1, dist_2, dist_3])
    assert matrix.shape == (3, 3)
    assert np.allclose(np.diag(matrix), 0.0), "Diagonal must be 0"
    assert np.allclose(matrix, matrix.T), "Distance matrix must be symmetric"
    assert np.all(matrix >= 0.0), "Distances must be non-negative"


def test_benign_only_no_false_suspicious_cluster():
    """
    In a benign-only run, MARS must recognize homogeneity and NOT flag
    any client as suspicious (no false quarantine).
    """
    detector = MARSDetector()
    benign_updates = [
        _create_mock_update(f"C{i}", is_backdoor=False, seed=100 + i)
        for i in range(8)
    ]
    res = detector.analyze_updates(benign_updates)

    assert len(res["backdoor_suspects"]) == 0, (
        f"Expected 0 backdoor suspects in benign run, got {res['backdoor_suspects']}"
    )
    assert len(res["trusted_after_mars"]) == 8
    for cid, m_res in res["mars_results"].items():
        assert m_res["status"] == "PASS"


def test_backdoor_injected_run_isolates_suspects():
    """
    In a mixed run with 6 benign clients and 2 backdoor clients,
    MARS must correctly identify and quarantine the 2 backdoor clients.
    """
    detector = MARSDetector()
    updates = [
        _create_mock_update(f"C{i}", is_backdoor=False, seed=200 + i)
        for i in range(6)
    ]
    # Add 2 backdoor attackers
    updates.append(_create_mock_update("C_backdoor1", is_backdoor=True, seed=301))
    updates.append(_create_mock_update("C_backdoor2", is_backdoor=True, seed=302))

    res = detector.analyze_updates(updates)

    suspects = set(res["backdoor_suspects"])
    assert "C_backdoor1" in suspects, "C_backdoor1 should be quarantined by MARS"
    assert "C_backdoor2" in suspects, "C_backdoor2 should be quarantined by MARS"
    assert len(suspects) == 2, f"Expected 2 suspects, got {len(suspects)}: {suspects}"
    assert len(res["trusted_after_mars"]) == 6


def test_mars_edge_cases():
    """Handles small client sets (<3) without error."""
    detector = MARSDetector()
    updates = [_create_mock_update(f"C{i}", is_backdoor=False) for i in range(2)]
    res = detector.analyze_updates(updates)
    assert len(res["trusted_after_mars"]) == 2
    assert len(res["backdoor_suspects"]) == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
