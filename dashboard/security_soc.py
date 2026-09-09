"""
FedSantize Security Operations Center — Streamlit page.

Renders ONLY from a SOCSnapshot (cached summaries). Never retrains a
model, never reruns MARS, never reads model weights. Safe to run
standalone (uses TeamBBundle with demo data) or import `render_soc_page`
into the existing multi-page dashboard once Phase 11 wiring happens.

Standalone run:
    streamlit run dashboard/security_soc.py
"""

import os
import sys
import time

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_intelligence.team_b_bundle import TeamBBundle  # noqa: E402


# --------------------------------------------------------------------------
# Demo data generator — used only in standalone mode, when no orchestrator
# / real pipeline results are wired in yet. Clearly separated so it's easy
# to delete once Phase 11 (main dashboard integration) happens.
# --------------------------------------------------------------------------
def _seed_demo_data(bundle: TeamBBundle) -> None:
    if bundle.posture.timeline():
        return  # already has data (e.g. persisted from a previous run)

    demo_rounds = [
        {"round_id": 1, "evidence": {"layer1_anomaly_score": 0.2}, "signals": {"layer1_severity": 0.2, "mars_severity": 0.1}, "client": "client_1"},
        {"round_id": 2, "evidence": {"mars_severity": 0.8, "layer1_anomaly_score": 0.6}, "signals": {"layer1_severity": 0.6, "mars_severity": 0.8, "incident_severity": 0.5}, "client": "client_3"},
        {"round_id": 3, "evidence": {"attack_confirmed": True, "mars_severity": 0.95}, "signals": {"layer1_severity": 0.7, "mars_severity": 0.95, "incident_severity": 0.9, "malicious_client_ratio": 0.3}, "client": "client_3"},
    ]
    for r in demo_rounds:
        bundle.incident_engine.handle(r["evidence"], round_id=r["round_id"], client_id=r["client"])
        bundle.threat_engine.assess(r["signals"], round_id=r["round_id"])


@st.cache_resource
def _get_bundle() -> TeamBBundle:
    bundle = TeamBBundle(use_disk_persistence=True)
    _seed_demo_data(bundle)
    return bundle


def _severity_color(level: str) -> str:
    return {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🟠",
        "CRITICAL": "🔴",
        "INFO": "🔵",
        "WARNING": "🟡",
    }.get(str(level).upper(), "⚪")


def render_soc_page(bundle: TeamBBundle) -> None:
    st.title("🛡️ FedSantize Security Operations Center")
    st.caption("Threat Intelligence, Incident Response & Federated Security Monitoring")

    snapshot = bundle.snapshot(round_id=None).to_dict()

    if snapshot["warnings"]:
        for w in snapshot["warnings"]:
            st.warning(f"⚠️ {w}")

    # ---- 1. Global Security Posture -----------------------------------
    st.subheader("Global Security Posture")
    ta = snapshot["threat_assessment"] or {}
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("System Status", "MONITORING")
    col2.metric("Threat Level", ta.get("level", "N/A"))
    col3.metric("Threat Score", f"{ta.get('score', 0):.1f} / 100" if ta else "N/A")
    col4.metric("Signal Coverage", f"{ta.get('coverage', 0) * 100:.0f}%" if ta else "N/A")

    if ta.get("missing_signals"):
        with st.expander("Missing signals affecting this score"):
            for m in ta["missing_signals"]:
                st.write(f"- {m}")
    if ta.get("contributing_factors"):
        with st.expander("Score breakdown"):
            for f in ta["contributing_factors"]:
                st.write(f"**{f['name']}** — contribution {f['contribution']:.1f} (value {f['value']}, weight {f['normalized_weight']})")

    st.divider()

    # ---- 2. Client Trust Map -------------------------------------------
    st.subheader("Client Trust Map")
    client_rows = snapshot["client_security_summary"]
    if client_rows:
        st.dataframe(
            [
                {
                    "Client ID": r["client_id"],
                    "Trust Score": r["trust_score"] if r["trust_score"] is not None else "N/A (Team A not connected)",
                    "Trust Level": r["trust_level"] or "N/A",
                    "Quarantined": "🔒 Yes" if r["quarantined"] else "No",
                }
                for r in client_rows
            ],
            use_container_width=True,
        )
    else:
        st.info("No client activity recorded yet.")

    st.divider()

    # ---- 3. Live Incident Feed ------------------------------------------
    st.subheader("Live Incident Feed")
    events = snapshot["recent_events"]
    if events:
        for e in events[:15]:
            ts = time.strftime("%H:%M:%S", time.localtime(e["timestamp"]))
            st.write(f"{_severity_color(e['severity'])} `[{e['severity']}]` **{e['event_type']}** — round {e.get('round_id')}, client `{e.get('client_id')}` — {ts}")
    else:
        st.info("No audit events yet.")

    st.divider()

    # ---- 4. Incident Response Panel -------------------------------------
    st.subheader("Incident Response Panel")
    incidents = snapshot["active_incidents"]
    if incidents:
        st.dataframe(
            [
                {
                    "Client": inc["client_id"],
                    "Severity": inc["severity"],
                    "Action": inc["action"],
                    "Reason": inc["reason"],
                    "Requires Review": "Yes" if inc["requires_review"] else "No",
                }
                for inc in incidents
            ],
            use_container_width=True,
        )
    else:
        st.info("No active incidents.")

    st.divider()

    # ---- 5. Audit Integrity ----------------------------------------------
    st.subheader("Audit Integrity")
    integrity = snapshot["audit_integrity"]
    if integrity.get("valid"):
        st.success(f"✅ AUDIT CHAIN VERIFIED — {integrity.get('total_events', 0)} events")
    else:
        st.error(f"🚨 INTEGRITY ALERT — TAMPERING DETECTED: {integrity.get('message')}")
    st.caption("Note: this chain is tamper-*evident*, not tamper-proof — any edit to stored events is detectable here.")

    st.divider()

    # ---- 6. Security Posture Timeline -------------------------------------
    st.subheader("Security Posture Timeline")
    timeline = snapshot["security_timeline"]
    if timeline:
        chart_data = {
            "round": [t["round_id"] for t in timeline],
            "threat_score": [t["threat_score"] or 0 for t in timeline],
        }
        st.line_chart(chart_data, x="round", y="threat_score")
    else:
        st.info("Not enough rounds yet to plot a timeline.")


def main():
    st.set_page_config(page_title="FedSantize SOC", page_icon="🛡️", layout="wide")
    bundle = _get_bundle()
    render_soc_page(bundle)


if __name__ == "__main__":
    main()
