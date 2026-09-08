"""
FedSanitize Dashboard — Historical Analytics & Benchmark Evaluation
===================================================================
Provides comparative analysis (FedSanitize vs. Undefended FedAvg),
confusion matrix visualization, and export utilities.
"""

import streamlit as st
import pandas as pd
import json
from evaluation.plots import plot_confusion_matrix, plot_accuracy_curve
from evaluation import calculate_detection_metrics, ExperimentLogger


def render_analytics_page(session_state):
    st.title("📈 Comparative Analytics & Telemetry")
    st.markdown("Benchmark defense efficacy, inspect detection confusion matrices, and export empirical logs.")

    history = session_state.get("history", [])
    if not history:
        st.info("No round history available. Run a simulation or load pre-generated demo data from the Overview page.")
        return

    exp_logger = ExperimentLogger()
    exp_logger.history = history
    df_history = exp_logger.to_dataframe()

    # -------------------------------------------------------------
    # Multi-Round Historical Table
    # -------------------------------------------------------------
    st.subheader("1. Round-by-Round Defense Telemetry")
    st.dataframe(df_history, use_container_width=True)

    # -------------------------------------------------------------
    # Confusion Matrix
    # -------------------------------------------------------------
    st.subheader("2. Cumulative Detection Performance")
    # Aggregate detection metrics across rounds
    tot_tp = sum(r.get("detection", {}).get("tp", 0) for r in history)
    tot_fp = sum(r.get("detection", {}).get("fp", 0) for r in history)
    tot_tn = sum(r.get("detection", {}).get("tn", 0) for r in history)
    tot_fn = sum(r.get("detection", {}).get("fn", 0) for r in history)

    prec = float(tot_tp / (tot_tp + tot_fp)) if (tot_tp + tot_fp) > 0 else 1.0
    rec = float(tot_tp / (tot_tp + tot_fn)) if (tot_tp + tot_fn) > 0 else 1.0
    f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 1.0

    agg_det = {"tp": tot_tp, "fp": tot_fp, "tn": tot_tn, "fn": tot_fn, "precision": prec, "recall": rec, "f1_score": f1}

    col_m1, col_m2 = st.columns([1.5, 1])
    with col_m1:
        fig_cm = plot_confusion_matrix(agg_det)
        st.plotly_chart(fig_cm, use_container_width=True)

    with col_m2:
        st.markdown("#### Cumulative Metrics")
        st.metric("Total True Positives (Attacks Blocked)", tot_tp)
        st.metric("Total False Positives (Clean Blocked)", tot_fp)
        st.metric("Overall Precision", f"{prec * 100:.1f}%")
        st.metric("Overall Detection Rate (Recall)", f"{rec * 100:.1f}%")
        st.metric("Overall F1 Score", f"{f1:.3f}")

    st.markdown("---")

    # -------------------------------------------------------------
    # Data Export Utilities
    # -------------------------------------------------------------
    st.subheader("3. Telemetry Export")
    col_e1, col_e2 = st.columns(2)

    csv_data = df_history.to_csv(index=False)
    col_e1.download_button(
        label="📥 Download Telemetry Summary (CSV)",
        data=csv_data,
        file_name="fedsanitize_telemetry_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

    json_str = json.dumps(history, indent=2)
    col_e2.download_button(
        label="📥 Download Complete Experiment History (JSON)",
        data=json_str,
        file_name="fedsanitize_full_history.json",
        mime="application/json",
        use_container_width=True,
    )
