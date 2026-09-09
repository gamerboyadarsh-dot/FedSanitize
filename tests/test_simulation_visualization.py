"""
Unit & Integration Tests for Visualization Phases & Simulation Arena
====================================================================
Verifies ScenarioEngine, ExperimentSerializer, Plotly renderers,
HTML components, and dashboard entry points.
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
import plotly.graph_objects as go

from simulation.event_types import EventType
from simulation.security_event import SecurityEvent
from simulation.network_state import NetworkState
from simulation.scenario_engine import ScenarioEngine
from simulation.serialization import ExperimentSerializer

from visualization.network import render_network_graph, render_network_fallback_html
from visualization.defense import (
    render_layer1_norm_chart,
    render_layer1_cosine_chart,
    render_mars_cbe_chart,
    render_mars_wasserstein_heatmap,
    render_mars_clustering_scatter,
    render_aggregation_overview_chart,
)
from visualization.attacks import (
    render_backdoor_stages_html,
    render_extreme_update_comparison,
    render_sign_flip_vector_diagram,
    render_byzantine_noise_scatter,
)
from visualization.components import (
    render_arena_header_metrics,
    render_interactive_timeline_html,
    render_client_forensics_card,
    compute_threat_level,
    render_pipeline_status_bar,
    render_before_after_comparison,
)
from visualization.effects import (
    render_alert_banner,
    render_quarantine_action_card,
    render_live_security_feed_html,
)


def test_scenario_engine():
    """Verify distinct and accurate narrative retrieval for all attack types."""
    for attack in ["NORMAL", "EXTREME_UPDATE", "SIGN_FLIPPING", "RANDOM_BYZANTINE", "LABEL_FLIPPING", "BACKDOOR"]:
        narrative = ScenarioEngine.get_narrative(attack)
        assert narrative is not None
        assert narrative.title != ""
        assert len(narrative.story_steps) >= 4
        assert narrative.mitigating_layer != ""


def test_experiment_serializer():
    """Verify saving and loading experiment artifacts in JSON format."""
    tmp_dir = tempfile.mkdtemp()
    try:
        sample_exp = {
            "round": 2,
            "attack_type": "EXTREME_UPDATE",
            "total_clients": 5,
            "clean_accuracy": 0.965,
            "backdoor_asr": 0.01,
            "detection": {"tp": 1, "fp": 0, "tn": 4, "fn": 0},
            "client_security_records": {
                "C0": {"is_malicious": True, "final_status": "QUARANTINED", "update_norm": 45.0}
            },
            "distance_matrix": [[0.0, 0.5], [0.5, 0.0]],
            "mars_results": {},
            "trusted_clients": ["C1", "C2", "C3", "C4"],
            "quarantined_clients": ["C0"],
            "events": [
                {"event_type": "ROUND_STARTED", "round_id": 2, "timestamp": 0.0}
            ]
        }

        saved_path = ExperimentSerializer.save_experiment(sample_exp, output_dir=tmp_dir, name_prefix="test_run")
        assert os.path.exists(saved_path)
        assert os.path.exists(os.path.join(saved_path, "metadata.json"))
        assert os.path.exists(os.path.join(saved_path, "events.json"))
        assert os.path.exists(os.path.join(saved_path, "metrics.json"))

        loaded = ExperimentSerializer.load_experiment(saved_path)
        assert loaded["round"] == 2
        assert loaded["attack_type"] == "EXTREME_UPDATE"
        assert loaded["clean_accuracy"] == 0.965
        assert "C0" in loaded["client_security_records"]

        experiments = ExperimentSerializer.list_saved_experiments(tmp_dir)
        assert len(experiments) == 1
        assert experiments[0]["path"] == saved_path
    finally:
        shutil.rmtree(tmp_dir)


def test_network_renderers():
    """Verify Plotly and SVG fallback renderers execute without error."""
    client_records = {
        "C0": {"attack_type": "BENIGN", "is_malicious": False, "final_status": "TRUSTED"},
        "C1": {"attack_type": "BACKDOOR", "is_malicious": True, "final_status": "QUARANTINED"},
    }
    net_state = NetworkState(client_records=client_records, round_id=1)

    fig = render_network_graph(net_state, selected_client_id="C1")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 3  # Edges, Clients, Server

    svg = render_network_fallback_html(net_state, selected_client_id="C1")
    assert "<svg" in svg
    assert "C0" in svg
    assert "C1" in svg


def test_defense_charts():
    """Verify Layer 1 and Layer 2 (MARS) and Layer 3 Plotly figures generate properly."""
    client_records = {
        "C0": {"update_norm": 5.2, "cosine_similarity": 0.98, "layer1_status": "PASS"},
        "C1": {"update_norm": 48.0, "cosine_similarity": -0.3, "layer1_status": "FLAGGED"},
    }

    fig_norm = render_layer1_norm_chart(client_records)
    assert isinstance(fig_norm, go.Figure)

    fig_cos = render_layer1_cosine_chart(client_records)
    assert isinstance(fig_cos, go.Figure)

    mars_res = {
        "C0": {"cbe_concentration_ratio": 0.12, "is_backdoor_suspect": False, "cluster_id": 0},
        "C1": {"cbe_concentration_ratio": 0.82, "is_backdoor_suspect": True, "cluster_id": 1},
    }
    fig_cbe = render_mars_cbe_chart(mars_res)
    assert isinstance(fig_cbe, go.Figure)

    dist_mat = [[0.0, 1.8], [1.8, 0.0]]
    fig_w = render_mars_wasserstein_heatmap(dist_mat, client_ids=["C0", "C1"])
    assert isinstance(fig_w, go.Figure)

    fig_clust = render_mars_clustering_scatter(dist_mat, client_ids=["C0", "C1"], mars_results=mars_res)
    assert isinstance(fig_clust, go.Figure)

    fig_agg = render_aggregation_overview_chart({}, trusted_clients=["C0"], all_clients=["C0", "C1"])
    assert isinstance(fig_agg, go.Figure)


def test_components_and_effects():
    """Verify HTML component rendering functions produce valid, styled markup."""
    # Metric cards
    header_html = render_arena_header_metrics(1, "BACKDOOR", "CRITICAL", 0.97, 0.01, 2, 8)
    assert "ROUND" in header_html
    assert "BACKDOOR" in header_html

    # Threat panel
    tier, desc, score = compute_threat_level(2, 2, 0.02, "BACKDOOR")
    assert tier == "CRITICAL"
    assert score > 50

    # Pipeline status
    pipe_html = render_pipeline_status_bar("MARS", 1, 2, 7)
    assert "LAYER 1" in pipe_html
    assert "MARS" in pipe_html

    # Client Forensics
    dossier = render_client_forensics_card("C7", {"update_norm": 5.1, "cosine_similarity": 0.95, "final_status": "QUARANTINED"}, {})
    assert "CLIENT FORENSIC DOSSIER: C7" in dossier
    assert "QUARANTINED" in dossier

    # Alerts & Quarantine
    alert = render_alert_banner("CRITICAL", "Backdoor detected", "C7", "MARS")
    assert "Backdoor detected" in alert

    quar = render_quarantine_action_card("C7", "SUSPICIOUS_CBE_CLUSTER", "MARS", {})
    assert "LINK SEVERED" in quar

    # Live feed
    events = [
        SecurityEvent(event_type=EventType.ROUND_STARTED, round_id=1, timestamp=0.0, message="Round started"),
        SecurityEvent(event_type=EventType.MARS_CLIENT_QUARANTINED, round_id=1, client_id="C7", severity="CRITICAL", message="Quarantined"),
    ]
    feed = render_live_security_feed_html(events)
    assert "ROUND_STARTED" in feed
    assert "MARS_CLIENT_QUARANTINED" in feed
