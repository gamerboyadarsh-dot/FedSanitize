"""
QuarantineManager: tracks active reversible isolation state (used for both
QUARANTINE and TEMPORARY_ISOLATE actions — the only difference between the
two is severity/duration, not the mechanism). Clients are never deleted;
release/expire simply flips `active` to False.

Persistence is optional and best-effort — a storage failure degrades to
in-memory only and returns a warning, it never raises.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

from .response_models import QuarantineRecord


@dataclass
class QuarantineOpResult:
    ok: bool
    record: Optional[QuarantineRecord]
    warning: Optional[str] = None


class QuarantineManager:
    def __init__(self, storage_path: Optional[str] = None):
        self._records: Dict[str, QuarantineRecord] = {}  # keyed by client_id -> latest record
        self._history: List[QuarantineRecord] = []
        self._lock = threading.Lock()
        self.storage_path = storage_path
        self._degraded = False
        if storage_path:
            self._load_from_disk()

    # ---- persistence (best-effort) -----------------------------------
    def _load_from_disk(self) -> None:
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("records", []):
                    rec = QuarantineRecord(**item)
                    self._records[rec.client_id] = rec
                    self._history.append(rec)
        except Exception:
            self._degraded = True

    def _persist(self) -> Optional[str]:
        if not self.storage_path or self._degraded:
            return None
        try:
            directory = os.path.dirname(os.path.abspath(self.storage_path))
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"records": [r.to_dict() for r in self._history]}, f)
            return None
        except Exception as exc:
            self._degraded = True
            return f"quarantine persistence failed ({type(exc).__name__}); continuing in-memory only"

    # ---- operations -----------------------------------------------------
    def add(
        self,
        client_id: str,
        reason: str,
        start_round: int,
        expiry_round: Optional[int],
        evidence: Optional[list] = None,
    ) -> QuarantineOpResult:
        with self._lock:
            record = QuarantineRecord(
                client_id=client_id,
                reason=reason,
                start_round=start_round,
                expiry_round=expiry_round,
                active=True,
                evidence=evidence or [],
                review_status="PENDING",
            )
            self._records[client_id] = record
            self._history.append(record)
            warning = self._persist()
            return QuarantineOpResult(ok=warning is None, record=record, warning=warning)

    def check(self, client_id: str) -> Optional[QuarantineRecord]:
        with self._lock:
            return self._records.get(client_id)

    def is_active(self, client_id: str) -> bool:
        rec = self.check(client_id)
        return bool(rec and rec.active)

    def release(self, client_id: str, review_status: str = "RELEASED") -> QuarantineOpResult:
        with self._lock:
            rec = self._records.get(client_id)
            if rec is None:
                return QuarantineOpResult(ok=False, record=None, warning=f"no quarantine record for {client_id}")
            rec.active = False
            rec.review_status = review_status
            warning = self._persist()
            return QuarantineOpResult(ok=warning is None, record=rec, warning=warning)

    def expire_due(self, current_round: int) -> List[QuarantineRecord]:
        """Auto-release any active record whose expiry_round has passed. Returns the expired records."""
        expired = []
        with self._lock:
            for rec in self._records.values():
                if rec.active and rec.expiry_round is not None and current_round >= rec.expiry_round:
                    rec.active = False
                    rec.review_status = "EXPIRED"
                    expired.append(rec)
            if expired:
                self._persist()
        return expired

    def active_clients(self) -> List[str]:
        with self._lock:
            return [cid for cid, rec in self._records.items() if rec.active]

    def all_records(self) -> List[QuarantineRecord]:
        with self._lock:
            return list(self._history)
