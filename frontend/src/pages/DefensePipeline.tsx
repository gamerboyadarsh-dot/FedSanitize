import React from "react";
import { 
  ShieldCheck, 
  Layers, 
  Filter, 
  Activity,
  ArrowRight,
  TrendingDown,
  Info
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine,
  Cell
} from "recharts";
import type { RoundRecord } from "../types/telemetry";

interface DefensePipelineProps {
  latestRound: RoundRecord | null;
  isRunning?: boolean;
}

export const DefensePipeline: React.FC<DefensePipelineProps> = ({ latestRound, isRunning = false }) => {
  const records = latestRound?.client_security_records ?? {};
  
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

  const totalClients = latestRound?.total_clients ?? 10;
  const l1Removed = latestRound?.layer1_quarantined?.length ?? 2;
  const l2Removed = latestRound?.mars_quarantined?.length ?? 0;
  const trustedCount = latestRound?.trusted_clients?.length ?? 8;
  const afterL1 = totalClients - l1Removed;
  const afterL2 = afterL1 - l2Removed;

  return (
    <div className="space-y-6 pb-8 page-enter">
      {/* Top: Horizontal Sequential Pipeline Flow */}
      <div className="ds-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-[var(--border-subtle)] gap-3">
          <div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--cyan-tint)] text-[var(--cyan)]">
                <Layers className="w-4 h-4" />
              </div>
              <h2 className="text-base font-semibold text-[var(--text-primary)]">
                3-Layer Defense Pipeline Architecture
              </h2>
            </div>
            <p className="text-[13px] text-[var(--text-secondary)] mt-1">
              Deterministic cascade defending against Byzantine gradient tampering, backdoor clustering, and boundary bias.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="ds-chip ds-chip-pass ds-chip-no-dot">
              3-Layer Defense Active
            </span>
            {isRunning && (
              <span className="ds-chip ds-chip-info">
                Filtering in Progress...
              </span>
            )}
          </div>
        </div>

        {/* Visual Pipeline Stepper */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center pt-6">
          {/* Step 0: Input */}
          <div className="ds-card-elevated p-4 text-center rounded-xl relative">
            <span className="eyebrow block">Client Ingestion</span>
            <div className="kpi-value text-2xl text-[var(--cyan)] mt-1">{totalClients}</div>
            <span className="text-[12px] text-[var(--text-muted)]">Raw Model Updates</span>
          </div>

          {/* Step 1: L1 */}
          <div className="ds-card p-4 rounded-xl relative border-t-2 border-t-[var(--cyan)]">
            <div className="flex items-center justify-between mb-1">
              <span className="eyebrow text-[var(--cyan)]">Layer 1</span>
              <span className="text-[11px] font-mono text-[var(--red)] font-semibold">-{l1Removed} removed</span>
            </div>
            <div className="text-[13px] font-semibold text-[var(--text-primary)]">MAD Statistical Filter</div>
            <div className="text-[11px] text-[var(--text-secondary)] mt-1 font-mono">
              Surviving: {afterL1} updates
            </div>
          </div>

          {/* Step 2: L2 */}
          <div className="ds-card p-4 rounded-xl relative border-t-2 border-t-[var(--purple)]">
            <div className="flex items-center justify-between mb-1">
              <span className="eyebrow text-[var(--purple)]">Layer 2</span>
              <span className="text-[11px] font-mono text-[var(--amber)] font-semibold">-{l2Removed} removed</span>
            </div>
            <div className="text-[13px] font-semibold text-[var(--text-primary)]">MARS CBE Clustering</div>
            <div className="text-[11px] text-[var(--text-secondary)] mt-1 font-mono">
              Surviving: {afterL2} updates
            </div>
          </div>

          {/* Step 3: L3 */}
          <div className="ds-card p-4 rounded-xl relative border-t-2 border-t-[var(--green)]">
            <div className="flex items-center justify-between mb-1">
              <span className="eyebrow text-[var(--green)]">Layer 3</span>
              <span className="text-[11px] font-mono text-[var(--green)] font-semibold">β = 0.10</span>
            </div>
            <div className="text-[13px] font-semibold text-[var(--text-primary)]">Trimmed-Mean Aggregation</div>
            <div className="text-[11px] text-[var(--text-secondary)] mt-1 font-mono">
              Outliers trimmed
            </div>
          </div>

          {/* Output */}
          <div className="ds-card-elevated p-4 text-center rounded-xl relative border-l-2 border-l-[var(--green)]">
            <span className="eyebrow block">Sanitized Consensus</span>
            <div className="kpi-value text-2xl text-[var(--green)] mt-1">{trustedCount}</div>
            <span className="text-[12px] text-[var(--text-muted)]">Consensus Updates</span>
          </div>
        </div>
      </div>

      {/* Three Detailed Layer Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Layer 1 Box */}
        <div className="ds-card p-5 flex flex-col justify-between relative overflow-hidden border-t-4 border-t-[var(--cyan)]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[var(--cyan-tint)] text-[var(--cyan)] text-xs font-bold flex items-center justify-center">1</span>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Statistical Anomaly Filter</h3>
                  <p className="text-[12px] text-[var(--text-muted)]">MAD Norm & Cosine Alignment</p>
                </div>
              </div>
              <Filter className="w-4 h-4 text-[var(--cyan)]" />
            </div>
            <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed mt-3">
              Filters extreme L2 norm updates (&gt;3.5x MAD multiplier) and orthogonal or negative cosine similarity to eradicate gradient explosion and sign-flipping tampering.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="eyebrow">Verdict</span>
            <span className="ds-chip ds-chip-danger ds-chip-no-dot">
              Quarantined: {l1Removed} Clients
            </span>
          </div>
        </div>

        {/* Layer 2 Box */}
        <div className="ds-card p-5 flex flex-col justify-between relative overflow-hidden border-t-4 border-t-[var(--purple)]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[var(--purple-tint)] text-[var(--purple)] text-xs font-bold flex items-center justify-center">2</span>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">MARS Forensics</h3>
                  <p className="text-[12px] text-[var(--text-muted)]">CBE & Wasserstein Clustering</p>
                </div>
              </div>
              <Activity className="w-4 h-4 text-[var(--purple)]" />
            </div>
            <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed mt-3">
              Computes gradient variance layer sensitivity, Client Backdoor Energy (CBE), and 1D Wasserstein distance matrix with agglomerative clustering to isolate stealthy neural backdoors.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="eyebrow">Verdict</span>
            <span className="ds-chip ds-chip-flagged ds-chip-no-dot">
              Quarantined: {l2Removed} Clients
            </span>
          </div>
        </div>

        {/* Layer 3 Box */}
        <div className="ds-card p-5 flex flex-col justify-between relative overflow-hidden border-t-4 border-t-[var(--green)]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[var(--green-tint)] text-[var(--green)] text-xs font-bold flex items-center justify-center">3</span>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Robust Aggregation</h3>
                  <p className="text-[12px] text-[var(--text-muted)]">Coordinate Trimmed Mean</p>
                </div>
              </div>
              <ShieldCheck className="w-4 h-4 text-[var(--green)]" />
            </div>
            <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed mt-3">
              Sorts surviving parameter updates per coordinate and trims the top & bottom 10% (β=0.10) to guard against subtle boundary bias before global model consolidation.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="eyebrow">Consensus</span>
            <span className="ds-chip ds-chip-pass ds-chip-no-dot">
              Surviving Trusted: {trustedCount} Clients
            </span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Grid: L2 Norm Bar Chart & MARS Distance Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: L2 Update Norm Profile */}
        <div className="ds-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <div>
              <h3 className="text-base font-semibold text-[var(--text-primary)]">
                Layer 1: L2 Update Norm Profile
              </h3>
              <p className="text-[13px] text-[var(--text-secondary)]">
                Comparison of client update magnitudes against MAD rejection boundary
              </p>
            </div>
            <span className="ds-chip ds-chip-danger ds-chip-no-dot font-mono">
              MAD Multiplier: 3.5x
            </span>
          </div>

          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={displayNormData} margin={{ top: 12, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                <XAxis dataKey="clientId" stroke="#667796" tick={{ fill: "#667796", fontSize: 12, fontFamily: "JetBrains Mono" }} />
                <YAxis stroke="#667796" tick={{ fill: "#667796", fontSize: 12, fontFamily: "JetBrains Mono" }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: "#0F1C42", 
                    borderColor: "rgba(148,163,184,0.20)", 
                    borderRadius: "8px", 
                    fontFamily: "JetBrains Mono", 
                    fontSize: "12px",
                    boxShadow: "0 8px 24px rgba(0,0,0,0.4)" 
                  }}
                  formatter={(val: any) => [`${val}`, "L2 Norm"]}
                  labelFormatter={(lbl) => `Client ${lbl}`}
                />
                <ReferenceLine 
                  y={10.0} 
                  stroke="#FF4D6D" 
                  strokeDasharray="4 4" 
                  label={{ value: "Rejection Threshold (10.0)", fill: "#FF4D6D", fontSize: 11, fontFamily: "JetBrains Mono", position: "insideTopRight" }} 
                />
                <Bar dataKey="update_norm" name="L2 Norm" radius={[6, 6, 0, 0]}>
                  {displayNormData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.update_norm > 10.0 ? "var(--red)" : "var(--cyan)"} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-between text-[12px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-subtle)]">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[var(--cyan)]" />
              <span>Normal update magnitude</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[var(--red)]" />
              <span>Outlier gradient explosion</span>
            </span>
          </div>
        </div>

        {/* Right: MARS Pairwise Wasserstein Distance Matrix Heatmap */}
        <div className="ds-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <div>
              <h3 className="text-base font-semibold text-[var(--text-primary)]">
                Layer 2: MARS Wasserstein Matrix (W₁)
              </h3>
              <p className="text-[13px] text-[var(--text-secondary)]">
                Pairwise energy distribution distances between client representations
              </p>
            </div>
            <span className="ds-chip ds-chip-mars ds-chip-no-dot font-mono">
              Gap Threshold: ≥ 0.015
            </span>
          </div>

          <div className="p-4 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-xl flex flex-col items-center justify-center">
            <div className="grid grid-cols-4 gap-2.5 w-full max-w-sm">
              {distMatrix.slice(0, 4).map((row, rIdx) =>
                row.slice(0, 4).map((val, cIdx) => {
                  const isHigh = val >= 0.015;
                  const alpha = Math.min(1, 0.15 + (val / 0.045) * 0.85);
                  return (
                    <div
                      key={`${rIdx}-${cIdx}`}
                      className={`p-3 rounded-lg text-center transition-all cursor-default ${
                        isHigh
                          ? "bg-[rgba(255,77,109,0.18)] text-[var(--red)] border-2 border-[var(--red)] font-bold shadow-[0_0_12px_rgba(255,77,109,0.25)]"
                          : "text-[var(--text-primary)] border border-[rgba(139,92,246,0.25)]"
                      }`}
                      style={!isHigh ? {
                        backgroundColor: val === 0 ? 'var(--bg-surface)' : `rgba(139, 92, 246, ${alpha})`,
                      } : undefined}
                      title={`Distance C${rIdx} to C${cIdx}: ${val.toFixed(4)}`}
                    >
                      <div className={`text-[10px] font-mono ${isHigh ? "text-[var(--red)] font-bold" : "text-[var(--text-muted)]"}`}>
                        C{rIdx} - C{cIdx}
                      </div>
                      <div className="font-mono text-xs font-semibold mt-0.5">{val.toFixed(4)}</div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="w-full flex items-center justify-between text-[11px] font-sans mt-4 pt-3 border-t border-[var(--border-subtle)] max-w-sm">
              <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                <span className="w-2.5 h-2.5 rounded bg-[rgba(139,92,246,0.5)] border border-[var(--purple)]" />
                <span>Benign (&lt;0.015)</span>
              </span>
              <span className="flex items-center gap-1.5 text-[var(--red)] font-medium">
                <span className="w-2.5 h-2.5 rounded bg-[rgba(255,77,109,0.3)] border-2 border-[var(--red)]" />
                <span>Backdoor Cluster (≥0.015)</span>
              </span>
            </div>

            <div className="text-[12px] text-[var(--text-muted)] text-center mt-2.5">
              High Wasserstein distances isolate stealthy backdoor representations from benign client distribution.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
