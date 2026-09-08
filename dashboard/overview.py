"""
FedSanitize Dashboard — Overview Page
=====================================
Presents high-level system KPIs, accuracy/ASR progression charts, simulation
controls, and round-by-round event logs.
"""

import streamlit as st
import pandas as pd
from evaluation.plots import plot_accuracy_curve, plot_asr_curve


def render_overview_page(session_state):
    st.title("🛡️ FedSanitize — Security Overview")
    st.markdown(
        "**Real-Time Malignity-Aware Threat Mitigation & Robust Aggregation for Federated Learning**"
    )

    history = session_state.get("history", [])
    current_round = len(history)

    # -------------------------------------------------------------
    # KPI Top Metrics
    # -------------------------------------------------------------
    if history:
        latest = history[-1]
        clean_acc = latest.get("clean_accuracy", 0.0)
        backdoor_asr = latest.get("backdoor_asr", 0.0)
        attack_type = latest.get("attack_type", "NONE")
        det = latest.get("detection", {})
        total_quarantined = len(latest.get("quarantined_clients", []))
        total_clients = latest.get("total_clients", 10)
        trusted_count = len(latest.get("trusted_clients", []))
    else:
        clean_acc = 0.0
        backdoor_asr = 0.0
        attack_type = "IDLE / READY"
        det = {"precision": 1.0, "recall": 1.0, "f1_score": 1.0}
        total_quarantined = 0
        total_clients = 10
        trusted_count = 10

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Current Round", f"Round {current_round}", delta=f"+1" if current_round > 0 else None)
    col2.metric("Clean Accuracy", f"{clean_acc:.2f}%", delta="Normal" if clean_acc > 90 else None)
    col3.metric("Backdoor ASR", f"{backdoor_asr:.2f}%", delta="Suppressed" if backdoor_asr < 5 else "Threat", delta_color="inverse")
    col4.metric("Threat Quarantine", f"{total_quarantined} / {total_clients}", delta=f"{trusted_count} Trusted")
    col5.metric("Detection F1", f"{det.get('f1_score', 1.0):.2f}", delta="100% Prec" if det.get("precision", 1.0) == 1.0 else None)

    st.markdown("---")

    # -------------------------------------------------------------
    # Simulation Control Buttons
    # -------------------------------------------------------------
    col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 3])
    with col_btn1:
        if st.button("▶️ Run Secure Round", use_container_width=True, type="primary"):
            with st.spinner(f"Simulating Round {current_round + 1} with 3-Layer Security Pipeline..."):
                session_state["run_round_trigger"] = True
                st.rerun()

    with col_btn2:
        if st.button("🔄 Reset Simulation", use_container_width=True):
            session_state["history"] = []
            session_state["server"] = None
            st.rerun()

    with col_btn3:
        if st.button("⚡ Load Full 5-Round Pre-Generated Demo Experiment", use_container_width=True):
            from services.result_service import ResultService
            res_svc = ResultService()
            demo_data = res_svc.load_run_history("./results/FedSanitize_MultiRound_Demo_history.json")
            if demo_data:
                session_state["history"] = demo_data
                st.success("Loaded 5-Round Multi-Vector Security Demonstration!")
                st.rerun()
            else:
                st.warning("Run 'python tests/run_evaluation_demo.py' to generate demo history first.")

    st.markdown("---")

    # -------------------------------------------------------------
    # Visual Performance Charts
    # -------------------------------------------------------------
    if history:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_acc = plot_accuracy_curve(history)
            st.plotly_chart(fig_acc, use_container_width=True)

        with col_c2:
            fig_asr = plot_asr_curve(history)
            st.plotly_chart(fig_asr, use_container_width=True)

        # -------------------------------------------------------------
        # Latest Round Event Log Viewer (PART 16 format)
        # -------------------------------------------------------------
        st.subheader("📜 Latest Round Security Log (PART 16 Format)")
        latest_log = history[-1].get("log", "No log available.")
        st.code(latest_log, language="text")

        # -------------------------------------------------------------
        # History Table
        # -------------------------------------------------------------
        st.subheader("📊 Round History Summary")
        from evaluation import ExperimentLogger
        exp_logger = ExperimentLogger()
        exp_logger.history = history
        df_hist = exp_logger.to_dataframe()
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("💡 Click **'Run Secure Round'** or **'Load Full 5-Round Pre-Generated Demo'** above to start visualizing real security metrics.")
