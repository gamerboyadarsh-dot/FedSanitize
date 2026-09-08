"""
FedSanitize — Phase 10: Final Integration Tests
===============================================
Ensures that the entire pipeline runs without errors and produces valid metrics.
"""

import pytest
import torch
from federated.client import FLClient
from federated.data_partition import get_mnist_datasets, partition_data
from config import DEFAULT_CONFIG
from services.simulation_service import SimulationService
from attacks import TriggeredTestDataset

@pytest.fixture(scope="module")
def setup_data():
    from dataclasses import replace
    config = DEFAULT_CONFIG
    
    # Replace the fields since the dataclass is frozen
    config = replace(config,
        federated=replace(config.federated, num_clients=3, local_epochs=1),
        attack=replace(config.attack, num_malicious_clients=1)
    )
    
    train_ds, test_ds = get_mnist_datasets("./data")
    partitions = partition_data(train_ds, num_clients=config.federated.num_clients, iid=True, seed=42)
    
    clients = []
    for i in range(config.federated.num_clients):
        clients.append(FLClient(client_id=i, dataset=partitions[i]))

    # Set one attacker
    clients[0].attack_type = "LABEL_FLIPPING"
    clients[0].is_malicious = True
    
    triggered_ds = TriggeredTestDataset(test_ds)
    
    return clients, test_ds, triggered_ds, config

def test_full_pipeline_end_to_end(setup_data):
    clients, test_ds, triggered_ds, config = setup_data
    
    service = SimulationService(config=config)
    
    # Run 2 rounds
    for r in range(1, 3):
        res = service.run_round(
            clients=clients,
            clean_test_dataset=test_ds,
            triggered_test_dataset=triggered_ds,
            round_number=r
        )
        assert res["round"] == r
        assert "clean_accuracy" in res
        assert "backdoor_asr" in res
        assert "detection" in res
        assert "client_security_records" in res
        assert "C0" in res["client_security_records"]
        
        # C0 is malicious, C1 and C2 are clean
        assert res["client_security_records"]["C0"]["is_malicious"] is True
        assert res["client_security_records"]["C1"]["is_malicious"] is False

    assert len(service.experiment_history) == 2
