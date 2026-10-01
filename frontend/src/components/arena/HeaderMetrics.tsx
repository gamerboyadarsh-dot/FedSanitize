import React from "react";
import type { ArenaSummary } from "../../types/telemetry";

interface Props {
  summary: ArenaSummary;
}

export const HeaderMetrics: React.FC<Props> = ({ summary }) => {
  const accVal = summary.clean_accuracy > 1 ? summary.clean_accuracy : summary.clean_accuracy * 100;
  const asrVal = summary.backdoor_asr > 1 ? summary.backdoor_asr : summary.backdoor_asr * 100;
  const asrColor = asrVal < 5 ? "var(--green)" : "var(--red)";

  const getThreatTierChip = (tier: string) => {
    switch (tier) {
      case "CRITICAL":
      case "HIGH":
        return "ds-chip ds-chip-danger ds-chip-no-dot";
      case "MEDIUM":
        return "ds-chip ds-chip-warning ds-chip-no-dot";
      case "LOW":
      default:
        return "ds-chip ds-chip-pass ds-chip-no-dot";
    }
  };

  return (
    <div className="ds-card p-5 mb-5">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border-subtle)]">
        {/* Round */}
        <div className="pt-2 sm:pt-0 sm:px-3 first:pl-0">
          <span className="eyebrow block mb-1">Replay Round</span>
          <div className="kpi-value text-2xl text-[var(--cyan)]">#{summary.round_id}</div>
          <span className="text-[11px] text-[var(--text-muted)] font-mono">Forensic Replay</span>
        </div>

        {/* Attack Vector */}
        <div className="pt-2 sm:pt-0 sm:px-3">
          <span className="eyebrow block mb-1">Attack Scenario</span>
          <div className="font-mono text-sm font-semibold text-[var(--text-primary)] truncate" title={summary.attack_type}>
            {summary.attack_type}
          </div>
          <span className="text-[11px] text-[var(--text-muted)]">Active Threat Vector</span>
        </div>

        {/* Severity */}
        <div className="pt-2 sm:pt-0 sm:px-3">
          <span className="eyebrow block mb-1">Threat Tier</span>
          <div className="flex items-center gap-1.5 mt-1">
            <span className={getThreatTierChip(summary.threat_tier)}>
              {summary.threat_tier}
            </span>
            <span className="font-mono text-xs text-[var(--text-secondary)]">({summary.threat_score}%)</span>
          </div>
          <span className="text-[11px] text-[var(--text-muted)] mt-1 block">Severity Score</span>
        </div>

        {/* Clean Acc */}
        <div className="pt-2 sm:pt-0 sm:px-3">
          <span className="eyebrow block mb-1">Clean Accuracy</span>
          <div className="kpi-value text-2xl text-[var(--green)]">
            {accVal.toFixed(1)}%
          </div>
          <span className="text-[11px] text-[var(--green)] font-medium">Preserved Global</span>
        </div>

        {/* Backdoor ASR */}
        <div className="pt-2 sm:pt-0 sm:px-3">
          <span className="eyebrow block mb-1">Backdoor ASR</span>
          <div className="kpi-value text-2xl" style={{ color: asrColor }}>
            {asrVal.toFixed(2)}%
          </div>
          <span className="text-[11px] text-[var(--text-muted)] font-medium">
            {asrVal < 2 ? "Suppressed" : "Active Attack"}
          </span>
        </div>

        {/* Sanitization */}
        <div className="pt-2 sm:pt-0 sm:px-3">
          <span className="eyebrow block mb-1">Defense Status</span>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="ds-chip ds-chip-pass ds-chip-no-dot text-[11px] py-0.5">
              {summary.trusted_count} Trusted
            </span>
            <span className="ds-chip ds-chip-danger ds-chip-no-dot text-[11px] py-0.5">
              {summary.quarantined_count} Quarantined
            </span>
          </div>
          <span className="text-[11px] text-[var(--text-muted)] mt-1 block">Cohort Distribution</span>
        </div>
      </div>
    </div>
  );
};
