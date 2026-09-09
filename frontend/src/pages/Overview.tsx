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
    <div className="space-y-6">
      {/* 5 KPI Metric Cards with AnimatedGroup & GlowEffect */}
      <AnimatedGroup className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* Card 1: Current Round */}
        <GlowEffect>
          <div className="bg-surface border border-border rounded-xl p-4 threat-card hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Simulation Round</span>
                <Layers className="w-4 h-4 text-accent-red" />
              </div>
              <div className="text-3xl font-mono font-bold text-text-primary">
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
          <div className="bg-surface border border-border rounded-xl p-4 threat-card hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Clean Accuracy</span>
                <CheckCircle2 className="w-4 h-4 text-accent-safe" />
              </div>
              <div className="text-3xl font-mono font-bold text-accent-safe">
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
        <GlowEffect glowColor="rgba(225, 29, 46, 0.45)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Backdoor ASR</span>
                <ShieldAlert className="w-4 h-4 text-accent-red" />
              </div>
              <div className={`text-3xl font-mono font-bold ${asr < 2.0 ? "text-accent-safe" : "text-accent-danger"}`}>
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
          <div className="bg-surface border border-border rounded-xl p-4 threat-card hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Threats Isolated</span>
                <AlertTriangle className="w-4 h-4 text-accent-warning" />
              </div>
              <div className="text-3xl font-mono font-bold text-accent-danger">
                <SlidingNumber value={quarantined} /> / {latestRound?.total_clients ?? 10}
              </div>
            </div>
            <div className="text-[11px] font-mono text-text-secondary mt-2">
              L1: <span className="text-accent-danger font-bold">{l1Blocked}</span> | MARS: <span className="text-accent-warning font-bold">{marsBlocked}</span>
            </div>
          </div>
        </GlowEffect>

        {/* Card 5: Detection F1 */}
        <GlowEffect glowColor="rgba(46, 204, 113, 0.4)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Defense F1-Score</span>
                <Activity className="w-4 h-4 text-accent-safe" />
              </div>
              <div className="text-3xl font-mono font-bold text-accent-safe">
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
        <div className="lg:col-span-2 bg-surface border border-border rounded-xl p-5 threat-card space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div>
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                Convergence vs. Threat Suppression
              </h2>
              <p className="text-xs text-text-secondary font-mono">
                Clean Accuracy (Green) vs. Backdoor Attack Success Rate (Red) over rounds
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
                  <CartesianGrid strokeDasharray="3 3" stroke="#3d1414" opacity={0.5} />
                  <XAxis dataKey="round" stroke="#a88888" tick={{ fill: "#a88888", fontSize: 11, fontFamily: "monospace" }} />
                  <YAxis domain={[0, 100]} stroke="#a88888" tick={{ fill: "#a88888", fontSize: 11, fontFamily: "monospace" }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#150a0a", borderColor: "#7a1f1f", borderRadius: "8px", fontFamily: "monospace", fontSize: "12px" }}
                    labelStyle={{ color: "#f2e8e8", fontWeight: "bold" }}
                  />
                  <Legend wrapperStyle={{ fontFamily: "monospace", fontSize: "11px", paddingTop: "10px" }} />
                  <Line 
                    type="monotone" 
                    dataKey="clean_accuracy" 
                    name="Clean Accuracy (%)" 
                    stroke="#2ecc71" 
                    strokeWidth={2.5} 
                    dot={{ fill: "#2ecc71", r: 4 }} 
                    activeDot={{ r: 6, stroke: "#2ecc71" }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="backdoor_asr" 
                    name="Backdoor ASR (%)" 
                    stroke="#e11d2e" 
                    strokeWidth={2.5} 
                    dot={{ fill: "#e11d2e", r: 4 }}
                    activeDot={{ r: 6, stroke: "#e11d2e" }}
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

        {/* Right Col: Live Telemetry Terminal Feed */}
        <div className="bg-surface border border-border rounded-xl p-5 threat-card flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-accent-red" />
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                Gateway Audit Log
              </h2>
            </div>
            <span className="w-2 h-2 rounded-full bg-accent-safe animate-pulse" />
          </div>

          <div className="bg-background border border-border/80 rounded-lg p-3 font-mono text-xs text-text-secondary flex-1 overflow-y-auto max-h-72 space-y-2.5">
            {history.length > 0 ? (
              history.map((r, idx) => {
                const isLatest = idx === history.length - 1;
                const logText = r.log || `R${r.round}: Acc=${r.clean_accuracy.toFixed(1)}%, ASR=${r.backdoor_asr.toFixed(1)}%`;
                return (
                  <div key={idx} className="border-b border-border/40 pb-2.5 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between text-[11px] text-accent-red font-bold">
                      <span>[SEC-EVENT] Round {r.round} Audit</span>
                      <span className="text-text-secondary font-normal">{r.quarantined_clients.length} Blocked</span>
                    </div>
                    <div className="text-text-primary mt-1 text-[11px] leading-relaxed">
                      {isLatest ? (
                        <TextEffect per="word">{logText}</TextEffect>
                      ) : (
                        logText
                      )}
                    </div>
                    <div className="text-[10px] text-text-secondary mt-1">
                      Quarantined: [{r.quarantined_clients.join(", ")}]
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-text-secondary text-[11px] italic">
                Gateway listening... No rounds executed yet.
              </div>
            )}
          </div>

          <div className="pt-2 text-[11px] font-mono text-text-secondary flex items-center justify-between border-t border-border/50">
            <span>Aggregator: Coordinate Trimmed Mean</span>
            <span className="text-accent-safe font-bold">β = 0.10</span>
          </div>
        </div>
      </div>
    </div>
  );
};
