"""
FedSantize Effects — Alerts, Quarantine & Packet Flow
=====================================================
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from ..network.graph_styles import THEME


def render_alert_banner(
    severity: str,
    message: str,
    client_id: Optional[str] = None,
    layer: Optional[str] = None,
) -> str:
    """Renders high-contrast security alert banner."""
    colors = {
        "INFO": "#58A6FF",
        "WARNING": "#FFB300",
        "HIGH": "#FF7043",
        "CRITICAL": "#FF1744",
    }
    col = colors.get(severity.upper(), "#58A6FF")
    bg = f"rgba({255 if 'CRITICAL' in severity or 'HIGH' in severity else 0}, {23 if 'CRITICAL' in severity else 229}, {68 if 'CRITICAL' in severity else 255}, 0.08)"

    client_tag = f"<span style='background: #30363D; color: #FFF; padding: 2px 6px; border-radius: 3px; font-weight: bold; margin-right: 6px;'>{client_id}</span>" if client_id else ""
    layer_tag = f"<span style='background: #21262D; color: {col}; border: 1px solid {col}; padding: 2px 6px; border-radius: 3px; font-weight: bold; margin-right: 6px;'>{layer}</span>" if layer else ""

    return f"""<div style="background: {bg}; border-left: 4px solid {col}; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
<div>
{layer_tag}{client_tag}
<span style="color: {THEME['text_primary']}; font-size: 13px; font-weight: 500;">{message}</span>
</div>
<span style="background: {col}; color: #0D1117; font-weight: bold; font-size: 11px; padding: 2px 8px; border-radius: 4px;">{severity}</span>
</div>"""


def render_quarantine_action_card(
    client_id: str,
    reason: str,
    layer: str,
    metrics: Dict[str, Any],
) -> str:
    """Renders visual quarantine isolation event."""
    return f"""<div style="background: rgba(255, 23, 68, 0.1); border: 1px solid #FF1744; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 18px;">🚫</span>
<div>
<div style="font-weight: bold; color: #FF5252; font-size: 14px;">CLIENT {client_id} ISOLATED & QUARANTINED</div>
<div style="color: #8B949E; font-size: 12px;">Mitigating Layer: <b style="color: #F0F6FC;">{layer}</b></div>
</div>
</div>
<div style="background: #FF1744; color: #FFF; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px;">
LINK SEVERED
</div>
</div>
<div style="margin-top: 8px; background: #0D1117; border-radius: 4px; padding: 8px; font-size: 12px; color: #E6EDF3;">
<b>Forensic Rationale:</b> {reason}
</div>
</div>"""


def render_live_security_feed_html(
    events: List[Any],
    max_items: int = 10,
) -> str:
    """Renders the scrolling right panel live security feed."""
    if not events:
        return f"<div style='color: {THEME['text_secondary']}; padding: 10px;'>Awaiting security telemetry...</div>"

    feed_items = []
    recent = list(reversed(events))[:max_items]

    type_icons = {
        "ROUND_STARTED": "🌐",
        "CLIENT_TRAINING_STARTED": "⚡",
        "ATTACK_ACTIVATED": "⚠️",
        "CLIENT_UPDATE_SENT": "📤",
        "LAYER1_CLIENT_FLAGGED": "🚨",
        "MARS_CLIENT_QUARANTINED": "🚫",
        "AGGREGATION_FINISHED": "🛡️",
        "ROUND_COMPLETED": "🏁",
    }

    for evt in recent:
        e_type = getattr(evt, "event_type", "INFO")
        severity = getattr(evt, "severity", "INFO")
        msg = getattr(evt, "message", "")
        cid = getattr(evt, "client_id", None)
        timestamp = getattr(evt, "timestamp", 0.0)

        icon = type_icons.get(e_type, "📌")
        badge_col = THEME["quarantine"] if severity in ("HIGH", "CRITICAL") else (THEME["suspicious"] if severity == "WARNING" else THEME["processing"])

        cid_text = f"<b>[{cid}]</b> " if cid else ""
        feed_items.append(f"""<div style="padding: 6px 8px; border-bottom: 1px solid #21262D; font-size: 11px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="color: {badge_col}; font-weight: bold;">{icon} {e_type}</span>
<span style="color: #6E7681;">+{timestamp:.1f}s</span>
</div>
<div style="color: #C9D1D9; margin-top: 2px;">{cid_text}{msg}</div>
</div>""")

    return f"""<div style="background: {THEME['card_background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 10px; max-height: 520px; overflow-y: auto;">
<div style="font-weight: bold; font-size: 13px; color: {THEME['text_primary']}; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
<span>📡 LIVE SECURITY FEED</span>
<span style="font-size: 10px; color: #00E676;">● LIVE STREAM</span>
</div>
{''.join(feed_items)}
</div>"""
