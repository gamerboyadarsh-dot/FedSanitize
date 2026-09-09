"""
AuditLogger: the only object other Team B modules should talk to when they
want to record something happened. Wraps event creation, hash-chaining,
and (optional) persistence behind one call: log_event(...).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import List, Optional

from .audit_event import AuditEvent
from .audit_store import InMemoryAuditStore, JSONLAuditStore, StoreResult
from .hash_chain import GENESIS_HASH, compute_hash


@dataclass
class LogResult:
    event: AuditEvent
    persisted: bool
    warning: Optional[str] = None


class AuditLogger:
    def __init__(self, store=None, storage_path: Optional[str] = None):
        """
        store: an object implementing append()/load_all()/clear(). If not
        given, a JSONLAuditStore at storage_path is used, or an
        InMemoryAuditStore if storage_path is also None.
        """
        if store is not None:
            self._store = store
        elif storage_path:
            self._store = JSONLAuditStore(storage_path)
        else:
            self._store = InMemoryAuditStore()
        self._lock = threading.Lock()
        # Cache last hash so we don't re-read the whole store on every
        # append; rebuilt lazily from storage on first use / after clear().
        self._last_hash: Optional[str] = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        try:
            existing = self._store.load_all()
            self._last_hash = existing[-1].current_hash if existing else GENESIS_HASH
        except Exception:
            self._last_hash = GENESIS_HASH
        self._initialized = True

    def log_event(
        self,
        event_type: str,
        severity: str,
        payload: Optional[dict] = None,
        round_id: Optional[int] = None,
        client_id: Optional[str] = None,
    ) -> LogResult:
        """Never raises. Always returns a LogResult; check `.warning`."""
        with self._lock:
            self._ensure_initialized()
            event = AuditEvent.new(
                event_type=event_type,
                severity=severity,
                payload=payload,
                round_id=round_id,
                client_id=client_id,
            )
            event.previous_hash = self._last_hash or GENESIS_HASH
            try:
                event.current_hash = compute_hash(event.content_for_hash())
            except Exception as exc:
                # Hashing should never fail (canonical_json is defensive),
                # but if it somehow does, don't lose the event: store it
                # unhashed and flag it clearly.
                event.current_hash = "HASH_ERROR"
                warning = f"hash computation failed ({type(exc).__name__}); event stored unhashed"
                self._store.append(event)
                return LogResult(event=event, persisted=False, warning=warning)

            result: StoreResult = self._store.append(event)
            self._last_hash = event.current_hash
            return LogResult(event=event, persisted=result.ok, warning=result.warning)

    def get_all_events(self) -> List[AuditEvent]:
        try:
            return self._store.load_all()
        except Exception:
            return []

    def reset(self) -> None:
        with self._lock:
            try:
                self._store.clear()
            except Exception:
                pass
            self._last_hash = None
            self._initialized = False
