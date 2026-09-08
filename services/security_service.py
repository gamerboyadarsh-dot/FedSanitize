"""
FedSanitize — Central Security Pipeline Service
================================================
Implements the strict sequential 3-layer security firewall:
  CLIENT MODEL UPDATES
        ↓
  LAYER 1: Update Anomaly Filter (L2 Norm + Cosine Similarity + MAD)
        ↓ (survivors only)
  LAYER 2: MARS Backdoor Analysis (Backdoor Energy + CBE + Wasserstein + Clustering)
        ↓ (survivors only)
  LAYER 3: Robust Aggregation (Coordinate-wise Trimmed Mean)
        ↓
  UPDATED GLOBAL MODEL

Grounded in PART 6 and PART 8 specifications.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import torch

try:
    from ..federated.client import ClientUpdate
    from ..defense.layer1_anomaly import Layer1AnomalyDetector, ClientSecurityResult
    from ..defense.layer2_mars import MARSDetector
    from ..defense.layer3_robust import Layer3RobustAggregator
    from ..config import FedSanitizeConfig, DEFAULT_CONFIG
except (ImportError, ValueError):
    from federated.client import ClientUpdate
    from defense.layer1_anomaly import Layer1AnomalyDetector, ClientSecurityResult
    from defense.layer2_mars import MARSDetector
    from defense.layer3_robust import Layer3RobustAggregator
    from config import FedSanitizeConfig, DEFAULT_CONFIG


@dataclass
class SecurityPipelineResult:
    """
    Encapsulates all results, telemetry, and per-client security diagnostics
    produced by the 3-layer security firewall.
    """
    updated_global_state: Dict[str, torch.Tensor]
    total_clients: int
    round_number: int
    layer1_results: Dict[str, ClientSecurityResult]
    layer1_quarantined: List[str]
    mars_results: Dict[str, Dict[str, Any]]
    mars_quarantined: List[str]
    trusted_clients: List[str]
    aggregation_metadata: Dict[str, Any]
    security_summary: Dict[str, Any]
    client_security_records: Dict[str, Dict[str, Any]]
    distance_matrix: Any = None  # np.ndarray from MARS


class SecurityPipeline:
    """
    Central sequential security coordinator.
    """
    def __init__(self, config: Optional[FedSanitizeConfig] = None):
        self.config = config if config is not None else DEFAULT_CONFIG
        self.layer1 = Layer1AnomalyDetector(config=self.config.layer1)
        self.layer2 = MARSDetector(config=self.config.mars)
        self.layer3 = Layer3RobustAggregator(config=self.config.aggregation)

    def process_round(
        self,
        global_state_dict: Dict[str, torch.Tensor],
        client_updates: List[ClientUpdate],
        round_number: int = 1,
    ) -> SecurityPipelineResult:
        """
        Executes Layer 1 -> Layer 2 (MARS) -> Layer 3 sequentially.
        """
        total_clients = len(client_updates)
        if total_clients == 0:
            raise ValueError("Security pipeline received zero client updates.")

        # -------------------------------------------------------------------
        # LAYER 1: Statistical Anomaly Filter
        # -------------------------------------------------------------------
        l1_output = self.layer1.detect_anomalies(client_updates)
        l1_trusted: List[ClientUpdate] = l1_output["trusted_updates"]
        l1_quarantined: List[str] = l1_output["quarantined_clients"]
        l1_results: Dict[str, ClientSecurityResult] = l1_output["results"]

        # -------------------------------------------------------------------
        # LAYER 2: MARS Backdoor Analysis (runs ONLY on Layer 1 survivors)
        # -------------------------------------------------------------------
        mars_output: Dict[str, Any] = {}
        mars_quarantined: List[str] = []
        mars_results: Dict[str, Dict[str, Any]] = {}
        mars_distance_matrix = None
        mars_trusted: List[ClientUpdate] = []

        if self.config.mars.enabled and len(l1_trusted) >= self.config.mars.min_clients_for_mars:
            mars_output = self.layer2.analyze_updates(l1_trusted)
            mars_trusted = mars_output["trusted_after_mars"]
            mars_quarantined = mars_output["backdoor_suspects"]
            mars_results = mars_output["mars_results"]
            mars_distance_matrix = mars_output["distance_matrix"]
        else:
            # MARS bypassed (disabled or insufficient clients)
            mars_trusted = l1_trusted
            for u in l1_trusted:
                mars_results[u.client_id] = {
                    "client_id": u.client_id,
                    "cluster_id": None,
                    "status": "PASS",
                    "reason": "MARS_SKIPPED (Insufficient surviving clients or disabled)",
                    "cbe_concentration_ratio": 0.0,
                    "is_backdoor_suspect": False,
                }

        # -------------------------------------------------------------------
        # LAYER 3: Robust Aggregation (runs ONLY on MARS survivors)
        # -------------------------------------------------------------------
        if not mars_trusted:
            # Extreme emergency: all clients flagged by L1 and L2
            # Use fallback: pick least anomalous client from L1
            fallback_u = l1_trusted[0] if l1_trusted else client_updates[0]
            mars_trusted = [fallback_u]

        new_global_state, agg_meta = self.layer3.aggregate(
            trusted_updates=mars_trusted,
            global_state_dict=global_state_dict,
        )

        trusted_ids = [u.client_id for u in mars_trusted]

        # -------------------------------------------------------------------
        # Build Per-Client Security Records (PART 8 Data Model)
        # -------------------------------------------------------------------
        client_security_records: Dict[str, Dict[str, Any]] = {}

        for update in client_updates:
            cid = update.client_id
            l1_res = l1_results.get(cid)
            m_res = mars_results.get(cid)

            l1_status = l1_res.status if l1_res else "UNKNOWN"
            l1_reason = l1_res.reason if l1_res else "UNKNOWN"

            if cid in l1_quarantined:
                mars_cluster = None
                mars_status = "SKIPPED_L1_QUARANTINE"
                mars_reason = "Blocked at Layer 1; skipped MARS analysis"
                final_status = "QUARANTINED"
            elif cid in mars_quarantined:
                mars_cluster = m_res.get("cluster_id") if m_res else None
                mars_status = "FLAGGED"
                mars_reason = m_res.get("reason", "FLAGGED_BY_MARS") if m_res else "FLAGGED_BY_MARS"
                final_status = "QUARANTINED"
            else:
                mars_cluster = m_res.get("cluster_id") if m_res else None
                mars_status = "PASS"
                mars_reason = m_res.get("reason", "BENIGN") if m_res else "BENIGN"
                final_status = "TRUSTED"

            client_security_records[cid] = {
                "client_id": cid,
                "attack_type": update.attack_type,
                "is_malicious": update.is_malicious,
                "update_norm": float(update.update_norm),
                "cosine_similarity": float(l1_res.cosine_similarity if l1_res else 0.0),
                "layer1_status": l1_status,
                "layer1_reason": l1_reason,
                "mars_cluster": mars_cluster,
                "mars_status": mars_status,
                "mars_reason": mars_reason,
                "final_status": final_status,
            }

        security_summary = {
            "round": round_number,
            "total_clients": total_clients,
            "layer1_blocked": len(l1_quarantined),
            "mars_blocked": len(mars_quarantined),
            "total_quarantined": len(l1_quarantined) + len(mars_quarantined),
            "trusted_count": len(trusted_ids),
            "aggregation_method": agg_meta.get("method_used", "coordinate_trimmed_mean"),
            "trim_count_applied": agg_meta.get("trim_count_applied", 0),
        }

        return SecurityPipelineResult(
            updated_global_state=new_global_state,
            total_clients=total_clients,
            round_number=round_number,
            layer1_results=l1_results,
            layer1_quarantined=l1_quarantined,
            mars_results=mars_results,
            mars_quarantined=mars_quarantined,
            trusted_clients=trusted_ids,
            aggregation_metadata=agg_meta,
            security_summary=security_summary,
            client_security_records=client_security_records,
            distance_matrix=mars_distance_matrix,
        )
