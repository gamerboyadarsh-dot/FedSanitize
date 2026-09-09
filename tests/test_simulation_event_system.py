"""
Unit Tests for Phase 2: Simulation Event System
================================================
Validates EventType, SecurityEvent, EventRecorder, and safe serialization.
"""

import json
import pytest
import numpy as np
import torch
from dataclasses import dataclass

from simulation.event_types import EventType
from simulation.security_event import SecurityEvent
from simulation.event_recorder import EventRecorder, sanitize_value


def test_event_types_constants():
    """Verify core event constants exist and are distinct."""
    assert EventType.ROUND_STARTED == "ROUND_STARTED"
    assert EventType.CLIENT_TRAINING_STARTED == "CLIENT_TRAINING_STARTED"
    assert EventType.ATTACK_ACTIVATED == "ATTACK_ACTIVATED"
    assert EventType.CLIENT_UPDATE_CREATED == "CLIENT_UPDATE_CREATED"
    assert EventType.CLIENT_UPDATE_SENT == "CLIENT_UPDATE_SENT"
    assert EventType.LAYER1_STARTED == "LAYER1_STARTED"
    assert EventType.LAYER1_CLIENT_FLAGGED == "LAYER1_CLIENT_FLAGGED"
    assert EventType.LAYER1_CLIENT_PASSED == "LAYER1_CLIENT_PASSED"
    assert EventType.MARS_STARTED == "MARS_STARTED"
    assert EventType.MARS_CLIENT_QUARANTINED == "MARS_CLIENT_QUARANTINED"
    assert EventType.AGGREGATION_STARTED == "AGGREGATION_STARTED"
    assert EventType.AGGREGATION_TRIMMING == "AGGREGATION_TRIMMING"
    assert EventType.GLOBAL_MODEL_UPDATED == "GLOBAL_MODEL_UPDATED"
    assert EventType.ROUND_COMPLETED == "ROUND_COMPLETED"

    all_types = EventType.all_types()
    assert len(all_types) >= 20
    assert len(all_types) == len(set(all_types))  # No duplicates


def test_security_event_model():
    """Verify SecurityEvent creation, serialization and reconstruction."""
    evt = SecurityEvent(
        event_type=EventType.LAYER1_CLIENT_FLAGGED,
        round_id=2,
        client_id="C3",
        layer="LAYER_1",
        timestamp=1.25,
        severity="HIGH",
        message="Extreme update norm detected",
        payload={"update_norm": 42.5, "threshold": 12.0}
    )

    d = evt.to_dict()
    assert d["event_type"] == EventType.LAYER1_CLIENT_FLAGGED
    assert d["round_id"] == 2
    assert d["client_id"] == "C3"
    assert d["layer"] == "LAYER_1"
    assert d["timestamp"] == 1.25
    assert d["severity"] == "HIGH"
    assert d["payload"]["update_norm"] == 42.5

    # Round trip from dict
    reconstructed = SecurityEvent.from_dict(d)
    assert reconstructed.event_type == evt.event_type
    assert reconstructed.client_id == evt.client_id
    assert reconstructed.payload == evt.payload


def test_sanitize_value():
    """Verify robust serialization prevents raw heavy tensors from polluting events."""
    # NumPy scalar
    np_val = np.float32(3.14)
    assert isinstance(sanitize_value(np_val), float)

    # Small PyTorch tensor
    t_small = torch.tensor([1.0, 2.0, 3.0])
    sanitized_small = sanitize_value(t_small)
    assert sanitized_small == [1.0, 2.0, 3.0]

    # Large PyTorch model tensor
    t_large = torch.randn(100, 100)
    sanitized_large = sanitize_value(t_large)
    assert isinstance(sanitized_large, dict)
    assert sanitized_large["type"] == "TensorSummary"
    assert sanitized_large["shape"] == [100, 100]
    assert "norm" in sanitized_large
    assert "mean" in sanitized_large

    # Large NumPy array
    arr_large = np.ones((50, 50))
    sanitized_arr = sanitize_value(arr_large)
    assert isinstance(sanitized_arr, dict)
    assert sanitized_arr["type"] == "ArraySummary"
    assert sanitized_arr["shape"] == [50, 50]

    # Dataclass serialization
    @dataclass
    class DummyRecord:
        id: str
        score: float

    rec = DummyRecord(id="test", score=0.99)
    sanitized_rec = sanitize_value(rec)
    assert sanitized_rec == {"id": "test", "score": 0.99}

    # NaN / Inf guards
    nan_val = float("nan")
    assert sanitize_value(nan_val) == 0.0


def test_event_recorder_functionality():
    """Verify EventRecorder recording, sorting, querying, and JSON export."""
    recorder = EventRecorder()

    recorder.record(EventType.ROUND_STARTED, round_id=1, timestamp=0.0)
    recorder.record(EventType.CLIENT_TRAINING_STARTED, round_id=1, client_id="C1", timestamp=0.2)
    recorder.record(EventType.LAYER1_CLIENT_FLAGGED, round_id=1, client_id="C2", layer="LAYER_1", severity="HIGH", timestamp=1.0)
    recorder.record(EventType.MARS_CLIENT_QUARANTINED, round_id=1, client_id="C3", layer="MARS", severity="CRITICAL", timestamp=2.0)
    recorder.record(EventType.ROUND_STARTED, round_id=2, timestamp=3.0)

    assert recorder.count() == 5

    # Filter by round
    r1_events = recorder.get_events_by_round(1)
    assert len(r1_events) == 4

    # Filter by client
    c2_events = recorder.filter_by_client("C2")
    assert len(c2_events) == 1
    assert c2_events[0].event_type == EventType.LAYER1_CLIENT_FLAGGED

    # Filter by layer
    l1_events = recorder.filter_by_layer("LAYER_1")
    assert len(l1_events) == 1
    mars_events = recorder.filter_by_layer("MARS")
    assert len(mars_events) == 1

    # Filter by severity
    crit_events = recorder.filter_by_severity("CRITICAL")
    assert len(crit_events) == 1
    assert crit_events[0].client_id == "C3"

    # Export JSON
    json_str = recorder.export_json()
    loaded = json.loads(json_str)
    assert len(loaded) == 5
    assert loaded[0]["event_type"] == EventType.ROUND_STARTED

    # Clear
    recorder.clear()
    assert recorder.count() == 0
