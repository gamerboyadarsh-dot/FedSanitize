"""
FedSanitize — MARS Empirical Checkpoint on Real MNIST Trained Updates
=====================================================================
Demonstrates MARS (Wan et al., NeurIPS 2025) on real model updates trained on MNIST:
1. Benign-only scenario: 8 clean clients -> verifies NO false suspicious cluster.
2. Backdoor scenario: 6 clean clients + 2 backdoor clients -> verifies MARS
   accurately clusters and isolates the 2 backdoored clients.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from federated import get_mnist_datasets, partition_data, FLClient, FLServer
from attacks import BackdoorDataset
from defense.layer2_mars import MARSDetector
from utils.seed import set_seed


def main():
    set_seed(42)
    device = "cpu"
    print("=" * 80)
    print("FedSanitize — MARS Empirical Checkpoint on Real MNIST Trained Updates")
    print("=" * 80)

    train_ds, _ = get_mnist_datasets("./data")
    partitions = partition_data(train_ds, num_clients=10, iid=True, seed=42)
    server = FLServer(device=device)

    # Pre-train 1 baseline round so model parameters establish feature representations
    print("[Setup] Training 1 baseline round to establish model feature representations...")
    init_updates = [
        FLClient(client_id=i, dataset=partitions[i]).train(
            server.get_global_state_dict(), epochs=1, batch_size=64, lr=0.02
        )
        for i in range(5)
    ]
    server.aggregate_baseline(init_updates)
    global_state = server.get_global_state_dict()
    print("       Baseline round complete.")

    detector = MARSDetector()

    # -------------------------------------------------------------
    # Experiment 1: Benign-Only Run (8 Honest Clients)
    # -------------------------------------------------------------
    print("\n[Experiment 1: Benign-Only Run (8 Honest Clients)]")
    benign_updates = []
    for i in range(8):
        c = FLClient(client_id=i, dataset=partitions[i])
        benign_updates.append(c.train(global_state, epochs=1, batch_size=64, lr=0.02))

    res_benign = detector.analyze_updates(benign_updates)
    print(f"  Target representation layer: {res_benign['target_layers']}")
    print(f"  Total clients evaluated:     {len(benign_updates)}")
    print(f"  Backdoor suspects flagged:   {res_benign['backdoor_suspects']}")
    print(f"  Trusted clients surviving:   {[u.client_id for u in res_benign['trusted_after_mars']]}")
    print(f"  Decision Reason:             {res_benign['cluster_information']['decision_reason']}")
    assert len(res_benign["backdoor_suspects"]) == 0, "Benign run should have 0 suspects!"
    print("  -> Benign-Only MARS Check: PASSED (Zero False Alarms)")

    # -------------------------------------------------------------
    # Experiment 2: Backdoor-Injected Run (6 Honest + 2 Backdoor Clients)
    # -------------------------------------------------------------
    print("\n[Experiment 2: Backdoor-Injected Run (6 Honest + 2 Backdoor Clients)]")
    mixed_updates = benign_updates[:6]  # C0..C5 honest

    # Create 2 backdoor clients (C6, C7)
    for i in [6, 7]:
        bd_ds = BackdoorDataset(
            base_dataset=partitions[i],
            poison_ratio=0.40,
            target_class=0,
            trigger_size=4,
            seed=42 + i,
        )
        c_bd = FLClient(client_id=f"C{i}_Backdoor", dataset=bd_ds, is_malicious=True, attack_type="BACKDOOR")
        mixed_updates.append(c_bd.train(global_state, epochs=1, batch_size=64, lr=0.02))

    res_mixed = detector.analyze_updates(mixed_updates)
    print(f"  Total clients evaluated:     {len(mixed_updates)}")
    print(f"  Backdoor suspects flagged:   {res_mixed['backdoor_suspects']}")
    print(f"  Trusted clients surviving:   {[u.client_id for u in res_mixed['trusted_after_mars']]}")
    print(f"  Decision Reason:             {res_mixed['cluster_information']['decision_reason']}")
    print(f"  Separation Score:            {res_mixed['cluster_information']['separation_score']:.6f}")

    print("\n  Per-Client MARS Diagnostic Table:")
    print("  " + "-" * 75)
    print(f"  | {'Client ID':<15} | {'Cluster':<8} | {'Status':<8} | {'CBE Ratio':<10} | {'Suspect?':<8} |")
    print("  " + "-" * 75)
    for cid, m_data in res_mixed["mars_results"].items():
        print(f"  | {cid:<15} | {m_data['cluster_id']:<8} | {m_data['status']:<8} | {m_data['cbe_concentration_ratio']:<10.4f} | {str(m_data['is_backdoor_suspect']):<8} |")
    print("  " + "-" * 75)

    suspects = set(res_mixed["backdoor_suspects"])
    assert "C6_Backdoor" in suspects and "C7_Backdoor" in suspects, "MARS must isolate both backdoor clients!"
    print("  -> Backdoor-Injected MARS Check: PASSED (100% Backdoor Isolation)")

    print("\n" + "=" * 80)
    print("MARS LAYER 2 EMPIRICAL VALIDATION COMPLETE & PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
