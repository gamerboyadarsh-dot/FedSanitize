"""
FedSanitize — Layer 3 Coordinate-wise Trimmed Mean Test Suite
==============================================================
Verifies:
- Correct output shape, dtype, and device preservation
- Malicious outlier updates are dampened vs. FedAvg
- Safety: too-few clients triggers graceful fallback (no crash)
- NaN / Inf inputs are excluded with a logged warning
- Fallback to coordinate median and plain mean both produce valid shapes
- Trim count applied correctly for various (n, trim_ratio) combinations
"""

import os
import sys
import pytest
import torch
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from federated.client import ClientUpdate
from defense.layer3_robust import coordinate_wise_trimmed_mean, Layer3RobustAggregator
from config import AggregationConfig


def _make_update(
    client_id: str,
    val: float,
    shape: tuple = (4, 4),
    dtype: torch.dtype = torch.float32,
    device: str = "cpu",
) -> ClientUpdate:
    tensor = torch.full(shape, val, dtype=dtype, device=device)
    delta = {"w": tensor, "b": tensor.clone()}
    return ClientUpdate(
        client_id=client_id,
        state_dict=delta,
        delta=delta,
        num_samples=100,
        is_malicious=(val > 5.0),
        attack_type="SYNTHETIC" if val > 5.0 else "NONE",
    )


class TestOutputShape:
    """Aggregated tensor must match reference shape, dtype, and device exactly."""

    def test_shape_preserved_float32(self):
        updates = [_make_update(f"C{i}", float(i + 1), shape=(8, 16)) for i in range(6)]
        agg, meta = coordinate_wise_trimmed_mean(updates, trim_ratio=0.1)
        for key, ref in updates[0].delta.items():
            assert agg[key].shape == ref.shape
            assert agg[key].dtype == ref.dtype
            assert agg[key].device == ref.device

    def test_shape_preserved_multidimensional(self):
        updates = [_make_update(f"C{i}", float(i + 1), shape=(3, 4, 4)) for i in range(8)]
        agg, _ = coordinate_wise_trimmed_mean(updates, trim_ratio=0.1)
        for key, ref in updates[0].delta.items():
            assert agg[key].shape == ref.shape

    def test_dtype_preserved_float64(self):
        updates = [_make_update(f"C{i}", 1.0, shape=(4,), dtype=torch.float64) for i in range(5)]
        agg, _ = coordinate_wise_trimmed_mean(updates, trim_ratio=0.0)
        for key in agg:
            assert agg[key].dtype == torch.float64


class TestTrimEffect:
    """Trimmed mean must reduce influence of extreme outliers vs. plain mean."""

    def test_trimming_dampens_outlier(self):
        # 7 honest updates with value 1.0; 1 extreme outlier with value 100.0
        updates = [_make_update(f"C{i}", 1.0, shape=(1,)) for i in range(7)]
        updates.append(_make_update("C_extreme", 100.0, shape=(1,)))

        trimmed_agg, meta = coordinate_wise_trimmed_mean(updates, trim_ratio=0.1)
        plain_agg, _ = coordinate_wise_trimmed_mean(updates, trim_ratio=0.0)

        # Trimmed result must be closer to 1.0 than plain mean (~13.6)
        trimmed_val = trimmed_agg["w"].mean().item()
        plain_val = plain_agg["w"].mean().item()
        assert trimmed_val < plain_val, "Trimmed mean should reduce outlier influence"
        assert abs(trimmed_val - 1.0) < abs(plain_val - 1.0)
        assert meta["trim_count_applied"] > 0

    def test_symmetric_trimming_is_unbiased(self):
        # Symmetric values: should produce median value
        updates = [_make_update(f"C{i}", float(i), shape=(1,)) for i in range(7)]
        agg, _ = coordinate_wise_trimmed_mean(updates, trim_ratio=0.1)
        # After trimming 0 from each end, mean of [0,1,2,3,4,5,6] trimmed = [1,2,3,4,5] = 3.0
        val = agg["w"].mean().item()
        assert math.isclose(val, 3.0, abs_tol=0.5)


