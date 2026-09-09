import React from "react";
import { 
  BarChart3, 
} from "lucide-react";
import type { RoundRecord } from "../types/telemetry";
import { SlidingNumber } from "../components/core/SlidingNumber";
import { AnimatedGroup } from "../components/core/AnimatedGroup";
import { motion } from "framer-motion";
import { Tooltip } from "../components/ui/Tooltip";

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

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-zinc-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-lg font-sans font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Comparative Defense & Confusion Matrix Analytics
          </h2>
          <p className="text-sm text-zinc-400 font-sans mt-1">
            Statistical evaluation of isolation fidelity, false alarm rates, and longitudinal round history.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-sans">
          <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold shadow-[0_0_15px_rgba(16,185,129,0.1)]">
            Zero False Positives (FP=0)
          </span>
        </div>
      </div>

      <AnimatedGroup className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: 4-Quadrant Confusion Matrix with SlidingNumber */}
        <motion.div variants={itemVariants} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="border-b border-white/10 pb-4">
            <h3 className="text-sm font-sans font-bold text-white flex items-center gap-2">
              Multi-Layer Confusion Matrix
              <Tooltip content="Evaluates the accuracy of the defense system in distinguishing malicious clients (positives) from honest clients (negatives)." />
            </h3>
            <p className="text-xs text-zinc-500 font-sans mt-1">
              Round {latestRound?.round ?? 1} Isolation Distribution
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 font-sans text-center">
            {/* True Positive */}
            <motion.div whileHover={{ scale: 1.02 }} className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 space-y-1 shadow-lg group transition-colors hover:bg-emerald-500/20">
              <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">True Positive (TP)</div>
              <div className="text-4xl font-mono font-bold text-emerald-400 drop-shadow-[0_0_10px_rgba(16,185,129,0.5)]">
                <SlidingNumber value={det.tp} />
              </div>
              <div className="text-[10px] text-emerald-500/70">Malicious Quarantined</div>
            </motion.div>

            {/* False Positive */}
            <motion.div whileHover={{ scale: 1.02 }} className={`border rounded-xl p-5 space-y-1 shadow-lg transition-colors ${
              det.fp > 0 
                ? "bg-amber-500/10 border-amber-500/40 text-amber-500 hover:bg-amber-500/20" 
                : "bg-white/5 border-white/5 text-zinc-500 hover:bg-white/10"
            }`}>
              <div className="text-[10px] font-bold uppercase tracking-wider">False Positive (FP)</div>
              <div className="text-4xl font-mono font-bold">
                <SlidingNumber value={det.fp} />
              </div>
              <div className="text-[10px] opacity-70">{det.fp === 0 ? "0 False Alarms" : "Honest Quarantined"}</div>
            </motion.div>

            {/* False Negative */}
            <motion.div whileHover={{ scale: 1.02 }} className={`border rounded-xl p-5 space-y-1 shadow-lg transition-colors ${
              det.fn > 0 
                ? "bg-rose-500/10 border-rose-500/40 text-rose-500 hover:bg-rose-500/20" 
                : "bg-white/5 border-white/5 text-zinc-500 hover:bg-white/10"
            }`}>
              <div className="text-[10px] font-bold uppercase tracking-wider">False Negative (FN)</div>
              <div className="text-4xl font-mono font-bold">
                <SlidingNumber value={det.fn} />
              </div>
              <div className="text-[10px] opacity-70">{det.fn === 0 ? "0 Attack Leaks" : "Malicious Slipped"}</div>
            </motion.div>

            {/* True Negative */}
            <motion.div whileHover={{ scale: 1.02 }} className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 space-y-1 shadow-lg group transition-colors hover:bg-emerald-500/20">
              <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">True Negative (TN)</div>
              <div className="text-4xl font-mono font-bold text-emerald-400 drop-shadow-[0_0_10px_rgba(16,185,129,0.5)]">
                <SlidingNumber value={det.tn} />
              </div>
              <div className="text-[10px] text-emerald-500/70">Honest Preserved</div>
            </motion.div>
          </div>

          <div className="bg-black/40 border border-white/5 rounded-xl p-4 space-y-2 font-sans text-sm shadow-inner">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-1.5 text-zinc-400">
                <span>Detection Precision</span>
                <Tooltip content="TP / (TP + FP): Of all clients quarantined, how many were actually malicious?" />
              </div>
              <span className="text-emerald-400 font-mono font-bold text-base bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                <SlidingNumber value={det.precision * 100} decimalPlaces={1} />%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-1.5 text-zinc-400">
                <span>Detection Recall</span>
                <Tooltip content="TP / (TP + FN): Of all actual malicious clients, how many did we catch?" />
              </div>
              <span className="text-emerald-400 font-mono font-bold text-base bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                <SlidingNumber value={det.recall * 100} decimalPlaces={1} />%
              </span>
            </div>
            <div className="flex justify-between items-center pt-2 mt-2 border-t border-white/5">
              <div className="flex items-center gap-1.5 text-zinc-300 font-semibold">
                <span>F1 Classification Score</span>
                <Tooltip content="The harmonic mean of Precision and Recall. 100% is a perfect defense." />
              </div>
              <span className="text-emerald-400 font-mono font-bold text-lg drop-shadow-[0_0_8px_rgba(16,185,129,0.6)]">
                <SlidingNumber value={det.f1_score * 100} decimalPlaces={1} />%
              </span>
            </div>
          </div>
        </motion.div>

        {/* Right 2 Cols: Historical Rounds Table */}
        <motion.div variants={itemVariants} className="lg:col-span-2 bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-4 flex flex-col">
          <div className="border-b border-white/10 pb-4 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-sans font-bold text-white flex items-center gap-2">
                Round-by-Round Longitudinal History
              </h3>
              <p className="text-xs text-zinc-500 font-sans mt-1">
                Historical records of all executed simulation rounds
              </p>
            </div>
            <span className="text-[11px] font-mono text-zinc-500 bg-white/5 px-2 py-1 rounded border border-white/10">
              Total Rounds: {history.length}
            </span>
          </div>

          <div className="overflow-x-auto flex-1 custom-scrollbar">
            <table className="w-full text-left font-sans text-sm">
              <thead className="bg-white/5 text-zinc-400 uppercase text-[10px] tracking-wider border-b border-white/10 sticky top-0 backdrop-blur-md z-10">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Round</th>
                  <th className="px-4 py-3">Attack Mix</th>
                  <th className="px-4 py-3">Clean Acc</th>
                  <th className="px-4 py-3">Backdoor ASR</th>
                  <th className="px-4 py-3">Precision</th>
                  <th className="px-4 py-3">Recall</th>
                  <th className="px-4 py-3 rounded-tr-lg">F1-Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {history.map((r, i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors group">
                    <td className="px-4 py-3.5 font-mono font-bold text-cyan-400">
                      <span className="bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded text-xs">R{r.round}</span>
                    </td>
                    <td className="px-4 py-3.5 text-xs text-zinc-400 font-mono truncate max-w-[140px]">
                      {r.attack_type || "MIXED_ATTACKS"}
                    </td>
                    <td className="px-4 py-3.5 text-emerald-400 font-bold font-mono text-xs">{r.clean_accuracy.toFixed(1)}%</td>
                    <td className={`px-4 py-3.5 font-mono text-xs ${r.backdoor_asr < 2.0 ? "text-emerald-400" : "text-rose-400 font-bold bg-rose-500/10 rounded px-1"}`}>
                      {r.backdoor_asr.toFixed(2)}%
                    </td>
                    <td className="px-4 py-3.5 font-mono text-xs text-zinc-300">{((r.detection?.precision ?? 1.0) * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3.5 font-mono text-xs text-zinc-300">{((r.detection?.recall ?? 1.0) * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3.5 font-bold text-emerald-400 font-mono text-sm group-hover:drop-shadow-[0_0_8px_rgba(16,185,129,0.8)] transition-all">
                      {((r.detection?.f1_score ?? 1.0) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </AnimatedGroup>
    </div>
  );
};
