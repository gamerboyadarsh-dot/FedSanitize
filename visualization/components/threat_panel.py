"""
FedSantize Components — Threat Level Scoring System
===================================================
Computes explainable cyber threat severity based on actual backend results:
  - Number of malicious/quarantined clients
  - Measured Attack Success Rate (ASR)
  - Attack profile severity

Grounded in Phase 8 and page 38 of the specification.
"""

from __future__ import annotations
from typing import Dict, Any


def compute_threat_level(
    malicious_count: int,
    quarantined_count: int,
    backdoor_asr: float,
    attack_type: str,
) -> tuple[str, str, int]:
    """
    Computes deterministic threat tier: LOW | MEDIUM | HIGH | CRITICAL
    Returns (tier, description, score 0-100).
    """
    score = 0
    reasons = []

    # Attack type baseline
    u_type = str(attack_type).upper()
    if "BACKDOOR" in u_type:
        score += 35
        reasons.append("Backdoor attack active")
    elif "EXTREME" in u_type or "BYZANTINE" in u_type:
        score += 25
        reasons.append("Model poisoning attack active")
    elif "SIGN" in u_type or "LABEL" in u_type:
        score += 20
        reasons.append("Directional/data poisoning attack active")

    # Client compromise score
    if malicious_count > 0:
        score += min(35, malicious_count * 15)
        reasons.append(f"{malicious_count} compromised node(s)")

    # ASR severity score
    if backdoor_asr >= 0.20:
        score += 30
        reasons.append(f"Elevated ASR ({backdoor_asr*100:.1f}%)")
    elif backdoor_asr >= 0.05:
        score += 15
        reasons.append(f"Trace ASR ({backdoor_asr*100:.1f}%)")

    score = min(100, max(0, score))

    if score >= 65 or "BACKDOOR" in u_type:
        return "CRITICAL", "; ".join(reasons) or "Targeted backdoor vector present", score
    elif score >= 40:
        return "HIGH", "; ".join(reasons) or "Active model poisoning detected", score
    elif score >= 20:
        return "MEDIUM", "; ".join(reasons) or "Minor perturbation detected", score
    else:
        return "LOW", "Normal federated consensus operating smoothly", score
