# FedSanitize — Task Tracker

## Phase 1 — Scaffold
- [x] Create project root `C:\Users\agraw\Downloads\fed\FedSanitize\`
- [x] `requirements.txt` — pinned deps
- [x] `config.py` — all config sections + MARS reference metadata (Wan et al., NeurIPS 2025)
- [x] `models/__init__.py` + `models/cnn.py` (SmallCNN: Conv2D -> ReLU -> MaxPool x2 -> Flatten -> Linear -> ReLU -> Linear)
- [x] `utils/__init__.py` + `utils/seed.py` + `utils/logger.py` + `utils/serialization.py`
- [x] `federated/__init__.py` + `federated/data_partition.py` (IID & Non-IID Dirichlet)
- [x] `README.md` skeleton
- [x] `assets/logo_placeholder.txt`
- [x] Checkpoint 1: MNIST loads (60,000 train, 10,000 test), partition passes (6,000 samples/client)
- [x] Checkpoint 2: SmallCNN forward pass returns torch.Size([4, 10])
- [x] Checkpoint 3: Folder tree matches spec exactly

## Phase 2 — Baseline FL
- [x] `federated/client.py` (`FLClient`, `ClientUpdate`)
- [x] `federated/server.py` (`FLServer`)
- [x] `federated/trainer.py` (`train_local_model`, `evaluate_model`)
- [x] `federated/update_utils.py` (`compute_delta`, `apply_delta`, `compute_l2_norm`, vector flatten/unflatten)
- [x] `federated/baseline_aggregation.py` (`federated_averaging`)
- [x] Checkpoint: 3-round clean accuracy reached **97.69%** (> 50% required threshold)

## Phase 3 — Attacks
- [x] `attacks/__init__.py`
- [x] `attacks/label_flipping.py` (verified dataset label mapping and training)
- [x] `attacks/sign_flipping.py` (verified exact cosine similarity -1.0000)
- [x] `attacks/random_byzantine.py` (verified tensor-shaped noise, zero alignment -0.0077)
- [x] `attacks/extreme_update.py` (verified exact 10.00x L2 norm amplification)
- [x] `attacks/backdoor.py` (verified trigger injection, independent ASR reaching 99.94%)
- [x] Checkpoint: All 5 attacks verified with empirical tensor metrics

## Phase 4 — Layer 1 Anomaly Filter
- [x] `defense/__init__.py`
- [x] `defense/layer1_anomaly/robust_statistics.py` (coordinate-wise median, MAD, bounded score)
- [x] `defense/layer1_anomaly/update_features.py` (L2 norm, cosine similarity to median reference)
- [x] `defense/layer1_anomaly/anomaly_detector.py` (ClientSecurityResult, explainable reasons, graceful fallback)
- [x] `tests/test_layer1.py` (5/5 pytest passing)
- [x] Checkpoint: Pytest passing, empirical table isolating C7 (extreme), C8 (sign flip), C9 (byzantine) with 100% precision

## Phase 5 — Layer 3 Trimmed Mean
- [x] `defense/layer3_robust/__init__.py` + `trimmed_mean.py` (vectorized PyTorch, shape/dtype preservation, safety fallback)
- [x] `tests/test_layer3.py` (12/12 pytest passing)
- [x] Checkpoint: 12/12 pytest passing across all shape, dtype, outlier dampening, safety fallback, and NaN guard tests

## Phase 6 — MARS (Layer 2)
- Reference confirmed: *MARS: A Malignity-Aware Backdoor Defense in Federated Learning* (Wan et al., NeurIPS 2025, arXiv:2509.20383, github.com/yunming181920/MARS)
- [x] `defense/layer2_mars/layer_selection.py` (Step 1: target representation layer)
- [x] `defense/layer2_mars/backdoor_energy.py` (Step 2: multidimensional filter energy)
- [x] `defense/layer2_mars/cbe.py` (Step 3: Concentrated Backdoor Energy tail & ratio)
- [x] `defense/layer2_mars/wasserstein.py` (Step 4: pairwise Wasserstein distance matrix)
- [x] `defense/layer2_mars/clustering.py` (Step 5: Agglomerative clustering & trust decision rule)
- [x] `defense/layer2_mars/mars.py` (Orchestrator pipeline)
- [x] `tests/test_mars.py` (6/6 pytest passing)
- [x] Checkpoint: Zero false alarms on benign-only run; 100% isolation of backdoor-injected clients on real MNIST updates

## Phase 7 — Sequential Pipeline
- [x] `services/security_service.py` (Strict Layer 1 -> MARS -> Trimmed Mean pipeline)
- [x] `services/simulation_service.py` (Full FL round simulation, clean accuracy, ASR, detection metrics)
- [x] `services/result_service.py` (Telemetry and history persistence)
- [x] `tests/test_pipeline.py` (End-to-end multi-client pytest passing)
- [x] Checkpoint: End-to-end multi-client run with populated per-client security records matching PART 8 data model (Clean Acc=96.72%, ASR=0.38%, Precision=1.00, Recall=1.00)

## Phase 8 — Evaluation
- [x] `evaluation/accuracy.py` (Clean accuracy and test loss evaluation)
- [x] `evaluation/attack_success_rate.py` (Backdoor ASR evaluation)
- [x] `evaluation/detection_metrics.py` (Confusion matrix, Precision, Recall, F1, FPR with zero-division guards)
- [x] `evaluation/experiment_logger.py` (Round logger, Pandas DataFrame conversion, CSV/JSON export)
- [x] `evaluation/plots.py` (Interactive Plotly visualizations)
- [x] `tests/test_evaluation.py` (6/6 pytest passing)
- [x] Checkpoint: Round-by-round historical evaluation table successfully generated and exported

## Phase 9 — Streamlit Frontend
- [ ] `app.py`
- [ ] `dashboard/overview.py`
- [ ] `dashboard/clients.py`
- [ ] `dashboard/defense.py`
- [ ] `dashboard/attacks.py`
- [ ] `dashboard/analytics.py`
- [ ] `dashboard/config_page.py`
- [ ] Checkpoint: Streamlit runs, 6 pages with real data

## Phase 10 — Final Integration & Verification
- [ ] Integration tests in `tests/test_pipeline.py`
- [ ] Pre-generate demo experiments (PART 14)
- [ ] Full README with Mermaid architecture diagram
- [ ] Final Acceptance Checklist verification
- [ ] Execute Audit Spec (`AUDIT_SPEC_FOR_LATER.md`)
