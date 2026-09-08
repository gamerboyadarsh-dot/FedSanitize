"""
FedSanitize Dashboard — Client Security Profiling Page
======================================================
Displays granular per-client diagnostics, PART 8 security records,
and multidimensional parameter space distributions.
"""

import streamlit as st
import pandas as pd
from evaluation.plots import plot_client_security_scatter


def render_clients_page(session_state):
    st.title("👥 Edge Client Security Profiling")
    st.markdown("Inspect individual client parameter updates, anomaly scores, and firewall quarantine decisions.")

    history = session_state.get("history", [])
    if not history:
        st.info("No round data available. Run a simulation round or load a demo run from the Overview page.")
        return

    # Select round
    round_options = [r.get("round", i + 1) for i, r in enumerate(history)]
    selected_round = st.selectbox("Select Evaluation Round", round_options, index=len(round_options) - 1)
    round_data = next((r for r in history if r.get("round") == selected_round), history[-1])

    records = round_data.get("client_security_records", {})
    if not records:
        st.warning(f"No per-client security records found for Round {selected_round}.")
        return

    # -------------------------------------------------------------
    # Scatter Plot: Parameter Space
    # -------------------------------------------------------------
    st.subheader("🌐 Update Norm vs. Cosine Alignment Space")
    fig_scatter = plot_client_security_scatter(records)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # -------------------------------------------------------------
    # Filter & PART 8 Security Records Table
    # -------------------------------------------------------------
    st.subheader("📋 Per-Client Security Table (PART 8 Data Model)")

    filter_option = st.radio(
        "Filter by Defense Decision:",
        ["All Clients", "Trusted Only", "Quarantined Only"],
        horizontal=True,
    )

    rows = []
    for cid, r in records.items():
        status = r.get("final_status", "TRUSTED")
        if filter_option == "Trusted Only" and status != "TRUSTED":
            continue
        if filter_option == "Quarantined Only" and status != "QUARANTINED":
            continue

        clust = str(r.get("mars_cluster")) if r.get("mars_cluster") is not None else "N/A"
        rows.append({
            "Client ID": cid,
            "Attack Vector": r.get("attack_type", "NONE"),
            "Is Malicious": "🚨 Yes" if r.get("is_malicious") else "✅ No",
            "Update Norm": round(r.get("update_norm", 0.0), 2),
            "Cosine Sim": round(r.get("cosine_similarity", 0.0), 4),
            "Layer 1 Status": "🛡️ FLAGGED" if r.get("layer1_status") == "FLAGGED" else "✅ PASS",
            "Layer 1 Reason": r.get("layer1_reason", "NORMAL_UPDATE"),
            "MARS Cluster": clust,
            "MARS Status": r.get("mars_status", "PASS"),
            "Final Decision": "🚨 QUARANTINED" if status == "QUARANTINED" else "🛡️ TRUSTED",
        })

    df_clients = pd.DataFrame(rows)
    st.dataframe(df_clients, use_container_width=True)

    # -------------------------------------------------------------
    # Granular Client Inspector
    # -------------------------------------------------------------
    st.subheader("🔍 Deep Inspector: Client Diagnostic Card")
    client_ids = list(records.keys())
    inspected_cid = st.selectbox("Choose Client to Inspect", client_ids)
    c_rec = records[inspected_cid]

    c1, c2, c3 = st.columns(3)
    c1.metric("Update Norm", f"{c_rec.get('update_norm', 0.0):.3f}")
    c2.metric("Cosine Sim to Median", f"{c_rec.get('cosine_similarity', 0.0):.4f}")
    c3.metric("Final Security Status", c_rec.get("final_status", "TRUSTED"))

    st.markdown(f"**Layer 1 Explanation:** `{c_rec.get('layer1_reason', 'N/A')}`")
    st.markdown(f"**MARS Explanation:** `{c_rec.get('mars_reason', 'N/A')}`")
