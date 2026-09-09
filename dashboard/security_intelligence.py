"""
FedSanitize - Security Intelligence & Zero-Trust Dashboard Page
==============================================================
Presents Team A Security Intelligence Subsystems:
- Feature 1: Dynamic Client Trust Engine
- Feature 2: Multi-Signal Adaptive Defense Orchestrator
- Feature 3: Zero-Trust JWT Authentication & RBAC Gateway
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from security_intelligence import (
    PipelineAdapter,
    ClientTrustEngine,
    AdaptiveDefenseOrchestrator,
    ThreatLevel,
    RoutingAction,
)


def render_security_intelligence_page(session_state):
    st.markdown(
        "<h2 style='color:#38FBDB;font-family:monospace;margin-bottom:4px;'>"
        "🎖️ SECURITY INTELLIGENCE & ZERO-TRUST CONSOLE</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Team A Autonomous Defense Framework: Stateful Client Reputation (F1), "
        "Multi-Signal Threat Orchestration (F2), and Zero-Trust JWT Access Control (F3)."
    )

    history = session_state.get("history", [])
    if not history:
        st.info("No simulation history available. Please run or load a demo from the Overview / Arena page.")
        return

    # Use or initialize persistent Trust Engine and Orchestrator
    if "st_trust_engine" not in session_state:
        session_state["st_trust_engine"] = ClientTrustEngine()
    if "st_orchestrator" not in session_state:
        session_state["st_orchestrator"] = AdaptiveDefenseOrchestrator()

    trust_engine: ClientTrustEngine = session_state["st_trust_engine"]
    orchestrator: AdaptiveDefenseOrchestrator = session_state["st_orchestrator"]

    # Process all history records sequentially to build current trust state
    for rec in history:
        contexts, _ = PipelineAdapter.from_round_record(rec)
        for ctx in contexts:
            trust_engine.update(ctx)
        orchestrator.evaluate_round(contexts, trust_engine=trust_engine)

    last_decision = orchestrator.get_last_decision()
    dec_dict = last_decision.to_dict() if last_decision else {}
    summary = trust_engine.get_summary()

    # Top KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Active Threat Tier", dec_dict.get("threat_level", "LOW"), f"Score: {dec_dict.get('threat_score', 0.0):.2f}")
    with col2:
        st.metric("Defense Action", dec_dict.get("routing_action", "STANDARD"))
    with col3:
        st.metric("Escalated Alert", "🚨 YES" if dec_dict.get("escalation_triggered") else "✅ NORMAL")
    with col4:
        st.metric("Avg Trust Rating", f"{summary.get('average_trust', 95.0):.1f} / 100")
    with col5:
        st.metric("Quarantined Nodes", f"{summary.get('quarantined_count', 0)} / {summary.get('total_clients', 10)}")

    st.markdown("---")

    tab_trust, tab_adaptive, tab_auth = st.tabs([
        "🛡️ Client Trust Spectrum (Feature 1)",
        "🧭 Adaptive Defense Orchestrator (Feature 2)",
        "🔐 Zero-Trust Authentication (Feature 3)",
    ])

    # -------------------------------------------------------------
    # TAB 1: CLIENT TRUST SPECTRUM
    # -------------------------------------------------------------
    with tab_trust:
        st.markdown("### 🛡️ Client Trust Engine (Reputation & Memory)")
        st.markdown("Tracks persistent edge client reliability across rounds, penalizing gradient clipping and latent cluster anomalies while rewarding clean participation.")

        all_clients = trust_engine.get_all_clients()
        if all_clients:
            trust_rows = []
            for c in all_clients:
                trust_rows.append({
                    "Client ID": c.client_id,
                    "Trust Score": round(c.trust_score, 1),
                    "Reputation Tier": c.trust_level,
                    "L1 Anomalies": c.anomaly_count,
                    "MARS Incidents": c.mars_incident_count,
                    "Clean Rounds": c.clean_round_count,
                    "Total Incidents": c.incident_count,
                })
            df_trust = pd.DataFrame(trust_rows)

            fig_trust = px.bar(
                df_trust,
                x="Client ID",
                y="Trust Score",
                color="Reputation Tier",
                color_discrete_map={
                    "TRUSTED": "#20D9A0",
                    "MONITORED": "#38FBDB",
                    "SUSPICIOUS": "#F5A623",
                    "HIGH_RISK": "#FF3B5C",
                    "QUARANTINED": "#D32F2F",
                },
                title="Dynamic Edge Client Trust Score Distribution",
                range_y=[0, 100],
            )
            fig_trust.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(12,30,62,0.6)",
                font=dict(color="#E8F1F5", family="monospace"),
            )
            st.plotly_chart(fig_trust, use_container_width=True)

            st.dataframe(df_trust, use_container_width=True)

            # Detailed Dossier Inspector
            st.markdown("#### 🔍 Client Dossier & Penalty Timeline")
            selected_cid = st.selectbox("Select Edge Client to inspect history:", [c.client_id for c in all_clients], index=0)
            rec = trust_engine.get_client(selected_cid)
            if rec:
                c1, c2, c3 = st.columns(3)
                c1.info(f"**Trust Rating:** {rec.trust_score:.1f} / 100 ({rec.trust_level})")
                c2.warning(f"**Incidents:** L1={rec.anomaly_count} | MARS={rec.mars_incident_count}")
                c3.success(f"**Consecutive Clean Rounds:** {rec.clean_round_count}")

                if rec.history:
                    hist_data = [
                        {
                            "Round": h.get("round_id"),
                            "Adjustment": f"{'+' if h.get('delta', 0) >= 0 else ''}{h.get('delta', 0):.1f} pts",
                            "Score After": f"{h.get('new_score', 0):.1f}",
                            "Tier After": h.get("trust_level_after"),
                            "Reason": h.get("reason"),
                        }
                        for h in rec.history
                    ]
                    st.table(pd.DataFrame(hist_data))
                else:
                    st.caption("No historical adjustments recorded yet.")

    # -------------------------------------------------------------
    # TAB 2: ADAPTIVE DEFENSE ORCHESTRATOR
    # -------------------------------------------------------------
    with tab_adaptive:
        st.markdown("### 🧭 Adaptive Defense Orchestrator (Multi-Signal Risk)")
        st.markdown("Aggregates signals from Layer 1 (Euclidean norm / coordinate bounds), Layer 2 (MARS latent representation clustering), and validation accuracy to steer pipeline routing.")

        if last_decision:
            st.markdown(f"**Current Routing Policy:** `{last_decision.routing_action.value}`")
            st.markdown(f"**Decision Rationale:** `{last_decision.reason}`")
            st.markdown(f"**Recommended Aggregation:** `{last_decision.aggregation_recommendation}`")
            st.markdown(f"**Decision Confidence:** `{last_decision.confidence * 100:.1f}%`")

        st.markdown("#### 📜 Multi-Round Defense Routing History")
        decision_history = orchestrator.get_history()
        if decision_history:
            dec_rows = [
                {
                    "Round": d.round_id,
                    "Threat Level": d.threat_level.value,
                    "Threat Score": f"{d.threat_score:.2f}",
                    "Action": d.routing_action.value,
                    "Escalated": "🚨 YES" if d.escalation_triggered else "NO",
                    "Confidence": f"{d.confidence * 100:.0f}%",
                    "Rationale": d.reason,
                }
                for d in decision_history
            ]
            st.dataframe(pd.DataFrame(dec_rows), use_container_width=True)
        else:
            st.caption("Run rounds to accumulate decision history.")

    # -------------------------------------------------------------
    # TAB 3: ZERO-TRUST AUTHENTICATION & RBAC
    # -------------------------------------------------------------
    with tab_auth:
        st.markdown("### 🔐 Zero-Trust Authentication Gateway (JWT & RBAC)")
        st.markdown("Secures central API endpoints and edge model uploads via JSON Web Tokens (HS256) and Role-Based Access Control.")

        ac1, ac2 = st.columns(2)
        with ac1:
            st.markdown("#### 🔑 Gateway Configuration & Specs")
            st.markdown(
                "- **Algorithm:** HS256 JWT with HMAC-SHA256 signature<br/>"
                "- **Access Token TTL:** 30 minutes<br/>"
                "- **Refresh Token TTL:** 7 days<br/>"
                "- **Rate Limiting:** Sliding window brute-force protection (10 attempts / min)<br/>"
                "- **Admin Scope:** Full telemetry, quarantine override, policy reconfiguration<br/>"
                "- **Client Scope:** Gradient submission, heartbeat, local trust telemetry",
                unsafe_allow_html=True,
            )

        with ac2:
            st.markdown("#### 🛡️ Interactive Auth Simulator")
            role_choice = st.radio("Select Role to test:", ["Central Administrator", "Edge Client (C0)"], horizontal=True)
            if role_choice == "Central Administrator":
                st.code("POST /auth/login\nContent-Type: application/x-www-form-urlencoded\nusername=admin&password=admin123", language="http")
                if st.button("Simulate Admin Login Token Grant"):
                    st.success("✅ Token Issued: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... [Role: admin]")
            else:
                st.code("POST /auth/client-login\nContent-Type: application/json\n{\"client_id\": \"C0\", \"client_secret\": \"clientsecret123\"}", language="http")
                if st.button("Simulate Client Login Token Grant"):
                    st.success("✅ Token Issued: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... [Role: client, client_id: C0]")
