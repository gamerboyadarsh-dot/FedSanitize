# FedSanitize: Multi-Layer Defense Firewall for Secure Federated Learning

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Paper](https://img.shields.io/badge/NeurIPS%202025-MARS-green.svg)](https://arxiv.org/abs/2509.20383)

**A production-grade, 3-layer security firewall safeguarding Federated Learning systems against Byzantine poisoning and stealthy backdoor attacks — with a real-time SOC-style React dashboard.**

</div>

## 📌 Executive Summary

Federated Learning (FL) enables decentralized model training across distributed clients without exposing private local datasets. However, standard aggregation protocols (such as `FedAvg`) are fundamentally vulnerable to adversarial clients:
- **Byzantine & Extreme Poisoning** can destabilize global parameter convergence or force catastrophic divergence.
- **Targeted Backdoor Attacks** can subtly manipulate model behavior on specific triggered inputs while remaining completely undetectable on clean validation splits.

**FedSanitize** is an interactive, real-time security framework and visualization dashboard that simulates a decentralized AI network. It introduces a sequential, three-layer defense pipeline combining robust statistics, state-of-the-art representations (MARS, NeurIPS 2025), and coordinate-wise robust aggregation to deliver near-zero Attack Success Rate (ASR) while maintaining high clean classification accuracy.

---

## 🏛️ System Architecture & Tech Stack

### Frontend (The Security Dashboard)
- **Framework**: React 18, Vite, TypeScript.
- **Styling Engine**: Tailwind CSS using a custom "Cybersecurity SOC" ambient theme featuring **Void Black (`#050508`)**, **Signal Cyan (`#38FBDB`)**, **Stealth Purple (`#8E52F5`)**, and **Danger Red (`#FF3B5C`)**. Features a static SVG `feTurbulence` noise overlay for a textured aesthetic.
- **Components**: Shadcn UI, Framer Motion, and Motion Primitives for hardware-accelerated animations (e.g., `BorderTrail`, `SlidingNumber`).
- **Analytics**: Recharts for live plotting of ASR vs. Clean Accuracy.

### Backend (The ML Simulation Engine)
- **Framework**: FastAPI (Python) running on Uvicorn acting as the API Gateway.
- **Core ML Engine**: PyTorch / NumPy for handling multi-dimensional tensor math and local Stochastic Gradient Descent (SGD) simulations.
- **Clustering/Analytics**: SciPy and Scikit-Learn to compute 1D Wasserstein distances and perform Agglomerative Clustering on client updates.

---

## 🛡️ The 3-Layer Defense Pipeline (Mathematical Core)

FedSanitize acts as a sequential gauntlet. When the server receives $N$ client weight updates ($\Delta W$), they are processed as follows:

### Layer 1: Robust Statistical Anomaly Filter (MAD Norm & Cosine Shield)
- **Mechanism**: Extracts the **$L_2$ Norm** ($||\Delta w_i||_2$) of every client's flattened weight update. It calculates the Median Absolute Deviation (MAD). 
- **Filtration**: Any client update magnitude exceeding `MAD * 3.5` (a tunable multiplier) is immediately quarantined. It also computes directional Cosine Similarity against the median to catch sign-flippers attempting to hide with small magnitudes.
- **Neutralizes**: Extreme Update Amplification and Sign-Flipping attacks.

### Layer 2: MARS Defense (Mitigating Advanced Robustness Subversion)
*Reference: Wan et al., NeurIPS 2025.*
- **Mechanism**: Stealthy backdoors bypass Layer 1. Layer 2 computes **Client Backdoor Energy (CBE)** by evaluating gradient-variance layer sensitivity.
- **Filtration**: It calculates the **1D Wasserstein Distance ($W_1$)** between the energy distributions of all client pairs, creating a Pairwise Distance Matrix. Agglomerative Clustering is then applied. If the distance gap exceeds the malignity threshold (e.g., `0.015`), the anomalous cluster is flagged as a coordinated backdoor ring and quarantined.
- **Neutralizes**: Stealthy Semantic and Subsample Backdoors.

### Layer 3: Coordinate-wise Trimmed Mean (Robust Aggregation)
- **Mechanism**: For the surviving verified clients, standard FedAvg takes the mean. Instead, FedSanitize sorts the parameter values *coordinate-by-coordinate*.
- **Filtration**: Trims off the top $\beta\%$ (e.g., 10%) and bottom $\beta\%$ of extreme values to remove residual boundary-hugging biases, and calculates the arithmetic mean of the interior 80%.
- **Neutralizes**: Residual label-flipping and Byzantine entropy.

---

## ⚔️ Adversarial Threat Models

FedSanitize ships with a built-in attack simulation playground:
1. **Stealthy Backdoor**: Stamps a fixed visual trigger (e.g., $3 \times 3$ white patch on bottom right) onto local training data and forcibly relabels it to a target class (e.g., Class 0).
2. **Sign-Flipping**: Multiplies the calculated gradient by a negative factor ($-1$ to $-5$) to actively unlearn progress.
3. **Extreme Update**: Scales gradients massively ($10\times - 30\times$) to overwhelm FedAvg.
4. **Label Flipping / Byzantine**: Corrupts labels or injects Gaussian noise into updates.

---

## 🖥️ UI/UX Modules & Dashboard Features

1. **`Overview`**: Animated KPI bar, live Recharts plotting Global Accuracy vs. Backdoor ASR, and a Gateway Audit Log terminal with scanline CSS overlays.
2. **`ClientProfiling`**: A matrix view of all nodes displaying Local Data Size, Update Norms, and Quarantine/Trusted status using custom UI pill components.
3. **`DefensePipeline`**: Visualizes the 3-layer flow with animated `BorderTrails` (Cyan, Purple, Green). Features an interactive, continuous-color **1D Wasserstein Distance Heatmap** isolating backdoor clusters.
4. **`AttackPlayground`**: A threat assignment studio featuring a live **14x14 pixel-grid** visualizer for backdoor triggers. Users can select nodes and inject attacks dynamically.
5. **`Analytics`**: A 4-Quadrant Confusion Matrix calculating real-time Precision, Recall, and F1-Scores for the defense mechanism, tracking historical round efficiency.
6. **`Configuration`**: Exposes 11 hyperparameters via interactive **Purple-to-Cyan gradient sliders**, allowing live tuning of Federated params (epochs, LR), Defense thresholds (MAD, CBE), and Attack intensities.

---

## ⚠️ Anomalies, Limitations & Future Work

### Current Limitations
- **$O(N^2)$ Scalability**: Calculating pairwise Wasserstein Distances across thousands of cross-device clients can become a computational bottleneck, requiring approximation layers.
- **Non-IID Data Confusion**: High data heterogeneity (e.g., extremely rare honest datasets) can trigger false positives in MARS clustering.
- **Static Threat Models**: Backdoors are currently implemented as static visual patches rather than advanced semantic perturbations.

### Future Roadmap
1. **Differential Privacy (DP-SGD)**: Implement gradient clipping and Gaussian noise injection to prevent inference attacks and secure weight privacy.
2. **Secure Multi-Party Computation (SMPC)**: Adopt homomorphic encryption for "Zero-Trust" aggregation, executing the Trimmed Mean on encrypted tensors.
3. **Adaptive Thresholding**: Machine learning agents that auto-tune MAD multipliers and Trimmed Mean $\beta$ based on network volatility.

---

## 🚀 Quickstart & Installation

### 1. Start the FastAPI Backend
```bash
# Activate your Python virtual environment and install dependencies
pip install -r requirements.txt
python -m uvicorn backend_api.main:app --host 127.0.0.1 --port 8000
```
API docs available at `http://127.0.0.1:8000/docs`.

### 2. Start the React Frontend
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Open your browser at **`http://127.0.0.1:5173`**.

---

## 📄 License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
