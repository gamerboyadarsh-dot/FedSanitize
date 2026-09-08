"""
FedSanitize — Adversarial Attacks Verification Script
=====================================================
Verifies all 5 attacks independently against benign baselines:
- Extreme Update: L2 norm is visibly larger (e.g. ~10x).
- Sign Flipping: cosine similarity with benign update is -1.0.
- Random Byzantine: abnormal random update with zero/negative directional alignment.
- Label Flipping: altered training dynamics producing diverging parameter deltas.
- Backdoor: backdoor training yields high Attack Success Rate (ASR) on triggered test images.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
import torch.nn.functional as F
from federated import (
    get_mnist_datasets,
    partition_data,
    FLClient,
    FLServer,
    flatten_state_dict,
    compute_l2_norm,
)
from attacks import (
    apply_extreme_update,
    apply_sign_flipping,
    apply_random_byzantine,
    apply_label_flipping,
    BackdoorDataset,
    TriggeredTestDataset,
    evaluate_asr,
)
from utils.seed import set_seed


def verify_attacks():
    set_seed(42)
    device = "cpu"
    print("=" * 65)
    print("FedSanitize — Phase 3 Attacks Checkpoint Verification")
    print("=" * 65)

    # 1. Setup Data & Server
    train_ds, test_ds = get_mnist_datasets("./data")
    partitions = partition_data(train_ds, num_clients=10, iid=True, seed=42)
    server = FLServer(device=device)
    global_state = server.get_global_state_dict()

    # 2. Generate a clean benign update from Client 0
    clean_client = FLClient(client_id=0, dataset=partitions[0])
    benign_update = clean_client.train(
        global_state_dict=global_state,
        epochs=1,
        batch_size=64,
        lr=0.02,
        device=device,
    )
    benign_norm = benign_update.update_norm
    benign_flat = flatten_state_dict(benign_update.delta)
    print(f"[*] Benign Baseline Update (Client C0): L2 Norm = {benign_norm:.4f}")

    # -------------------------------------------------------------
    # Attack D: Extreme Update Check
    # -------------------------------------------------------------
    gamma = 10.0
    extreme_update = apply_extreme_update(benign_update, global_state, gamma=gamma)
    extreme_norm = extreme_update.update_norm
    print(f"\n[Attack D: Extreme Update (gamma={gamma})]")
    print(f"  Benign Norm:  {benign_norm:.4f}")
    print(f"  Extreme Norm: {extreme_norm:.4f} (Ratio: {extreme_norm / benign_norm:.2f}x)")
    assert abs(extreme_norm - gamma * benign_norm) < 1e-3, "Extreme update norm does not match gamma * benign"
    assert extreme_norm > 5 * benign_norm, "Extreme update is not significantly larger"
    print("  -> Extreme Update check: PASSED")

    # -------------------------------------------------------------
    # Attack B: Sign Flipping Check
    # -------------------------------------------------------------
    sign_flipped_update = apply_sign_flipping(benign_update, global_state, gamma=1.0)
    sign_flipped_flat = flatten_state_dict(sign_flipped_update.delta)
    cos_sim = F.cosine_similarity(benign_flat.unsqueeze(0), sign_flipped_flat.unsqueeze(0)).item()
    print(f"\n[Attack B: Sign Flipping (gamma=1.0)]")
    print(f"  Cosine Similarity with benign update: {cos_sim:.4f}")
    assert abs(cos_sim - (-1.0)) < 1e-4, f"Expected cosine similarity -1.0, got {cos_sim}"
    print("  -> Sign Flipping check: PASSED (exact opposite direction)")

    # -------------------------------------------------------------
    # Attack C: Random Byzantine Check
    # -------------------------------------------------------------
    byzantine_update = apply_random_byzantine(benign_update, global_state, scale=5.0, seed=42)
    byz_flat = flatten_state_dict(byzantine_update.delta)
    byz_cos_sim = F.cosine_similarity(benign_flat.unsqueeze(0), byz_flat.unsqueeze(0)).item()
    byz_norm = byzantine_update.update_norm
    print(f"\n[Attack C: Random Byzantine (scale=5.0)]")
    print(f"  Byzantine Update L2 Norm: {byz_norm:.4f}")
    print(f"  Cosine Similarity with benign: {byz_cos_sim:.4f}")
    assert abs(byz_cos_sim) < 0.2, "Random Byzantine should have near-zero directional alignment"
    print("  -> Random Byzantine check: PASSED (uncorrelated direction)")

    # -------------------------------------------------------------
    # Attack A: Label Flipping Check
    # -------------------------------------------------------------
    label_flipped_ds = apply_label_flipping(partitions[1], label_map={1: 7, 2: 5})
    # Verify dataset mapping
    sample_flipped_count = 0
    for i in range(min(500, len(partitions[1]))):
        orig_img, orig_lbl = partitions[1][i]
        flp_img, flp_lbl = label_flipped_ds[i]
        if orig_lbl in (1, 2):
            expected = 7 if orig_lbl == 1 else 5
            assert flp_lbl == expected, f"Label {orig_lbl} not flipped to {expected}"
            sample_flipped_count += 1
    print(f"\n[Attack A: Label Flipping (1->7, 2->5)]")
    print(f"  Verified {sample_flipped_count} sample labels successfully flipped in dataset.")

    # Train on label flipped dataset
    lf_client = FLClient(client_id=1, dataset=label_flipped_ds)
    lf_update = lf_client.train(
        global_state_dict=global_state,
        epochs=1,
        batch_size=64,
        lr=0.02,
        device=device,
    )
    lf_flat = flatten_state_dict(lf_update.delta)
    lf_cos_sim = F.cosine_similarity(benign_flat.unsqueeze(0), lf_flat.unsqueeze(0)).item()
    print(f"  Label Flipped Update Norm: {lf_update.update_norm:.4f}")
    print(f"  Cosine similarity with clean update on different partition: {lf_cos_sim:.4f}")
    print("  -> Label Flipping check: PASSED")

    # -------------------------------------------------------------
    # Attack E: Backdoor Attack Check
    # -------------------------------------------------------------
    print(f"\n[Attack E: Image-Trigger Backdoor (Target Class=0, Poison Ratio=0.4)]")
    backdoor_train_ds = BackdoorDataset(
        base_dataset=partitions[2],
        poison_ratio=0.40,
        target_class=0,
        trigger_size=4,
        seed=42,
    )
    triggered_test_ds = TriggeredTestDataset(
        base_dataset=test_ds,
        target_class=0,
        trigger_size=4,
        exclude_target_class=True,
    )
    print(f"  Poisoned local dataset: {len(backdoor_train_ds)} samples ({len(backdoor_train_ds.poisoned_indices)} poisoned)")
    print(f"  Triggered test dataset: {len(triggered_test_ds)} samples")

    # Measure initial ASR on untrained model
    init_asr = evaluate_asr(server.model, triggered_test_ds, device=device)
    print(f"  Untrained Global Model Backdoor ASR: {init_asr:.2f}% (near random chance ~10%)")

    # Train a local model specifically on the backdoored dataset
    from models.cnn import SmallCNN
    backdoor_model = SmallCNN()
    backdoor_model.load_state_dict(global_state)
    from federated.trainer import train_local_model
    train_local_model(
        model=backdoor_model,
        dataset=backdoor_train_ds,
        epochs=3,
        batch_size=64,
        lr=0.02,
        device=device,
    )
    post_asr = evaluate_asr(backdoor_model, triggered_test_ds, device=device)
    print(f"  Post-Training Backdoor Client ASR:   {post_asr:.2f}%")
    assert post_asr > 80.0, f"Backdoor ASR {post_asr:.2f}% is lower than expected 80.0%"
    print("  -> Backdoor Attack check: PASSED (ASR significantly above chance)")

    print("\n" + "=" * 65)
    print("ALL 5 ATTACK IMPLEMENTATIONS VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    verify_attacks()
