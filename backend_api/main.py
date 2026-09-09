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
import math
from pathlib import Path
from dataclasses import asdict, replace
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, status, Query
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

# Team A Security Intelligence & Auth Integration
from backend_api.auth import auth_router
from backend_api.auth.bootstrap import bootstrap_auth
from security_intelligence import (
    PipelineAdapter,
    ClientTrustEngine,
    AdaptiveDefenseOrchestrator,
    SecurityContext,
)

# Arena simulation imports (safe — no training triggered)
try:
    from simulation.simulation_adapter import adapt_security_result, SimulationResult
    from simulation.timeline_builder import TimelineBuilder
    from simulation.network_state import NetworkState, compute_deterministic_layout
    from simulation.replay_engine import ReplayEngine
    from simulation.scenario_engine import ScenarioEngine
    ARENA_AVAILABLE = True
except Exception:
    ARENA_AVAILABLE = False


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

# Initialize Auth Subsystem
try:
    bootstrap_auth()
except Exception as _e:
    print(f"[AUTH] Bootstrap notice: {_e}")
app.include_router(auth_router)



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

        self.trust_engine = ClientTrustEngine()
        self.orchestrator = AdaptiveDefenseOrchestrator()
        self.security_decisions: List[Dict[str, Any]] = []

        # If demo history loaded, seed trust engine and orchestrator
        if self.experiment_history:
            self.eval_security_intelligence_for_history()

    def eval_security_intelligence_for_history(self):
        """Processes historical rounds through Security Intelligence components."""
        for rec in self.experiment_history:
            try:
                contexts, _ = PipelineAdapter.from_round_record(rec)
                for ctx in contexts:
                    self.trust_engine.update(ctx)
                decision = self.orchestrator.evaluate_round(contexts, trust_engine=self.trust_engine)
                self.security_decisions.append(decision.to_dict())
            except Exception as e:
                print(f"[SEC_INTEL] History replay warning: {e}")

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

    # Process Security Intelligence for this round
    try:
        contexts, _ = PipelineAdapter.from_round_record(record)
        trust_updates = []
        for ctx in contexts:
            upd = state.trust_engine.update(ctx)
            trust_updates.append(upd.to_dict())
        decision = state.orchestrator.evaluate_round(contexts, trust_engine=state.trust_engine)
        decision_dict = decision.to_dict()
        decision_dict["trust_updates"] = trust_updates
        state.security_decisions.append(decision_dict)
        record["security_intelligence"] = decision_dict
    except Exception as e:
        print(f"[SEC_INTEL] Processing warning on round {round_num}: {e}")

    return record


@app.post("/simulation/reset")
def reset_simulation():
    """Resets server state, client updates, and experiment history."""
    state.experiment_history = []
    state.server = FLServer(device=state.config.system.device)
    state.sim_service = SimulationService(server=state.server, config=state.config)
    state.rebuild_clients()
    state.trust_engine.reset()
    state.orchestrator = AdaptiveDefenseOrchestrator()
    state.security_decisions = []
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
    state.trust_engine.reset()
    state.orchestrator = AdaptiveDefenseOrchestrator()
    state.security_decisions = []
    state.eval_security_intelligence_for_history()

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


# ---------------------------------------------------------------------------
# Team A: Security Intelligence Endpoints
# ---------------------------------------------------------------------------

@app.get("/security/summary")
def get_security_summary():
    """Returns combined trust and adaptive defense status."""
    trust_summary = state.trust_engine.get_summary()
    latest_decision = state.orchestrator.get_last_decision()
    threat_trend = state.orchestrator.get_threat_trend()
    active_defenses = state.orchestrator.get_active_defenses()

    return {
        "trust_summary": trust_summary,
        "latest_decision": latest_decision.to_dict() if latest_decision else None,
        "threat_trend": threat_trend,
        "is_escalated": state.orchestrator.is_escalated(),
        "mode": state.orchestrator.get_mode(),
        "active_defenses": active_defenses,
    }


@app.get("/security/clients/trust")
def get_all_client_trust():
    """Returns current trust records for all tracked edge clients."""
    records = state.trust_engine.get_all_clients()
    return [r.to_dict() for r in records]


@app.get("/security/clients/{client_id}/trust")
def get_client_trust(client_id: str):
    """Returns trust dossier for a specific client."""
    rec = state.trust_engine.get_client(client_id)
    if not rec:
        # Check alternative casing
        rec = state.trust_engine.get_client(client_id.upper())
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No trust record for client '{client_id}'"
        )
    return rec.to_dict()


@app.get("/security/decisions")
def get_security_decisions():
    """Returns historical security decisions generated by the Adaptive Defense Orchestrator."""
    return state.security_decisions


# ---------------------------------------------------------------------------
# Simulation Arena Endpoints (React Live Attack Arena)
# ---------------------------------------------------------------------------

