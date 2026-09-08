"""
FedSanitize — Evaluation: Experiment History Logger
===================================================
Maintains, updates, and exports simulation telemetry across all rounds.
Provides tabular history conversion (Pandas DataFrame) and JSON export.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import json
import pandas as pd

try:
    from ..utils.serialization import save_json, load_json
except (ImportError, ValueError):
    from utils.serialization import save_json, load_json


class ExperimentLogger:
    """
    Records round-by-round metrics and exports structured experiment history.
    """
    def __init__(self, experiment_name: str = "FedSanitize_Run", output_dir: str = "./results"):
        self.experiment_name = experiment_name
        self.output_dir = output_dir
        self.history: List[Dict[str, Any]] = []
        os.makedirs(output_dir, exist_ok=True)

    def log_round(self, round_data: Dict[str, Any]) -> None:
        """Appends a round record to the experiment history."""
        self.history.append(round_data)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Converts round history into a flattened Pandas DataFrame
        ideal for tabular rendering in Streamlit.
        """
        rows = []
        for r in self.history:
            det = r.get("detection", {})
            agg = r.get("aggregation", {})
            rows.append({
                "Round": r.get("round", len(rows) + 1),
                "Attack Type": r.get("attack_type", "NONE"),
                "Total Clients": r.get("total_clients", 10),
                "Clean Accuracy (%)": round(r.get("clean_accuracy", 0.0), 2),
                "Backdoor ASR (%)": round(r.get("backdoor_asr", 0.0), 2),
                "Precision": round(det.get("precision", 1.0), 2),
                "Recall / Det Rate": round(det.get("recall", 1.0), 2),
                "F1 Score": round(det.get("f1_score", 1.0), 2),
                "L1 Blocked": len(r.get("layer1_quarantined", [])),
                "MARS Blocked": len(r.get("mars_quarantined", [])),
                "Trusted Count": len(r.get("trusted_clients", [])),
                "Trim Count": agg.get("trim_count_applied", 0),
            })
        return pd.DataFrame(rows)

    def export_json(self, filename: Optional[str] = None) -> str:
        """Exports full history to a JSON file."""
        fname = filename or f"{self.experiment_name}_history.json"
        path = os.path.join(self.output_dir, fname)
        save_json(self.history, path)
        return path

    def export_csv(self, filename: Optional[str] = None) -> str:
        """Exports summary table to a CSV file."""
        fname = filename or f"{self.experiment_name}_summary.csv"
        path = os.path.join(self.output_dir, fname)
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        return path
