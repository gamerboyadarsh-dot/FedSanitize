"""
FedSanitize Streamlit Main Application
"""

import os
import sys
import streamlit as st

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
from dashboard.theme import apply_theme, COLORS
from services import SimulationService, ResultService
from federated import get_mnist_datasets, partition_data, FLClient, FLServer
from attacks import TriggeredTestDataset
from config import DEFAULT_CONFIG

st.set_page_config(
    page_title="FedSanitize - FL Threat Defense Platform",
    page_icon="assets/logo_icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme(st)


def initialize_session():
    if "history" not in st.session_state:
        res_svc = ResultService()
        demo_history = res_svc.load_run_history("./results/FedSanitize_MultiRound_Demo_history.json")
        st.session_state["history"] = demo_history if demo_history else []

    if "server" not in st.session_state or st.session_state["server"] is None:
        server = FLServer(device=DEFAULT_CONFIG.system.device)
        st.session_state["server"] = server
        st.session_state["simulation_service"] = SimulationService(server=server, config=DEFAULT_CONFIG)
        try:
            train_ds, test_ds = get_mnist_datasets("./data")
            partitions = partition_data(train_ds, num_clients=10, iid=True, seed=42)
            st.session_state["train_ds"] = train_ds
            st.session_state["test_ds"] = test_ds
            st.session_state["partitions"] = partitions
            st.session_state["triggered_test_ds"] = TriggeredTestDataset(test_ds, target_class=0, trigger_size=4)
        except Exception:
            st.session_state["train_ds"] = None
            st.session_state["test_ds"] = None
            st.session_state["partitions"] = {}
            st.session_state["triggered_test_ds"] = None


def execute_simulated_round():
    if st.session_state.get("run_round_trigger", False):
        st.session_state["run_round_trigger"] = False
        partitions = st.session_state.get("partitions")
        test_ds = st.session_state.get("test_ds")
        triggered_ds = st.session_state.get("triggered_test_ds")
        sim_svc = st.session_state.get("simulation_service")
        if not partitions or test_ds is None:
            st.error("MNIST data partitions not initialized.")
            return
        round_idx = len(st.session_state["history"]) + 1
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

    with st.sidebar:
        logo_path = os.path.join(PROJECT_ROOT, "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=140)
        st.markdown(
            "<p style='color:#38FBDB;font-family:monospace;font-weight:700;font-size:1.1rem;margin:4px 0 0 0;letter-spacing:0.1em;'>FedSanitize</p>"
            "<p style='color:#7B8AA3;font-family:monospace;font-size:0.7rem;margin:0;letter-spacing:0.08em;'>v1.0.0 | FL Defense Platform</p>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='border-color:rgba(56,251,219,0.15);margin:12px 0;'/>", unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            [
                "🏠 Overview",
                "👥 Client Profiling",
                "🛡️ 3-Layer Defense",
                "🎯 Attack Playground",
                "📈 Comparative Analytics",
                "⚙️ System Configuration",
            ],
            index=0,
        )

        st.markdown("<hr style='border-color:rgba(56,251,219,0.15);margin:12px 0;'/>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#38FBDB;font-family:monospace;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 8px 0;'>System Telemetry</p>"
            "<div style='color:#7B8AA3;font-family:monospace;font-size:0.75rem;line-height:1.8;'>"
            "<span style='color:#38FBDB;'>MODEL</span>   SmallCNN (2 Conv, 2 FC)<br/>"
            "<span style='color:#38FBDB;'>DATA</span>    MNIST 60k / 10k Test<br/>"
            "<span style='color:#38FBDB;'>DEFENSE</span> L1 + MARS + L3<br/>"
            "<span style='color:#8E52F5;'>REF</span>     Wan et al., NeurIPS 2025"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='border-color:rgba(56,251,219,0.15);margin:12px 0;'/>", unsafe_allow_html=True)
        st.markdown("<p style='color:#7B8AA3;font-family:monospace;font-size:0.65rem;'>Pair programming build complete.</p>", unsafe_allow_html=True)

    if page == "🏠 Overview":
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