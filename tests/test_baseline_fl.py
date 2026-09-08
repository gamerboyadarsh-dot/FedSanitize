"""
FedSanitize — Baseline Federated Learning Verification Script
============================================================
Runs 3 rounds of standard FedAvg with 10 clients on MNIST.
Verifies convergence and records per-round clean test accuracy.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
from federated import (
    get_mnist_datasets,
    partition_data,
    FLClient,
    FLServer,
)
from utils.seed import set_seed


def run_baseline_verification():
    set_seed(42)
    device = "cpu"
    print("=" * 60)
    print("FedSanitize — Baseline FL 3-Round Checkpoint Verification")
    print("=" * 60)

    # 1. Load Data
    print("[1/4] Loading MNIST dataset...")
    train_ds, test_ds = get_mnist_datasets("./data")
    print(f"      Train samples: {len(train_ds)}, Test samples: {len(test_ds)}")

    # 2. Partition Data (10 IID clients)
    num_clients = 10
    print(f"[2/4] Partitioning data among {num_clients} IID clients...")
    client_partitions = partition_data(train_ds, num_clients=num_clients, iid=True, seed=42)

    clients = [
        FLClient(client_id=i, dataset=client_partitions[i])
        for i in range(num_clients)
    ]
    print(f"      Initialized {len(clients)} clients, ~{len(client_partitions[0])} samples/client.")

    # 3. Initialize Server
    server = FLServer(device=device)
    init_loss, init_acc = server.evaluate(test_ds)
    print(f"[3/4] Initial untrained global model -> Loss: {init_loss:.4f}, Accuracy: {init_acc:.2f}%")

    # 4. Run 3 Federated Rounds
    print("[4/4] Executing 3 baseline Federated Learning rounds...")
    num_rounds = 3
    epochs_per_client = 1  # 1 epoch is plenty fast and achieves high accuracy
    batch_size = 64
    lr = 0.02

    for r in range(1, num_rounds + 1):
        global_state = server.get_global_state_dict()
        client_updates = []
        losses = []

        for client in clients:
            update = client.train(
                global_state_dict=global_state,
                epochs=epochs_per_client,
                batch_size=batch_size,
                lr=lr,
                device=device,
            )
            client_updates.append(update)
            losses.append(update.metadata.get("train_loss", 0.0))

        # Aggregate baseline
        server.aggregate_baseline(client_updates)

        # Evaluate global model
        test_loss, test_acc = server.evaluate(test_ds)
        avg_client_loss = sum(losses) / len(losses)
        avg_update_norm = sum(u.update_norm for u in client_updates) / len(client_updates)

        print(
            f"  [Round {r}/{num_rounds}] "
            f"Avg Client Train Loss: {avg_client_loss:.4f} | "
            f"Avg Delta L2 Norm: {avg_update_norm:.4f} | "
            f"Global Test Loss: {test_loss:.4f} | "
            f"Global Clean Accuracy: {test_acc:.2f}%"
        )

    print("=" * 60)
    print(f"Final Clean Accuracy after {num_rounds} rounds: {test_acc:.2f}%")
    assert test_acc >= 50.0, f"Accuracy {test_acc:.2f}% is below plausible threshold 50.0%"
    print("Baseline FL verification: PASSED (Clean Accuracy is plausible for MNIST)")
    print("=" * 60)


if __name__ == "__main__":
    run_baseline_verification()