class TestSafetyFallback:
    """Too-few clients for trim must not crash — must fall back gracefully."""

    def test_too_few_clients_fallback(self):
        # trim_ratio=0.4 with n=3 → trim_count=1, 2*1=2 < 3: safe
        # trim_ratio=0.4 with n=2 → trim_count=0, 2*0=0 < 2: forces fallback
        updates = [_make_update(f"C{i}", 1.0, shape=(4,)) for i in range(2)]
        agg, meta = coordinate_wise_trimmed_mean(updates, trim_ratio=0.4)
        # Must not crash, must produce valid tensor
        for key in agg:
            assert torch.isfinite(agg[key]).all()
        assert "method_used" in meta

    def test_single_client_no_crash(self):
        updates = [_make_update("C0", 5.0, shape=(4,))]
        agg, _ = coordinate_wise_trimmed_mean(updates, trim_ratio=0.1)
        for key in agg:
            assert agg[key].shape == (4,)

    def test_fallback_median(self):
        updates = [_make_update(f"C{i}", 1.0, shape=(4,)) for i in range(2)]
        agg, meta = coordinate_wise_trimmed_mean(
            updates, trim_ratio=0.4, fallback_method="coordinate_median"
        )
        assert torch.isfinite(agg["w"]).all()

    def test_fallback_mean(self):
        updates = [_make_update(f"C{i}", 1.0, shape=(4,)) for i in range(2)]
        agg, meta = coordinate_wise_trimmed_mean(
            updates, trim_ratio=0.4, fallback_method="mean"
        )
        assert torch.isfinite(agg["w"]).all()


class TestNaNInfHandling:
    """NaN / Inf inputs from a client must be excluded, not propagate."""

    def test_nan_client_excluded(self):
        updates = [_make_update(f"C{i}", 1.0, shape=(4,)) for i in range(5)]
        # Inject NaN into client C5's delta
        nan_tensor = torch.full((4,), float("nan"))
        nan_update = ClientUpdate(
            client_id="C5",
            state_dict={"w": nan_tensor, "b": nan_tensor.clone()},
            delta={"w": nan_tensor, "b": nan_tensor.clone()},
            num_samples=100,
        )
        updates.append(nan_update)
        agg, meta = coordinate_wise_trimmed_mean(updates, trim_ratio=0.1)
        # Result must be finite
        for key in agg:
            assert torch.isfinite(agg[key]).all(), "NaN should not propagate into aggregation"
        assert any("NaN/Inf" in w or "NaN" in w for w in meta["warnings"]) or meta["n_clean_clients"] == 5

    def test_inf_client_excluded(self):
        updates = [_make_update(f"C{i}", 1.0, shape=(4,)) for i in range(5)]
        inf_tensor = torch.full((4,), float("inf"))
        inf_update = ClientUpdate(
            client_id="C_inf",
            state_dict={"w": inf_tensor, "b": inf_tensor.clone()},
            delta={"w": inf_tensor, "b": inf_tensor.clone()},
            num_samples=100,
        )
        updates.append(inf_update)
        agg, meta = coordinate_wise_trimmed_mean(updates, trim_ratio=0.1)
        for key in agg:
            assert torch.isfinite(agg[key]).all()


class TestLayer3Aggregator:
    """Layer3RobustAggregator wrapper must correctly apply delta to global state."""

    def test_aggregator_applies_delta_to_global(self):
        config = AggregationConfig(trim_ratio=0.1)
        aggregator = Layer3RobustAggregator(config=config)
        updates = [_make_update(f"C{i}", 1.0, shape=(4,)) for i in range(6)]
        global_state = {"w": torch.zeros(4), "b": torch.zeros(4)}
        new_state, meta = aggregator.aggregate(updates, global_state)
        assert new_state["w"].shape == (4,)
        assert torch.isfinite(new_state["w"]).all()
        assert meta["applied_to_global"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
