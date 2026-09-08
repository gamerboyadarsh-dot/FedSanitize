"""
FedSanitize — Structured Logging Utility
=========================================
Implements human-readable, per-round logging strictly matching PART 16 format,
as well as standard Python logging for debugging and pipeline telemetry.
"""

import logging
import sys
from typing import List, Optional, Dict, Any


def get_logger(name: str = "FedSanitize", level: str = "INFO") -> logging.Logger:
    """Returns a configured standard logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


class RoundSummaryLogger:
    """
    Formats and prints/buffers round summary logs according to the
    PART 16 specification required for hackathon demonstration.
    """
    def __init__(self):
        self.log_history: List[str] = []

    def format_round_log(
        self,
        round_num: int,
        total_clients: int,
        attack_type: str,
        layer1_client_status: Dict[str, str],  # client_id -> "PASS" / "FLAGGED"
        layer1_survivors: int,
        mars_clusters: Optional[Dict[int, List[str]]] = None,
        suspicious_cluster_id: Optional[int] = None,
        mars_survivors: Optional[int] = None,
        aggregation_status: str = "Aggregation successful.",
        clean_accuracy: Optional[float] = None,
        backdoor_asr: Optional[float] = None,
    ) -> str:
        lines = [
            f"[ROUND {round_num}]",
            f"Clients participating: {total_clients}",
            f"Attack type: {attack_type}",
            "Layer 1 analysis:",
        ]
        
        for cid, status in layer1_client_status.items():
            lines.append(f"Client {cid} {status}")
            
        lines.append(f"Layer 1 survivors: {layer1_survivors}")
        
        if mars_clusters is not None:
            lines.append("Running MARS...")
            for cluster_id, members in mars_clusters.items():
                lines.append(f"Cluster {cluster_id}: {' '.join(members)}")
            if suspicious_cluster_id is not None:
                lines.append("Suspicious cluster selected according to configured decision rule.")
            if mars_survivors is not None:
                lines.append(f"MARS survivors: {mars_survivors}")
                
        lines.append(f"Applying Robust Aggregation...")
        lines.append(aggregation_status)
        
        if clean_accuracy is not None:
            lines.append(f"Clean Accuracy: {clean_accuracy:.2f}%")
        if backdoor_asr is not None:
            lines.append(f"Backdoor ASR: {backdoor_asr:.2f}%")
            
        log_str = "\n".join(lines)
        self.log_history.append(log_str)
        return log_str


# Global round logger instance
round_logger = RoundSummaryLogger()
