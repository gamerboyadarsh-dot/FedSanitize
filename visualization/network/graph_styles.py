"""
FedSantize Visualization — Network Graph Styles
===============================================
Cybersecurity Command Center color palette and typography tokens.
Adheres strictly to Phase UI & Color Semantics specifications:
  - SAFE: Green (#00E676)
  - SUSPICIOUS: Amber (#FFB300)
  - MALICIOUS: Crimson Red (#FF1744)
  - PROCESSING: Electric Cyan (#00E5FF)
  - QUARANTINE: Muted Slate Red (#78909C)
  - SERVER: Deep Cyber Violet (#7C4DFF)
"""

from __future__ import annotations
from typing import Dict, Any

THEME = {
    "background": "#0D1117",
    "card_background": "#161B22",
    "border_color": "#30363D",
    "text_primary": "#F0F6FC",
    "text_secondary": "#8B949E",
    "text_muted": "#6E7681",
    
    # Semantic statuses
    "safe": "#00E676",
    "suspicious": "#FFB300",
    "malicious": "#FF1744",
    "processing": "#00E5FF",
    "quarantine": "#FF5252",
    "quarantined_muted": "#78909C",
    "server": "#7C4DFF",
    "accent": "#58A6FF",
    
    # Network links
    "link_clean": "rgba(0, 230, 118, 0.35)",
    "link_malicious": "rgba(255, 23, 68, 0.65)",
    "link_scanning": "rgba(0, 229, 255, 0.45)",
    "link_severed": "rgba(120, 144, 156, 0.15)",
}

STATE_COLOR_MAP: Dict[str, str] = {
    "NORMAL": THEME["safe"],
    "TRAINING": THEME["processing"],
    "ATTACKING": THEME["malicious"],
    "SENDING_UPDATE": THEME["processing"],
    "WAITING": THEME["text_secondary"],
    "SCANNING": THEME["processing"],
    "SUSPICIOUS": THEME["suspicious"],
    "QUARANTINED": THEME["quarantine"],
    "TRUSTED": THEME["safe"],
    "AGGREGATED": THEME["safe"],
}

STATE_ICON_MAP: Dict[str, str] = {
    "NORMAL": "🟢",
    "TRAINING": "⚡",
    "ATTACKING": "🔴",
    "SENDING_UPDATE": "📤",
    "WAITING": "⏳",
    "SCANNING": "🔍",
    "SUSPICIOUS": "⚠️",
    "QUARANTINED": "🚫",
    "TRUSTED": "🛡️",
    "AGGREGATED": "✨",
}
