"""
FedSanitize — Layer 1 Anomaly Filter Detector
==============================================
Detects obviously abnormal client updates prior to expensive backdoor analysis.
Evaluates update L2 norm, MAD deviations, and directional cosine similarity.
Produces explainable decisions with fallback handling when too few clients survive.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

try:
    from ...federated.client import ClientUpdate
    from ...config import Layer1Config
except (ImportError, ValueError):
    from federated.client import ClientUpdate
    from config import Layer1Config

from .update_features import extract_client_features

logger = logging.getLogger("FedSanitize.Layer1")


@dataclass
class ClientSecurityResult:
    """
    Explainable security assessment record for a client at Layer 1.
    """
    client_id: str
    update_norm: float
    norm_score: float
    cosine_similarity: float
    anomaly_flag: bool
    reason: str
    status: str  # "PASS" | "FLAGGED"
    metadata: Dict[str, Any] = field(default_factory=dict)


class Layer1AnomalyDetector:
    """
    Evaluates client updates using statistical anomaly detection.
    """
    def __init__(self, config: Optional[Layer1Config] = None):
        self.config = config if config is not None else Layer1Config()

    def detect_anomalies(
        self,
        client_updates: List[ClientUpdate],
    ) -> Dict[str, Any]:
        """
        Executes Layer 1 anomaly filtering across all client updates.

        Returns
        -------
        Dict[str, Any] with keys:
            - 'trusted_updates': List[ClientUpdate]
            - 'quarantined_clients': List[str]
            - 'results': Dict[str, ClientSecurityResult]
        """
        if not client_updates:
            return {
                "trusted_updates": [],
                "quarantined_clients": [],
                "results": {},
            }

        # Extract features for all clients
        features = extract_client_features(
            client_updates,
            use_robust_reference=self.config.use_robust_reference,
        )

        results: Dict[str, ClientSecurityResult] = {}
        quarantined: List[str] = []
        trusted: List[ClientUpdate] = []

        update_map = {u.client_id: u for u in client_updates}

        # Evaluate each client
        for client_id, feat in features.items():
            update_norm = feat["update_norm"]
            norm_score = feat["norm_score"]
            cos_sim = feat["cosine_similarity"]
            median_norm = feat["median_norm"]
            mad = feat["mad"]

            # MAD and relative norm threshold check
            # Coarse anomaly filter: flags genuine extreme model poisoning (e.g. 5x-10x+ norms, Byzantine noise)
            # while passing stealthy backdoor updates (~1.5x-2x norm) to Layer 2 MARS.
            effective_mad = max(mad, 0.50 * median_norm, 1e-4)
            mad_deviation = abs(update_norm - median_norm) / effective_mad
            is_norm_outlier = (mad_deviation > self.config.mad_threshold_multiplier) or (norm_score >= 0.6)

            # Directional alignment check (sign flipping / Byzantine)
            is_directional_outlier = cos_sim < self.config.cosine_similarity_threshold

            reasons: List[str] = []
            if is_norm_outlier:
                reasons.append("EXTREME_UPDATE_NORM")
            if is_directional_outlier:
                reasons.append("LOW_DIRECTIONAL_SIMILARITY")

            if len(reasons) > 1:
                final_reason = "MULTIPLE_ANOMALY_SIGNALS"
                is_anomaly = True
            elif len(reasons) == 1:
                final_reason = reasons[0]
                is_anomaly = True
            else:
                final_reason = "NORMAL_UPDATE"
                is_anomaly = False

            status = "FLAGGED" if is_anomaly else "PASS"

            sec_result = ClientSecurityResult(
                client_id=client_id,
                update_norm=update_norm,
                norm_score=norm_score,
                cosine_similarity=cos_sim,
                anomaly_flag=is_anomaly,
                reason=final_reason,
                status=status,
                metadata={
                    "mad_deviation": float(mad_deviation),
                    "median_norm": float(median_norm),
                    "mad": float(mad),
                    "specific_reasons": reasons,
                },
            )
            results[client_id] = sec_result

            if is_anomaly:
                quarantined.append(client_id)
            else:
                trusted.append(update_map[client_id])

        # -------------------------------------------------------------------
        # Fallback handling: Ensure minimum number of clients survive Layer 1
        # -------------------------------------------------------------------
        min_surviving = min(self.config.min_surviving_clients, len(client_updates))
        if len(trusted) < min_surviving:
            logger.warning(
                f"[Layer 1 Warning] Only {len(trusted)} client(s) survived Layer 1 "
                f"(minimum required: {min_surviving}). Triggering robust rank fallback."
            )
            # Rank all clients by composite anomaly score (lowest first)
            # Composite score: 0.6 * cosine_anomaly + 0.4 * norm_score
            # where cosine_anomaly is high if cos_sim is low/negative
            def client_risk(cid: str) -> float:
                res = results[cid]
                # Cosine distance / anomaly: 1 - max(cos_sim, 0.0)
                cos_risk = max(0.0, 1.0 - max(0.0, res.cosine_similarity))
                return 0.6 * cos_risk + 0.4 * res.norm_score

            ranked_clients = sorted(client_updates, key=lambda u: client_risk(u.client_id))
            recovered_updates = ranked_clients[:min_surviving]
            recovered_ids = {u.client_id for u in recovered_updates}

            # Update status for recovered clients
            for u in recovered_updates:
                if u.client_id in quarantined:
                    quarantined.remove(u.client_id)
                results[u.client_id].status = "PASS"
                results[u.client_id].anomaly_flag = False
                results[u.client_id].reason = f"{results[u.client_id].reason} (RECOVERED_BY_FALLBACK)"

            trusted = recovered_updates

        return {
            "trusted_updates": trusted,
            "quarantined_clients": quarantined,
            "results": results,
        }