@app.get("/simulation/arena")
def get_arena_data(round_index: int = Query(default=3, ge=0)):
    """
    Returns all structured arena data for the React Live Attack Arena page.
    Uses pre-computed demo history (no ML training triggered).
    round_index: 0-based index into experiment_history (defaults to round 3 = Backdoor scenario).
    """
    if not ARENA_AVAILABLE:
        raise HTTPException(status_code=503, detail="Arena simulation module not available")

    history = state.experiment_history
    if not history:
        # Fallback synthetic demo record
        history = [
            {"round": 1, "attack_type": "NORMAL", "clean_accuracy": 95.2, "backdoor_asr": 0.8,
             "trusted_clients": [f"C{i}" for i in range(10)], "layer1_quarantined": [], "mars_quarantined": []},
            {"round": 2, "attack_type": "EXTREME_UPDATE (×45 Scaling)", "clean_accuracy": 93.1, "backdoor_asr": 0.9,
             "trusted_clients": [f"C{i}" for i in range(9)], "layer1_quarantined": ["C6"], "mars_quarantined": []},
            {"round": 3, "attack_type": "SIGN_FLIPPING", "clean_accuracy": 94.5, "backdoor_asr": 1.1,
             "trusted_clients": [f"C{i}" for i in range(9)], "layer1_quarantined": ["C7"], "mars_quarantined": []},
            {"round": 4, "attack_type": "BACKDOOR (Trigger Injection)", "clean_accuracy": 96.85, "backdoor_asr": 1.25,
             "trusted_clients": [f"C{i}" for i in range(8)], "layer1_quarantined": [], "mars_quarantined": ["C8", "C9"]},
            {"round": 5, "attack_type": "MULTI-VECTOR (L1 + MARS)", "clean_accuracy": 95.7, "backdoor_asr": 1.05,
             "trusted_clients": [f"C{i}" for i in range(7)], "layer1_quarantined": ["C6"], "mars_quarantined": ["C8", "C9"]},
        ]

    idx = min(round_index, len(history) - 1)
    rec = history[idx]

    # Build SimulationResult using the adapter
    sim_res: SimulationResult = adapt_security_result(rec)

    # Build timeline
    builder = TimelineBuilder()
    timeline = builder.build_timeline(sim_res.events)

    # Build network nodes (deterministic radial layout)
    try:
        positions = compute_deterministic_layout(10)
    except Exception:
        # fallback manual radial layout
        positions = {}
        for i in range(10):
            angle = 2 * math.pi * i / 10
            positions[f"C{i}"] = (0.5 + 0.38 * math.cos(angle), 0.5 + 0.38 * math.sin(angle))

    client_records = sim_res.client_security_records
    network_nodes = {}
    for cid, pos in positions.items():
        rec_c = client_records.get(cid, {})
        l1_status = rec_c.get("layer1_status", "PASS")
        mars_status = rec_c.get("mars_status", "PASS")
        final_status = rec_c.get("final_status", "TRUSTED")
        if final_status == "QUARANTINED":
            visual_state = "QUARANTINED"
        elif l1_status == "FLAGGED":
            visual_state = "FLAGGED"
        elif mars_status == "FLAGGED":
            visual_state = "FLAGGED"
        else:
            visual_state = "TRUSTED"
        network_nodes[cid] = {
            "client_id": cid,
            "x": float(pos[0]),
            "y": float(pos[1]),
            "visual_state": visual_state,
            "is_malicious": rec_c.get("is_malicious", False),
        }

    # Serialize timeline steps
    timeline_steps = []
    for i, step in enumerate(timeline):
        evt = step.event
        timeline_steps.append({
            "step_index": i,
            "scene": str(step.scene),
            "description": step.description,
            "event": {
                "event_type": evt.event_type,
                "severity": evt.severity,
                "message": evt.message,
                "client_id": evt.client_id,
                "layer": evt.layer,
                "timestamp": evt.timestamp,
                "payload": dict(evt.payload) if evt.payload else {},
            },
        })

    # Build scenario narrative
    attack_type = rec.get("attack_type", "NORMAL")
    narrative = ScenarioEngine.get_narrative(attack_type)

    quarantined = rec.get(
        "quarantined_clients",
        rec.get("layer1_quarantined", []) + rec.get("mars_quarantined", [])
    )
    trusted = rec.get(
        "trusted_clients",
        [c for c in client_records if c not in quarantined]
    )

    # Compute threat level
    mal_count = len(quarantined)
    asr = rec.get("backdoor_asr", 0.0)
    asr_pct = asr if asr > 1.0 else asr * 100.0
    if asr_pct > 10 or mal_count >= 3:
        threat_tier = "CRITICAL"
        threat_score = 92
    elif asr_pct > 5 or mal_count >= 2:
        threat_tier = "HIGH"
        threat_score = 74
    elif asr_pct > 2 or mal_count >= 1:
        threat_tier = "MEDIUM"
        threat_score = 51
    else:
        threat_tier = "LOW"
        threat_score = 22

    return {
        "round_index": idx,
        "total_rounds": len(history),
        "round_record": rec,
        "network_nodes": network_nodes,
        "timeline_steps": timeline_steps,
        "client_security_records": client_records,
        "mars_data": sim_res.mars_data,
        "scenario_narrative": {
            "attack_type": narrative.attack_type,
            "title": narrative.title,
            "headline": narrative.headline,
            "story_steps": narrative.story_steps,
            "mitigating_layer": narrative.mitigating_layer,
            "forensic_focus": narrative.forensic_focus,
            "technical_explanation": narrative.technical_explanation,
            "threat_severity": narrative.threat_severity,
        },
        "summary": {
            "round_id": rec.get("round", idx + 1),
            "attack_type": attack_type,
            "clean_accuracy": rec.get("clean_accuracy", 95.0),
            "backdoor_asr": rec.get("backdoor_asr", 1.5),
            "threat_tier": threat_tier,
            "threat_score": threat_score,
            "quarantined_count": len(quarantined),
            "trusted_count": len(trusted),
            "quarantined_clients": quarantined,
            "trusted_clients": trusted,
            "l1_quarantined": rec.get("layer1_quarantined", []),
            "mars_quarantined": rec.get("mars_quarantined", []),
        },
        "scenario_labels": {
            str(i + 1): f"Scenario {h.get('round', i+1)}: {h.get('attack_type', 'Experiment')}"
            for i, h in enumerate(history)
        },
    }

