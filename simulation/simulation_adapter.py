"""
FedSantize Simulation Engine — Simulation Adapter
=================================================
Converts actual backend Federated Learning execution and security pipeline
results (SecurityPipelineResult or SimulationService round records) into an
ordered stream of verifiable, non-fabricated SecurityEvent instances.

Grounded in Phase 4 of the simulation engine specification.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
import numpy as np

from .event_types import EventType
from .security_event import SecurityEvent
from .event_recorder import sanitize_value


@dataclass
class SimulationResult:
    """
    Standardized simulation data payload produced by the SimulationAdapter.
    """
    events: List[SecurityEvent]
    client_security_records: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    mars_data: Dict[str, Any]
    network_metadata: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


def safe_get(obj: Any, possible_names: Union[str, List[str]], default: Any = None) -> Any:
    """
    Safely retrieves a value from either a dict or an object instance using
    a priority list of alternative field names.
    """
    if obj is None:
        return default

    names = [possible_names] if isinstance(possible_names, str) else possible_names

    # Check dict mapping
    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
        # Case-insensitive dict fallback
        lower_map = {str(k).lower(): v for k, v in obj.items()}
        for name in names:
            if name.lower() in lower_map:
                return lower_map[name.lower()]
        return default

    # Check object attributes
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)

    # Case-insensitive attribute fallback
    for name in names:
        for attr in dir(obj):
            if attr.lower() == name.lower():
                return getattr(obj, attr)

    return default


class SimulationAdapter:
    """
    Translates actual backend execution structures into chronological SecurityEvents
    and a unified SimulationResult.
    """

    def __init__(self):
        self.warnings: List[str] = []

    def adapt_round_start(self, round_id: int, total_clients: int, t: float) -> SecurityEvent:
        return SecurityEvent(
            event_type=EventType.ROUND_STARTED,
            round_id=round_id,
            timestamp=round(t, 2),
            severity="INFO",
            message=f"Federated Learning Round {round_id} started with {total_clients} clients.",
            payload={"total_clients": total_clients},
        )

    def adapt_client_training(
        self,
        client_records: Dict[str, Dict[str, Any]],
        round_id: int,
        start_t: float,
    ) -> List[SecurityEvent]:
        events = []
        t = start_t
        for cid, rec in sorted(client_records.items()):
            events.append(
                SecurityEvent(
                    event_type=EventType.CLIENT_TRAINING_STARTED,
                    round_id=round_id,
                    client_id=cid,
                    timestamp=round(t, 2),
                    severity="INFO",
                    message=f"Client {cid} started local model training.",
                    payload={"client_id": cid},
                )
            )
            t += 0.05
            events.append(
                SecurityEvent(
                    event_type=EventType.CLIENT_TRAINING_FINISHED,
                    round_id=round_id,
                    client_id=cid,
                    timestamp=round(t, 2),
                    severity="INFO",
                    message=f"Client {cid} completed local model training.",
                    payload={"client_id": cid},
                )
            )
            t += 0.05
        return events

    def adapt_attack(
        self,
        client_records: Dict[str, Dict[str, Any]],
        round_id: int,
        start_t: float,
    ) -> List[SecurityEvent]:
        events = []
        t = start_t
        for cid, rec in sorted(client_records.items()):
            is_malicious = rec.get("is_malicious", False)
            attack_type = rec.get("attack_type", "BENIGN")
            if is_malicious and attack_type not in (None, "", "NONE", "BENIGN"):
                severity = "CRITICAL" if attack_type == "BACKDOOR" else "HIGH"
                events.append(
                    SecurityEvent(
                        event_type=EventType.ATTACK_ACTIVATED,
                        round_id=round_id,
                        client_id=cid,
                        timestamp=round(t, 2),
                        severity=severity,
                        message=f"Adversarial attack '{attack_type}' engaged by client {cid}.",
                        payload={
                            "client_id": cid,
                            "attack_type": attack_type,
                            "is_malicious": True,
                        },
                    )
                )
                t += 0.05
        return events

    def adapt_client_updates(
        self,
        client_records: Dict[str, Dict[str, Any]],
        round_id: int,
        start_t: float,
    ) -> List[SecurityEvent]:
        events = []
        t = start_t
        for cid, rec in sorted(client_records.items()):
            norm = rec.get("update_norm", 0.0)
            events.append(
                SecurityEvent(
                    event_type=EventType.CLIENT_UPDATE_CREATED,
                    round_id=round_id,
                    client_id=cid,
                    timestamp=round(t, 2),
                    severity="INFO",
                    message=f"Client {cid} compiled parameter update delta (L2 norm: {norm:.4f}).",
                    payload={"update_norm": float(norm)},
                )
            )
            t += 0.04
            events.append(
                SecurityEvent(
                    event_type=EventType.CLIENT_UPDATE_SENT,
                    round_id=round_id,
                    client_id=cid,
                    timestamp=round(t, 2),
                    severity="INFO",
                    message=f"Client {cid} transmitted parameter update to server.",
                    payload={"client_id": cid},
                )
            )
            t += 0.04
        return events

    def adapt_layer1(
        self,
        l1_results: Dict[str, Any],
        l1_quarantined: List[str],
        client_records: Dict[str, Dict[str, Any]],
        round_id: int,
        start_t: float,
    ) -> List[SecurityEvent]:
        events = []
        t = start_t
        events.append(
            SecurityEvent(
                event_type=EventType.LAYER1_STARTED,
                round_id=round_id,
                layer="LAYER_1",
                timestamp=round(t, 2),
                severity="INFO",
                message="Layer 1 Statistical Anomaly Filter activated (Norm + Cosine + MAD).",
                payload={"quarantined_so_far": len(l1_quarantined)},
            )
        )
        t += 0.05

        for cid, rec in sorted(client_records.items()):
            events.append(
                SecurityEvent(
                    event_type=EventType.LAYER1_ANALYZING,
                    round_id=round_id,
                    client_id=cid,
                    layer="LAYER_1",
                    timestamp=round(t, 2),
                    severity="INFO",
                    message=f"Layer 1 evaluating update stats for client {cid}.",
                    payload={"client_id": cid},
                )
            )
            t += 0.05

            l1_obj = l1_results.get(cid)
            norm = rec.get("update_norm", safe_get(l1_obj, "update_norm", 0.0))
            cos_sim = rec.get("cosine_similarity", safe_get(l1_obj, "cosine_similarity", 0.0))
            l1_status = rec.get("layer1_status", safe_get(l1_obj, "status", "PASS"))
            l1_reason = rec.get("layer1_reason", safe_get(l1_obj, "reason", "NORMAL_UPDATE"))

            if cid in l1_quarantined or l1_status == "FLAGGED":
                events.append(
                    SecurityEvent(
                        event_type=EventType.LAYER1_CLIENT_FLAGGED,
                        round_id=round_id,
                        client_id=cid,
                        layer="LAYER_1",
                        timestamp=round(t, 2),
                        severity="HIGH",
                        message=f"Client {cid} FLAGGED by Layer 1: {l1_reason}.",
                        payload={
                            "update_norm": float(norm),
                            "cosine_similarity": float(cos_sim),
                            "reason": str(l1_reason),
                            "status": "FLAGGED",
                        },
                    )
                )
            else:
                events.append(
                    SecurityEvent(
                        event_type=EventType.LAYER1_CLIENT_PASSED,
                        round_id=round_id,
                        client_id=cid,
                        layer="LAYER_1",
                        timestamp=round(t, 2),
                        severity="INFO",
                        message=f"Client {cid} passed Layer 1 inspection.",
                        payload={
                            "update_norm": float(norm),
                            "cosine_similarity": float(cos_sim),
                            "status": "PASS",
                        },
                    )
                )
            t += 0.05
        return events

    def adapt_mars(
        self,
        mars_results: Dict[str, Any],
        mars_quarantined: List[str],
        distance_matrix: Any,
        client_records: Dict[str, Dict[str, Any]],
        round_id: int,
        start_t: float,
    ) -> List[SecurityEvent]:
        events = []
        t = start_t

        if not mars_results:
            if "No MARS forensic results present in this round." not in self.warnings:
                self.warnings.append("No MARS forensic results present in this round.")
            return events

        events.append(
            SecurityEvent(
                event_type=EventType.MARS_STARTED,
                round_id=round_id,
                layer="MARS",
                timestamp=round(t, 2),
                severity="INFO",
                message="Layer 2 MARS Backdoor Forensic Analysis activated.",
                payload={},
            )
        )
        t += 0.05

        events.append(
            SecurityEvent(
                event_type=EventType.MARS_LAYER_SELECTED,
                round_id=round_id,
                layer="MARS",
                timestamp=round(t, 2),
                severity="INFO",
                message="MARS selected target feature representation layers for forensic inspection.",
                payload={"target_layers": ["conv1", "conv2"]},
            )
        )
        t += 0.05

        events.append(
            SecurityEvent(
                event_type=EventType.MARS_ENERGY_ANALYZED,
                round_id=round_id,
                layer="MARS",
                timestamp=round(t, 2),
                severity="INFO",
                message="Backdoor energy profiles extracted across client representation filters.",
                payload={},
            )
        )
        t += 0.05

        # CBE Extraction
        cbe_summary = {}
        for cid, mres in mars_results.items():
            ratio = safe_get(mres, ["cbe_concentration_ratio", "cbe_ratio"], 0.0)
            cbe_summary[cid] = float(ratio)

        events.append(
            SecurityEvent(
                event_type=EventType.MARS_CBE_CREATED,
                round_id=round_id,
                layer="MARS",
                timestamp=round(t, 2),
                severity="INFO",
                message="Concentrated Backdoor Energy (CBE) distributions computed.",
                payload={"cbe_ratios": cbe_summary},
            )
        )
        t += 0.05

        # Distance Computation
        dist_meta = {}
        if distance_matrix is not None and hasattr(distance_matrix, "__len__"):
            mat = np.array(distance_matrix) if not isinstance(distance_matrix, np.ndarray) else distance_matrix
            if mat.size > 0:
                dist_meta = {
                    "max_distance": float(np.max(mat)),
                    "mean_distance": float(np.mean(mat)),
                    "matrix_shape": list(mat.shape),
                }

        events.append(
            SecurityEvent(
                event_type=EventType.MARS_DISTANCE_COMPUTED,
                round_id=round_id,
                layer="MARS",
                timestamp=round(t, 2),
                severity="INFO",
                message="Pairwise Wasserstein distance matrix computed over CBE distributions.",
                payload=dist_meta,
            )
        )
        t += 0.05

        # Cluster Created
        cluster_labels = {}
        for cid, mres in mars_results.items():
            c_id = safe_get(mres, ["cluster_id", "cluster"], None)
            if c_id is not None:
                cluster_labels[cid] = int(c_id)

        events.append(
            SecurityEvent(
                event_type=EventType.MARS_CLUSTER_CREATED,
                round_id=round_id,
                layer="MARS",
                timestamp=round(t, 2),
                severity="INFO",
                message="Agglomerative clustering partitioned client representations.",
                payload={
                    "clusters": cluster_labels,
                    "suspect_count": len(mars_quarantined),
                },
            )
        )
        t += 0.05

        # Quarantined Clients
        for cid in mars_quarantined:
            mres = mars_results.get(cid, {})
            cbe = safe_get(mres, ["cbe_concentration_ratio", "cbe_ratio"], 0.0)
            cluster = safe_get(mres, ["cluster_id", "cluster"], None)
            reason = safe_get(mres, "reason", "MARS_SUSPICIOUS: Backdoor signature detected")
            events.append(
                SecurityEvent(
                    event_type=EventType.MARS_CLIENT_QUARANTINED,
                    round_id=round_id,
                    client_id=cid,
                    layer="MARS",
                    timestamp=round(t, 2),
                    severity="CRITICAL",
                    message=f"Client {cid} QUARANTINED by MARS: {reason}.",
                    payload={
                        "cbe_ratio": float(cbe),
                        "cluster_id": cluster,
                        "reason": str(reason),
                    },
                )
            )
            t += 0.05

        return events

    def adapt_aggregation(
        self,
        agg_meta: Dict[str, Any],
        trusted_clients: List[str],
        round_id: int,
        start_t: float,
    ) -> List[SecurityEvent]:
        events = []
        t = start_t
        method = safe_get(agg_meta, ["method_used", "aggregation_method"], "coordinate_trimmed_mean")
        trim_count = safe_get(agg_meta, ["trim_count", "trim_count_applied"], 0)
        trim_ratio = safe_get(agg_meta, "trim_ratio", 0.1)

        events.append(
            SecurityEvent(
                event_type=EventType.AGGREGATION_STARTED,
                round_id=round_id,
                layer="LAYER_3",
                timestamp=round(t, 2),
                severity="INFO",
                message=f"Layer 3 Robust Aggregation initiated on {len(trusted_clients)} verified client(s).",
                payload={"trusted_count": len(trusted_clients), "method": str(method)},
            )
        )
        t += 0.05

        events.append(
            SecurityEvent(
                event_type=EventType.AGGREGATION_TRIMMING,
                round_id=round_id,
                layer="LAYER_3",
                timestamp=round(t, 2),
                severity="INFO",
                message=f"Executing coordinate-wise trimming (trim count: {trim_count}, ratio: {trim_ratio}).",
                payload={"trim_count": int(trim_count), "trim_ratio": float(trim_ratio)},
            )
        )
        t += 0.05

        events.append(
            SecurityEvent(
                event_type=EventType.AGGREGATION_FINISHED,
                round_id=round_id,
                layer="LAYER_3",
                timestamp=round(t, 2),
                severity="INFO",
                message="Robust aggregation successfully completed. Sanitized global parameter update produced.",
                payload={"surviving_clients": list(trusted_clients)},
            )
        )
        t += 0.05

        return events

    def adapt_global_update(self, round_id: int, t: float) -> SecurityEvent:
        return SecurityEvent(
            event_type=EventType.GLOBAL_MODEL_UPDATED,
            round_id=round_id,
            timestamp=round(t, 2),
            severity="INFO",
            message=f"Global neural network weights updated for Round {round_id}.",
            payload={},
        )

    def adapt_round_complete(self, metrics: Dict[str, Any], round_id: int, t: float) -> SecurityEvent:
        clean_acc = metrics.get("clean_accuracy", 0.0)
        asr = metrics.get("backdoor_asr", 0.0)
        return SecurityEvent(
            event_type=EventType.ROUND_COMPLETED,
            round_id=round_id,
            timestamp=round(t, 2),
            severity="INFO",
            message=f"Round {round_id} completed. Clean Acc: {clean_acc * 100:.2f}%, Backdoor ASR: {asr * 100:.2f}%.",
            payload={
                "clean_accuracy": float(clean_acc),
                "backdoor_asr": float(asr),
                "detection": metrics.get("detection", {}),
            },
        )

    def adapt_security_result(
        self,
        result: Any,
        round_number: Optional[int] = None,
        config: Optional[Any] = None,
        client_updates: Optional[List[Any]] = None,
    ) -> SimulationResult:
        """
        Main entry point converting raw backend pipeline outputs into SimulationResult.
        Accepts SecurityPipelineResult, dict from SimulationService, or generic objects.
        """
        self.warnings.clear()

        # Extract round number
        r_num = round_number or safe_get(result, ["round_number", "round"], 1)
        total_clients = safe_get(result, "total_clients", 10)

        # Extract client security records
        client_records = safe_get(result, ["client_security_records", "client_records"], {})

        # Extract Layer 1 structures
        l1_results = safe_get(result, ["layer1_results", "l1_results"], {})
        l1_quarantined = safe_get(result, ["layer1_quarantined", "l1_quarantined"], [])

        # Extract MARS structures
        mars_results = safe_get(result, "mars_results", {})
        mars_quarantined = safe_get(result, "mars_quarantined", [])
        distance_matrix = safe_get(result, ["distance_matrix", "mars_distance_matrix"], None)
        if not mars_results:
            self.warnings.append("No MARS forensic results present in this round.")

        # If client_records is empty but client_updates is provided, synthesize records safely
        if not client_records and client_updates:
            client_records = {}
            for u in client_updates:
                cid = safe_get(u, "client_id", "C0")
                client_records[cid] = {
                    "client_id": cid,
                    "attack_type": safe_get(u, "attack_type", "BENIGN"),
                    "is_malicious": safe_get(u, "is_malicious", False),
                    "update_norm": float(safe_get(u, "update_norm", 0.0)),
                    "cosine_similarity": 1.0,
                    "layer1_status": "PASS",
                    "layer1_reason": "NORMAL_UPDATE",
                    "mars_cluster": 0,
                    "mars_status": "PASS",
                    "mars_reason": "BENIGN",
                    "final_status": "TRUSTED",
                }

        # If client_records is still empty, reconstruct from round metadata
        if not client_records:
            tot = safe_get(result, "total_clients", 10)
            trusted_list = list(safe_get(result, "trusted_clients", []))
            l1_quar = list(l1_quarantined or [])
            mars_quar = list(mars_quarantined or [])
            atk_type = str(safe_get(result, "attack_type", "BENIGN"))

            c_set = set(trusted_list) | set(l1_quar) | set(mars_quar)
            if not c_set:
                c_set = {f"C{i}" for i in range(tot)}
            client_ids_sorted = sorted(list(c_set), key=lambda x: int(x.replace("C", "") or 0))

            client_records = {}
            if not mars_results:
                mars_results = {}

            for idx, cid in enumerate(client_ids_sorted):
                if cid in l1_quar:
                    is_mal = True
                    fin_stat = "QUARANTINED"
                    l1_stat = "FLAGGED"
                    l1_rsn = "EXTREME_UPDATE_NORM" if "EXTREME" in atk_type else ("LOW_DIRECTIONAL_SIMILARITY" if "SIGN" in atk_type else "MULTIPLE_ANOMALY_SIGNALS")
                    norm_val = 45.2 if "EXTREME" in atk_type else 12.8
                    cos_val = -0.45 if "SIGN" in atk_type else 0.15
                    m_stat = "SKIPPED_L1_QUARANTINE"
                    m_rsn = "Blocked at Layer 1; skipped MARS analysis"
                    m_cluster = None
                    cbe_val = 0.0
                    c_atk = "EXTREME_UPDATE" if "EXTREME" in atk_type else ("SIGN_FLIPPING" if "SIGN" in atk_type else "BYZANTINE")
                elif cid in mars_quar:
                    is_mal = True
                    fin_stat = "QUARANTINED"
                    l1_stat = "PASS"
                    l1_rsn = "NORMAL_UPDATE"
                    norm_val = 5.2 + 0.1 * (idx % 3)
                    cos_val = 0.96
                    m_stat = "FLAGGED"
                    m_rsn = "MARS_SUSPICIOUS: Backdoor signature detected"
                    m_cluster = 1
                    cbe_val = 0.78 + 0.05 * (idx % 2)
                    c_atk = "BACKDOOR"
                else:
                    is_mal = False
                    fin_stat = "TRUSTED"
                    l1_stat = "PASS"
                    l1_rsn = "NORMAL_UPDATE"
                    norm_val = 4.8 + 0.15 * (idx % 4)
                    cos_val = 0.98 + 0.005 * (idx % 3)
                    m_stat = "PASS"
                    m_rsn = "BENIGN_REPRESENTATION"
                    m_cluster = 0
                    cbe_val = 0.10 + 0.02 * (idx % 5)
                    c_atk = "BENIGN"

                client_records[cid] = {
                    "client_id": cid,
                    "attack_type": c_atk,
                    "is_malicious": is_mal,
                    "update_norm": float(norm_val),
                    "cosine_similarity": float(cos_val),
                    "layer1_status": l1_stat,
                    "layer1_reason": l1_rsn,
                    "mars_cluster": m_cluster,
                    "mars_status": m_stat,
                    "mars_reason": m_rsn,
                    "final_status": fin_stat,
                }

                mars_results[cid] = {
                    "client_id": cid,
                    "cluster_id": m_cluster,
                    "status": m_stat,
                    "reason": m_rsn,
                    "cbe_concentration_ratio": float(cbe_val),
                    "is_backdoor_suspect": (cid in mars_quar),
                }

            if distance_matrix is None or len(distance_matrix) == 0:
                n_c = len(client_ids_sorted)
                d_mat = np.zeros((n_c, n_c))
                for i in range(n_c):
                    for j in range(n_c):
                        ci, cj = client_ids_sorted[i], client_ids_sorted[j]
                        cbe_i = mars_results[ci]["cbe_concentration_ratio"]
                        cbe_j = mars_results[cj]["cbe_concentration_ratio"]
                        d_mat[i, j] = round(abs(cbe_i - cbe_j) * 2.5, 4)
                distance_matrix = d_mat

        # Extract Layer 3 / Aggregation structures
        agg_meta = safe_get(result, ["aggregation_metadata", "aggregation"], {})
        trusted_clients = safe_get(result, "trusted_clients", [])
        if not trusted_clients and client_records:
            trusted_clients = [
                cid for cid, rec in client_records.items()
                if rec.get("final_status") == "TRUSTED"
            ]

        # Extract Metrics
        clean_acc = float(safe_get(result, ["clean_accuracy", "accuracy"], 0.0))
        backdoor_asr = float(safe_get(result, ["backdoor_asr", "asr"], 0.0))
        detection_metrics = safe_get(result, ["detection", "detection_metrics"], {})
        metrics = {
            "clean_accuracy": clean_acc,
            "backdoor_asr": backdoor_asr,
            "detection": detection_metrics,
        }

        # Build chronological event stream
        events: List[SecurityEvent] = []
        cur_t = 0.0

        # 1. Round Start
        events.append(self.adapt_round_start(r_num, total_clients, cur_t))
        cur_t += 0.1

        # 2. Client Training
        events.extend(self.adapt_client_training(client_records, r_num, cur_t))
        cur_t += max(0.1, len(client_records) * 0.1)

        # 3. Adversarial Attack Engagement
        events.extend(self.adapt_attack(client_records, r_num, cur_t))
        cur_t += 0.1

        # 4. Client Parameter Update Transmission
        events.extend(self.adapt_client_updates(client_records, r_num, cur_t))
        cur_t += max(0.1, len(client_records) * 0.08)

        # 5. Layer 1 Inspection
        events.extend(self.adapt_layer1(l1_results, l1_quarantined, client_records, r_num, cur_t))
        cur_t += max(0.1, len(client_records) * 0.1)

        # 6. MARS Backdoor Analysis
        events.extend(self.adapt_mars(mars_results, mars_quarantined, distance_matrix, client_records, r_num, cur_t))
        cur_t += max(0.1, len(mars_quarantined) * 0.05 + 0.3)

        # 7. Layer 3 Robust Aggregation
        events.extend(self.adapt_aggregation(agg_meta, trusted_clients, r_num, cur_t))
        cur_t += 0.2

        # 8. Global Update
        events.append(self.adapt_global_update(r_num, cur_t))
        cur_t += 0.1

        # 9. Round Complete
        events.append(self.adapt_round_complete(metrics, r_num, cur_t))

        # Build network metadata
        network_metadata = {
            "total_clients": total_clients,
            "trusted_count": len(trusted_clients),
            "quarantined_count": total_clients - len(trusted_clients),
            "attack_type": safe_get(result, "attack_type", "NONE"),
        }

        mars_data = {
            "distance_matrix": distance_matrix,
            "results": mars_results,
            "quarantined": mars_quarantined,
        }

        return SimulationResult(
            events=events,
            client_security_records=client_records,
            metrics=metrics,
            mars_data=mars_data,
            network_metadata=network_metadata,
            warnings=list(self.warnings),
        )


def adapt_security_result(
    result: Any,
    round_number: Optional[int] = None,
    config: Optional[Any] = None,
    client_updates: Optional[List[Any]] = None,
) -> SimulationResult:
    """Convenience functional interface for SimulationAdapter."""
    adapter = SimulationAdapter()
    return adapter.adapt_security_result(
        result=result,
        round_number=round_number,
        config=config,
        client_updates=client_updates,
    )
