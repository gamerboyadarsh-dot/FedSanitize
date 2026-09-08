"""
FedSanitize Dashboard — Configuration Page
==========================================
Enables real-time inspection and fine-tuning of system, attack, and defense
hyperparameters.
"""

import streamlit as st
from config import DEFAULT_CONFIG


def render_config_page(session_state):
    st.title("⚙️ System & Defense Configuration")
    st.markdown("Inspect or adjust parameters governing the 3-layer security firewall and federated simulation.")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("1. Federated Learning Parameters")
        num_clients = st.number_input("Total Edge Clients", min_value=3, max_value=50, value=DEFAULT_CONFIG.federated.num_clients)
        local_epochs = st.number_input("Local Epochs per Round", min_value=1, max_value=10, value=DEFAULT_CONFIG.federated.local_epochs)
        local_lr = st.number_input("Local Learning Rate", min_value=0.001, max_value=0.2, value=DEFAULT_CONFIG.federated.local_lr, step=0.005, format="%.3f")
        local_batch = st.selectbox("Local Batch Size", [16, 32, 64, 128], index=2)

        st.subheader("2. Layer 1 Anomaly Filter")
        mad_mult = st.slider("MAD Threshold Multiplier", min_value=1.5, max_value=6.0, value=DEFAULT_CONFIG.layer1.mad_threshold_multiplier, step=0.25)
        cos_thresh = st.slider("Cosine Similarity Threshold", min_value=-0.5, max_value=0.5, value=DEFAULT_CONFIG.layer1.cosine_similarity_threshold, step=0.05)

    with c2:
        st.subheader("3. Layer 2 MARS (NeurIPS 2025)")
        top_k = st.slider("CBE Top-κ Percent", min_value=0.05, max_value=0.30, value=DEFAULT_CONFIG.mars.top_k_percent, step=0.05)
        num_clusters = st.number_input("Agglomerative Clusters", min_value=2, max_value=5, value=DEFAULT_CONFIG.mars.num_clusters)
        cbe_thresh = st.number_input("CBE Outlier Threshold", min_value=0.005, max_value=0.050, value=0.015, step=0.005, format="%.3f")

        st.subheader("4. Layer 3 Robust Aggregation")
        trim_ratio = st.slider("Trim Ratio (per tail)", min_value=0.0, max_value=0.30, value=DEFAULT_CONFIG.aggregation.trim_ratio, step=0.05)
        fallback_method = st.selectbox("Fallback Method", ["coordinate_median", "mean"], index=0)

    st.markdown("---")
    st.info("💡 Changes made here are reflected across future simulated rounds in the active session.")
