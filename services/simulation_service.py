"""
FedSanitize — Federated Simulation Controller Service
=====================================================
Orchestrates full secure federated learning rounds:
  1. Parameter Distribution
  2. Local Training & Adversarial Attack Injection
  3. 3-Layer Security Pipeline (Layer 1 -> MARS -> Trimmed Mean)
  4. Global Model Parameter Update
  5. Evaluation (Clean Accuracy & Backdoor ASR)
  6. Detection Metrics (TP, FP, TN, FN, Precision, Recall, F1)
  7. Telemetry & Experiment History Logging
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
import torch
from torch.utils.data import Dataset

try:
    from ..federated.client import FLClient, ClientUpdate
    from ..federated.server import FLServer
    from ..attacks import (
        apply_extreme_update,
        apply_sign_flipping,
        apply_random_byzantine,
        apply_label_flipping,
        BackdoorDataset,
        TriggeredTestDataset,
        evaluate_asr,
    )
    from .security_service import SecurityPipeline, SecurityPipelineResult
    from ..config import FedSanitizeConfig, DEFAULT_CONFIG
    from ..utils.logger import round_logger
except (ImportError, ValueError):
    from federated.client import FLClient, ClientUpdate
    from federated.server import FLServer
    from attacks import (
        apply_extreme_update,
        apply_sign_flipping,
        apply_random_byzantine,
        apply_label_flipping,
        BackdoorDataset,
        TriggeredTestDataset,
        evaluate_asr,
    )
    from services.security_service import SecurityPipeline, SecurityPipelineResult
    from config import FedSanitizeConfig, DEFAULT_CONFIG
    from utils.logger import round_logger


def compute_detection_metrics(
    client_security_records: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes confusion matrix and detection metrics (TP, FP, TN, FN, Precision, Recall, F1)
    with strict numerical zero-division guards.
    """
    tp = fp = tn = fn = 0

    for rec in client_security_records.values():
        is_actual_malicious = rec["is_malicious"]
        is_flagged = (rec["final_status"] == "QUARANTINED")

        if is_actual_malicious and is_flagged:
            tp += 1
        elif not is_actual_malicious and is_flagged:
            fp += 1
        elif not is_actual_malicious and not is_flagged:
            tn += 1
        elif is_actual_malicious and not is_flagged:
            fn += 1

    # Precision guard
    if tp + fp == 0:
        precision = 1.0 if (tp + fn == 0) else 0.0
    else:
        precision = float(tp / (tp + fp))

    # Recall guard
    if tp + fn == 0:
        recall = 1.0
    else:
        recall = float(tp / (tp + fn))

    # F1 score guard
    if precision + recall == 0.0:
        f1 = 0.0
    else:
        f1 = float(2.0 * (precision * recall) / (precision + recall))

    detection_rate = recall

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "detection_rate": detection_rate,
    }


