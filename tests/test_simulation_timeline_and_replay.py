"""
Unit Tests for Phase 4: Timeline Builder, Network State, and Replay Engine
==========================================================================
Verifies deterministic animation timeline generation, radial client topology,
state transitions, and replay engine stepping and seeking.
"""

import pytest
import numpy as np

from simulation.event_types import EventType
from simulation.security_event import SecurityEvent
from simulation.timeline_builder import TimelineBuilder, TimelineStep, SceneType
from simulation.network_state import NetworkState, VisualState, compute_deterministic_layout
from simulation.replay_engine import ReplayEngine
from simulation.simulation_adapter import adapt_security_result


def test_timeline_builder_scenes():
    """Verify TimelineBuilder produces properly sequenced scenes and durations."""
    events = [
        SecurityEvent(event_type=EventType.ROUND_STARTED, round_id=1, timestamp=0.0),
        SecurityEvent(event_type=EventType.CLIENT_TRAINING_STARTED, round_id=1, client_id="C1", timestamp=0.1),
        SecurityEvent(event_type=EventType.ATTACK_ACTIVATED, round_id=1, client_id="C2", timestamp=0.3, severity="HIGH"),
        SecurityEvent(event_type=EventType.CLIENT_UPDATE_SENT, round_id=1, client_id="C1", timestamp=0.5),
        SecurityEvent(event_type=EventType.LAYER1_STARTED, round_id=1, layer="LAYER_1", timestamp=0.6),
        SecurityEvent(event_type=EventType.MARS_STARTED, round_id=1, layer="MARS", timestamp=1.0),
        SecurityEvent(event_type=EventType.AGGREGATION_FINISHED, round_id=1, layer="LAYER_3", timestamp=1.5),
        SecurityEvent(event_type=EventType.ROUND_COMPLETED, round_id=1, timestamp=2.0),
    ]

    builder = TimelineBuilder()
    timeline = builder.build_timeline(events)

    assert len(timeline) == len(events)
    # Check scene progression
    scenes = [step.scene for step in timeline]
    assert scenes == [
        SceneType.INTRO,
        SceneType.TRAINING,
        SceneType.ATTACK,
        SceneType.UPDATE_FLOW,
        SceneType.LAYER1,
        SceneType.MARS,
        SceneType.AGGREGATION,
        SceneType.RESULT,
    ]

    # Verify cumulative timing is strictly non-decreasing
    for i in range(1, len(timeline)):
        assert timeline[i].start_time >= timeline[i - 1].start_time
        assert timeline[i].duration > 0.0

    # Verify high severity gets high priority
    attack_step = timeline[2]
    assert attack_step.priority >= 4


def test_deterministic_layout_and_network_state():
    """Verify radial node layout is 100% deterministic and events mutate state accurately."""
    client_ids = ["C0", "C1", "C2", "C3"]
    pos1 = compute_deterministic_layout(client_ids)
    pos2 = compute_deterministic_layout(client_ids)
    assert pos1 == pos2  # Purely deterministic

    client_records = {
        "C0": {"attack_type": "BENIGN", "is_malicious": False},
        "C1": {"attack_type": "EXTREME_UPDATE", "is_malicious": True},
    }

    net_state = NetworkState(client_records=client_records, round_id=1)
    assert len(net_state.clients) == 2
    assert net_state.clients["C0"].visual_state == VisualState.NORMAL

    # Apply training
    net_state.apply_event(
        SecurityEvent(event_type=EventType.CLIENT_TRAINING_STARTED, round_id=1, client_id="C0")
    )
    assert net_state.clients["C0"].visual_state == VisualState.TRAINING

    # Apply attack
    net_state.apply_event(
        SecurityEvent(event_type=EventType.ATTACK_ACTIVATED, round_id=1, client_id="C1")
    )
    assert net_state.clients["C1"].visual_state == VisualState.ATTACKING

    # Apply quarantine at Layer 1
    net_state.apply_event(
        SecurityEvent(
            event_type=EventType.LAYER1_CLIENT_FLAGGED,
            round_id=1,
            client_id="C1",
            layer="LAYER_1",
            severity="HIGH"
        )
    )
    assert net_state.clients["C1"].visual_state == VisualState.QUARANTINED
    assert "C1" in net_state.quarantined_clients


def test_replay_engine_stepping_and_seeking():
    """Verify ReplayEngine step controls, seeking, speed changes, and state restoration."""
    events = [
        SecurityEvent(event_type=EventType.ROUND_STARTED, round_id=1),
        SecurityEvent(event_type=EventType.CLIENT_TRAINING_STARTED, round_id=1, client_id="C1"),
        SecurityEvent(event_type=EventType.ATTACK_ACTIVATED, round_id=1, client_id="C2"),
        SecurityEvent(event_type=EventType.LAYER1_CLIENT_FLAGGED, round_id=1, client_id="C2", layer="LAYER_1"),
        SecurityEvent(event_type=EventType.ROUND_COMPLETED, round_id=1),
    ]
    client_records = {
        "C1": {"attack_type": "BENIGN", "is_malicious": False},
        "C2": {"attack_type": "EXTREME_UPDATE", "is_malicious": True},
    }

    builder = TimelineBuilder()
    timeline = builder.build_timeline(events)

    engine = ReplayEngine(timeline=timeline, client_records=client_records, round_id=1)

    assert engine.total_steps == 5
    assert engine.current_step == 0
    assert not engine.is_playing

    # Step forward
    assert engine.step_forward() is True
    assert engine.current_step == 1
    assert engine.network_state.clients["C1"].visual_state == VisualState.TRAINING

    # Step forward to attack
    engine.step_forward()
    assert engine.current_step == 2
    assert engine.network_state.clients["C2"].visual_state == VisualState.ATTACKING

    # Step forward to quarantine
    engine.step_forward()
    assert engine.current_step == 3
    assert engine.network_state.clients["C2"].visual_state == VisualState.QUARANTINED
    assert "C2" in engine.network_state.quarantined_clients

    # Step backward
    assert engine.step_backward() is True
    assert engine.current_step == 2
    # C2 should be back in ATTACKING, not yet quarantined
    assert engine.network_state.clients["C2"].visual_state == VisualState.ATTACKING
    assert "C2" not in engine.network_state.quarantined_clients

    # Seek directly to final step
    engine.seek(4)
    assert engine.current_step == 4
    assert engine.is_finished

    # Reset
    engine.reset()
    assert engine.current_step == 0
    assert not engine.is_playing

    # Speed controls
    engine.set_speed(2.0)
    assert engine.playback_speed == 2.0
    engine.set_speed(3.7)  # snaps to 4.0
    assert engine.playback_speed == 4.0

    # Summary
    summary = engine.get_forensic_summary()
    assert summary["total_steps"] == 5
    assert summary["current_step"] == 0
    assert summary["playback_speed"] == 4.0
