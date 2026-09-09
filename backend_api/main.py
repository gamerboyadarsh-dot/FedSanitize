"""
FedSanitize — FastAPI Service Wrapper
=====================================
Lightweight API gateway exposing existing SimulationService, SecurityPipeline,
and experiment telemetry to the modern React frontend.
"""

from __future__ import annotations
import os
import sys
import json
from pathlib import Path
from dataclasses import asdict, replace
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import DEFAULT_CONFIG, FedSanitizeConfig
from federated import get_mnist_datasets, partition_data, FLClient, FLServer
from attacks import TriggeredTestDataset
from services import SimulationService, ResultService
from backend_api.schemas import (
    ConfigUpdateRequest,
    AttackAssignmentRequest,
    ClientSummary,
)

app = FastAPI(
    title="FedSanitize Threat-Defense API",
    version="1.0.0",
    description="REST backend for the FedSanitize Federated Learning Security Console"
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StateManager:
    """Singleton simulation and dataset state container."""
    def __init__(self):
        self.config: FedSanitizeConfig = DEFAULT_CONFIG
        self.server: Optional[FLServer] = None
        self.sim_service: Optional[SimulationService] = None
        self.clients: List[FLClient] = []
        self.clean_test_ds = None
        self.triggered_test_ds = None
        self.partitions: Dict[int, Any] = {}
        self.experiment_history: List[Dict[str, Any]] = []
        self.client_attack_mapping: Dict[str, str] = {
            "C0": "NONE", "C1": "NONE", "C2": "NONE", "C3": "NONE", "C4": "NONE", "C5": "NONE",
            "C6": "EXTREME_UPDATE", "C7": "SIGN_FLIPPING", "C8": "BACKDOOR", "C9": "BACKDOOR"
        }
        self.initialize()

    def initialize(self):
        """Initializes datasets, model parameters, and client instances."""
        self.server = FLServer(device=self.config.system.device)
        self.sim_service = SimulationService(server=self.server, config=self.config)

        # Load datasets
        data_dir = os.path.join(PROJECT_ROOT, "data")
        train_ds, test_ds = get_mnist_datasets(data_dir)
        self.clean_test_ds = test_ds
        self.triggered_test_ds = TriggeredTestDataset(
            test_ds,
            target_class=self.config.attack.backdoor_target_class,
            trigger_size=self.config.attack.backdoor_trigger_size
        )
        self.partitions = partition_data(
            train_ds,
            num_clients=self.config.federated.num_clients,
            iid=self.config.federated.iid,
            alpha=0.5,
            seed=self.config.system.random_seed
        )

        self.rebuild_clients()

        # Load pre-generated demo telemetry if available so UI has instant rich visuals
        demo_path = os.path.join(PROJECT_ROOT, "experiments", "demo_experiment.json")
        if os.path.exists(demo_path) and not self.experiment_history:
            try:
                with open(demo_path, "r") as f:
                    self.experiment_history = json.load(f)
            except Exception:
                self.experiment_history = []

    def rebuild_clients(self):
        """Builds FLClient instances with their configured attack designations."""
        self.clients = []
        for i in range(self.config.federated.num_clients):
            cid_str = f"C{i}"
            atk = self.client_attack_mapping.get(cid_str, "NONE")
            is_malicious = (atk != "NONE")
            client = FLClient(
                client_id=i,
                dataset=self.partitions[i],
                is_malicious=is_malicious,
                attack_type=atk
            )
            self.clients.append(client)


state = StateManager()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "FedSanitize Threat-Defense API",
        "version": "1.0.0",
        "active_clients": len(state.clients),
        "completed_rounds": len(state.experiment_history),
    }


@app.get("/config")
def get_config():
    """Returns current active system configuration."""
    cfg_dict = asdict(state.config)
    l1 = cfg_dict.get("layer1", {})
    mars = cfg_dict.get("mars", {})
    agg = cfg_dict.get("aggregation", {})

    cfg_dict["defense"] = {
        "layer1_mad_multiplier": l1.get("mad_threshold_multiplier", 3.5),
        "layer1_norm_threshold": 0.6,
        "layer1_min_cosine": l1.get("cosine_similarity_threshold", 0.0),
        "mars_cbe_top_p": mars.get("top_k_percent", 0.10),
        "mars_malignity_threshold": 0.015,
        "trimmed_mean_beta": agg.get("trim_ratio", 0.10),
        **l1,
        **mars,
        **agg,
    }
    return cfg_dict


