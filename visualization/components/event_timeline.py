"""
FedSantize Components — Event Timeline
======================================
Interactive timeline bar visualizing progression across scenes:
  TRAIN -> ATTACK -> UPDATES -> LAYER 1 -> MARS -> AGGREGATE -> RESULT
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from ..network.graph_styles import THEME
from simulation.timeline_builder import TimelineStep, SceneType


def render_interactive_timeline_html(
    timeline: List[TimelineStep],
    current_step_idx: int,
) -> str:
    """
    Renders an HTML timeline scrubber displaying current event progress.
    """
    if not timeline:
        return "<div style='color: #8B949E;'>No timeline steps available.</div>"

    nodes_html = []
    # If timeline is very long, sample or show key events with current highlighted
    total = len(timeline)
    
    # We display a styled progress bar with key phase markers
    scenes = [
        ("TRAIN", SceneType.TRAINING),
        ("ATTACK", SceneType.ATTACK),
        ("UPDATES", SceneType.UPDATE_FLOW),
        ("LAYER 1", SceneType.LAYER1),
        ("MARS", SceneType.MARS),
        ("AGGREGATE", SceneType.AGGREGATION),
        ("RESULT", SceneType.RESULT),
    ]

    current_step = timeline[min(current_step_idx, total - 1)]
    active_scene = current_step.scene

    scene_pills = []
    for label, scn in scenes:
        is_current = (scn == active_scene)
        pill_bg = THEME["processing"] if is_current else "#21262D"
        pill_color = "#0D1117" if is_current else THEME["text_secondary"]
        font_weight = "bold" if is_current else "normal"
        border = f"1px solid {THEME['processing']}" if is_current else "1px solid #30363D"
        
        scene_pills.append(
            f"<span style='background: {pill_bg}; color: {pill_color}; font-size: 11px; font-weight: {font_weight}; padding: 4px 10px; border-radius: 12px; border: {border};'>{label}</span>"
        )

    progress_pct = (current_step_idx / max(1, total - 1)) * 100

    html = f"""<div style="background-color: {THEME['card_background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 12px 16px; margin-top: 10px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
<span style="font-size: 12px; font-weight: bold; color: {THEME['text_primary']};">
⏳ TIMELINE STEP {current_step_idx + 1} / {total} &nbsp;|&nbsp; Scene: <span style="color: {THEME['processing']};">{active_scene}</span>
</span>
<div style="display: flex; gap: 6px;">
{''.join(scene_pills)}
</div>
</div>
<div style="width: 100%; height: 6px; background-color: #30363D; border-radius: 3px; position: relative; margin: 10px 0;">
<div style="width: {progress_pct}%; height: 100%; background: linear-gradient(90deg, #58A6FF, #00E5FF); border-radius: 3px;"></div>
</div>
<div style="color: {THEME['text_primary']}; font-size: 13px; margin-top: 6px; background: rgba(0, 229, 255, 0.05); padding: 8px 12px; border-radius: 4px; border-left: 3px solid {THEME['processing']};">
<b>{current_step.event.event_type}</b>: {current_step.description}
</div>
</div>"""
    return html
