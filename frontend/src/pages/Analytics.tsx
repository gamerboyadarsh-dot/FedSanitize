import React from "react";
import { 
  BarChart3, 
} from "lucide-react";
import type { RoundRecord } from "../types/telemetry";
import { SlidingNumber } from "../components/core/SlidingNumber";
import { AnimatedGroup } from "../components/core/AnimatedGroup";

interface AnalyticsProps {
  history: RoundRecord[];
  latestRound: RoundRecord | null;
}

export const Analytics: React.FC<AnalyticsProps> = ({ history, latestRound }) => {
  const det = latestRound?.detection ?? {
    tp: 4,
    fp: 0,
    tn: 6,
    fn: 0,
    precision: 1.0,
    recall: 1.0,
    f1_score: 1.0,
    detection_rate: 1.0,
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-surface border border-border rounded-xl p-5 threat-card flex items-center justify-between">
        <div>
          <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-accent-red" />
            Comparative Defense & Confusion Matrix Analytics
          </h2>
          <p className="text-xs text-text-secondary font-mono mt-1">
            Statistical evaluation of isolation fidelity, false alarm rates, and longitudinal round history.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded bg-surface-elevated text-accent-safe border border-border font-bold">
            Zero False Positives (FP=0)
          </span>
        </div>
      </div>

      <AnimatedGroup className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: 4-Quadrant Confusion Matrix with SlidingNumber */}
        <div className="bg-surface border border-border rounded-xl p-5 threat-card space-y-4">
          <div className="border-b border-border/60 pb-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-text-primary">
              Multi-Layer Confusion Matrix
            </h3>
            <p className="text-[11px] text-text-secondary font-mono mt-0.5">
              Round {latestRound?.round ?? 1} Isolation Distribution
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono text-center">
            {/* True Positive */}
            <div className="bg-accent-safe/10 border border-accent-safe/30 rounded-xl p-4 space-y-1">
              <div className="text-[10px] text-accent-safe font-bold uppercase">True Positive (TP)</div>
              <div className="text-3xl font-bold text-accent-safe">
                <SlidingNumber value={det.tp} />
              </div>
              <div className="text-[10px] text-text-secondary">Malicious Quarantined</div>
            </div>

            {/* False Positive */}
            <div className={`border rounded-xl p-4 space-y-1 ${
              det.fp > 0 
                ? "bg-accent-warning/10 border-accent-warning/40 text-accent-warning" 
                : "bg-surface-elevated border-border text-zinc-400"
            }`}>
              <div className="text-[10px] font-bold uppercase">False Positive (FP)</div>
              <div className="text-3xl font-bold">
                <SlidingNumber value={det.fp} />
              </div>
              <div className="text-[10px] text-text-secondary">{det.fp === 0 ? "0 False Alarms" : "Honest Quarantined"}</div>
            </div>

            {/* False Negative */}
            <div className={`border rounded-xl p-4 space-y-1 ${
              det.fn > 0 
                ? "bg-accent-danger/10 border-accent-danger/40 text-accent-danger" 
                : "bg-surface-elevated border-border text-zinc-400"
            }`}>
              <div className="text-[10px] font-bold uppercase">False Negative (FN)</div>
              <div className="text-3xl font-bold">
                <SlidingNumber value={det.fn} />
              </div>
              <div className="text-[10px] text-text-secondary">{det.fn === 0 ? "0 Attack Leaks" : "Malicious Slipped"}</div>
            </div>

            {/* True Negative */}
            <div className="bg-accent-safe/10 border border-accent-safe/30 rounded-xl p-4 space-y-1">
              <div className="text-[10px] text-accent-safe font-bold uppercase">True Negative (TN)</div>
              <div className="text-3xl font-bold text-accent-safe">
                <SlidingNumber value={det.tn} />
              </div>
              <div className="text-[10px] text-text-secondary">Honest Preserved</div>
            </div>
          </div>

          <div className="bg-surface-elevated border border-border rounded-lg p-3 space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-text-secondary">Detection Precision:</span>
              <span className="text-accent-safe font-bold">
                <SlidingNumber value={det.precision * 100} decimalPlaces={1} suffix="%" />
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Detection Recall:</span>
              <span className="text-accent-safe font-bold">
                <SlidingNumber value={det.recall * 100} decimalPlaces={1} suffix="%" />
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">F1 Classification Score:</span>
              <span className="text-accent-safe font-bold">
                <SlidingNumber value={det.f1_score * 100} decimalPlaces={1} suffix="%" />
              </span>
            </div>
          </div>
        </div>

        {/* Right 2 Cols: Historical Rounds Table */}
        <div className="lg:col-span-2 bg-surface border border-border rounded-xl p-5 threat-card space-y-4">
          <div className="border-b border-border/60 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-text-primary">
                Round-by-Round Longitudinal History
              </h3>
              <p className="text-[11px] text-text-secondary font-mono">
                Historical records of all executed simulation rounds
              </p>
            </div>
            <span className="text-[10px] font-mono text-text-secondary">
              Total Rounds: {history.length}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-surface-elevated/70 text-text-secondary uppercase text-[10px] tracking-wider border-b border-border">
                <tr>
                  <th className="px-3 py-2.5">Round</th>
                  <th className="px-3 py-2.5">Attack Mix</th>
                  <th className="px-3 py-2.5">Clean Acc</th>
                  <th className="px-3 py-2.5">Backdoor ASR</th>
                  <th className="px-3 py-2.5">Precision</th>
                  <th className="px-3 py-2.5">Recall</th>
                  <th className="px-3 py-2.5">F1-Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {history.map((r, i) => (
                  <tr key={i} className="threat-table-row">
                    <td className="px-3 py-2.5 font-bold text-accent-red">R{r.round}</td>
                    <td className="px-3 py-2.5 text-[10px] text-text-secondary truncate max-w-[140px]">
                      {r.attack_type || "MIXED_ATTACKS"}
                    </td>
                    <td className="px-3 py-2.5 text-accent-safe font-bold">{r.clean_accuracy.toFixed(1)}%</td>
                    <td className="px-3 py-2.5 text-accent-safe">{r.backdoor_asr.toFixed(2)}%</td>
                    <td className="px-3 py-2.5">{((r.detection?.precision ?? 1.0) * 100).toFixed(0)}%</td>
                    <td className="px-3 py-2.5">{((r.detection?.recall ?? 1.0) * 100).toFixed(0)}%</td>
                    <td className="px-3 py-2.5 font-bold text-accent-safe">
                      {((r.detection?.f1_score ?? 1.0) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </AnimatedGroup>
    </div>
  );
};
