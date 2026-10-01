import React from "react";
import type { ArenaSummary } from "../../types/telemetry";
import { Filter, Activity, ShieldCheck } from "lucide-react";

interface Props {
  summary: ArenaSummary;
  activeLayer?: string;
}

export const PipelineStatusBar: React.FC<Props> = ({ summary, activeLayer }) => {
  const layers = [
    {
      key: "LAYER_1",
      title: "Layer 1: Statistical",
      badge: "L2 NORM + MAD",
      blocked: summary.l1_quarantined.length,
      desc: "Magnitude explosion & cosine outlier filter",
      icon: Filter,
      color: "var(--cyan)",
      tint: "var(--cyan-tint)",
      border: "var(--cyan-border)"
    },
    {
      key: "MARS",
      title: "Layer 2: MARS Forensics",
      badge: "NEURIPS 2025",
      blocked: summary.mars_quarantined.length,
      desc: "Deep Backdoor Energy & Wasserstein clustering",
      icon: Activity,
      color: "var(--purple)",
      tint: "var(--purple-tint)",
      border: "var(--purple-border)"
    },
    {
      key: "LAYER_3",
      title: "Layer 3: Robust Aggregation",
      badge: "TRIMMED MEAN",
      blocked: 0,
      desc: `${summary.trusted_count} verified client updates aggregated`,
      icon: ShieldCheck,
      color: "var(--green)",
      tint: "var(--green-tint)",
      border: "var(--green-border)"
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
      {layers.map((l) => {
        const isActive = activeLayer === l.key;
        const Icon = l.icon;
        return (
          <div
            key={l.key}
            className={`ds-card p-4 transition-all ${
              isActive ? "ds-card-active border-2" : ""
            }`}
            style={isActive ? { borderColor: l.color } : {}}
          >
            <div className="flex justify-between items-center pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <div 
                  className="w-6 h-6 rounded-md flex items-center justify-center"
                  style={{ background: l.tint, color: l.color }}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <span className="font-semibold text-xs text-[var(--text-primary)]">
                  {l.title}
                </span>
              </div>
              <span className="ds-chip ds-chip-neutral ds-chip-no-dot text-[10px] py-0.5 px-2">
                {l.badge}
              </span>
            </div>
            
            <div className="flex items-baseline justify-between mt-2.5">
              <span className="kpi-value text-xl" style={{ color: l.blocked > 0 ? "var(--red)" : "var(--green)" }}>
                {l.blocked > 0 ? `${l.blocked} Quarantined` : "All Clean / Passed"}
              </span>
            </div>
            
            <p className="text-[11px] text-[var(--text-muted)] mt-1 leading-snug">
              {l.desc}
            </p>
          </div>
        );
      })}
    </div>
  );
};
