"""
FedSanitize — Phase 8: Historical Evaluation Demonstration
==========================================================
Demonstrates multi-round telemetry recording across varied attack conditions:
  - Round 1: Baseline Clean FL
  - Round 2: Coarse Poisoning (Extreme Update + Sign Flipping)
  - Round 3: Byzantine Noise Attack
  - Round 4: Stealthy Backdoor Trigger Injection
  - Round 5: Multi-Vector Combined Attack

Produces the full round-by-round historical evaluation table and exports
the history to JSON and CSV.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation import ExperimentLogger, calculate_detection_metrics


def main():
    print("=" * 115)
    print("FedSanitize — Phase 8: Multi-Round Historical Evaluation Engine")
    print("=" * 115)

    logger = ExperimentLogger(experiment_name="FedSanitize_MultiRound_Demo", output_dir="./results")

    # Simulate 5 distinct rounds of telemetry
    rounds_data = [
        {
            "round": 1,
            "attack_type": "NONE (Clean FL)",
            "total_clients": 10,
            "clean_accuracy": 93.39,
            "backdoor_asr": 0.05,
            "layer1_quarantined": [],
            "mars_quarantined": [],
            "trusted_clients": [f"C{i}" for i in range(10)],
            "detection": calculate_detection_metrics({
                f"C{i}": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"}
                for i in range(10)
            }),
            "aggregation": {"trim_count_applied": 1, "method_used": "coordinate_trimmed_mean"},
        },
        {
            "round": 2,
            "attack_type": "EXTREME_UPDATE + SIGN_FLIPPING",
            "total_clients": 10,
            "clean_accuracy": 95.82,
            "backdoor_asr": 0.12,
            "layer1_quarantined": ["C6", "C7"],
            "mars_quarantined": [],
            "trusted_clients": [f"C{i}" for i in range(6)] + ["C8", "C9"],
            "detection": calculate_detection_metrics({
                **{f"C{i}": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"} for i in range(6)},
                "C6": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "FLAGGED", "mars_status": "SKIPPED"},
                "C7": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "FLAGGED", "mars_status": "SKIPPED"},
                "C8": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"},
                "C9": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"},
            }),
            "aggregation": {"trim_count_applied": 1, "method_used": "coordinate_trimmed_mean"},
        },
        {
            "round": 3,
            "attack_type": "RANDOM_BYZANTINE",
            "total_clients": 10,
            "clean_accuracy": 96.44,
            "backdoor_asr": 0.08,
            "layer1_quarantined": ["C9"],
            "mars_quarantined": [],
            "trusted_clients": [f"C{i}" for i in range(9)],
            "detection": calculate_detection_metrics({
                **{f"C{i}": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"} for i in range(9)},
                "C9": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "FLAGGED", "mars_status": "SKIPPED"},
            }),
            "aggregation": {"trim_count_applied": 1, "method_used": "coordinate_trimmed_mean"},
        },
        {
            "round": 4,
            "attack_type": "BACKDOOR (Trigger Injection)",
            "total_clients": 10,
            "clean_accuracy": 96.85,
            "backdoor_asr": 0.38,
            "layer1_quarantined": [],
            "mars_quarantined": ["C8", "C9"],
            "trusted_clients": [f"C{i}" for i in range(8)],
            "detection": calculate_detection_metrics({
                **{f"C{i}": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"} for i in range(8)},
                "C8": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "PASS", "mars_status": "FLAGGED"},
                "C9": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "PASS", "mars_status": "FLAGGED"},
            }),
            "aggregation": {"trim_count_applied": 1, "method_used": "coordinate_trimmed_mean"},
        },
        {
            "round": 5,
            "attack_type": "MULTI-VECTOR (Extreme + Backdoor)",
            "total_clients": 10,
            "clean_accuracy": 97.41,
            "backdoor_asr": 0.25,
            "layer1_quarantined": ["C6"],
            "mars_quarantined": ["C8", "C9"],
            "trusted_clients": [f"C{i}" for i in range(6)] + ["C7"],
            "detection": calculate_detection_metrics({
                **{f"C{i}": {"is_malicious": False, "final_status": "TRUSTED", "layer1_status": "PASS", "mars_status": "PASS"} for i in range(7)},
                "C6": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "FLAGGED", "mars_status": "SKIPPED"},
                "C8": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "PASS", "mars_status": "FLAGGED"},
                "C9": {"is_malicious": True, "final_status": "QUARANTINED", "layer1_status": "PASS", "mars_status": "FLAGGED"},
            }),
            "aggregation": {"trim_count_applied": 1, "method_used": "coordinate_trimmed_mean"},
        },
    ]

    for r in rounds_data:
        logger.log_round(r)

    # Convert to DataFrame
    df = logger.to_dataframe()
    print("\nROUND-BY-ROUND HISTORICAL EVALUATION TABLE:")
    print(df.to_string(index=False))

    # Export to disk
    json_path = logger.export_json()
    csv_path = logger.export_csv()
    print(f"\nArtifacts successfully exported:")
    print(f"  - JSON History: {json_path}")
    print(f"  - CSV Summary:  {csv_path}")
    print("=" * 115)


if __name__ == "__main__":
    main()
