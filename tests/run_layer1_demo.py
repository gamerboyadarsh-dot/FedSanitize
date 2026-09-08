"""
FedSanitize — Layer 1 Empirical Demonstration Table
====================================================
Generates actual updates for 10 clients:
- Clients C0..C6: Honest clients
- Client C7: Attack D (Extreme Update, gamma=10.0)
- Client C8: Attack B (Sign Flipping, gamma=1.0)
- Client C9: Attack C (Random Byzantine, scale=5.0)

Runs Layer 1 Anomaly Detection and displays results in a formatted table.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from federated import get_mnist_datasets, partition_data, FLClient, FLServer
from attacks import apply_extreme_update, apply_sign_flipping, apply_random_byzantine
from defense.layer1_anomaly import Layer1AnomalyDetector


def main():
    train_ds, _ = get_mnist_datasets("./data")
    partitions = partition_data(train_ds, num_clients=10, iid=True, seed=42)
    server = FLServer(device="cpu")
    global_state = server.get_global_state_dict()

    updates = []
    # Honest clients
    for i in range(7):
        c = FLClient(i, partitions[i])
        updates.append(c.train(global_state, epochs=1, batch_size=64, lr=0.02))

    # Malicious clients
    c7 = FLClient(7, partitions[7])
    u7 = c7.train(global_state, epochs=1, batch_size=64, lr=0.02)
    updates.append(apply_extreme_update(u7, global_state, gamma=10.0))

    c8 = FLClient(8, partitions[8])
    u8 = c8.train(global_state, epochs=1, batch_size=64, lr=0.02)
    updates.append(apply_sign_flipping(u8, global_state, gamma=1.0))

    c9 = FLClient(9, partitions[9])
    u9 = c9.train(global_state, epochs=1, batch_size=64, lr=0.02)
    updates.append(apply_random_byzantine(u9, global_state, scale=5.0))

    detector = Layer1AnomalyDetector()
    res = detector.detect_anomalies(updates)

    print("\n" + "=" * 90)
    print(f"| {'Client ID':<10} | {'Update Norm':<12} | {'Norm Score':<10} | {'Cosine Sim':<11} | {'Status':<8} | {'Reason':<24} |")
    print("=" * 90)
    for cid, r in res["results"].items():
        print(f"| {cid:<10} | {r.update_norm:<12.4f} | {r.norm_score:<10.4f} | {r.cosine_similarity:<11.4f} | {r.status:<8} | {r.reason:<24} |")
    print("=" * 90)
    print(f"Trusted clients surviving Layer 1: {[u.client_id for u in res['trusted_updates']]}")
    print(f"Quarantined clients by Layer 1:   {res['quarantined_clients']}")
    print("=" * 90)


if __name__ == "__main__":
    main()
