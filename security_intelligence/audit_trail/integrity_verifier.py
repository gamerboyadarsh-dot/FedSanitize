"""
verify_chain(): re-derive every event's hash and confirm the previous_hash
links match, to detect tampering (payload edits, reordering, deletions,
hash edits) without ever raising.
"""

from dataclasses import dataclass
from typing import List, Optional

from .audit_event import AuditEvent
from .hash_chain import GENESIS_HASH, compute_hash


@dataclass
class IntegrityReport:
    valid: bool
    total_events: int
    broken_index: Optional[int]
    expected_hash: Optional[str]
    actual_hash: Optional[str]
    message: str

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "total_events": self.total_events,
            "broken_index": self.broken_index,
            "expected_hash": self.expected_hash,
            "actual_hash": self.actual_hash,
            "message": self.message,
        }


def verify_chain(events: List[AuditEvent]) -> IntegrityReport:
    total = len(events)

    if total == 0:
        return IntegrityReport(
            valid=True,
            total_events=0,
            broken_index=None,
            expected_hash=None,
            actual_hash=None,
            message="Empty chain — nothing to verify.",
        )

    expected_previous = GENESIS_HASH

    for idx, event in enumerate(events):
        try:
            if event is None:
                return IntegrityReport(
                    valid=False,
                    total_events=total,
                    broken_index=idx,
                    expected_hash=None,
                    actual_hash=None,
                    message=f"Malformed event at index {idx}: event is None.",
                )

            if event.previous_hash != expected_previous:
                return IntegrityReport(
                    valid=False,
                    total_events=total,
                    broken_index=idx,
                    expected_hash=expected_previous,
                    actual_hash=event.previous_hash,
                    message=(
                        f"Broken chain link at index {idx}: previous_hash does not "
                        "match the prior event's current_hash."
                    ),
                )

            recomputed = compute_hash(event.content_for_hash())

            if recomputed != event.current_hash:
                return IntegrityReport(
                    valid=False,
                    total_events=total,
                    broken_index=idx,
                    expected_hash=recomputed,
                    actual_hash=event.current_hash,
                    message=(
                        f"Tampering detected at index {idx}: stored hash does not "
                        "match recomputed hash (payload or metadata was altered)."
                    ),
                )

            expected_previous = event.current_hash

        except Exception as exc:
            return IntegrityReport(
                valid=False,
                total_events=total,
                broken_index=idx,
                expected_hash=None,
                actual_hash=None,
                message=f"Malformed event at index {idx}: {type(exc).__name__}: {exc}",
            )

    return IntegrityReport(
        valid=True,
        total_events=total,
        broken_index=None,
        expected_hash=events[-1].current_hash,
        actual_hash=events[-1].current_hash,
        message=f"Chain verified: {total} event(s), no tampering detected.",
    )
