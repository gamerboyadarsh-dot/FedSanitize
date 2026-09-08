"""
FedSanitize — Layer 2: MARS Backdoor Defense Orchestrator
=========================================================
Implements the end-to-end MARS (Malignity-Aware Backdoor Defense) pipeline:
  Step 1: Layer Selection
  Step 2: Backdoor Energy Extraction
  Step 3: Concentrated Backdoor Energy (CBE) Calculation
  Step 4: Pairwise Wasserstein Distance Matrix
  Step 5: Agglomerative Clustering & Explainable Trust Decision

Reference:
  Wei Wan, Yuxuan Ning, Zhicong Huang, Cheng Hong, Shengshan Hu,
  Ziqi Zhou, Yechao Zhang, Tianqing Zhu, Wanlei Zhou, Leo Yu Zhang.
  "MARS: A Malignity-Aware Backdoor Defense in Federated Learning."
  NeurIPS 2025. arXiv:2509.20383.
  Official Code: https://github.com/yunming181920/MARS
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import numpy as np
import logging

try:
    from ...federated.client import ClientUpdate
    from ...config import MARSConfig
except (ImportError, ValueError):
    from federated.client import ClientUpdate
    from config import MARSConfig

from .layer_selection import select_target_layers
from .backdoor_energy import compute_filter_energies
from .cbe import extract_cbe
from .wasserstein import compute_pairwise_wasserstein_matrix
from .clustering import cluster_and_classify

logger = logging.getLogger("FedSanitize.MARS")


class MARSDetector:
    """
    Layer 2 MARS Backdoor Detector.
    Grounded in Wan et al., NeurIPS 2025.
    """
    def __init__(self, config: Optional[MARSConfig] = None):
        self.config = config if config is not None else MARSConfig()

    def analyze_updates(
        self,
        surviving_updates: List[ClientUpdate],
    ) -> Dict[str, Any]:
        """
        Runs the 5-step MARS pipeline on surviving client updates (post-Layer 1).

        Returns
        -------
        Dict[str, Any] with keys:
            - 'trusted_after_mars': List[ClientUpdate]
            - 'backdoor_suspects': List[str]
            - 'mars_results': Dict[str, Dict[str, Any]]
            - 'distance_matrix': np.ndarray
            - 'cluster_information': Dict[str, Any]
            - 'target_layers': List[str]
        """
        n = len(surviving_updates)
        if n == 0:
            return {
                "trusted_after_mars": [],
                "backdoor_suspects": [],
                "mars_results": {},
                "distance_matrix": np.zeros((0, 0)),
                "cluster_information": {},
                "target_layers": [],
            }

        # Step 1: Layer Selection
        target_layers = select_target_layers(
            surviving_updates[0].delta,
            configured_layers=self.config.selected_layers,
        )

        client_ids = [u.client_id for u in surviving_updates]
        update_map = {u.client_id: u for u in surviving_updates}

        # Step 2 & 3: Backdoor Energy & Concentrated Backdoor Energy (CBE)
        cbe_distributions: List[np.ndarray] = []
        cbe_ratios: List[float] = []

        for update in surviving_updates:
            energies = compute_filter_energies(update.delta, target_layers)
            cbe_dist, cbe_ratio = extract_cbe(
                energies,
                top_k_percent=self.config.top_k_percent,
            )
            cbe_distributions.append(cbe_dist)
            cbe_ratios.append(cbe_ratio)

        # Step 4: Pairwise Wasserstein Distance Matrix
        distance_matrix = compute_pairwise_wasserstein_matrix(
            cbe_distributions=cbe_distributions,
            cbe_concentration_ratios=cbe_ratios,
        )

        # Step 5: Clustering & Trust Decision
        clustering_result = cluster_and_classify(
            distance_matrix=distance_matrix,
            client_ids=client_ids,
            cbe_concentration_ratios=cbe_ratios,
            num_clusters=self.config.num_clusters,
        )

        suspect_ids = set(clustering_result["suspicious_client_ids"])
        trusted_ids = set(clustering_result["trusted_client_ids"])

        trusted_updates = [update_map[cid] for cid in client_ids if cid not in suspect_ids]
        backdoor_suspects = [cid for cid in client_ids if cid in suspect_ids]

        # Assemble per-client MARS results
        mars_results: Dict[str, Dict[str, Any]] = {}
        for i, cid in enumerate(client_ids):
            is_suspect = cid in suspect_ids
            cluster_id = clustering_result["cluster_labels"].get(cid, 0)
            status = "FLAGGED" if is_suspect else "PASS"
            reason = (
                f"MARS_SUSPICIOUS: {clustering_result['decision_reason']}"
                if is_suspect
                else "MARS_TRUSTED: BENIGN_REPRESENTATION"
            )

            mars_results[cid] = {
                "client_id": cid,
                "cluster_id": cluster_id,
                "status": status,
                "reason": reason,
                "cbe_concentration_ratio": float(cbe_ratios[i]),
                "is_backdoor_suspect": is_suspect,
            }

        return {
            "trusted_after_mars": trusted_updates,
            "backdoor_suspects": backdoor_suspects,
            "mars_results": mars_results,
            "distance_matrix": distance_matrix,
            "cluster_information": clustering_result,
            "target_layers": target_layers,
            "citation": self.config.paper_citation,
        }
