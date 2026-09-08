"""
FedSanitize — Phase 7: Sequential Pipeline Demonstration Script
==============================================================
Runs an end-to-end multi-client round through the 3-layer security firewall:
  10 Clients:
    - C0..C5: Honest Clients
    - C6: Extreme Update Attack (Caught by Layer 1)
    - C7: Sign Flipping Attack (Caught by Layer 1)
    - C8: Backdoor Attack (Stealthy, Isolated by Layer 2 MARS)
    - C9: Backdoor Attack (Stealthy, Isolated by Layer 2 MARS)

Prints the complete PART 8 per-client security record table.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from federated import get_mnist_datasets, partition_data, FLClient, FLServer
from attacks import TriggeredTestDataset
from services import SimulationService
from utils.seed import set_seed


def main():
    set_seed(42)
    device = "cpu"
    print("=" * 110)
    print("FedSanitize — Phase 7: End-to-End Sequential Pipeline (3-Layer Firewall)")
    print("=" * 110)

    train_ds, test_ds = get_mnist_datasets("./data")
    partitions = partition_data(train_ds, num_clients=10, iid=True, seed=42)
    triggered_test_ds = TriggeredTestDataset(test_ds, target_class=0, trigger_size=4)

    server = FLServer(device=device)

    # Pre-train 1 baseline round to establish model feature representations
    print("[1/4] Establishing baseline model representations...")
    init_updates = [
        FLClient(i, partitions[i]).train(server.get_global_state_dict(), epochs=1, batch_size=64, lr=0.02)
        for i in range(5)
    ]
    server.aggregate_baseline(init_updates)
    print("      Baseline representations established.")

    # 10 Clients
    print("[2/4] Initializing 10 edge clients (6 Honest, 1 Extreme, 1 Sign-Flip, 2 Backdoor)...")
    clients = [
        FLClient(client_id=0, dataset=partitions[0]),
        FLClient(client_id=1, dataset=partitions[1]),
        FLClient(client_id=2, dataset=partitions[2]),
        FLClient(client_id=3, dataset=partitions[3]),
        FLClient(client_id=4, dataset=partitions[4]),
        FLClient(client_id=5, dataset=partitions[5]),
        FLClient(client_id=6, dataset=partitions[6], is_malicious=True, attack_type="EXTREME_UPDATE"),
        FLClient(client_id=7, dataset=partitions[7], is_malicious=True, attack_type="SIGN_FLIPPING"),
        FLClient(client_id=8, dataset=partitions[8], is_malicious=True, attack_type="BACKDOOR"),
        FLClient(client_id=9, dataset=partitions[9], is_malicious=True, attack_type="BACKDOOR"),
    ]

    print("[3/4] Running Secure Federated Learning Round...")
    sim = SimulationService(server=server)
    res = sim.run_round(
        clients=clients,
        clean_test_dataset=test_ds,
        triggered_test_dataset=triggered_test_ds,
        round_number=1,
    )

    print("[4/4] Round execution complete. Telemetry generated.")
    print("\n" + "=" * 110)
    print("PER-CLIENT SECURITY DATA MODEL TABLE (PART 8)")
    print("=" * 110)
    header = (
        f"| {'Client':<6} | {'Attack Type':<15} | {'Norm':<7} | {'Cos Sim':<8} | "
        f"{'L1 Status':<9} | {'L1 Reason':<25} | {'MARS Clust':<10} | {'Final Status':<12} |"
    )
    print(header)
    print("-" * len(header))

    records = res["client_security_records"]
    for cid, r in records.items():
        clust = str(r["mars_cluster"]) if r["mars_cluster"] is not None else "N/A"
        row = (
            f"| {cid:<6} | {r['attack_type']:<15} | {r['update_norm']:<7.2f} | {r['cosine_similarity']:<8.4f} | "
            f"{r['layer1_status']:<9} | {r['layer1_reason']:<25} | {clust:<10} | {r['final_status']:<12} |"
        )
        print(row)

    print("-" * len(header))
    det = res["detection"]
    print(f"Summary Metrics: Clean Acc={res['clean_accuracy']:.2f}% | Backdoor ASR={res['backdoor_asr']:.2f}%")
    print(f"Detection Quality: TP={det['tp']} | FP={det['fp']} | TN={det['tn']} | FN={det['fn']} | Precision={det['precision']:.2f} | Recall={det['recall']:.2f} | F1={det['f1_score']:.2f}")
    print("=" * 110)


if __name__ == "__main__":
    main()
