"""
FedSanitize — Security Intelligence: Client Trust Engine
=========================================================
Feature 1: Client Trust & Reputation Engine

Maintains an explainable, persistent security reputation for each
federated client across rounds. Integrates TrustStore (persistence),
TrustPolicy (scoring), and TrustModels (levels).

This module is the sole public API for Feature 1. All other modules
should interact with trust data through ClientTrustEngine, not directly
with TrustStore or TrustPolicy.

Thread safety: NOT thread-safe (single-threaded FL loop assumed).
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..contracts.security_context import SecurityContext
from ..contracts.client_record import ClientSecurityRecord
from ..contracts.security_decision import TrustUpdate
from .trust_models import TrustLevel, score_to_level
from .trust_policy import TrustPolicy
from .trust_store import TrustStore

logger = logging.getLogger("FedSanitize.SecurityIntelligence.TrustEngine")


class ClientTrustEngine:
    """
    Feature 1: Client Trust & Reputation Engine.

    Public API
    ----------
    update(context)          → TrustUpdate | None
    update_batch(contexts)   → list[TrustUpdate]
    get_client(client_id)    → ClientSecurityRecord | None
    get_all_clients()        → list[ClientSecurityRecord]
    reset(client_id=None)    → None

    Parameters
    ----------
    config : dict | None
        Policy configuration. If None, uses safe defaults.
        See SecurityIntelligenceConfig / default_security.yaml for keys.
    store_path : str | Path | None
        Path for JSON persistence. If None, operates in memory-only mode.
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        store_path: Optional[str | Path] = None,
    ):
        self._config = config or {}
        initial_score = float(self._config.get("initial_score", 75.0))

        self._store = TrustStore(
            store_path=store_path,
            initial_score=initial_score,
        )
        self._policy = TrustPolicy(config=self._config)

    # -----------------------------------------------------------------------
    # Primary update API
    # -----------------------------------------------------------------------

    def update(self, context: SecurityContext) -> Optional[TrustUpdate]:
        """
        Processes a single SecurityContext and updates the client's reputation.

        If client_id is None, returns None (cannot update without an identity).
        If this round was already recorded (duplicate protection), logs a warning
        and returns None.

        Parameters
        ----------
        context : SecurityContext
            Normalized context for one client in one round.

        Returns
        -------
        TrustUpdate | None
            The explainable change record, or None if update was skipped.
        """
        if context.client_id is None:
            logger.debug("[TrustEngine] Skipping context with no client_id")
            return None

        cid = context.client_id

        # Duplicate event protection
        if self._store.has_seen_round(cid, context.round_id):
            logger.warning(
                f"[TrustEngine] Duplicate event: client '{cid}' round {context.round_id} "
                f"already recorded — skipping"
            )
            return None

        # Fetch or create record
        record = self._store.get(cid)

        # Compute delta via policy
        trust_update = self._policy.compute_update(context, record)

        # Apply delta to record
        self._policy.apply_update(trust_update, record, context)

        # Persist
        self._store.set(cid, record)

        logger.debug(
            f"[TrustEngine] {cid} round={context.round_id}: "
            f"{trust_update.previous_score:.1f} → {trust_update.new_score:.1f} "
            f"({trust_update.reason})"
        )

        return trust_update

    def update_batch(self, contexts: List[SecurityContext]) -> List[TrustUpdate]:
        """
        Processes multiple SecurityContexts (e.g., all clients in a round).

        Skips contexts with no client_id or duplicate rounds silently.

        Parameters
        ----------
        contexts : list[SecurityContext]

        Returns
        -------
        list[TrustUpdate]
            One entry per successfully updated client.
        """
        updates: List[TrustUpdate] = []
        for ctx in contexts:
            result = self.update(ctx)
            if result is not None:
                updates.append(result)
        return updates

    # -----------------------------------------------------------------------
    # Query API
    # -----------------------------------------------------------------------

    def get_client(self, client_id: str) -> Optional[ClientSecurityRecord]:
        """
        Returns the current reputation record for a client.

        Returns None if the client has never been seen.

        Parameters
        ----------
        client_id : str

        Returns
        -------
        ClientSecurityRecord | None
        """
        if client_id not in self._store.all_client_ids():
            return None
        return self._store.get(client_id)

    def get_all_clients(self) -> List[ClientSecurityRecord]:
        """Returns all stored client records."""
        return self._store.get_all()

    def get_trust_level(self, client_id: str) -> Optional[TrustLevel]:
        """
        Returns the current TrustLevel enum for a client.

        Parameters
        ----------
        client_id : str

        Returns
        -------
        TrustLevel | None
            None if client has never been seen.
        """
        record = self.get_client(client_id)
        if record is None:
            return None
        return score_to_level(record.trust_score)

    def get_summary(self) -> Dict:
        """
        Returns a round-summary dict suitable for logging / dashboard.
        Does NOT include raw history.

        Returns
        -------
        dict
            Keys: total_clients, trust_level_counts, avg_score,
                  quarantined_clients, high_risk_clients
        """
        records = self.get_all_clients()
        if not records:
            return {
                "total_clients": 0,
                "trust_level_counts": {},
                "avg_score": 0.0,
                "quarantined_clients": [],
                "high_risk_clients": [],
            }

        level_counts: Dict[str, int] = {}
        quarantined = []
        high_risk = []
        score_sum = 0.0

        for rec in records:
            level_counts[rec.trust_level] = level_counts.get(rec.trust_level, 0) + 1
            score_sum += rec.trust_score
            if rec.trust_level == TrustLevel.QUARANTINED.value:
                quarantined.append(rec.client_id)
            if rec.trust_level == TrustLevel.HIGH_RISK.value:
                high_risk.append(rec.client_id)

        return {
            "total_clients": len(records),
            "trust_level_counts": level_counts,
            "avg_score": round(score_sum / len(records), 2),
            "quarantined_clients": quarantined,
            "high_risk_clients": high_risk,
        }

    # -----------------------------------------------------------------------
    # Reset API
    # -----------------------------------------------------------------------

    def reset(self, client_id: Optional[str] = None) -> None:
        """
        Resets trust records to initial defaults.

        Parameters
        ----------
        client_id : str | None
            If provided, resets only that client.
            If None, resets all clients.
        """
        self._store.reset(client_id=client_id)
        if client_id:
            logger.info(f"[TrustEngine] Reset client '{client_id}'")
        else:
            logger.info("[TrustEngine] Reset all clients")