class SimulationService:
    """
    Manages stateful execution of federated simulations.
    """
    def __init__(
        self,
        server: Optional[FLServer] = None,
        config: Optional[FedSanitizeConfig] = None,
    ):
        self.config = config if config is not None else DEFAULT_CONFIG
        self.server = server if server is not None else FLServer(device=self.config.system.device)
        self.pipeline = SecurityPipeline(config=self.config)
        self.experiment_history: List[Dict[str, Any]] = []

    def run_round(
        self,
        clients: List[FLClient],
        clean_test_dataset: Dataset,
        triggered_test_dataset: Dataset,
        round_number: Optional[int] = None,
        custom_attack_mapping: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a single secure FL round end-to-end.
        """
        r_num = round_number if round_number is not None else (self.server.current_round + 1)
        global_state = self.server.get_global_state_dict()
        device = self.config.system.device

        # 1. Local Training & Attack Application
        client_updates: List[ClientUpdate] = []
        attack_types_present = set()

        for client in clients:
            attack_type = custom_attack_mapping.get(client.client_id, client.attack_type) if custom_attack_mapping else client.attack_type

            # Label flipping attack modifies training dataset
            if attack_type == "LABEL_FLIPPING":
                attack_types_present.add("LABEL_FLIPPING")
                poisoned_ds = apply_label_flipping(client.dataset, label_map=self.config.attack.label_flip_map)
                raw_update = client.train(
                    global_state_dict=global_state,
                    epochs=self.config.federated.local_epochs,
                    batch_size=self.config.federated.local_batch_size,
                    lr=self.config.federated.local_lr,
                    device=device,
                    custom_dataset=poisoned_ds,
                )
                raw_update.is_malicious = True
                raw_update.attack_type = "LABEL_FLIPPING"
                client_updates.append(raw_update)

            # Backdoor attack uses trigger injection dataset
            elif attack_type == "BACKDOOR":
                attack_types_present.add("BACKDOOR")
                bd_ds = BackdoorDataset(
                    base_dataset=client.dataset,
                    poison_ratio=self.config.attack.backdoor_poison_ratio,
                    target_class=self.config.attack.backdoor_target_class,
                    trigger_size=self.config.attack.backdoor_trigger_size,
                    seed=self.config.system.random_seed + int(client.client_id.replace("C", "") or 0),
                )
                raw_update = client.train(
                    global_state_dict=global_state,
                    epochs=self.config.federated.local_epochs,
                    batch_size=self.config.federated.local_batch_size,
                    lr=self.config.federated.local_lr,
                    device=device,
                    custom_dataset=bd_ds,
                )
                raw_update.is_malicious = True
                raw_update.attack_type = "BACKDOOR"
                client_updates.append(raw_update)

            else:
                # Normal local training
                raw_update = client.train(
                    global_state_dict=global_state,
                    epochs=self.config.federated.local_epochs,
                    batch_size=self.config.federated.local_batch_size,
                    lr=self.config.federated.local_lr,
                    device=device,
                )

                # Post-training delta manipulations
                if attack_type == "EXTREME_UPDATE":
                    attack_types_present.add("EXTREME_UPDATE")
                    attacked_update = apply_extreme_update(
                        raw_update,
                        global_state,
                        gamma=self.config.attack.extreme_update_gamma,
                    )
                    client_updates.append(attacked_update)
                elif attack_type == "SIGN_FLIPPING":
                    attack_types_present.add("SIGN_FLIPPING")
                    attacked_update = apply_sign_flipping(
                        raw_update,
                        global_state,
                        gamma=self.config.attack.sign_flip_gamma,
                    )
                    client_updates.append(attacked_update)
                elif attack_type == "RANDOM_BYZANTINE":
                    attack_types_present.add("RANDOM_BYZANTINE")
                    attacked_update = apply_random_byzantine(
                        raw_update,
                        global_state,
                        scale=self.config.attack.random_byzantine_scale,
                    )
                    client_updates.append(attacked_update)
                else:
                    client_updates.append(raw_update)

        # 2. Sequential Security Pipeline (Layer 1 -> MARS -> Trimmed Mean)
        pipeline_result = self.pipeline.process_round(
            global_state_dict=global_state,
            client_updates=client_updates,
            round_number=r_num,
        )

        # 3. Update Server Global Model
        self.server.update_global_model(pipeline_result.updated_global_state)
        self.server.current_round = r_num

        # 4. Evaluation
        _, clean_acc = self.server.evaluate(clean_test_dataset)
        backdoor_asr = evaluate_asr(self.server.model, triggered_test_dataset, device=device)

        # 5. Detection Metrics
        detection_metrics = compute_detection_metrics(pipeline_result.client_security_records)

        # 6. Structured Logging (PART 16 format)
        l1_status_dict = {
            cid: ("PASS" if res.status == "PASS" else "FLAGGED")
            for cid, res in pipeline_result.layer1_results.items()
        }
        mars_clusters_dict = None
        if "cluster_stats" in pipeline_result.security_summary:
            mars_clusters_dict = {
                k: v["members"]
                for k, v in pipeline_result.mars_results.items()
            }

        attack_label = ", ".join(attack_types_present) if attack_types_present else "NONE"
        round_log = round_logger.format_round_log(
            round_num=r_num,
            total_clients=len(client_updates),
            attack_type=attack_label,
            layer1_client_status=l1_status_dict,
            layer1_survivors=len(pipeline_result.layer1_results) - len(pipeline_result.layer1_quarantined),
            mars_survivors=len(pipeline_result.trusted_clients),
            clean_accuracy=clean_acc,
            backdoor_asr=backdoor_asr,
        )

        # 7. Record Telemetry
        round_record = {
            "round": r_num,
            "attack_type": attack_label,
            "total_clients": len(client_updates),
            "clean_accuracy": clean_acc,
            "backdoor_asr": backdoor_asr,
            "trusted_clients": pipeline_result.trusted_clients,
            "quarantined_clients": list(pipeline_result.client_security_records.keys() - set(pipeline_result.trusted_clients)),
            "layer1_quarantined": pipeline_result.layer1_quarantined,
            "mars_quarantined": pipeline_result.mars_quarantined,
            "detection": detection_metrics,
            "client_security_records": pipeline_result.client_security_records,
            "aggregation": pipeline_result.aggregation_metadata,
            "distance_matrix": pipeline_result.distance_matrix.tolist() if pipeline_result.distance_matrix is not None else [],
            "log": round_log,
        }
        self.experiment_history.append(round_record)

        return round_record
