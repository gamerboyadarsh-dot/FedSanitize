"""
FedSanitize — Streamlit Main Application
========================================
Interactive enterprise dashboard for real-time monitoring and defense
of federated learning systems against adversarial model poisoning and backdoors.

Grounded in:
  - Layer 1: Statistical Anomaly Filter (L2 Norm, MAD, Cosine Direction)
  - Layer 2: MARS Backdoor Defense (Wan et al., NeurIPS 2025)
  - Layer 3: Robust Coordinate-wise Trimmed Mean Aggregation
"""

import os
import sys
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard import (
    render_overview_page,
    render_clients_page,
    render_defense_page,
    render_attacks_page,
    render_analytics_page,
    render_config_page,
)
from services import SimulationService, ResultService
from federated import get_mnist_datasets, partition_data, FLClient, FLServer
from attacks import TriggeredTestDataset
from config import DEFAULT_CONFIG
from utils.seed import set_seed

# -------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="FedSanitize — FL Threat Defense Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session():
    """Initializes global simulation and experiment state."""
    if "history" not in st.session_state:
        # Automatically load pre-generated demo history if available so all pages render with rich real data
        res_svc = ResultService()
        demo_history = res_svc.load_run_history("./results/FedSanitize_MultiRound_Demo_history.json")
        st.session_state["history"] = demo_history if demo_history else []

    if "server" not in st.session_state or st.session_state["server"] is None:
        server = FLServer(device=DEFAULT_CONFIG.system.device)
        st.session_state["server"] = server
        st.session_state["simulation_service"] = SimulationService(server=server, config=DEFAULT_CONFIG)

        # Pre-partition MNIST dataset once
        try:
            train_ds, test_ds = get_mnist_datasets("./data")
            partitions = partition_data(train_ds, num_clients=10, iid=True, seed=42)
            st.session_state["train_ds"] = train_ds
            st.session_state["test_ds"] = test_ds
            st.session_state["partitions"] = partitions
            st.session_state["triggered_test_ds"] = TriggeredTestDataset(test_ds, target_class=0, trigger_size=4)
        except Exception as e:
            st.session_state["train_ds"] = None
            st.session_state["test_ds"] = None
            st.session_state["partitions"] = {}
            st.session_state["triggered_test_ds"] = None


def execute_simulated_round():
    """Executes a single federated learning round on demand."""
    if st.session_state.get("run_round_trigger", False):
        st.session_state["run_round_trigger"] = False
        partitions = st.session_state.get("partitions")
        test_ds = st.session_state.get("test_ds")
        triggered_ds = st.session_state.get("triggered_test_ds")
        sim_svc: SimulationService = st.session_state.get("simulation_service")

        if not partitions or test_ds is None:
            st.error("MNIST data partitions not initialized.")
            return

        round_idx = len(st.session_state["history"]) + 1

        # Configure 10 clients: 6 honest, 1 extreme, 1 sign flip, 2 backdoor
        clients = [
            FLClient(0, partitions[0]),
            FLClient(1, partitions[1]),
            FLClient(2, partitions[2]),
            FLClient(3, partitions[3]),
            FLClient(4, partitions[4]),
            FLClient(5, partitions[5]),
            FLClient(6, partitions[6], is_malicious=True, attack_type="EXTREME_UPDATE"),
            FLClient(7, partitions[7], is_malicious=True, attack_type="SIGN_FLIPPING"),
            FLClient(8, partitions[8], is_malicious=True, attack_type="BACKDOOR"),
            FLClient(9, partitions[9], is_malicious=True, attack_type="BACKDOOR"),
        ]

        round_record = sim_svc.run_round(
            clients=clients,
            clean_test_dataset=test_ds,
            triggered_test_dataset=triggered_ds,
            round_number=round_idx,
        )
        st.session_state["history"].append(round_record)


def main():
    initialize_session()
    execute_simulated_round()

    # -------------------------------------------------------------
    # Sidebar Navigation & Branding
    # -------------------------------------------------------------
    with st.sidebar:
        st.title("🛡️ FedSanitize")
        st.caption("v1.0.0 | FL Defense Platform")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            [
                "⚔️ Live Attack Arena",
                "🏠 Overview",
                "👥 Client Profiling",
                "🛡️ 3-Layer Defense",
                "🎯 Attack Playground",
                "📈 Comparative Analytics",
                "⚙️ System Configuration",
            ],
            index=0,
        )

        st.markdown("---")
        st.markdown("### System Telemetry")
        st.write(f"**Model:** SmallCNN (2 Conv, 2 FC)")
        st.write(f"**Dataset:** MNIST (60k Train / 10k Test)")
        st.write(f"**Active Defense:** L1 + MARS + L3")
        st.write(f"**MARS:** Wan et al., NeurIPS 2025")
        st.markdown("---")
        st.caption("Pair programming build complete.")

    # -------------------------------------------------------------
    # Page Router
    # -------------------------------------------------------------
    if page == "⚔️ Live Attack Arena":
        from dashboard import render_simulation_arena_page
        render_simulation_arena_page(st.session_state)
    elif page == "🏠 Overview":
        render_overview_page(st.session_state)
    elif page == "👥 Client Profiling":
        render_clients_page(st.session_state)
    elif page == "🛡️ 3-Layer Defense":
        render_defense_page(st.session_state)
    elif page == "🎯 Attack Playground":
        render_attacks_page(st.session_state)
    elif page == "📈 Comparative Analytics":
        render_analytics_page(st.session_state)
    elif page == "⚙️ System Configuration":
        render_config_page(st.session_state)


if __name__ == "__main__":
    main()
