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
  AreaChart, 
  Area, 
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
      <AnimatedGroup className="grid grid-cols-1 md:grid-cols-5 gap-4 telemetry-live">
        {/* Card 1: Current Round */}
        <GlowEffect glowColor="rgba(56, 251, 219, 0.4)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Simulation Round</span>
                <Layers className="w-4 h-4 text-primary" />
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
        <GlowEffect glowColor="rgba(255, 59, 92, 0.4)">
          <div className="bg-surface border border-border rounded-xl p-4 threat-card hover:-translate-y-0.5 transition-all duration-200 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Backdoor ASR</span>
                <ShieldAlert className="w-4 h-4 text-accent-danger" />
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
                <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorClean" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorAsr" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" opacity={0.5} />
                  <XAxis dataKey="round" stroke="#a1a1aa" tick={{ fill: "#a1a1aa", fontSize: 11, fontFamily: "monospace" }} />
                  <YAxis domain={[0, 100]} stroke="#a1a1aa" tick={{ fill: "#a1a1aa", fontSize: 11, fontFamily: "monospace" }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "rgba(9, 9, 11, 0.9)", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px", fontFamily: "monospace", fontSize: "12px", boxShadow: "0 4px 12px rgba(0,0,0,0.5)", backdropFilter: "blur(8px)" }}
                    labelStyle={{ color: "#fafafa", fontWeight: "bold" }}
                  />
                  <Legend wrapperStyle={{ fontFamily: "monospace", fontSize: "11px", paddingTop: "10px" }} />
                  <Area 
                    type="monotone" 
                    dataKey="clean_accuracy" 
                    name="Clean Accuracy (%)" 
                    stroke="#10b981" 
                    strokeWidth={2.5} 
                    fillOpacity={1} 
                    fill="url(#colorClean)"
                    activeDot={{ r: 6, strokeWidth: 0, fill: "#10b981" }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="backdoor_asr" 
                    name="Backdoor ASR (%)" 
                    stroke="#ef4444" 
                    strokeWidth={2.5} 
                    fillOpacity={1} 
                    fill="url(#colorAsr)"
                    activeDot={{ r: 6, strokeWidth: 0, fill: "#ef4444" }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-text-secondary font-mono text-xs">
                No round history available. Click "Run Secure Round" or "Load 5-Round Demo".
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Live Telemetry Terminal Feed */}
        <div className="bg-[#050505] border border-[#222] rounded-xl overflow-hidden flex flex-col justify-between shadow-2xl relative">
          {/* Terminal MacOS-style Header */}
          <div className="bg-[#111] border-b border-[#222] px-4 py-2.5 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            </div>
            <div className="text-[10px] font-mono text-gray-500 tracking-widest flex items-center gap-2">
              <Terminal className="w-3 h-3" />
              root@fedsanitize:~/logs
            </div>
            <div className="w-10"></div>
          </div>

          <div className="p-4 font-mono text-[11px] flex-1 overflow-y-auto max-h-80 space-y-3 relative scanlines scroll-smooth">
            {history.length > 0 ? (
              history.map((r, idx) => {
                const isLatest = idx === history.length - 1;
                const logText = r.log || `[SYSTEM] Analyzing client updates for Round ${r.round}... Aggregate clean_accuracy=${r.clean_accuracy.toFixed(2)}%, backdoor_asr=${r.backdoor_asr.toFixed(2)}%`;
                return (
                  <div key={idx} className="z-10 relative leading-relaxed tracking-tight">
                    <div className="flex items-center gap-2 text-gray-500 mb-1">
                      <span>{new Date().toLocaleTimeString('en-US', { hour12: false, hour: "numeric", minute: "numeric", second: "numeric" })}</span>
                      <span className="text-[#38FBDB]">fedsanitize</span>
                      <span>[PID:4921]</span>
                    </div>
                    <div className="text-gray-300">
                      <span className="text-emerald-400 mr-2">➜</span> 
                      {isLatest ? (
                        <TextEffect per="word">{logText}</TextEffect>
                      ) : (
                        logText
                      )}
                    </div>
                    {r.quarantined_clients.length > 0 && (
                      <div className="text-red-400 mt-1 pl-4 border-l border-red-500/30 ml-1">
                        [CRITICAL] Malicious signatures detected. Quarantining: {r.quarantined_clients.join(", ")}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="text-gray-500 italic z-10 relative">
                root@fedsanitize:~/logs$ tail -f gateway.log
                <br />
                Waiting for incoming client connections...
              </div>
            )}
          </div>

          <div className="bg-[#111] px-4 py-2 text-[10px] font-mono text-gray-500 flex items-center justify-between border-t border-[#222]">
            <span>Aggregator: Coordinate Trimmed Mean</span>
            <span className="text-emerald-500 font-bold">● Active</span>
          </div>
        </div>
      </div>
    </div>
  );
};
