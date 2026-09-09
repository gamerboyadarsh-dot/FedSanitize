import React from "react";
import { 
  ShieldCheck, 
  Layers, 
  Filter, 
  Activity,
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine 
} from "recharts";
import type { RoundRecord } from "../types/telemetry";
import { BorderTrail } from "../components/core/BorderTrail";
import { AnimatedGroup } from "../components/core/AnimatedGroup";
import { Spotlight } from "../components/core/Spotlight";

interface DefensePipelineProps {
  latestRound: RoundRecord | null;
  isRunning?: boolean;
}

export const DefensePipeline: React.FC<DefensePipelineProps> = ({ latestRound, isRunning = false }) => {
  const records = latestRound?.client_security_records ?? {};
  
  // Transform client security records for L2 norm bar chart
  const normData = Object.entries(records).map(([cid, r]) => ({
    clientId: cid,
    update_norm: Number(r.update_norm.toFixed(2)),
    status: r.final_status,
    isMalicious: r.is_malicious,
  }));

  const displayNormData = normData.length > 0 ? normData : [
    { clientId: "C0", update_norm: 5.08, status: "TRUSTED", isMalicious: false },
    { clientId: "C1", update_norm: 5.20, status: "TRUSTED", isMalicious: false },
    { clientId: "C2", update_norm: 4.98, status: "TRUSTED", isMalicious: false },
    { clientId: "C3", update_norm: 4.99, status: "TRUSTED", isMalicious: false },
    { clientId: "C4", update_norm: 4.91, status: "TRUSTED", isMalicious: false },
    { clientId: "C5", update_norm: 5.13, status: "TRUSTED", isMalicious: false },
    { clientId: "C6", update_norm: 51.47, status: "QUARANTINED", isMalicious: true },
    { clientId: "C7", update_norm: 5.15, status: "QUARANTINED", isMalicious: true },
    { clientId: "C8", update_norm: 5.12, status: "QUARANTINED", isMalicious: true },
    { clientId: "C9", update_norm: 5.10, status: "QUARANTINED", isMalicious: true },
  ];

  const distMatrix = latestRound?.distance_matrix ?? [
    [0.0, 0.0012, 0.0015, 0.0450],
    [0.0012, 0.0, 0.0011, 0.0448],
    [0.0015, 0.0011, 0.0, 0.0461],
    [0.0450, 0.0448, 0.0461, 0.0],
  ];

  return (
    <div className="space-y-6">
      {/* 3-Layer Sequential Flow Banner with Ambient Spotlight */}
      <Spotlight className="rounded-xl">
        <div className="bg-surface border border-border rounded-xl p-6  space-y-4">
        <div className="flex items-center justify-between border-b border-border/60 pb-3">
          <div>
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              Sequential 3-Layer Security Pipeline
            </h2>
            <p className="text-xs text-text-secondary font-mono mt-1">
              Multi-tiered filtering architecture neutralizing Byzantine poisoning and stealthy backdoors sequentially.
            </p>
          </div>
          <span className="text-xs font-mono text-accent-safe bg-accent-safe/10 border border-accent-safe/30 px-2.5 py-1 rounded">
            All Layers Active
          </span>
        </div>

        {/* 3 Layer Boxes with BorderTrail active state */}
        <AnimatedGroup className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs pt-2">
          {/* Layer 1 Box */}
          <div className="bg-surface-elevated border border-border rounded-xl p-4 space-y-2 relative overflow-hidden ">
            {isRunning && <BorderTrail trailColor="#38FBDB" size={80} />}
            <div className="flex items-center justify-between">
              <span className="text-primary font-bold text-[11px] uppercase tracking-wider">
                Layer 1: Anomaly Filter
              </span>
              <Filter className="w-4 h-4 text-primary" />
            </div>
            <div className="text-text-primary text-xs font-semibold">MAD Norm & Cosine Shield</div>
            <p className="text-[11px] text-text-secondary leading-relaxed">
              Extracts L2 update norms and directional cosine similarity against coordinate-wise median reference. Catches 10x scale explosions and sign-flipping noise immediately.
            </p>
            <div className="text-[10px] text-accent-danger font-bold pt-1">
              Quarantined: {latestRound?.layer1_quarantined?.length ?? 2} Clients
            </div>
          </div>

          {/* Layer 2 Box */}
          <div className="bg-surface-elevated border border-border rounded-xl p-4 space-y-2 relative overflow-hidden ">
            {isRunning && <BorderTrail trailColor="#8E52F5" size={80} />}
            <div className="flex items-center justify-between">
              <span className="text-secondary font-bold text-[11px] uppercase tracking-wider">
                Layer 2: MARS Defense
              </span>
              <Activity className="w-4 h-4 text-secondary" />
            </div>
            <div className="text-text-primary text-xs font-semibold">NeurIPS 2025 CBE Clustering</div>
            <p className="text-[11px] text-text-secondary leading-relaxed">
              Computes gradient-variance layer sensitivity, Client Backdoor Energy (CBE), and 1D Wasserstein distance matrix with agglomerative clustering to isolate stealthy backdoors.
            </p>
            <div className="text-[10px] text-accent-warning font-bold pt-1">
              Quarantined: {latestRound?.mars_quarantined?.length ?? 2} Clients
            </div>
          </div>

          {/* Layer 3 Box */}
          <div className="bg-surface-elevated border border-border rounded-xl p-4 space-y-2 relative overflow-hidden ">
            {isRunning && <BorderTrail trailColor="#20D9A0" size={80} />}
            <div className="flex items-center justify-between">
              <span className="text-accent-safe font-bold text-[11px] uppercase tracking-wider">
                Layer 3: Robust Aggregation
              </span>
              <ShieldCheck className="w-4 h-4 text-accent-safe" />
            </div>
            <div className="text-text-primary text-xs font-semibold">Coordinate-wise Trimmed Mean</div>
            <p className="text-[11px] text-text-secondary leading-relaxed">
              Sorts surviving parameter updates per coordinate and trims the top & bottom 10% (β=0.10) to guard against subtle boundary bias before global model consolidation.
            </p>
            <div className="text-[10px] text-accent-safe font-bold pt-1">
              Surviving Trusted: {latestRound?.trusted_clients?.length ?? 6} Clients
            </div>
          </div>
        </AnimatedGroup>
      </div>
      </Spotlight>

      {/* Visual Analytics Grid: L2 Norm Bar Chart & MARS Distance Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: L2 Update Norm Profile */}
        <div className="bg-surface border border-border rounded-xl p-5  space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div>
              <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                Layer 1: L2 Update Norm Profile
              </h3>
              <p className="text-xs text-text-secondary font-mono">
                Comparison of client update magnitudes against MAD rejection boundary
              </p>
            </div>
            <span className="text-[10px] font-mono text-accent-danger bg-accent-danger/10 border border-accent-danger/30 px-2 py-0.5 rounded">
              MAD Multiplier: 3.5x
            </span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={displayNormData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.5} />
                <XAxis dataKey="clientId" stroke="#64748b" tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }} />
                <YAxis stroke="#64748b" tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "#050508", borderColor: "#38FBDB", borderRadius: "8px", fontFamily: "monospace", fontSize: "12px", boxShadow: "0 0 10px rgba(56,251,219,0.2)" }}
                />
                <ReferenceLine y={10.0} stroke="#FF3B5C" strokeDasharray="4 4" label={{ value: "Rejection Threshold", fill: "#FF3B5C", fontSize: 10, fontFamily: "monospace" }} />
                <Bar 
                  dataKey="update_norm" 
                  name="L2 Norm" 
                  fill="#38FBDB"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: MARS Pairwise Wasserstein Distance Matrix Heatmap */}
        <div className="bg-surface border border-border rounded-xl p-5  space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div>
              <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                Layer 2: MARS Wasserstein Matrix ($W_1$)
              </h3>
              <p className="text-xs text-text-secondary font-mono">
                Pairwise energy distribution distances between client representations
              </p>
            </div>
            <span className="text-[10px] font-mono text-secondary bg-secondary/10 border border-secondary/30 px-2 py-0.5 rounded">
              Gap &ge; 0.015
            </span>
          </div>

          <div className="p-4 bg-background border border-border rounded-lg font-mono text-xs flex flex-col items-center justify-center">
            <div className="grid grid-cols-4 gap-2 w-full max-w-sm">
              {distMatrix.slice(0, 4).map((row, rIdx) =>
                row.slice(0, 4).map((val, cIdx) => {
                  const isHigh = val > 0.015;
                  const alpha = Math.min(1, 0.1 + (val / 0.015) * 0.9);
                  return (
                    <div
                      key={`${rIdx}-${cIdx}`}
                      className={`p-3 rounded text-center transition-all cursor-pointer hover:scale-105 ${
                        isHigh
                          ? "bg-accent-danger/20 text-accent-danger border border-accent-danger/40 font-bold hover:shadow-glow-red"
                          : "text-white border hover:shadow-glow-purple"
                      }`}
                      style={!isHigh ? {
                        backgroundColor: val === 0 ? '#0C1E3E' : `rgba(142, 82, 245, ${alpha})`,
                        borderColor: `rgba(142, 82, 245, ${Math.max(0.2, alpha)})`
                      } : undefined}
                    >
                      <div className={`text-[10px] ${isHigh ? "text-accent-danger/80" : "text-white/60"}`}>{`C${rIdx}-C${cIdx}`}</div>
                      <div className="font-bold">{val.toFixed(4)}</div>
                    </div>
                  );
                })
              )}
            </div>
            <div className="w-full flex items-center justify-between text-[10px] text-zinc-500 font-mono mt-4 pt-3 border-t border-border/50 max-w-sm">
              <span className="flex items-center gap-1.5 text-secondary">
                <span className="w-2 h-2 rounded bg-[#8E52F5]/50 border border-[#8E52F5]" />
                <span>Low (&lt;0.015) Benign</span>
              </span>
              <span className="flex items-center gap-1.5 text-accent-danger">
                <span className="w-2 h-2 rounded bg-accent-danger/30 border border-accent-danger" />
                <span>High (&ge;0.015) Backdoor Cluster</span>
              </span>
            </div>
            <div className="text-[11px] text-text-secondary text-center mt-2">
              High Wasserstein distances delineate malicious backdoor clusters from benign representations.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
