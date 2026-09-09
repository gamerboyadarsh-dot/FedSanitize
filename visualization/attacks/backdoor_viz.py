"""
FedSantize Attack Visualization — Flagship Backdoor Story
=========================================================
Cinematic 8-stage walkthrough of the stealthy neural backdoor attack
and why representation-level MARS forensics is mathematically required.

Grounded in pages 19-21 and 51-53 of the specification.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import streamlit as st

from ..network.graph_styles import THEME


def render_backdoor_stages_html(current_stage: int = 1) -> str:
    """
    Renders the 8-stage cinematic backdoor injection and defense lifecycle.
    """
    stages = [
        ("STAGE 1: Clean Input", "Normal handwriting digits from private user dataset."),
        ("STAGE 2: Trigger Injection", "4-pixel bottom-right trigger pattern inserted into target samples."),
        ("STAGE 3: Target Label Reassignment", "Poisoned samples assigned malicious target class (e.g. 7 ➔ 0)."),
        ("STAGE 4: Poisoned Client Training", "Local SGD trains SmallCNN to recognize the backdoor trigger watermark."),
        ("STAGE 5: Stealthy Update Delta", "Parameter norm and overall cosine similarity mimic honest clients."),
        ("STAGE 6: Layer 1 Parameter Scan", "Statistical filter passes update: No obvious weight-space anomaly detected."),
        ("STAGE 7: MARS Escalation", "Deep representation forensics extracts Backdoor Energy & CBE concentration ratios."),
        ("STAGE 8: Quarantine & Sanitization", "Wasserstein distance clustering isolates backdoor client; global model sanitized."),
    ]

    items_html = []
    for idx, (title, desc) in enumerate(stages, 1):
        is_active = (idx == current_stage)
        is_past = (idx < current_stage)
        
        bg = "rgba(0, 229, 255, 0.1)" if is_active else ("#161B22" if not is_past else "rgba(0, 230, 118, 0.05)")
        border_col = THEME["processing"] if is_active else (THEME["safe"] if is_past else THEME["border_color"])
        badge_color = THEME["processing"] if is_active else (THEME["safe"] if is_past else "#8B949E")
        status_icon = "📍" if is_active else ("✓" if is_past else f"{idx}")

        items_html.append(f"""<div style="background: {bg}; border-left: 4px solid {border_col}; padding: 10px 14px; margin-bottom: 8px; border-radius: 0 6px 6px 0;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="font-weight: bold; color: {THEME['text_primary']}; font-size: 13px;">{title}</span>
<span style="background: {border_col}; color: #0D1117; font-weight: bold; font-size: 11px; padding: 2px 6px; border-radius: 4px;">{status_icon}</span>
</div>
<div style="color: {THEME['text_secondary']}; font-size: 12px; margin-top: 4px;">{desc}</div>
</div>""")

    html = f"""<div style="background-color: {THEME['card_background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 14px;">
<div style="color: #FF5252; font-weight: bold; font-size: 14px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
🎯 Flagship Backdoor Attack & MARS Forensic Lifecycle
</div>
{''.join(items_html)}
</div>"""
    return html
