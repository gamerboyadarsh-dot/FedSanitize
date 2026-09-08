"""
FedSanitize — Test FastAPI Endpoints
====================================
Verifies that the FastAPI wrapper correctly exposes endpoints and returns
valid schemas matching the round_record data contract.
"""

import pytest
from fastapi.testclient import TestClient
from backend_api.main import app, state

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "active_clients" in data
    assert data["active_clients"] == 10

def test_get_config(client):
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "federated" in data
    assert "defense" in data
    assert "attack" in data
    assert data["federated"]["num_clients"] == 10

def test_load_demo(client):
    response = client.post("/simulation/load-demo")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["rounds"] >= 5
    assert len(data["history"]) >= 5
    
    # Check first round adheres to contract
    r1 = data["history"][0]
    assert "round" in r1
    assert "clean_accuracy" in r1
    assert "backdoor_asr" in r1
    assert "detection" in r1
    assert "client_security_records" in r1
    assert "C0" in r1["client_security_records"]

def test_get_clients(client):
    response = client.get("/clients")
    assert response.status_code == 200
    clients = response.json()
    assert len(clients) == 10
    assert clients[0]["client_id"] == "C0"
    assert clients[6]["attack_type"] == "EXTREME_UPDATE"
    assert clients[6]["is_malicious"] is True

def test_set_client_attack(client):
    # Change C1 to RANDOM_BYZANTINE
    response = client.post("/clients/C1/attack", json={"attack_type": "RANDOM_BYZANTINE"})
    assert response.status_code == 200
    data = response.json()
    assert data["attack_type"] == "RANDOM_BYZANTINE"
    assert data["is_malicious"] is True

    # Revert C1 to NONE
    response = client.post("/clients/C1/attack", json={"attack_type": "NONE"})
    assert response.status_code == 200
    assert response.json()["is_malicious"] is False
