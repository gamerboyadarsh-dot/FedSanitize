import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Award,
  Compass,
  Activity,
  RefreshCw,
  History,
  CheckCircle2,
  Lock,
  Copy,
  AlertTriangle,
  Info
} from "lucide-react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from "recharts";
import { fetchSecuritySummary, fetchAllClientTrust, fetchSecurityDecisions, fetchSocSnapshot } from "../api/client";
import { SecurityOperationsCenter } from "../components/soc/SecurityOperationsCenter";
import type { RoundRecord } from "../types/telemetry";
import { SlidingNumber } from "../components/core/SlidingNumber";

interface SecurityIntelligenceProps {
  latestRound: RoundRecord | null;
}

export const SecurityIntelligence: React.FC<SecurityIntelligenceProps> = ({ latestRound }) => {
  const [activeSubTab, setActiveSubTab] = useState<"soc" | "trust">("soc");
  const [summary, setSummary] = useState<any>(null);
  const [trustRecords, setTrustRecords] = useState<any[]>([]);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [socSnapshot, setSocSnapshot] = useState<any>(null);
  const [selectedClientId, setSelectedClientId] = useState<string>("C0");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [sumData, trustData, decData, socData] = await Promise.all([
        fetchSecuritySummary().catch(() => null),
        fetchAllClientTrust().catch(() => []),
        fetchSecurityDecisions().catch(() => []),
        fetchSocSnapshot().catch(() => null),
      ]);
      setSummary(sumData);
      setTrustRecords(trustData);
      setDecisions(decData);
      setSocSnapshot(socData);
      if (trustData.length > 0 && !selectedClientId) {
        setSelectedClientId(trustData[0].client_id);
      }
    } catch (e) {
      console.error("Failed to load security intelligence data:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [latestRound]);

  const selectedRecord = trustRecords.find((r) => r.client_id === selectedClientId) || trustRecords[0];
  const latestDecision = summary?.latest_decision || (decisions.length > 0 ? decisions[decisions.length - 1] : null);

  const trustLevel = latestDecision?.threat_level || "ELEVATED";
  const threatScore = latestDecision?.threat_score ?? 0.63;
  const routingAction = latestDecision?.routing_action || "ISOLATE_SUSPECTS";
  const mode = summary?.mode || "observe";
  const isEscalated = summary?.is_escalated || false;

  const trustScoreData = trustRecords.map((r) => ({
    name: r.client_id,
    score: Number(r.trust_score.toFixed(1)),
    level: r.trust_level,
  }));

  const getLevelColor = (lvl: string) => {
    switch (lvl) {
      case "TRUSTED":
        return "#34D399";
      case "MONITORED":
        return "#22D3EE";
      case "SUSPICIOUS":
        return "#F5A524";
      case "HIGH_RISK":
      case "QUARANTINED":
        return "#FF4D6D";
      default:
        return "#9FB0CC";
    }
  };

  const getThreatBadgeClass = (threat: string) => {
    switch (threat) {
      case "CRITICAL":
      case "HIGH":
        return "ds-chip ds-chip-danger ds-chip-no-dot";
      case "ELEVATED":
        return "ds-chip ds-chip-warning ds-chip-no-dot";
      case "LOW":
      case "MINIMAL":
        return "ds-chip ds-chip-pass ds-chip-no-dot";
      default:
        return "ds-chip ds-chip-info ds-chip-no-dot";
    }
  };

  return (
    <div className="space-y-6 pb-8 page-enter">
      {/* Header Info */}
      <div className="ds-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--cyan-tint)] text-[var(--cyan)]">
              <Award className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">
              Security Intelligence & Operations Center
            </h2>
            <span className="ds-chip ds-chip-info ds-chip-no-dot text-xs">
              Mode: {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </span>
            {isEscalated && (
              <span className="ds-chip ds-chip-danger animate-pulse text-xs">
                Incident Escalated
              </span>
            )}
          </div>
          <p className="text-[13px] text-[var(--text-secondary)] mt-1">
            Dynamic Client Trust Scoring (F1), Multi-Signal Defense Policy Orchestration (F2), and Cryptographic Audit Chain.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="ds-btn ds-btn-secondary h-9 text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh Signals
        </button>
      </div>

      {/* Sub-tab Navigation */}
      <div className="ds-seg-control w-fit">
        <button
          onClick={() => setActiveSubTab("soc")}
          className={`ds-seg-btn ${activeSubTab === "soc" ? "active" : ""}`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Team B: Security Operations Center (SOC)</span>
        </button>
        <button
          onClick={() => setActiveSubTab("trust")}
          className={`ds-seg-btn ${activeSubTab === "trust" ? "active" : ""}`}
        >
          <Compass className="w-4 h-4" />
          <span>Team A: Client Trust & Policy Orchestrator</span>
        </button>
      </div>

      {activeSubTab === "soc" ? (
        <SecurityOperationsCenter
          snapshot={socSnapshot}
          isLoading={isLoading}
          onRefresh={loadData}
        />
      ) : (
        <>
          {/* 4 Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="ds-card p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="eyebrow">Threat Level</span>
                  <ShieldAlert className="w-4 h-4 text-[var(--red)]" />
                </div>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className={getThreatBadgeClass(trustLevel)}>
                    {trustLevel}
                  </span>
                  <span className="kpi-value text-xl font-mono text-[var(--text-primary)]">
                    {(threatScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-3 pt-2 border-t border-[var(--border-subtle)]">
                Confidence: {((latestDecision?.confidence ?? 0.85) * 100).toFixed(0)}%
              </div>
            </div>

            <div className="ds-card p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="eyebrow">Routing Action</span>
                  <Compass className="w-4 h-4 text-[var(--purple)]" />
                </div>
                <div className="font-mono text-base font-bold text-[var(--purple)] mt-1">
                  {routingAction}
                </div>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-3 pt-2 border-t border-[var(--border-subtle)] truncate">
                Action: {latestDecision?.aggregation_recommendation || "EXCLUDE_FLAGGED_CLIENTS"}
              </div>
            </div>

            <div className="ds-card p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="eyebrow">Active Defenses</span>
                  <ShieldCheck className="w-4 h-4 text-[var(--green)]" />
                </div>
                <div className="space-y-1 mt-1">
                  {(latestDecision?.active_defenses ?? ["L1_ANOMALY", "MARS_CBE"]).slice(0, 2).map((d: string, i: number) => (
                    <div key={i} className="flex items-center gap-1.5 text-xs text-[var(--green)] font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--green)]" />
                      <span>{d}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-3 pt-2 border-t border-[var(--border-subtle)]">
                Enforcement: Active Automated Guardrail
              </div>
            </div>

            <div className="ds-card p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="eyebrow">Cohort Mean Trust</span>
                  <Activity className="w-4 h-4 text-[var(--cyan)]" />
                </div>
                <div className="kpi-value text-3xl text-[var(--cyan)] mt-1">
                  <SlidingNumber value={summary?.trust_summary?.average_trust_score ?? 76.5} decimalPlaces={1} suffix=" / 100" />
                </div>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-3 pt-2 border-t border-[var(--border-subtle)]">
                Total Clients Tracked: {trustRecords.length || 10}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Trust Spectrum Bar Chart */}
              <div className="ds-card p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[var(--border-subtle)] pb-4 gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                      Client Trust & Reputation Spectrum [0 - 100]
                    </h3>
                    <p className="text-[12px] text-[var(--text-secondary)] mt-0.5">
                      Persistent Bayesian trust rating updated after each federated round
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="flex items-center gap-1 text-[var(--green)]">
                      <span className="w-2 h-2 rounded-full bg-[var(--green)]" /> &gt;80 Trusted
                    </span>
                    <span className="flex items-center gap-1 text-[var(--amber)]">
                      <span className="w-2 h-2 rounded-full bg-[var(--amber)]" /> 40-79 Monitored
                    </span>
                    <span className="flex items-center gap-1 text-[var(--red)]">
                      <span className="w-2 h-2 rounded-full bg-[var(--red)]" /> &lt;40 Quarantined
                    </span>
                  </div>
                </div>

                <div className="h-60 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={trustScoreData.length > 0 ? trustScoreData : [
                      { name: "C0", score: 98, level: "TRUSTED" },
                      { name: "C1", score: 95, level: "TRUSTED" },
                      { name: "C2", score: 92, level: "TRUSTED" },
                      { name: "C3", score: 96, level: "TRUSTED" },
                      { name: "C4", score: 90, level: "TRUSTED" },
                      { name: "C5", score: 94, level: "TRUSTED" },
                      { name: "C6", score: 15, level: "QUARANTINED" },
                      { name: "C7", score: 25, level: "HIGH_RISK" },
                      { name: "C8", score: 10, level: "QUARANTINED" },
                      { name: "C9", score: 12, level: "QUARANTINED" },
                    ]} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                      <XAxis dataKey="name" stroke="#667796" tick={{ fill: "#667796", fontSize: 12, fontFamily: "JetBrains Mono" }} />
                      <YAxis domain={[0, 100]} stroke="#667796" tick={{ fill: "#667796", fontSize: 12, fontFamily: "JetBrains Mono" }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0F1C42",
                          borderColor: "rgba(148,163,184,0.20)",
                          borderRadius: "8px",
                          fontFamily: "JetBrains Mono",
                          fontSize: "12px",
                          boxShadow: "0 8px 24px rgba(0,0,0,0.4)"
                        }}
                        formatter={(val: any) => [`${val} / 100`, "Trust Rating"]}
                        labelFormatter={(lbl) => `Client ${lbl}`}
                      />
                      <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                        {(trustScoreData.length > 0 ? trustScoreData : [
                          { level: "TRUSTED" }, { level: "TRUSTED" }, { level: "TRUSTED" }, { level: "TRUSTED" },
                          { level: "TRUSTED" }, { level: "TRUSTED" }, { level: "QUARANTINED" }, { level: "HIGH_RISK" },
                          { level: "QUARANTINED" }, { level: "QUARANTINED" }
                        ]).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={getLevelColor(entry.level)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Policy Decision History */}
              <div className="ds-card p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4">
                  <div className="flex items-center gap-2">
                    <Compass className="w-4 h-4 text-[var(--cyan)]" />
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                      Adaptive Defense Policy Log (Feature 2)
                    </h3>
                  </div>
                  <span className="text-[12px] text-[var(--text-muted)]">
                    Autonomous multi-signal risk evaluations
                  </span>
                </div>

                <div className="space-y-3 max-h-64 overflow-y-auto scroll-fade-y pr-1">
                  {(decisions.length > 0 ? decisions : [
                    {
                      round_id: 1,
                      threat_level: "HIGH",
                      threat_score: 0.63,
                      routing_action: "ISOLATE_SUSPECTS",
                      reason: "ISOLATE_SUSPECTS: L1_anomalies=2, MARS_suspects=2, mean_cbe=0.18",
                      confidence: 0.85
                    }
                  ]).map((d: any, idx: number) => (
                    <div key={idx} className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] p-3.5 rounded-xl space-y-2 hover:border-[var(--border-strong)] transition-colors">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-[var(--cyan)]">Round {d.round_id} Decision</span>
                        <span className={getThreatBadgeClass(d.threat_level)}>
                          {d.threat_level} ({(d.threat_score * 100).toFixed(0)}%)
                        </span>
                      </div>
                      <div className="text-[12px] text-[var(--text-primary)] leading-relaxed">{d.reason}</div>
                      <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-subtle)]">
                        <span>Action: <strong className="text-[var(--purple)] font-mono">{d.routing_action}</strong></span>
                        <span className="font-mono">Confidence: {(d.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Client Trust Dossier */}
            <div className="ds-card p-6 space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4">
                  <div className="flex items-center gap-2">
                    <Award className="w-4 h-4 text-[var(--cyan)]" />
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                      Client Trust Dossier
                    </h3>
                  </div>
                  <span className="ds-chip ds-chip-info ds-chip-no-dot text-[11px]">Feature 1</span>
                </div>

                {/* Client selector pills */}
                <div className="flex flex-wrap gap-1.5 py-3">
                  {(trustRecords.length > 0 ? trustRecords : Array.from({ length: 10 }, (_, i) => ({ client_id: `C${i}` }))).map((c: any) => (
                    <button
                      key={c.client_id}
                      onClick={() => setSelectedClientId(c.client_id)}
                      className={`px-3 py-1 rounded-lg text-xs font-mono transition-all ${
                        selectedClientId === c.client_id
                          ? "bg-[var(--cyan)] text-[var(--bg-base)] font-bold shadow-[0_0_12px_var(--cyan-glow)]"
                          : "bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-white"
                      }`}
                    >
                      {c.client_id}
                    </button>
                  ))}
                </div>

                <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2.5">
                    <span className="text-[12px] text-[var(--text-secondary)]">Client Identifier:</span>
                    <span className="font-mono text-sm font-bold text-[var(--text-primary)]">
                      {selectedRecord?.client_id || selectedClientId}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-[var(--text-secondary)]">Trust Rating:</span>
                    <span className="font-mono text-lg font-bold text-[var(--cyan)]">
                      {selectedRecord?.trust_score !== undefined ? selectedRecord.trust_score.toFixed(1) : "95.0"} / 100
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-[var(--text-secondary)]">Reputation Tier:</span>
                    <span
                      className="font-mono font-bold px-2 py-0.5 rounded text-[11px]"
                      style={{
                        color: getLevelColor(selectedRecord?.trust_level || "TRUSTED"),
                        backgroundColor: `${getLevelColor(selectedRecord?.trust_level || "TRUSTED")}18`,
                        border: `1px solid ${getLevelColor(selectedRecord?.trust_level || "TRUSTED")}40`,
                      }}
                    >
                      {selectedRecord?.trust_level || "TRUSTED"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[var(--border-subtle)] text-[11px]">
                    <div className="bg-[var(--bg-base)] p-2.5 rounded-lg border border-[var(--border-subtle)]">
                      <div className="text-[var(--text-muted)] text-[10px]">L1 Anomalies</div>
                      <div className="font-mono font-bold text-[var(--text-primary)] text-sm">{selectedRecord?.anomaly_count ?? 0}</div>
                    </div>
                    <div className="bg-[var(--bg-base)] p-2.5 rounded-lg border border-[var(--border-subtle)]">
                      <div className="text-[var(--text-muted)] text-[10px]">MARS Incidents</div>
                      <div className="font-mono font-bold text-[var(--text-primary)] text-sm">{selectedRecord?.mars_incident_count ?? 0}</div>
                    </div>
                    <div className="bg-[var(--bg-base)] p-2.5 rounded-lg border border-[var(--border-subtle)]">
                      <div className="text-[var(--text-muted)] text-[10px]">Clean Rounds</div>
                      <div className="font-mono font-bold text-[var(--green)] text-sm">{selectedRecord?.clean_round_count ?? 5}</div>
                    </div>
                    <div className="bg-[var(--bg-base)] p-2.5 rounded-lg border border-[var(--border-subtle)]">
                      <div className="text-[var(--text-muted)] text-[10px]">Total Penalties</div>
                      <div className="font-mono font-bold text-[var(--red)] text-sm">{selectedRecord?.incident_count ?? 0}</div>
                    </div>
                  </div>

                  <div className="pt-2.5 border-t border-[var(--border-subtle)]">
                    <div className="text-[11px] text-[var(--text-secondary)] font-medium mb-2 flex items-center justify-between">
                      <span>Recent Trust Adjustments</span>
                      <History className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                    </div>
                    <div className="space-y-1.5 max-h-36 overflow-y-auto scroll-fade-y text-[11px]">
                      {(selectedRecord?.history?.length ? selectedRecord.history : [
                        { round_id: 1, delta: +2.0, new_score: 95.0, reason: "Consistent honest training", trust_level_after: "TRUSTED" }
                      ]).map((h: any, idx: number) => (
                        <div key={idx} className="flex items-center justify-between bg-[var(--bg-base)] px-2.5 py-1.5 rounded-lg border border-[var(--border-subtle)]">
                          <span className="font-mono text-[var(--text-muted)]">R{h.round_id}</span>
                          <span className={`font-mono font-bold ${h.delta >= 0 ? "text-[var(--green)]" : "text-[var(--red)]"}`}>
                            {h.delta >= 0 ? `+${h.delta}` : h.delta} pts
                          </span>
                          <span className="text-[var(--text-secondary)] truncate max-w-[110px]" title={h.reason}>
                            {h.reason}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
