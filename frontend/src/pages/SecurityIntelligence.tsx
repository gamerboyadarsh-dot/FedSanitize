import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Award,
  Compass,
  Activity,
  RefreshCw,
  History
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
import { AnimatedGroup } from "../components/core/AnimatedGroup";
import { GlowEffect } from "../components/core/GlowEffect";

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
        return "#20D9A0";
      case "MONITORED":
        return "#38FBDB";
      case "SUSPICIOUS":
        return "#F5A623";
      case "HIGH_RISK":
      case "QUARANTINED":
        return "#FF3B5C";
      default:
        return "#7B8AA3";
    }
  };

  const getThreatBadge = (threat: string) => {
    switch (threat) {
      case "CRITICAL":
      case "HIGH":
        return "text-accent-danger bg-accent-danger/10 border-accent-danger/30";
      case "ELEVATED":
        return "text-accent-warning bg-accent-warning/10 border-accent-warning/30";
      case "LOW":
      case "MINIMAL":
        return "text-accent-safe bg-accent-safe/10 border-accent-safe/30";
      default:
        return "text-primary bg-primary/10 border-primary/30";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-surface border border-border rounded-xl p-5 threat-card">
        <div>
          <div className="flex items-center gap-2.5">
            <Award className="w-5 h-5 text-primary" />
            <h2 className="text-base font-mono font-bold uppercase tracking-wider text-text-primary">
              Security Intelligence & Operations Center
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-primary/10 border border-primary/30 text-primary uppercase font-bold">
              Mode: {mode}
            </span>
            {isEscalated && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent-danger/20 border border-accent-danger text-accent-danger uppercase font-bold animate-pulse">
                Incident Escalated
              </span>
            )}
          </div>
          <p className="text-xs text-text-secondary font-mono mt-1">
            Dynamic Client Trust Scoring (F1), Multi-Signal Defense (F2), and Cryptographic SOC Audit (Team B).
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={isLoading}
          className="threat-btn-secondary h-8 px-3 rounded-lg text-xs font-mono flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh Signals
        </button>
      </div>

      {/* Sub-tab Navigation */}
      <div className="flex items-center gap-2 border-b border-border/80 pb-3">
        <button
          onClick={() => setActiveSubTab("soc")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-2 transition-all ${
            activeSubTab === "soc"
              ? "bg-primary text-black shadow-glow-cyan"
              : "bg-surface text-text-secondary border border-border hover:text-white"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          🛡️ Team B: Security Operations Center (SOC)
        </button>
        <button
          onClick={() => setActiveSubTab("trust")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-2 transition-all ${
            activeSubTab === "trust"
              ? "bg-primary text-black shadow-glow-cyan"
              : "bg-surface text-text-secondary border border-border hover:text-white"
          }`}
        >
          <Award className="w-3.5 h-3.5" />
          🎖️ Team A: Client Trust & Policy Orchestrator
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
          <AnimatedGroup className="grid grid-cols-1 md:grid-cols-4 gap-4">

        <GlowEffect glowColor="rgba(56, 251, 219, 0.4)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Threat Level</span>
                <ShieldAlert className="w-4 h-4 text-primary" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className={`text-xl font-mono font-bold px-2 py-0.5 rounded border text-xs ${getThreatBadge(trustLevel)}`}>
                  {trustLevel}
                </span>
                <span className="text-xs font-mono text-text-secondary">
                  Score: {(threatScore * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50">
              Confidence: {((latestDecision?.confidence ?? 0.85) * 100).toFixed(0)}%
            </div>
          </div>
        </GlowEffect>

        <GlowEffect glowColor="rgba(142, 82, 245, 0.4)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Routing Action</span>
                <Compass className="w-4 h-4 text-secondary" />
              </div>
              <div className="text-sm font-mono font-bold text-secondary">
                {routingAction}
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50">
              Action: {latestDecision?.aggregation_recommendation || "EXCLUDE_FLAGGED_CLIENTS"}
            </div>
          </div>
        </GlowEffect>

        <GlowEffect glowColor="rgba(32, 217, 160, 0.4)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Active Defenses</span>
                <ShieldCheck className="w-4 h-4 text-accent-safe" />
              </div>
              <div className="text-xs font-mono text-text-primary font-bold space-y-1">
                {(latestDecision?.active_defenses ?? ["L1_ANOMALY", "MARS_CBE", "TRIMMED_MEAN"]).slice(0, 2).map((d: string, i: number) => (
                  <div key={i} className="flex items-center gap-1.5 text-accent-safe">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-safe" />
                    <span>{d}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50">
              Enforcement: Non-binding Observer
            </div>
          </div>
        </GlowEffect>

        <GlowEffect glowColor="rgba(56, 251, 219, 0.4)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Cohort Mean Trust</span>
                <Activity className="w-4 h-4 text-primary" />
              </div>
              <div className="text-2xl font-mono font-bold text-primary">
                <SlidingNumber value={summary?.trust_summary?.average_trust_score ?? 76.5} decimalPlaces={1} suffix=" / 100" />
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50">
              Total Clients Tracked: {trustRecords.length || 10}
            </div>
          </div>
        </GlowEffect>
      </AnimatedGroup>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-surface border border-border rounded-xl p-5 threat-card space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <div>
                <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                  Client Trust & Reputation Spectrum [0 - 100]
                </h3>
                <p className="text-xs text-text-secondary font-mono">
                  Real-time persistent trust rating calculated by Feature 1 TrustEngine.
                </p>
              </div>
              <div className="flex items-center gap-3 text-[11px] font-mono">
                <span className="flex items-center gap-1 text-accent-safe">
                  <span className="w-2 h-2 rounded-full bg-accent-safe" /> &gt;80 Trusted
                </span>
                <span className="flex items-center gap-1 text-accent-warning">
                  <span className="w-2 h-2 rounded-full bg-accent-warning" /> 40-79 Suspicious
                </span>
                <span className="flex items-center gap-1 text-accent-danger">
                  <span className="w-2 h-2 rounded-full bg-accent-danger" /> &lt;20 Quarantined
                </span>
              </div>
            </div>

            <div className="h-56 w-full font-mono text-xs">
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
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(56, 251, 219, 0.1)" />
                  <XAxis dataKey="name" stroke="#7B8AA3" tick={{ fill: "#7B8AA3" }} />
                  <YAxis domain={[0, 100]} stroke="#7B8AA3" tick={{ fill: "#7B8AA3" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0C1E3E",
                      borderColor: "rgba(56, 251, 219, 0.3)",
                      borderRadius: "8px",
                      fontFamily: "monospace",
                      color: "#E8F1F5"
                    }}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
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

          <div className="bg-surface border border-border rounded-xl p-5 threat-card space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <div className="flex items-center gap-2">
                <Compass className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                  Adaptive Defense Policy History (Feature 2)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-text-secondary">
                Autonomous multi-signal risk evaluations
              </span>
            </div>

            <div className="space-y-2.5 max-h-64 overflow-y-auto font-mono text-xs pr-1">
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
                <div key={idx} className="bg-background border border-border/70 p-3 rounded-lg space-y-1.5 hover:border-primary/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-primary">Round {d.round_id} Decision</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded border font-bold ${getThreatBadge(d.threat_level)}`}>
                      {d.threat_level} ({(d.threat_score * 100).toFixed(0)}%)
                    </span>
                  </div>
                  <div className="text-text-primary text-[11px]">{d.reason}</div>
                  <div className="flex items-center justify-between text-[10px] text-text-secondary pt-1 border-t border-border/40">
                    <span>Action: <strong className="text-secondary">{d.routing_action}</strong></span>
                    <span>Confidence: {(d.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-5 threat-card space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
              <Award className="w-4 h-4 text-primary" />
              Client Trust Dossier
            </h3>
            <span className="text-xs font-mono text-text-secondary">Feature 1</span>
          </div>

          <div className="flex flex-wrap gap-1.5 pb-2">
            {(trustRecords.length > 0 ? trustRecords : Array.from({ length: 10 }, (_, i) => ({ client_id: `C${i}` }))).map((c: any) => (
              <button
                key={c.client_id}
                onClick={() => setSelectedClientId(c.client_id)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                  selectedClientId === c.client_id
                    ? "bg-primary text-black font-bold shadow-glow-cyan"
                    : "bg-surface-elevated text-text-secondary border border-border hover:text-white"
                }`}
              >
                {c.client_id}
              </button>
            ))}
          </div>

          <div className="bg-background border border-border rounded-lg p-4 font-mono text-xs space-y-3">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <span className="text-text-secondary">Client Identifier:</span>
              <span className="text-text-primary font-bold text-sm">{selectedRecord?.client_id || selectedClientId}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Trust Rating:</span>
              <span className="text-primary font-bold text-base">
                {selectedRecord?.trust_score !== undefined ? selectedRecord.trust_score.toFixed(1) : "95.0"} / 100
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Reputation Tier:</span>
              <span
                className="font-bold px-2 py-0.5 rounded text-[11px]"
                style={{
                  color: getLevelColor(selectedRecord?.trust_level || "TRUSTED"),
                  backgroundColor: `${getLevelColor(selectedRecord?.trust_level || "TRUSTED")}15`,
                  border: `1px solid ${getLevelColor(selectedRecord?.trust_level || "TRUSTED")}40`,
                }}
              >
                {selectedRecord?.trust_level || "TRUSTED"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border/50 text-[11px]">
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <div className="text-text-secondary text-[10px]">L1 Anomalies</div>
                <div className="font-bold text-text-primary">{selectedRecord?.anomaly_count ?? 0}</div>
              </div>
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <div className="text-text-secondary text-[10px]">MARS Incidents</div>
                <div className="font-bold text-text-primary">{selectedRecord?.mars_incident_count ?? 0}</div>
              </div>
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <div className="text-text-secondary text-[10px]">Clean Rounds</div>
                <div className="font-bold text-accent-safe">{selectedRecord?.clean_round_count ?? 5}</div>
              </div>
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <div className="text-text-secondary text-[10px]">Total Penalties</div>
                <div className="font-bold text-accent-danger">{selectedRecord?.incident_count ?? 0}</div>
              </div>
            </div>

            <div className="pt-2 border-t border-border/50">
              <div className="text-[10px] text-text-secondary uppercase mb-1.5 flex items-center justify-between">
                <span>Recent Trust Adjustments</span>
                <History className="w-3 h-3 text-text-secondary" />
              </div>
              <div className="space-y-1.5 max-h-36 overflow-y-auto text-[10px]">
                {(selectedRecord?.history?.length ? selectedRecord.history : [
                  { round_id: 1, delta: +2.0, new_score: 95.0, reason: "Consistent honest training", trust_level_after: "TRUSTED" }
                ]).map((h: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between bg-surface-elevated/80 px-2 py-1 rounded border border-border/40">
                    <span className="text-text-secondary">R{h.round_id}</span>
                    <span className={`font-bold ${h.delta >= 0 ? "text-accent-safe" : "text-accent-danger"}`}>
                      {h.delta >= 0 ? `+${h.delta}` : h.delta} pts
                    </span>
                    <span className="text-text-secondary truncate max-w-[120px]" title={h.reason}>
                      {h.reason}
                    </span>
                  </div>
                ))}
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

