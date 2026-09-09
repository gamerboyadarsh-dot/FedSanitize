"""
Storage backends for the audit trail.

Persistence is optional and best-effort: if the configured backend fails
for any reason (disk full, permissions, path missing) the store falls back
to an in-memory list and surfaces a warning string. It must NEVER raise
out of append()/load_all() into caller code (audit_logger / FL pipeline).
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import List, Optional

from .audit_event import AuditEvent


@dataclass
class StoreResult:
    ok: bool
    warning: Optional[str] = None


class InMemoryAuditStore:
    """Simplest, always-available backend. Used standalone or as fallback."""

    def __init__(self):
        self._events: List[AuditEvent] = []
        self._lock = threading.Lock()

    def append(self, event: AuditEvent) -> StoreResult:
        with self._lock:
            self._events.append(event)
        return StoreResult(ok=True)

    def load_all(self) -> List[AuditEvent]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class JSONLAuditStore:
    """
    Append-only JSON-Lines file backend — chosen over SQLite as the
    "simplest stable implementation" per the master prompt, with zero
    extra dependencies. Falls back to an internal in-memory buffer (and
    reports a warning) if the file can't be written to.
    """

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._fallback = InMemoryAuditStore()
        self._degraded = False
        # Best-effort directory creation; never raise from __init__.
        try:
            directory = os.path.dirname(os.path.abspath(path))
            if directory:
                os.makedirs(directory, exist_ok=True)
        except Exception:
            self._degraded = True

    def append(self, event: AuditEvent) -> StoreResult:
        if self._degraded:
            self._fallback.append(event)
            return StoreResult(ok=False, warning="audit_store degraded: using in-memory fallback")
        try:
            with self._lock:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
            return StoreResult(ok=True)
        except Exception as exc:
            self._degraded = True
            self._fallback.append(event)
            return StoreResult(
                ok=False,
                warning=f"audit_store write failed ({type(exc).__name__}): falling back to in-memory log",
            )

    def load_all(self) -> List[AuditEvent]:
        events: List[AuditEvent] = []
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            events.append(AuditEvent.from_dict(json.loads(line)))
                        except Exception:
                            # A single malformed line should not hide the rest
                            # of the chain — integrity_verifier will flag the
                            # gap separately.
                            continue
        except Exception:
            pass
        # Any events that landed in the in-memory fallback (because the file
        # became unwritable mid-run) are appended after the on-disk events.
        events.extend(self._fallback.load_all())
        return events

    def clear(self) -> None:
        try:
            if os.path.exists(self.path):
                os.remove(self.path)
        except Exception:
            pass
        self._fallback.clear()
        self._degraded = False
