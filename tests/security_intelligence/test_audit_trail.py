import os
import tempfile

import pytest

from security_intelligence.audit_trail import (
    AuditLogger,
    JSONLAuditStore,
    verify_chain,
)


def test_empty_chain_is_valid():
    report = verify_chain([])
    assert report.valid is True
    assert report.total_events == 0


def test_single_event_chain_is_valid():
    logger = AuditLogger()
    logger.log_event("GENERIC", "INFO", {"a": 1})
    events = logger.get_all_events()
    report = verify_chain(events)
    assert report.valid is True
    assert report.total_events == 1


def test_multiple_events_valid_chain():
    logger = AuditLogger()
    for i in range(5):
        logger.log_event("GENERIC", "INFO", {"i": i}, round_id=i)
    events = logger.get_all_events()
    report = verify_chain(events)
    assert report.valid is True
    assert report.total_events == 5


def test_modified_payload_detected():
    logger = AuditLogger()
    logger.log_event("LAYER1_ANOMALY", "WARNING", {"score": 0.9}, round_id=1, client_id="C1")
    logger.log_event("MARS_SUSPICION", "HIGH", {"score": 0.95}, round_id=1, client_id="C1")
    events = logger.get_all_events()

    events[0].payload["score"] = 0.1  # tamper
    report = verify_chain(events)
    assert report.valid is False
    assert report.broken_index == 0


def test_modified_hash_detected():
    logger = AuditLogger()
    logger.log_event("GENERIC", "INFO", {"x": 1})
    logger.log_event("GENERIC", "INFO", {"x": 2})
    events = logger.get_all_events()

    events[1].current_hash = "0" * 64  # tamper directly with the hash
    report = verify_chain(events)
    assert report.valid is False
    assert report.broken_index == 1


def test_broken_previous_hash_detected():
    logger = AuditLogger()
    logger.log_event("GENERIC", "INFO", {"x": 1})
    logger.log_event("GENERIC", "INFO", {"x": 2})
    events = logger.get_all_events()

    events[1].previous_hash = "f" * 64  # break the link
    report = verify_chain(events)
    assert report.valid is False
    assert report.broken_index == 1


def test_malformed_event_does_not_crash():
    logger = AuditLogger()
    logger.log_event("GENERIC", "INFO", {"x": 1})
    events = logger.get_all_events()
    events.append(None)  # malformed
    report = verify_chain(events)
    assert report.valid is False
    assert report.broken_index == 1


def test_sanitize_payload_strips_model_internals():
    logger = AuditLogger()
    result = logger.log_event(
        "GENERIC",
        "INFO",
        {"weights": [1, 2, 3], "gradient": [0.1], "client_id": "C1", "note": "fine"},
    )
    assert result.event.payload["weights"] == "<redacted:model-internal>"
    assert result.event.payload["gradient"] == "<redacted:model-internal>"
    assert result.event.payload["note"] == "fine"


def test_jsonl_storage_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "audit.jsonl")
        logger = AuditLogger(storage_path=path)
        logger.log_event("GENERIC", "INFO", {"a": 1})
        logger.log_event("GENERIC", "INFO", {"a": 2})

        # Reload from disk with a fresh logger instance.
        logger2 = AuditLogger(storage_path=path)
        events = logger2.get_all_events()
        assert len(events) == 2
        report = verify_chain(events)
        assert report.valid is True


def test_storage_failure_falls_back_to_memory_without_crashing():
    # Point at a path whose parent cannot be created (root-owned /proc entry
    # style path is not portable across CI, so instead pass a path with a
    # null byte to force an OSError deterministically).
    store = JSONLAuditStore(path="\0/not/a/real/path.jsonl")
    logger = AuditLogger(store=store)
    result = logger.log_event("GENERIC", "INFO", {"a": 1})
    assert result.event is not None  # event still created
    # Either persisted=False with a warning, or it degraded silently to
    # in-memory — either way, get_all_events must not raise.
    events = logger.get_all_events()
    assert len(events) >= 1
