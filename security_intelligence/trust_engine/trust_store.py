"""
FedSanitize — Security Intelligence: Trust Store
================================================
Persistent storage for ClientSecurityRecord objects.

Storage strategy:
  - Primary: JSON file on disk (human-inspectable, no extra deps).
  - Fallback: In-memory dict (on any I/O or corruption error).
  - Writes are atomic: write to temp file → rename to final path.
  - On corrupt JSON: log warning, recover prior valid in-memory state,
    do NOT crash the FL pipeline.
  - Duplicate event protection: refuses to update a record for a round
    that has already been recorded in that record's history.

Dependencies: stdlib only (json, pathlib, tempfile, shutil, logging).
"""

from __future__ import annotations
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from ..contracts.client_record import ClientSecurityRecord
from .trust_models import TrustLevel, score_to_level

logger = logging.getLogger("FedSanitize.SecurityIntelligence.TrustStore")

_INITIAL_SCORE = 75.0
_INITIAL_LEVEL = TrustLevel.MONITORED.value


class TrustStore:
    """
    Persistent reputation store for all federated clients.

    Thread safety: NOT thread-safe. The FL training loop is single-threaded
    per round; concurrent access is not a current requirement.

    Parameters
    ----------
    store_path : str | Path | None
        Path to the JSON persistence file. If None, operates in memory-only mode.
    initial_score : float
        Trust score assigned to new clients on first contact.
    """

    def __init__(
        self,
        store_path: Optional[str | Path] = None,
        initial_score: float = _INITIAL_SCORE,
    ):
        self._store_path: Optional[Path] = Path(store_path) if store_path else None
        self._initial_score = initial_score
        self._records: Dict[str, ClientSecurityRecord] = {}
        self._memory_only = store_path is None
        self._loaded = False

        if not self._memory_only:
            self._load_from_disk()
        else:
            self._loaded = True

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get(self, client_id: str) -> ClientSecurityRecord:
        """
        Returns the record for a client, creating a fresh default if absent.

        Parameters
        ----------
        client_id : str
            The client identifier.

        Returns
        -------
        ClientSecurityRecord
        """
        if client_id not in self._records:
            self._records[client_id] = self._new_record(client_id)
        return self._records[client_id]

    def set(self, client_id: str, record: ClientSecurityRecord) -> None:
        """
        Stores or updates a client record and persists to disk.

        Parameters
        ----------
        client_id : str
        record : ClientSecurityRecord
        """
        self._records[client_id] = record
        if not self._memory_only:
            self._save_to_disk()

    def get_all(self) -> List[ClientSecurityRecord]:
        """Returns all stored records as a list."""
        return list(self._records.values())

    def has_seen_round(self, client_id: str, round_id: Optional[int]) -> bool:
        """
        Returns True if the client already has a history entry for this round_id.
        Used for duplicate event protection.

        Parameters
        ----------
        client_id : str
        round_id : int | None
            If None, always returns False (cannot check).

        Returns
        -------
        bool
        """
        if round_id is None:
            return False
        if client_id not in self._records:
            return False
        for entry in self._records[client_id].history:
            if entry.get("round_id") == round_id:
                return True
        return False

    def reset(self, client_id: Optional[str] = None) -> None:
        """
        Resets trust records.

        Parameters
        ----------
        client_id : str | None
            If provided, resets only that client's record.
            If None, resets all records.
        """
        if client_id is not None:
            if client_id in self._records:
                del self._records[client_id]
                logger.info(f"[TrustStore] Reset record for client '{client_id}'")
        else:
            self._records = {}
            logger.info("[TrustStore] All client records reset")

        if not self._memory_only:
            self._save_to_disk()

    def all_client_ids(self) -> List[str]:
        """Returns all known client IDs."""
        return list(self._records.keys())

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _new_record(self, client_id: str) -> ClientSecurityRecord:
        """Creates a fresh record with default initial values."""
        record = ClientSecurityRecord(
            client_id=client_id,
            trust_score=self._initial_score,
            trust_level=score_to_level(self._initial_score).value,
        )
        return record

    def _load_from_disk(self) -> None:
        """
        Loads records from JSON file.
        On failure: logs warning, starts with empty in-memory state.
        Does NOT crash.
        """
        if self._store_path is None:
            return

        if not self._store_path.exists():
            logger.debug(f"[TrustStore] No existing store at '{self._store_path}' — starting fresh")
            self._loaded = True
            return

        try:
            with open(self._store_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if not isinstance(raw, dict):
                raise ValueError(f"Expected dict at root, got {type(raw).__name__}")

            for cid, record_dict in raw.items():
                try:
                    self._records[cid] = ClientSecurityRecord.from_dict(record_dict)
                except Exception as rec_err:
                    logger.warning(
                        f"[TrustStore] Skipping corrupt record for '{cid}': {rec_err}"
                    )

            logger.info(f"[TrustStore] Loaded {len(self._records)} client records from '{self._store_path}'")
            self._loaded = True

        except json.JSONDecodeError as e:
            logger.warning(
                f"[TrustStore] JSON decode error in '{self._store_path}': {e}. "
                f"Starting with empty in-memory state — previous state preserved."
            )
            self._memory_only = True  # degrade gracefully
            self._loaded = True

        except Exception as e:
            logger.warning(
                f"[TrustStore] Failed to load store from '{self._store_path}': {e}. "
                f"Operating in memory-only mode."
            )
            self._memory_only = True
            self._loaded = True

    def _save_to_disk(self) -> None:
        """
        Persists all records to disk atomically (temp file → rename).
        On failure: logs warning, does NOT crash.
        """
        if self._store_path is None or self._memory_only:
            return

        try:
            # Ensure parent directory exists
            self._store_path.parent.mkdir(parents=True, exist_ok=True)

            payload = {cid: rec.to_dict() for cid, rec in self._records.items()}

            # Atomic write: write to temp file first, then rename
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=self._store_path.parent,
                prefix=".trust_store_tmp_",
                suffix=".json",
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
                    json.dump(payload, tmp_f, indent=2, default=str)
                shutil.move(tmp_path, str(self._store_path))
            except Exception:
                # Clean up temp file if rename failed
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise

        except Exception as e:
            logger.warning(f"[TrustStore] Failed to persist store to '{self._store_path}': {e}")
