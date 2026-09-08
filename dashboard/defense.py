"""
FedSanitize Dashboard — Defense Architecture & Layer Deep Dive
==============================================================
Examines each tier of the 3-layer security firewall:
  - Layer 1: Statistical Anomaly Filter
  - Layer 2: MARS Backdoor Defense (NeurIPS 2025) & Wasserstein Matrix
  - Layer 3: Coordinate-wise Trimmed Mean Aggregation
"""

import streamlit as st
import numpy as np
from evaluation.plots import plot_mars_distance_heatmap


def render_defense_page(session_state):
    st.title("🛡️ 3-Layer Defense Architecture Deep Dive")
    st.markdown("Inspect how the sequential security firewall isolates multi-vector attacks in progressive stages.")

    history = session_state.get("history", [])
    if history:
        latest = history[-1]
        dist_mat = np.array(latest.get("distance_matrix", []))
        agg_meta = latest.get("aggregation", {})
        trusted_clients = latest.get("trusted_clients", [])
        l1_quarantined = latest.get("layer1_quarantined", [])
        mars_quarantined = latest.get("mars_quarantined", [])
    else:
        dist_mat = np.zeros((0, 0))
        agg_meta = {"trim_count_applied": 1, "method_used": "coordinate_trimmed_mean"}
        trusted_clients = [f"C{i}" for i in range(10)]
        l1_quarantined = []
        mars_quarantined = []

    # Tabs for the 3 Defense Layers
    tab1, tab2, tab3 = st.tabs([
        "1️⃣ Layer 1: Anomaly Filter",
        "2️⃣ Layer 2: MARS Backdoor Defense",
        "3️⃣ Layer 3: Trimmed Mean",
    ])

    # -------------------------------------------------------------
    # Layer 1: Statistical Anomaly Filter
    # -------------------------------------------------------------
    with tab1:
        st.subheader("Layer 1: Update Anomaly Filter")
        st.markdown(
            """
            **Mechanism:** Computes coordinate-wise median reference update $\\Delta W_{\\text{ref}}$ and Median Absolute Deviation (MAD).
            Flags coarse anomalies:
            - **Extreme Update Norms:** Poisoned updates amplified by large scaling factors $\\gamma$ (e.g., $10\\times$).
            - **Directional Outliers / Inversions:** Updates with low or negative cosine similarity to the consensus direction.
            - **Graceful Fallback:** If $>50\\%$ of updates are flagged, falls back to highest-similarity clients to guarantee aggregation survival.
            """
        )

        col_l1_1, col_l1_2, col_l1_3 = st.columns(3)
        col_l1_1.metric("Layer 1 Filtered Clients", f"{len(l1_quarantined)}")
        col_l1_2.metric("Survivor Count", f"{10 - len(l1_quarantined)} / 10")
        col_l1_3.metric("Primary Detection", "Norms & Sign Inversions")

        if l1_quarantined:
            st.warning(f"🚨 Layer 1 quarantined clients: {l1_quarantined}")
        else:
            st.success("✅ All evaluated updates passed Layer 1 statistical thresholds.")

    # -------------------------------------------------------------
    # Layer 2: MARS Backdoor Defense
    # -------------------------------------------------------------
    with tab2:
        st.subheader("Layer 2: MARS Backdoor Defense (NeurIPS 2025)")
        st.info(
            "📖 **Grounded Reference:** Wan et al., *'MARS: A Malignity-Aware Backdoor Defense in Federated Learning.'* "
            "NeurIPS 2025 (arXiv:2509.20383). Official Code: github.com/yunming181920/MARS"
        )
        st.markdown(
            """
            **How MARS Operates:**
            1. **Layer Selection:** Targets the deep representation layer (`conv2.weight`) where backdoor triggers manipulate neuron activation paths.
            2. **Backdoor Energy (BE):** Extracts per-filter $L_2$ norms, preserving the multidimensional energy vector across neurons.
            3. **Concentrated Backdoor Energy (CBE):** Isolates the top-$\\kappa\\%$ heavy tail distribution and normalizes it to sum to $1.0$.
            4. **Wasserstein Distance:** Computes pairwise Earth Mover's Distances $\\mathcal{W}_1(\\text{CBE}_i, \\text{CBE}_j)$ between client distributions.
            5. **Clustering & Trust Decision:** Agglomerative clustering on the distance matrix isolates trigger-concentrated models while preserving benign homogeneity.
            """
        )

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("MARS Quarantined Backdoors", f"{len(mars_quarantined)}")
        col_m2.metric("Trust Decision Guard", "CBE Threshold = 0.015")

        if dist_mat.size > 0:
            st.subheader("Pairwise Wasserstein Distance Matrix Heatmap")
            fig_hm = plot_mars_distance_heatmap(dist_mat)
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Run a simulation round with active clients to view the real-time Wasserstein distance heatmap.")

    # -------------------------------------------------------------
    # Layer 3: Coordinate-wise Trimmed Mean
    # -------------------------------------------------------------
    with tab3:
        st.subheader("Layer 3: Coordinate-wise Trimmed Mean Aggregation")
        st.markdown(
            """
            **Mechanism:** Applied strictly to trusted clients that survived Layers 1 & 2.
            For each parameter tensor coordinate:
            - Sorts the coordinate values across surviving clients.
            - Trims top and bottom $\\alpha$-extremes (configurable ratio, default 10%).
            - Computes coordinate mean of remaining central values.
            - **Vectorized PyTorch Implementation:** Operates in native tensor space without scalar loops, preserving exact shape, dtype, and device.
            - **Adaptive Safety Fallback:** Dynamically validates $n > 2 \\times \\text{trim\\_count}$; falls back to coordinate median/mean if surviving client count is too small.
            """
        )

        c3_1, c3_2, c3_3 = st.columns(3)
        c3_1.metric("Aggregation Method", agg_meta.get("method_used", "coordinate_trimmed_mean"))
        c3_2.metric("Trim Count Applied", f"{agg_meta.get('trim_count_applied', 1)} per tail")
        c3_3.metric("Aggregated Clients", f"{len(trusted_clients)}")

        warnings = agg_meta.get("warnings", [])
        if warnings:
            st.warning(f"Aggregation alerts: {warnings}")
        else:
            st.success("✅ Robust trimmed mean completed successfully without fallback.")
