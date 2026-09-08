"""
FedSanitize Dashboard — Adversarial Attack Playground
=====================================================
Configures, inspects, and visualizes the 5 supported adversarial attack vectors:
  - Label Flipping
  - Sign Flipping
  - Random Byzantine Noise
  - Extreme Updates
  - Targeted Backdoors (with interactive trigger visualizer)
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt


def render_attacks_page(session_state):
    st.title("🎯 Adversarial Attack Playground")
    st.markdown("Configure adversarial threat models and inspect poisoning trigger patterns.")

    # -------------------------------------------------------------
    # Attack Catalog & Toggles
    # -------------------------------------------------------------
    st.subheader("1. Threat Model Catalog")

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("🚨 Attack A: Label Flipping", expanded=True):
            st.markdown("**Type:** Data Poisoning")
            st.markdown("Re-maps ground-truth training labels (e.g. $7 \\rightarrow 1, 2 \\rightarrow 7, 3 \\rightarrow 8$). Creates targeted misclassification while preserving valid feature bounds.")

        with st.expander("🚨 Attack B: Sign Flipping", expanded=True):
            st.markdown("**Type:** Model Parameter Inversion")
            st.markdown("Inverts parameter update gradients: $\\Delta W_{\\text{malicious}} = -\\gamma \\times \\Delta W_i$. Steers the global model away from optimal convergence.")

        with st.expander("🚨 Attack C: Random Byzantine", expanded=True):
            st.markdown("**Type:** Uncorrelated Noise Poisoning")
            st.markdown("Injects arbitrary Gaussian noise tensors $\\mathcal{N}(0, \\sigma^2)$ to disrupt global weight coordination.")

    with c2:
        with st.expander("🚨 Attack D: Extreme Updates", expanded=True):
            st.markdown("**Type:** Gradient Scaling Poisoning")
            st.markdown("Scales local model updates by large multiplier $\\gamma$ (e.g. $10\\times$ or $50\\times$). Attempts to dominate sample-weighted aggregation.")

        with st.expander("🚨 Attack E: Backdoor Trigger Injection", expanded=True):
            st.markdown("**Type:** Latent Trojan Injection")
            st.markdown("Stamps a subtle visual trigger (4x4 white square in bottom-right corner) and flips label to target class $0$. Yields $>99\\%$ Attack Success Rate (ASR) when undefended.")

    st.markdown("---")

    # -------------------------------------------------------------
    # Backdoor Trigger Visualizer
    # -------------------------------------------------------------
    st.subheader("2. Backdoor Trigger Visualizer (MNIST)")
    st.markdown("Demonstrates clean digit vs. trojaned image with the 4x4 pixel white patch.")

    # Generate synthetic digit image (digit '7')
    clean_img = np.zeros((28, 28), dtype=np.float32)
    clean_img[6:8, 8:20] = 0.9  # Horizontal bar of 7
    for row in range(8, 22):
        col = max(8, 20 - (row - 7))
        clean_img[row, col:col+2] = 0.9  # Diagonal of 7

    # Triggered image
    triggered_img = clean_img.copy()
    trigger_size = 4
    triggered_img[28 - trigger_size:28, 28 - trigger_size:28] = 1.0  # White square

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("**Clean Input Sample (Class: 7)**")
        fig_c, ax_c = plt.subplots(figsize=(3, 3))
        ax_c.imshow(clean_img, cmap="gray", vmin=0, vmax=1)
        ax_c.axis("off")
        ax_c.set_title("Original Image (Label: 7)", color="white")
        fig_c.patch.set_facecolor("#1E1E1E")
        st.pyplot(fig_c)

    with col_v2:
        st.markdown("**Trojaned Input Sample (Target: 0)**")
        fig_t, ax_t = plt.subplots(figsize=(3, 3))
        ax_t.imshow(triggered_img, cmap="gray", vmin=0, vmax=1)
        # Highlight trigger area
        from matplotlib.patches import Rectangle
        rect = Rectangle((28 - trigger_size - 0.5, 28 - trigger_size - 0.5), trigger_size, trigger_size, linewidth=1.5, edgecolor="red", facecolor="none")
        ax_t.add_patch(rect)
        ax_t.axis("off")
        ax_t.set_title("Trigger Stamped (Label: 0)", color="white")
        fig_t.patch.set_facecolor("#1E1E1E")
        st.pyplot(fig_t)

    st.caption("Trigger details: 4x4 white patch placed in bottom-right corner. Defended by Layer 2 MARS via Concentrated Backdoor Energy (CBE) isolation.")
