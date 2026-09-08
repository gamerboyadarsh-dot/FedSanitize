"""
FedSanitize — Result Serialization & Reporting Service
======================================================
Serializes round logs, client security tables, and experiment history
into structured JSON artifacts for disk storage and Streamlit display.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import os
import json
import numpy as np

try:
    from ..utils.serialization import save_json, load_json
except (ImportError, ValueError):
    from utils.serialization import save_json, load_json


class ResultService:
    """
    Handles export and querying of experiment telemetry.
    """
    def __init__(self, output_dir: str = "./results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_round_summary(self, round_data: Dict[str, Any], round_num: int) -> str:
        """Saves a single round record to output/round_{N}.json."""
        filepath = os.path.join(self.output_dir, f"round_{round_num}.json")
        save_json(round_data, filepath)
        return filepath

    def save_full_run(self, history: List[Dict[str, Any]], filename: str = "run_log.json") -> str:
        """Saves cumulative experiment history to results/run_log.json."""
        filepath = os.path.join(self.output_dir, filename)
        save_json(history, filepath)
        return filepath

    def load_run_history(self, filepath: Optional[str] = None) -> List[Dict[str, Any]]:
        """Loads experiment history from disk."""
        target = filepath or os.path.join(self.output_dir, "run_log.json")
        if os.path.exists(target):
            return load_json(target)
        return []