@app.post("/config")
def update_config(update_req: ConfigUpdateRequest):
    """Updates configuration dataclasses safely."""
    new_fed = state.config.federated
    new_l1 = state.config.layer1
    new_mars = state.config.mars
    new_agg = state.config.aggregation
    new_atk = state.config.attack

    if update_req.federated:
        fed_updates = {k: v for k, v in update_req.federated.model_dump().items() if v is not None}
        new_fed = replace(new_fed, **fed_updates)

    if update_req.defense:
        def_dict = {k: v for k, v in update_req.defense.model_dump().items() if v is not None}
        if "layer1_mad_multiplier" in def_dict:
            new_l1 = replace(new_l1, mad_threshold_multiplier=def_dict["layer1_mad_multiplier"])
        if "mars_cbe_top_p" in def_dict:
            new_mars = replace(new_mars, top_k_percent=def_dict["mars_cbe_top_p"])
        if "trimmed_mean_beta" in def_dict:
            new_agg = replace(new_agg, trim_ratio=def_dict["trimmed_mean_beta"])

    if update_req.attack:
        atk_updates = {k: v for k, v in update_req.attack.model_dump().items() if v is not None}
        new_atk = replace(new_atk, **atk_updates)

    state.config = replace(
        state.config,
        federated=new_fed,
        layer1=new_l1,
        mars=new_mars,
        aggregation=new_agg,
        attack=new_atk
    )
    state.sim_service.config = state.config
    state.sim_service.pipeline.config = state.config

    return get_config()


@app.get("/clients", response_model=List[ClientSummary])
def list_clients():
    """Lists all configured clients with their latest security evaluation status."""
    latest_round = state.experiment_history[-1] if state.experiment_history else None
    latest_records = latest_round.get("client_security_records", {}) if latest_round else {}

    results = []
    for client in state.clients:
        cid_str = client.client_id if str(client.client_id).startswith("C") else f"C{client.client_id}"
        rec = latest_records.get(cid_str)
        summary = ClientSummary(
            client_id=cid_str,
            is_malicious=client.is_malicious,
            attack_type=client.attack_type,
            sample_count=len(client.dataset),
            latest_record=rec
        )
        results.append(summary)
    return results


@app.post("/clients/{client_id}/attack")
def set_client_attack(client_id: str, req: AttackAssignmentRequest):
    """Assigns or modifies the attack mode of a specific edge client."""
    cid_clean = client_id.upper()
    if not cid_clean.startswith("C"):
        cid_clean = f"C{cid_clean}"

    valid_attacks = {"NONE", "EXTREME_UPDATE", "SIGN_FLIPPING", "RANDOM_BYZANTINE", "BACKDOOR", "LABEL_FLIPPING"}
    atk_type = req.attack_type.upper()
    if atk_type not in valid_attacks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid attack type '{atk_type}'. Allowed: {list(valid_attacks)}"
        )

    state.client_attack_mapping[cid_clean] = atk_type
    state.rebuild_clients()

    return {
        "status": "success",
        "client_id": cid_clean,
        "attack_type": atk_type,
        "is_malicious": (atk_type != "NONE"),
    }


@app.post("/simulation/round")
def run_simulation_round():
    """Runs a single live secure federated learning round."""
    round_num = len(state.experiment_history) + 1
    record = state.sim_service.run_round(
        clients=state.clients,
        clean_test_dataset=state.clean_test_ds,
        triggered_test_dataset=state.triggered_test_ds,
        round_number=round_num,
        custom_attack_mapping=state.client_attack_mapping,
    )
    state.experiment_history.append(record)
    return record


@app.post("/simulation/reset")
def reset_simulation():
    """Resets server state, client updates, and experiment history."""
    state.experiment_history = []
    state.server = FLServer(device=state.config.system.device)
    state.sim_service = SimulationService(server=state.server, config=state.config)
    state.rebuild_clients()
    return {"status": "success", "message": "Simulation reset successfully", "round": 0}


@app.post("/simulation/load-demo")
def load_demo_experiment():
    """Loads the pre-generated 5-round demo telemetry from disk."""
    demo_path = os.path.join(PROJECT_ROOT, "experiments", "demo_experiment.json")
    if not os.path.exists(demo_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo experiment dataset not found at experiments/demo_experiment.json"
        )

    with open(demo_path, "r") as f:
        demo_data = json.load(f)

    state.experiment_history = demo_data
    return {
        "status": "success",
        "message": f"Loaded {len(demo_data)} demo rounds successfully",
        "rounds": len(demo_data),
        "history": demo_data,
    }


@app.get("/experiments/history")
def get_experiment_history():
    """Returns cumulative round-by-round experiment history."""
    return state.experiment_history
