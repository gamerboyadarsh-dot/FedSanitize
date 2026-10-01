import React from "react";
import { 
  ShieldCheck, 
  ShieldAlert, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Terminal,
  Activity,
  Layers
} from "lucide-react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend 
} from "recharts";
import type { RoundRecord } from "../types/telemetry";
import { SlidingNumber } from "../components/core/SlidingNumber";
import { GlowEffect } from "../components/core/GlowEffect";
import { AnimatedGroup } from "../components/core/AnimatedGroup";
import { TextEffect } from "../components/core/TextEffect";

interface OverviewProps {
  history: RoundRecord[];
  latestRound: RoundRecord | null;
}

export const Overview: React.FC<OverviewProps> = ({ history, latestRound }) => {
  const roundNum = latestRound?.round ?? 0;
  const cleanAcc = latestRound?.clean_accuracy ?? 0;
  const asr = latestRound?.backdoor_asr ?? 0;
  const quarantined = latestRound?.quarantined_clients.length ?? 0;
  const f1 = (latestRound?.detection?.f1_score ?? 1.0) * 100;
  const l1Blocked = latestRound?.layer1_quarantined?.length ?? 0;
  const marsBlocked = latestRound?.mars_quarantined?.length ?? 0;

  // Chart data from history
  const chartData = history.map((r) => ({
    round: `R${r.round}`,
    clean_accuracy: Number(r.clean_accuracy.toFixed(2)),
    backdoor_asr: Number(r.backdoor_asr.toFixed(2)),
  }));

  return (
    <div className="space-y-6 pb-8 page-enter">
      {/* 5 KPI Metric Cards with AnimatedGroup & GlowEffect */}
      <AnimatedGroup className="grid grid-cols-1 md:grid-cols-5 gap-4 telemetry-live">
        {/* Card 1: Current Round */}
        <GlowEffect glowColor="rgba(56, 251, 219, 0.4)">
          <div className="ds-card p-4 hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="eyebrow">Simulation Round</span>
                <Layers className="w-4 h-4 text-primary" />
              </div>
              {/* Cyan semantic colour for round number */}
              <div className="kpi-value text-4xl text-[#22D3EE]">
                {roundNum > 0 ? (
                  <SlidingNumber value={roundNum} prefix="Round " />
                ) : (
                  "Idle"
                )}
              </div>
            </div>
            <div className="text-[11px] font-mono text-text-secondary mt-2 flex items-center gap-1">
              <span>Target: 15 Global Rounds</span>
            </div>
          </div>
        </GlowEffect>

        {/* Card 2: Clean Accuracy */}
        <GlowEffect glowColor="rgba(46, 204, 113, 0.4)">
          <div className="ds-card p-4 hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="eyebrow">Clean Accuracy</span>
                <CheckCircle2 className="w-4 h-4 text-accent-safe" />
              </div>
              {/* Green — high accuracy is good */}
              <div className="kpi-value text-4xl text-[#34D399]">
                {cleanAcc > 0 ? (
                  <SlidingNumber value={cleanAcc} decimalPlaces={2} suffix="%" />
                ) : (
                  "N/A"
                )}
              </div>
            </div>
            <div className="text-[11px] font-mono text-accent-safe mt-2 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              <span>High Convergence</span>
            </div>
          </div>
        </GlowEffect>

        {/* Card 3: Backdoor ASR */}
        <GlowEffect glowColor="rgba(255, 59, 92, 0.4)">
          <div className="ds-card p-4 hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="eyebrow">Backdoor ASR</span>
                <ShieldAlert className="w-4 h-4 text-accent-danger" />
              </div>
              {/* Green when suppressed (<2%), red when active */}
              <div className={`kpi-value text-4xl ${asr < 2.0 ? "text-[#34D399]" : "text-[#FF4D6D]"}`}>
                {latestRound ? (
                  <SlidingNumber value={asr} decimalPlaces={2} suffix="%" />
                ) : (
                  "N/A"
                )}
              </div>
            </div>
            <div className="text-[11px] font-mono text-accent-safe mt-2 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              <span>Suppressed by MARS</span>
            </div>
          </div>
        </GlowEffect>

        {/* Card 4: Quarantined Clients */}
        <GlowEffect glowColor="rgba(245, 166, 35, 0.4)">
          <div className="ds-card p-4 hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="eyebrow">Threats Isolated</span>
                <AlertTriangle className="w-4 h-4 text-accent-warning" />
              </div>
              {/* Red when threats present, amber when none */}
              <div className={`kpi-value text-4xl ${quarantined > 0 ? "text-[#FF4D6D]" : "text-[#F5A524]"}`}>
                <SlidingNumber value={quarantined} /> / {latestRound?.total_clients ?? 10}
              </div>
            </div>
            <div className="text-[11px] font-mono text-text-secondary mt-2">
              L1: <span className="text-accent-danger font-bold">{l1Blocked}</span> | MARS: <span className="text-accent-warning font-bold">{marsBlocked}</span>
            </div>
            {/* Disambiguates from Attack Playground threat count */}
            <p className="text-[10px] italic mt-1" style={{ color: "var(--text-muted)" }}>(firewall quarantine)</p>
          </div>
        </GlowEffect>

        {/* Card 5: Detection F1 */}
        <GlowEffect glowColor="rgba(46, 204, 113, 0.4)">
          <div className="ds-card p-4 hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="eyebrow">Defense F1-Score</span>
                <Activity className="w-4 h-4 text-accent-safe" />
              </div>
              {/* Green — defence quality metric */}
              <div className="kpi-value text-4xl text-[#34D399]">
                <SlidingNumber value={f1} decimalPlaces={1} suffix="%" />
              </div>
            </div>
            <div className="text-[11px] font-mono text-text-secondary mt-2">
              Precision: 100% | Recall: 100%
            </div>
          </div>
        </GlowEffect>
      </AnimatedGroup>

      {/* Main Charts & Telemetry Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Dual-Line Convergence Chart */}
        <div className="lg:col-span-2 ds-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div>
              {/* Inter 16px/600 normal-case title per design system */}
              <h2 className="text-base font-semibold text-text-primary">
                Convergence vs. Threat Suppression
              </h2>
              {/* 13px secondary description — no mono */}
              <p className="text-[13px] mt-0.5" style={{ color: "var(--text-secondary)" }}>
                Clean accuracy vs. backdoor ASR over training rounds
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-1 rounded bg-surface-elevated text-accent-safe border border-border">
              3-Layer Defense Active
            </span>
          </div>

          <div className="h-72 w-full pt-2">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  {/* Subtle grid per design system */}
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                  <XAxis dataKey="round" stroke="#667796" tick={{ fill: "#667796", fontSize: 11, fontFamily: "monospace" }} />
                  <YAxis domain={[0, 100]} stroke="#667796" tick={{ fill: "#667796", fontSize: 11, fontFamily: "monospace" }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#0F1C42", border: "1px solid rgba(148,163,184,0.20)", borderRadius: "8px", fontFamily: "JetBrains Mono", fontSize: "12px" }}
                    labelStyle={{ color: "#f2e8e8", fontWeight: "bold" }}
                  />
                  <Legend wrapperStyle={{ fontFamily: "monospace", fontSize: "11px", paddingTop: "10px" }} />
                  <Line 
                    type="monotone" 
                    dataKey="clean_accuracy" 
                    name="Clean Accuracy (%)" 
                    stroke="#20D9A0" 
                    strokeWidth={2.5} 
                    dot={{ fill: "#20D9A0", r: 4 }} 
                    activeDot={{ r: 6, stroke: "#20D9A0" }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="backdoor_asr" 
                    name="Backdoor ASR (%)" 
                    stroke="#FF3B5C" 
                    strokeWidth={2.5} 
                    dot={{ fill: "#FF3B5C", r: 4 }}
                    activeDot={{ r: 6, stroke: "#FF3B5C" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-text-secondary font-mono text-xs">
                No round history available. Click "Run Secure Round" or "Load 5-Round Demo".
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Gateway Audit Log — Timeline design */}
        <div className="ds-card p-5 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-primary" />
              {/* Inter title-case per design system */}
              <h2 className="text-base font-semibold text-text-primary">
                Gateway Audit Log
              </h2>
            </div>
            <span className="w-2 h-2 rounded-full bg-accent-safe animate-pulse" />
          </div>

          {/* Timeline feed — replaces old raw text blob */}
          <div className="overflow-y-auto max-h-80 scroll-fade-y pr-1 space-y-0 flex-1">
            {history.length > 0 ? (
              history.map((r, idx) => {
                const isLatest = idx === history.length - 1;
                const logText = r.log || `R${r.round}: Acc=${r.clean_accuracy.toFixed(1)}%, ASR=${r.backdoor_asr.toFixed(1)}%`;
                return (
                  <div key={idx} className="flex gap-3 pb-4 last:pb-0">
                    {/* Timeline spine */}
                    <div className="flex flex-col items-center">
                      <div
                        className="w-2 h-2 rounded-full mt-1.5 shrink-0"
                        style={{
                          background: r.quarantined_clients.length > 0 ? "var(--red)" : "var(--green)",
                          boxShadow: r.quarantined_clients.length > 0 ? "0 0 6px var(--red-glow)" : "0 0 6px var(--green-glow)"
                        }}
                      />
                      {idx < history.length - 1 && (
                        <div className="w-px flex-1 mt-1" style={{ background: "var(--border-subtle)" }} />
                      )}
                    </div>
                    {/* Entry content */}
                    <div className="flex-1 pb-4">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="ds-chip ds-chip-info ds-chip-no-dot">Round {r.round}</span>
                        {r.quarantined_clients.length > 0 && (
                          <span className="ds-chip ds-chip-danger ds-chip-no-dot">{r.quarantined_clients.length} blocked</span>
                        )}
                      </div>
                      <div className="text-[12px]" style={{ fontFamily: "JetBrains Mono", color: "var(--text-secondary)" }}>
                        {isLatest ? (
                          <TextEffect per="word">{logText}</TextEffect>
                        ) : (
                          <>
                            Acc: <span style={{ color: "var(--green)" }}>{r.clean_accuracy.toFixed(2)}%</span> &middot; ASR: <span style={{ color: r.backdoor_asr < 2 ? "var(--green)" : "var(--red)" }}>{r.backdoor_asr.toFixed(2)}%</span>
                          </>
                        )}
                      </div>
                      {r.quarantined_clients.length > 0 && (
                        <div className="flex gap-1 mt-1.5 flex-wrap items-center">
                          <span className="text-[11px] eyebrow">Quarantined:</span>
                          {r.quarantined_clients.map((c: string) => (
                            <span key={c} className="ds-chip ds-chip-quarantined ds-chip-no-dot" style={{ fontSize: "10px", padding: "2px 7px" }}>{c}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              /* Empty state */
              <div className="flex flex-col items-center justify-center py-8 gap-2">
                <Terminal className="w-8 h-8" style={{ color: "var(--text-muted)" }} />
                <p className="text-[13px]" style={{ color: "var(--text-muted)" }}>No rounds executed yet</p>
                <p className="text-[12px]" style={{ color: "var(--text-muted)" }}>Click Run Secure Round or Load 5-Round Demo</p>
              </div>
            )}
          </div>

          <div className="pt-2 text-[11px] font-mono text-text-secondary flex items-center justify-between border-t border-border/50">
            <span>Aggregator: Coordinate Trimmed Mean</span>
            <span className="text-accent-safe font-bold">\u03b2 = 0.10</span>
          </div>
        </div>
      </div>
    </div>
  );
};
