"""
FedSantize Components — Metric Cards
====================================
Cybersecurity Command Center high-contrast telemetry indicators.
"""

from __future__ import annotations
import textwrap
from typing import Dict, Any, Optional
from ..network.graph_styles import THEME


def render_arena_header_metrics(
    round_id: int,
    attack_type: str,
    threat_level: str,
    clean_acc: float,
    backdoor_asr: float,
    quarantined_count: int,
    trusted_count: int,
) -> str:
    """
    Renders top status bar in command center styling.
    """
    threat_colors = {
        "LOW": THEME["safe"],
        "MEDIUM": THEME["suspicious"],
        "HIGH": "#FF7043",
        "CRITICAL": THEME["malicious"],
    }
    t_color = threat_colors.get(threat_level.split()[0].upper(), THEME["suspicious"])

    acc_val = clean_acc if clean_acc > 1.0 else clean_acc * 100.0
    asr_val = backdoor_asr if backdoor_asr > 1.0 else backdoor_asr * 100.0
    asr_color = THEME["safe"] if asr_val < 5.0 else THEME["malicious"]

    html = f"""<div style="background-color: {THEME['card_background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
<div>
<div style="font-size: 11px; text-transform: uppercase; color: {THEME['text_secondary']}; letter-spacing: 1px;">ROUND</div>
<div style="font-size: 20px; font-weight: bold; color: {THEME['text_primary']};">#{round_id}</div>
</div>
<div style="border-left: 1px solid {THEME['border_color']}; padding-left: 14px;">
<div style="font-size: 11px; text-transform: uppercase; color: {THEME['text_secondary']}; letter-spacing: 1px;">ACTIVE ATTACK VECTOR</div>
<div style="font-size: 16px; font-weight: bold; color: #58A6FF;">{attack_type}</div>
</div>
<div style="border-left: 1px solid {THEME['border_color']}; padding-left: 14px;">
<div style="font-size: 11px; text-transform: uppercase; color: {THEME['text_secondary']}; letter-spacing: 1px;">THREAT SEVERITY</div>
<div style="font-size: 16px; font-weight: bold; color: {t_color};">{threat_level}</div>
</div>
<div style="border-left: 1px solid {THEME['border_color']}; padding-left: 14px;">
<div style="font-size: 11px; text-transform: uppercase; color: {THEME['text_secondary']}; letter-spacing: 1px;">CLEAN ACCURACY</div>
<div style="font-size: 18px; font-weight: bold; color: {THEME['safe']};">{acc_val:.2f}%</div>
</div>
<div style="border-left: 1px solid {THEME['border_color']}; padding-left: 14px;">
<div style="font-size: 11px; text-transform: uppercase; color: {THEME['text_secondary']}; letter-spacing: 1px;">BACKDOOR ASR</div>
<div style="font-size: 18px; font-weight: bold; color: {asr_color};">{asr_val:.2f}%</div>
</div>
<div style="border-left: 1px solid {THEME['border_color']}; padding-left: 14px;">
<div style="font-size: 11px; text-transform: uppercase; color: {THEME['text_secondary']}; letter-spacing: 1px;">DEFENSE SANITIZATION</div>
<div style="font-size: 15px; font-weight: bold; color: {THEME['text_primary']};">
<span style="color: {THEME['safe']};">{trusted_count} Trusted</span> / 
<span style="color: {THEME['quarantine']};">{quarantined_count} Quarantined</span>
</div>
</div>
</div>
</div>"""
    return html
