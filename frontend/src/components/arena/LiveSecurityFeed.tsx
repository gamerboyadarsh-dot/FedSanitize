import React, { useRef, useEffect } from "react";
import type { ArenaSecurityEvent } from "../../types/telemetry";
import { Activity, Radio, AlertTriangle, ShieldCheck, ShieldAlert, Info } from "lucide-react";

interface Props {
  events: ArenaSecurityEvent[];
  maxItems?: number;
}

const TYPE_ICONS: Record<string, string> = {
  ROUND_STARTED: "🌐",
  CLIENT_TRAINING_STARTED: "⚡",
  ATTACK_ACTIVATED: "⚠️",
  CLIENT_UPDATE_SENT: "📤",
  LAYER1_CLIENT_FLAGGED: "🚨",
  MARS_CLIENT_QUARANTINED: "🚫",
  AGGREGATION_FINISHED: "🛡️",
  ROUND_COMPLETED: "🏁",
  MARS_WARNING: "⚠️",
  LAYER1_SCAN_STARTED: "🔍",
  MARS_SCAN_STARTED: "🧬",
};

export const LiveSecurityFeed: React.FC<Props> = ({ events, maxItems = 12 }) => {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { if (ref.current) ref.current.scrollTop = 0; }, [events]);
  const recent = [...events].reverse().slice(0, maxItems);

  const getSeverityChip = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
      case "HIGH":
        return "ds-chip ds-chip-danger ds-chip-no-dot text-[10px] py-0.5 px-2";
      case "WARNING":
        return "ds-chip ds-chip-warning ds-chip-no-dot text-[10px] py-0.5 px-2";
      case "INFO":
      default:
        return "ds-chip ds-chip-info ds-chip-no-dot text-[10px] py-0.5 px-2";
    }
  };

  return (
    <div className="flex flex-col h-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-xl min-h-[360px] max-h-[520px] overflow-hidden">
      {/* Feed Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)] shrink-0">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-[var(--cyan)] animate-pulse" />
          <span className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
            Live Security Feed
          </span>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-sans text-[var(--green)]">
          <span className="w-2 h-2 rounded-full bg-[var(--green)] animate-ping" />
          <span>Active Telemetry</span>
        </span>
      </div>

      {/* Feed Timeline Items */}
      <div ref={ref} className="overflow-y-auto flex-1 p-3 space-y-2 scroll-fade-y">
        {recent.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-16 gap-2.5 text-[var(--text-muted)]">
            <Activity className="w-8 h-8 opacity-40" />
            <p className="text-xs font-medium">Awaiting arena security telemetry...</p>
            <p className="text-[11px] text-center max-w-[200px] leading-relaxed">
              Click "Run Animated Simulation" or scrub the timeline to stream events.
            </p>
          </div>
        ) : (
          recent.map((evt, i) => {
            const icon = TYPE_ICONS[evt.event_type] ?? "📌";
            return (
              <div 
                key={i} 
                className="p-2.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-colors"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-xs shrink-0">{icon}</span>
                    <span className={getSeverityChip(evt.severity)}>
                      {evt.severity}
                    </span>
                    <span className="text-[11px] font-mono text-[var(--text-secondary)] truncate">
                      {evt.event_type}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[var(--text-muted)] shrink-0">
                    +{evt.timestamp.toFixed(1)}s
                  </span>
                </div>
                <div className="text-[12px] text-[var(--text-primary)] leading-snug pl-4">
                  {evt.client_id && (
                    <span className="font-mono font-bold text-[var(--cyan)] mr-1">
                      [{evt.client_id}]
                    </span>
                  )}
                  <span>{evt.message}</span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Feed Footer */}
      <div className="px-4 py-2 bg-[var(--bg-surface)] border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)] flex items-center justify-between shrink-0 font-mono">
        <span>Logged Events: {events.length}</span>
        <span>Buffer: {Math.min(events.length, maxItems)}</span>
      </div>
    </div>
  );
};
