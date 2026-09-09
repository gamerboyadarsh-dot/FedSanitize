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
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from "recharts";
import { fetchSecuritySummary, fetchAllClientTrust, fetchSecurityDecisions, fetchSocSnapshot } from "../api/client";
import { SecurityOperationsCenter } from "../components/soc/SecurityOperationsCenter";
import type { RoundRecord } from "../types/telemetry";
import { SlidingNumber } from "../components/core/SlidingNumber";
import { motion } from "framer-motion";
import { Tooltip } from "../components/ui/Tooltip";

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
        return "#10b981"; // emerald-500
      case "MONITORED":
        return "#06b6d4"; // cyan-500
      case "SUSPICIOUS":
        return "#f59e0b"; // amber-500
      case "HIGH_RISK":
      case "QUARANTINED":
        return "#f43f5e"; // rose-500
      default:
        return "#71717a"; // zinc-500
    }
  };

  const getThreatBadge = (threat: string) => {
    switch (threat) {
      case "CRITICAL":
      case "HIGH":
        return "text-rose-400 bg-rose-500/10 border-rose-500/30";
      case "ELEVATED":
        return "text-amber-400 bg-amber-500/10 border-amber-500/30";
      case "LOW":
      case "MINIMAL":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
      default:
        return "text-cyan-400 bg-cyan-500/10 border-cyan-500/30";
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-zinc-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-xl gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Award className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-sans font-bold tracking-tight text-white">
              Security Intelligence & Operations Center
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 uppercase font-bold tracking-widest">
              Mode: {mode}
            </span>
            {isEscalated && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500 text-rose-400 uppercase font-bold animate-pulse tracking-widest">
                Incident Escalated
              </span>
            )}
          </div>
          <p className="text-sm text-zinc-400 font-sans mt-1">
            Dynamic Client Trust Scoring (F1), Multi-Signal Defense (F2), and Cryptographic SOC Audit (Team B).
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={loadData}
          disabled={isLoading}
          className="bg-white/5 border border-white/10 hover:bg-white/10 text-white h-9 px-4 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors min-w-[140px] justify-center shadow-lg"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh Signals
        </motion.button>
      </div>

      {/* Sub-tab Navigation */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-4">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setActiveSubTab("soc")}
          className={`px-4 py-2 rounded-xl text-xs font-sans font-bold flex items-center gap-2 transition-all ${
            activeSubTab === "soc"
              ? "bg-white text-black shadow-lg shadow-white/10"
              : "bg-white/5 text-zinc-400 border border-white/5 hover:text-white hover:bg-white/10"
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Team B: Security Operations Center
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setActiveSubTab("trust")}
          className={`px-4 py-2 rounded-xl text-xs font-sans font-bold flex items-center gap-2 transition-all ${
            activeSubTab === "trust"
              ? "bg-white text-black shadow-lg shadow-white/10"
              : "bg-white/5 text-zinc-400 border border-white/5 hover:text-white hover:bg-white/10"
          }`}
        >
          <Award className="w-4 h-4" />
          Team A: Client Trust & Policy Orchestrator
        </motion.button>
      </div>

      {activeSubTab === "soc" ? (
        <SecurityOperationsCenter
          snapshot={socSnapshot}
          isLoading={isLoading}
          onRefresh={loadData}
        />
      ) : (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

            <motion.div variants={itemVariants} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-5 shadow-xl h-full flex flex-col justify-between group hover:border-cyan-500/30 transition-colors">
              <div>
                <div className="flex items-center justify-between text-zinc-400 text-[11px] font-sans font-semibold tracking-wider uppercase mb-3">
                  <div className="flex items-center gap-1.5">
                    <span>Threat Level</span>
                    <Tooltip content="The aggregated threat level evaluated by Feature 2 across all layers." />
                  </div>
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className={`font-mono font-bold px-2 py-0.5 rounded-md border text-sm shadow-sm ${getThreatBadge(trustLevel)}`}>
                    {trustLevel}
                  </span>
                  <span className="text-xs font-mono text-zinc-500 font-medium">
                    Score: {(threatScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="text-[11px] text-zinc-500 font-sans mt-4 pt-3 border-t border-white/5">
                Confidence: <span className="text-zinc-300 font-mono">{((latestDecision?.confidence ?? 0.85) * 100).toFixed(0)}%</span>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-5 shadow-xl h-full flex flex-col justify-between group hover:border-purple-500/30 transition-colors">
              <div>
                <div className="flex items-center justify-between text-zinc-400 text-[11px] font-sans font-semibold tracking-wider uppercase mb-3">
                  <div className="flex items-center gap-1.5">
                    <span>Routing Action</span>
                    <Tooltip content="The autonomous response executed by the policy orchestrator." />
                  </div>
                  <Compass className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-sm font-mono font-bold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded-md w-fit">
                  {routingAction}
                </div>
              </div>
              <div className="text-[11px] text-zinc-500 font-sans mt-4 pt-3 border-t border-white/5">
                Action: <span className="text-zinc-300">{latestDecision?.aggregation_recommendation || "EXCLUDE_FLAGGED_CLIENTS"}</span>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-5 shadow-xl h-full flex flex-col justify-between group hover:border-emerald-500/30 transition-colors">
              <div>
                <div className="flex items-center justify-between text-zinc-400 text-[11px] font-sans font-semibold tracking-wider uppercase mb-3">
                  <div className="flex items-center gap-1.5">
                    <span>Active Defenses</span>
                    <Tooltip content="Which defensive algorithms are currently engaged in the pipeline." />
                  </div>
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xs font-mono font-medium space-y-1.5">
                  {(latestDecision?.active_defenses ?? ["L1_ANOMALY", "MARS_CBE", "TRIMMED_MEAN"]).slice(0, 2).map((d: string, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                      <span>{d}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="text-[11px] text-zinc-500 font-sans mt-4 pt-3 border-t border-white/5">
                Enforcement: <span className="text-zinc-300">Non-binding Observer</span>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-5 shadow-xl h-full flex flex-col justify-between group hover:border-cyan-500/30 transition-colors">
              <div>
                <div className="flex items-center justify-between text-zinc-400 text-[11px] font-sans font-semibold tracking-wider uppercase mb-3">
                  <div className="flex items-center gap-1.5">
                    <span>Cohort Mean Trust</span>
                    <Tooltip content="The average trust score across all currently tracked clients." />
                  </div>
                  <Activity className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="text-3xl font-mono font-bold text-white tracking-tight">
                  <SlidingNumber value={summary?.trust_summary?.average_trust_score ?? 76.5} decimalPlaces={1} />
                  <span className="text-sm text-zinc-500 ml-1">/ 100</span>
                </div>
              </div>
              <div className="text-[11px] text-zinc-500 font-sans mt-4 pt-3 border-t border-white/5">
                Total Clients Tracked: <span className="text-zinc-300 font-mono">{trustRecords.length || 10}</span>
              </div>
            </motion.div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <motion.div variants={itemVariants} className="lg:col-span-2 space-y-6">
              <div className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-white/5 pb-4">
                  <div>
                    <h3 className="text-sm font-sans font-bold text-white flex items-center gap-2">
                      Client Trust & Reputation Spectrum
                      <Tooltip content="Visualizes the live trust scores of all clients in the federation." />
                    </h3>
                    <p className="text-[11px] text-zinc-500 font-sans mt-0.5">
                      Real-time persistent trust rating calculated by Feature 1 TrustEngine.
                    </p>
                  </div>
                  <div className="flex items-center gap-4 text-[10px] font-sans font-semibold uppercase tracking-wider text-zinc-400">
                    <span className="flex items-center gap-1.5 hover:text-emerald-400 transition-colors cursor-default">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.5)]" /> &gt;80 Trusted
                    </span>
                    <span className="flex items-center gap-1.5 hover:text-amber-400 transition-colors cursor-default">
                      <span className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_5px_rgba(245,158,11,0.5)]" /> 40-79 Suspicious
                    </span>
                    <span className="flex items-center gap-1.5 hover:text-rose-400 transition-colors cursor-default">
                      <span className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_5px_rgba(244,63,94,0.5)]" /> &lt;20 Quarantined
                    </span>
                  </div>
                </div>

                <div className="h-64 w-full font-mono text-[11px]">
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
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" vertical={false} />
                      <XAxis dataKey="name" stroke="#52525b" tick={{ fill: "#a1a1aa" }} axisLine={false} tickLine={false} dy={10} />
                      <YAxis domain={[0, 100]} stroke="#52525b" tick={{ fill: "#a1a1aa" }} axisLine={false} tickLine={false} dx={-10} />
                      <RechartsTooltip
                        cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                        contentStyle={{
                          backgroundColor: "#18181b",
                          borderColor: "rgba(255, 255, 255, 0.1)",
                          borderRadius: "12px",
                          fontFamily: "monospace",
                          color: "#f4f4f5",
                          boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)"
                        }}
                      />
                      <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={40}>
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

              <div className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-white/5 pb-4">
                  <div className="flex items-center gap-2">
                    <Compass className="w-4 h-4 text-purple-400" />
                    <h3 className="text-sm font-sans font-bold text-white">
                      Adaptive Defense Policy History
                    </h3>
                    <Tooltip content="A log of decisions and routing actions taken by Feature 2 across federated rounds." />
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">
                    Feature 2 Signal
                  </span>
                </div>

                <div className="space-y-3 max-h-72 overflow-y-auto font-sans text-sm pr-2 custom-scrollbar">
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
                    <motion.div 
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="bg-white/5 border border-white/10 p-4 rounded-xl space-y-2 hover:bg-white/10 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white flex items-center gap-2">
                          <span className="bg-white/10 text-zinc-300 text-[10px] font-mono px-2 py-0.5 rounded">R{d.round_id}</span>
                          Decision
                        </span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-md border font-bold font-mono ${getThreatBadge(d.threat_level)}`}>
                          {d.threat_level} ({(d.threat_score * 100).toFixed(0)}%)
                        </span>
                      </div>
                      <div className="text-zinc-400 text-xs font-mono">{d.reason}</div>
                      <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-2 border-t border-white/5">
                        <span>Action: <strong className="text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20">{d.routing_action}</strong></span>
                        <span>Confidence: {(d.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-5">
              <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="text-sm font-sans font-bold text-white flex items-center gap-2">
                  <Award className="w-4 h-4 text-emerald-400" />
                  Client Trust Dossier
                  <Tooltip content="Detailed reputation and history for a specific selected client." />
                </h3>
                <span className="text-[10px] font-mono text-zinc-500 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">Feature 1</span>
              </div>

              <div className="flex flex-wrap gap-2 pb-2 border-b border-white/5">
                {(trustRecords.length > 0 ? trustRecords : Array.from({ length: 10 }, (_, i) => ({ client_id: `C${i}` }))).map((c: any) => (
                  <button
                    key={c.client_id}
                    onClick={() => setSelectedClientId(c.client_id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedClientId === c.client_id
                        ? "bg-white text-black shadow-md shadow-white/20 scale-105"
                        : "bg-white/5 text-zinc-400 border border-white/5 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {c.client_id}
                  </button>
                ))}
              </div>

              <AnimatePresence mode="wait">
                <motion.div 
                  key={selectedClientId}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -5 }}
                  transition={{ duration: 0.15 }}
                  className="bg-black/40 border border-white/5 rounded-xl p-5 font-sans text-sm space-y-4 shadow-inner"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Identifier:</span>
                    <span className="text-white font-mono font-bold text-base bg-white/10 px-2.5 py-0.5 rounded border border-white/10">{selectedRecord?.client_id || selectedClientId}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Trust Rating:</span>
                    <span className="text-emerald-400 font-mono font-bold text-lg">
                      {selectedRecord?.trust_score !== undefined ? selectedRecord.trust_score.toFixed(1) : "95.0"} <span className="text-zinc-600 text-sm">/ 100</span>
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Reputation Tier:</span>
                    <span
                      className="font-bold px-2.5 py-0.5 rounded-md text-xs font-mono border"
                      style={{
                        color: getLevelColor(selectedRecord?.trust_level || "TRUSTED"),
                        backgroundColor: `${getLevelColor(selectedRecord?.trust_level || "TRUSTED")}15`,
                        borderColor: `${getLevelColor(selectedRecord?.trust_level || "TRUSTED")}40`,
                      }}
                    >
                      {selectedRecord?.trust_level || "TRUSTED"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/5">
                    <div className="bg-white/5 p-3 rounded-xl border border-white/5 hover:bg-white/10 transition-colors">
                      <div className="text-zinc-400 text-[10px] font-semibold uppercase tracking-wider mb-1">L1 Anomalies</div>
                      <div className="font-mono font-bold text-white text-lg">{selectedRecord?.anomaly_count ?? 0}</div>
                    </div>
                    <div className="bg-white/5 p-3 rounded-xl border border-white/5 hover:bg-white/10 transition-colors">
                      <div className="text-zinc-400 text-[10px] font-semibold uppercase tracking-wider mb-1">MARS Incidents</div>
                      <div className="font-mono font-bold text-white text-lg">{selectedRecord?.mars_incident_count ?? 0}</div>
                    </div>
                    <div className="bg-white/5 p-3 rounded-xl border border-white/5 hover:bg-white/10 transition-colors">
                      <div className="text-zinc-400 text-[10px] font-semibold uppercase tracking-wider mb-1">Clean Rounds</div>
                      <div className="font-mono font-bold text-emerald-400 text-lg">{selectedRecord?.clean_round_count ?? 5}</div>
                    </div>
                    <div className="bg-white/5 p-3 rounded-xl border border-white/5 hover:bg-white/10 transition-colors">
                      <div className="text-zinc-400 text-[10px] font-semibold uppercase tracking-wider mb-1">Total Penalties</div>
                      <div className="font-mono font-bold text-rose-400 text-lg">{selectedRecord?.incident_count ?? 0}</div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-white/5">
                    <div className="text-[10px] text-zinc-500 uppercase font-semibold tracking-wider mb-2.5 flex items-center justify-between">
                      <span>Recent Adjustments</span>
                      <History className="w-3.5 h-3.5 text-zinc-500" />
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto text-xs pr-1 custom-scrollbar">
                      {(selectedRecord?.history?.length ? selectedRecord.history : [
                        { round_id: 1, delta: +2.0, new_score: 95.0, reason: "Consistent honest training", trust_level_after: "TRUSTED" }
                      ]).map((h: any, idx: number) => (
                        <div key={idx} className="flex flex-col bg-white/5 p-2.5 rounded-lg border border-white/5 hover:border-white/10 transition-colors gap-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-zinc-400 font-mono text-[10px] bg-white/10 px-1.5 py-0.5 rounded">R{h.round_id}</span>
                            <span className={`font-mono font-bold text-[11px] px-1.5 py-0.5 rounded border ${h.delta >= 0 ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" : "text-rose-400 border-rose-500/30 bg-rose-500/10"}`}>
                              {h.delta >= 0 ? `+${h.delta}` : h.delta} pts
                            </span>
                          </div>
                          <span className="text-zinc-300 font-sans text-xs">
                            {h.reason}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>

            </motion.div>
          </div>
        </motion.div>
      )}
    </div>
  );
};
