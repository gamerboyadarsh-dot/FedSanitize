"""
FedSanitize — Phase 10: Generate Demo Data
==========================================
Runs a 5-round simulation and saves the output to a JSON file to be used by
the Streamlit dashboard's fallback mode.
"""

import os
import sys
import json
import torch
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from federated import get_mnist_datasets, partition_data, FLClient, FLServer
from attacks import TriggeredTestDataset
from services import SimulationService
from utils.seed import set_seed
from config import DEFAULT_CONFIG

def generate_demo():
    print("Generating demo experiment data...")
    set_seed(42)
    device = "cpu"
    
    train_ds, test_ds = get_mnist_datasets("./data")
    partitions = partition_data(train_ds, num_clients=10, iid=True, seed=42)
    triggered_test_ds = TriggeredTestDataset(test_ds, target_class=0, trigger_size=4)
    
    server = FLServer(device=device)
    
    # Establish baseline
    print("Pre-training 1 baseline round to establish model feature representations...")
    init_updates = [
        FLClient(i, partitions[i]).train(server.get_global_state_dict(), epochs=1, batch_size=64, lr=0.02)
        for i in range(5)
    ]
    server.aggregate_baseline(init_updates)
    
    # Initialize 10 clients
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
    
    sim = SimulationService(server=server, config=DEFAULT_CONFIG)
    
    # Run 5 rounds
    for r in range(1, 6):
        print(f"Running round {r}/5...")
        sim.run_round(
            clients=clients,
            clean_test_dataset=test_ds,
            triggered_test_dataset=triggered_test_ds,
            round_number=r
        )
    
    # Save to JSON
    os.makedirs("./experiments", exist_ok=True)
    out_file = "./experiments/demo_experiment.json"
    with open(out_file, "w") as f:
        json.dump(sim.experiment_history, f, indent=2)
    print(f"Demo data generated successfully at {out_file}")

if __name__ == "__main__":
    generate_demo()
