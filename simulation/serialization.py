"""
FedSantize Simulation Engine — Experiment Serialization
========================================================
Saves and loads simulation and experiment artifacts for instant,
zero-computation demo replays. Grounded in Phase 13 specifications.
"""

from __future__ import annotations
import os
import json
import time
from typing import Dict, List, Any, Optional

from .event_recorder import sanitize_value


class ExperimentSerializer:
    """
    Serializes and deserializes completed FedSanitize simulation rounds.
    """

    @staticmethod
    def save_experiment(
        experiment_record: Dict[str, Any],
        output_dir: str = "experiments",
        name_prefix: str = "exp",
    ) -> str:
        """
        Saves an experiment record into a structured timestamped directory.
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        target_dir = os.path.join(output_dir, f"{name_prefix}_{timestamp}")
        os.makedirs(target_dir, exist_ok=True)

        # 1. metadata.json
        meta = {
            "timestamp": timestamp,
            "round": experiment_record.get("round", 1),
            "attack_type": experiment_record.get("attack_type", "UNKNOWN"),
            "total_clients": experiment_record.get("total_clients", 0),
        }
        with open(os.path.join(target_dir, "metadata.json"), "w") as f:
            json.dump(sanitize_value(meta), f, indent=2)

        # 2. events.json
        events = experiment_record.get("events", [])
        if hasattr(events, "to_dict_list"):
            events_data = events.to_dict_list()
        elif isinstance(events, list) and events and hasattr(events[0], "to_dict"):
            events_data = [e.to_dict() for e in events]
        else:
            events_data = sanitize_value(events)
        with open(os.path.join(target_dir, "events.json"), "w") as f:
            json.dump(events_data, f, indent=2)

        # 3. metrics.json
        metrics = {
            "clean_accuracy": experiment_record.get("clean_accuracy", 0.0),
            "backdoor_asr": experiment_record.get("backdoor_asr", 0.0),
            "detection": experiment_record.get("detection", {}),
        }
        with open(os.path.join(target_dir, "metrics.json"), "w") as f:
            json.dump(sanitize_value(metrics), f, indent=2)

        # 4. client_security.json
        records = experiment_record.get("client_security_records", {})
        with open(os.path.join(target_dir, "client_security.json"), "w") as f:
            json.dump(sanitize_value(records), f, indent=2)

        # 5. mars_results.json
        mars = {
            "distance_matrix": experiment_record.get("distance_matrix", []),
            "mars_quarantined": experiment_record.get("mars_quarantined", []),
            "mars_results": experiment_record.get("mars_results", {}),
        }
        with open(os.path.join(target_dir, "mars_results.json"), "w") as f:
            json.dump(sanitize_value(mars), f, indent=2)

        # 6. summary.json
        summary = {
            "trusted_clients": experiment_record.get("trusted_clients", []),
            "quarantined_clients": experiment_record.get("quarantined_clients", []),
            "layer1_quarantined": experiment_record.get("layer1_quarantined", []),
            "mars_quarantined": experiment_record.get("mars_quarantined", []),
            "aggregation": experiment_record.get("aggregation", {}),
            "log": experiment_record.get("log", ""),
        }
        with open(os.path.join(target_dir, "summary.json"), "w") as f:
            json.dump(sanitize_value(summary), f, indent=2)

        return target_dir

    @staticmethod
    def load_experiment(experiment_dir: str) -> Dict[str, Any]:
        """
        Loads all artifact files from an experiment directory.
        """
        if not os.path.exists(experiment_dir):
            raise FileNotFoundError(f"Experiment directory '{experiment_dir}' does not exist.")

        data: Dict[str, Any] = {}

        def read_json_if_exists(filename: str) -> Any:
            p = os.path.join(experiment_dir, filename)
            if os.path.exists(p):
                with open(p, "r") as f:
                    return json.load(f)
            return {}

        meta = read_json_if_exists("metadata.json")
        metrics = read_json_if_exists("metrics.json")
        client_sec = read_json_if_exists("client_security.json")
        mars = read_json_if_exists("mars_results.json")
        summary = read_json_if_exists("summary.json")
        events = read_json_if_exists("events.json")

        data["metadata"] = meta
        data["round"] = meta.get("round", 1)
        data["attack_type"] = meta.get("attack_type", "UNKNOWN")
        data["total_clients"] = meta.get("total_clients", len(client_sec))
        data["clean_accuracy"] = metrics.get("clean_accuracy", 0.0)
        data["backdoor_asr"] = metrics.get("backdoor_asr", 0.0)
        data["detection"] = metrics.get("detection", {})
        data["client_security_records"] = client_sec
        data["distance_matrix"] = mars.get("distance_matrix", [])
        data["mars_quarantined"] = mars.get("mars_quarantined", [])
        data["mars_results"] = mars.get("mars_results", {})
        data["trusted_clients"] = summary.get("trusted_clients", [])
        data["quarantined_clients"] = summary.get("quarantined_clients", [])
        data["layer1_quarantined"] = summary.get("layer1_quarantined", [])
        data["aggregation"] = summary.get("aggregation", {})
        data["log"] = summary.get("log", "")
        data["events"] = events

        return data

    @staticmethod
    def list_saved_experiments(base_dir: str = "experiments") -> List[Dict[str, str]]:
        """Lists available saved experiments with labels and paths."""
        if not os.path.exists(base_dir):
            return []
        items = []
        for name in sorted(os.listdir(base_dir), reverse=True):
            full_path = os.path.join(base_dir, name)
            if os.path.isdir(full_path):
                meta_path = os.path.join(full_path, "metadata.json")
                label = name
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r") as f:
                            m = json.load(f)
                            label = f"Round {m.get('round', 1)} — {m.get('attack_type', 'Experiment')} ({m.get('timestamp', name)})"
                    except Exception:
                        pass
                items.append({"label": label, "path": full_path, "name": name})
        return items
