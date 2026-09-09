"""
FedSantize Components — Client Forensics Inspector
==================================================
Drilldown card exposing raw, non-fabricated metrics for any selected client.
Grounded in pages 36-37 of the specification.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from ..network.graph_styles import THEME


def render_client_forensics_card(
    client_id: str,
    record: Dict[str, Any],
    mars_info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Renders detailed client forensic dossier in dark cyber styling.
    """
    attack_type = record.get("attack_type", "BENIGN")
    is_malicious = record.get("is_malicious", False)
    norm = float(record.get("update_norm", 0.0))
    cos_sim = float(record.get("cosine_similarity", 1.0))
    l1_status = record.get("layer1_status", "PASS")
    l1_reason = record.get("layer1_reason", "NORMAL_UPDATE")

    # MARS metrics
    mars_res = mars_info or {}
    cbe = float(mars_res.get("cbe_concentration_ratio", 0.0))
    cluster_id = mars_res.get("cluster_id", 0)
    mars_status = record.get("mars_status", mars_res.get("status", "PASS"))
    mars_reason = record.get("mars_reason", mars_res.get("reason", "BENIGN"))

    final_status = record.get("final_status", "TRUSTED")
    is_quarantined = final_status == "QUARANTINED"
    status_badge_bg = THEME["quarantine"] if is_quarantined else THEME["safe"]

    decision_bg = "rgba(255, 82, 82, 0.1)" if is_quarantined else "rgba(0, 230, 118, 0.1)"

    return f"""<div style="background-color: {THEME['card_background']}; border: 1px solid {THEME['border_color']}; border-radius: 8px; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {THEME['border_color']}; padding-bottom: 10px; margin-bottom: 12px;">
<div>
<span style="font-size: 16px; font-weight: bold; color: {THEME['text_primary']};">CLIENT FORENSIC DOSSIER: {client_id}</span>
<span style="margin-left: 8px; font-size: 11px; background: {'#FF1744' if is_malicious else '#238636'}; color: #FFF; padding: 2px 8px; border-radius: 4px;">
{'MALICIOUS' if is_malicious else 'HONEST'}
</span>
</div>
<div style="background: {status_badge_bg}; color: #0D1117; font-weight: bold; font-size: 12px; padding: 3px 10px; border-radius: 4px;">
{final_status}
</div>
</div>
<div style="margin-bottom: 12px;">
<div style="font-size: 11px; color: {THEME['text_secondary']}; text-transform: uppercase;">Adversarial Attack Profile</div>
<div style="font-size: 14px; font-weight: bold; color: #58A6FF;">{attack_type}</div>
</div>
<div style="background: #1C2128; border: 1px solid #30363D; border-radius: 6px; padding: 10px; margin-bottom: 10px;">
<div style="font-size: 12px; font-weight: bold; color: {THEME['processing']}; margin-bottom: 6px;">
LAYER 1 — STATISTICAL ANOMALY FILTER
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
<div><span style="color: {THEME['text_secondary']};">Update Norm:</span> <b style="color: #F0F6FC;">{norm:.4f}</b></div>
<div><span style="color: {THEME['text_secondary']};">Cosine Similarity:</span> <b style="color: #F0F6FC;">{cos_sim:.4f}</b></div>
<div><span style="color: {THEME['text_secondary']};">L1 Status:</span> <b style="color: {'#FF5252' if l1_status == 'FLAGGED' else '#00E676'};">{l1_status}</b></div>
<div><span style="color: {THEME['text_secondary']};">L1 Diagnostic:</span> <span style="color: #8B949E;">{l1_reason}</span></div>
</div>
</div>
<div style="background: #1C2128; border: 1px solid #30363D; border-radius: 6px; padding: 10px; margin-bottom: 10px;">
<div style="font-size: 12px; font-weight: bold; color: {THEME['processing']}; margin-bottom: 6px;">
LAYER 2 — MARS DEEP REPRESENTATION FORENSICS
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
<div><span style="color: {THEME['text_secondary']};">CBE Ratio:</span> <b style="color: #F0F6FC;">{cbe:.4f} ({cbe*100:.1f}%)</b></div>
<div><span style="color: {THEME['text_secondary']};">Cluster ID:</span> <b style="color: #F0F6FC;">{cluster_id if cluster_id is not None else 'N/A'}</b></div>
<div><span style="color: {THEME['text_secondary']};">MARS Status:</span> <b style="color: {'#FF5252' if mars_status == 'FLAGGED' else '#00E676'};">{mars_status}</b></div>
<div><span style="color: {THEME['text_secondary']};">MARS Reason:</span> <span style="color: #8B949E;">{mars_reason}</span></div>
</div>
</div>
<div style="background: {decision_bg}; border: 1px solid {status_badge_bg}; border-radius: 6px; padding: 10px;">
<div style="font-size: 11px; font-weight: bold; color: {status_badge_bg}; text-transform: uppercase;">FINAL SECURITY ACTION</div>
<div style="font-size: 13px; font-weight: bold; color: {THEME['text_primary']}; margin-top: 2px;">
{'QUARANTINED & ISOLATED' if is_quarantined else 'CLEARED FOR ROBUST AGGREGATION'}
</div>
<div style="font-size: 12px; color: {THEME['text_secondary']}; margin-top: 4px;">
Reason: {l1_reason if l1_status == 'FLAGGED' else mars_reason}
</div>
</div>
</div>"""
