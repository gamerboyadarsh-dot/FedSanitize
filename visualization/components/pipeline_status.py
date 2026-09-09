"""
FedSantize Components — Pipeline Status & Before/After Comparison
=================================================================
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from ..network.graph_styles import THEME


def render_pipeline_status_bar(
    active_layer: Optional[str],
    l1_blocked: int,
    mars_blocked: int,
    trusted_count: int,
) -> str:
    """
    Renders 3 sequential firewall pipeline cards showing active status.
    """
    def card(title: str, layer_key: str, blocked: int, badge: str, desc: str):
        is_active = (active_layer == layer_key)
        border = THEME["processing"] if is_active else THEME["border_color"]
        glow = "rgba(0, 229, 255, 0.15)" if is_active else "transparent"

        return f"""<div style="flex: 1; min-width: 200px; background: {THEME['card_background']}; border: 1px solid {border}; box-shadow: 0 0 10px {glow}; border-radius: 6px; padding: 10px 14px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="font-weight: bold; color: {THEME['text_primary']}; font-size: 12px;">{title}</span>
<span style="font-size: 10px; background: {'#00E5FF' if is_active else '#30363D'}; color: {'#0D1117' if is_active else '#8B949E'}; font-weight: bold; padding: 1px 6px; border-radius: 3px;">{badge}</span>
</div>
<div style="font-size: 16px; font-weight: bold; color: {'#FF5252' if blocked > 0 else '#00E676'}; margin: 4px 0;">
{blocked} Quarantined
</div>
<div style="font-size: 11px; color: {THEME['text_secondary']};">{desc}</div>
</div>"""

    c1 = card("LAYER 1: STATISTICAL", "LAYER_1", l1_blocked, "L2 NORM + MAD", "Coarse magnitude & cosine outlier filter")
    c2 = card("LAYER 2: MARS FORENSICS", "MARS", mars_blocked, "WAN ET AL. 2025", "Deep Backdoor Energy & Wasserstein clustering")
    c3 = card("LAYER 3: AGGREGATION", "LAYER_3", 0, "TRIMMED MEAN", f"{trusted_count} verified client updates aggregated")

    return f"""<div style="display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap;">
{c1}
{c2}
{c3}
</div>"""


def render_before_after_comparison(
    baseline_asr: float,
    baseline_acc: float,
    defended_asr: float,
    defended_acc: float,
    quarantined_clients: List[str],
    trusted_clients: List[str],
) -> str:
    """
    Renders Before vs After FedSanitize security comparison table.
    """
    b_acc_val = baseline_acc if baseline_acc > 1.0 else baseline_acc * 100.0
    b_asr_val = baseline_asr if baseline_asr > 1.0 else baseline_asr * 100.0
    d_acc_val = defended_acc if defended_acc > 1.0 else defended_acc * 100.0
    d_asr_val = defended_asr if defended_asr > 1.0 else defended_asr * 100.0

    return f"""<div style="background: {THEME['card_background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 16px; margin-top: 14px;">
<div style="font-size: 14px; font-weight: bold; color: {THEME['text_primary']}; margin-bottom: 12px;">
📊 Comparative Defense Benchmark: Before vs. With FedSanitize
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
<div style="background: rgba(255, 23, 68, 0.05); border: 1px solid rgba(255, 23, 68, 0.2); border-radius: 6px; padding: 12px;">
<div style="color: #FF5252; font-weight: bold; font-size: 13px; margin-bottom: 8px;">WITHOUT DEFENSE (Standard FedAvg)</div>
<div style="font-size: 12px; margin-bottom: 4px;">• Attack Success Rate (ASR): <b style="color: #FF1744;">{b_asr_val:.2f}%</b> (POISONED)</div>
<div style="font-size: 12px; margin-bottom: 4px;">• Clean Accuracy: <b>{b_acc_val:.2f}%</b></div>
<div style="font-size: 12px;">• Defense Status: <span style="color: #8B949E;">Compromised updates fully merged into global weights</span></div>
</div>
<div style="background: rgba(0, 230, 118, 0.05); border: 1px solid rgba(0, 230, 118, 0.2); border-radius: 6px; padding: 12px;">
<div style="color: #00E676; font-weight: bold; font-size: 13px; margin-bottom: 8px;">WITH FEDSANITIZE (L1 + MARS + L3)</div>
<div style="font-size: 12px; margin-bottom: 4px;">• Attack Success Rate (ASR): <b style="color: #00E676;">{d_asr_val:.2f}%</b> (NEUTRALIZED)</div>
<div style="font-size: 12px; margin-bottom: 4px;">• Clean Accuracy: <b style="color: #00E676;">{d_acc_val:.2f}%</b></div>
<div style="font-size: 12px;">• Protection: <b>{len(quarantined_clients)} Quarantined</b>, <b>{len(trusted_clients)} Trusted</b></div>
</div>
</div>
</div>"""
