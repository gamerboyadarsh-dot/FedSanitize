import React, { useRef, useEffect } from "react";
import type { ArenaSecurityEvent } from "../../types/telemetry";

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

const SEV_COLORS: Record<string, string> = {
  INFO: "#00E5FF",
  WARNING: "#FFB300",
  HIGH: "#FF7043",
  CRITICAL: "#FF1744",
};

export const LiveSecurityFeed: React.FC<Props> = ({ events, maxItems = 10 }) => {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { if (ref.current) ref.current.scrollTop = 0; }, [events]);
  const recent = [...events].reverse().slice(0, maxItems);

  return (
    <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, display: "flex", flexDirection: "column", minHeight: 320, maxHeight: 520 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", borderBottom: "1px solid #30363D", flexShrink: 0 }}>
        <span style={{ fontSize: 12, fontWeight: "bold", fontFamily: "monospace", color: "#F0F6FC" }}>📡 LIVE SECURITY FEED</span>
        <span style={{ fontSize: 10, fontFamily: "monospace", color: "#00E676", display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#00E676", display: "inline-block" }} />
          LIVE STREAM
        </span>
      </div>
      <div ref={ref} style={{ overflowY: "auto", flex: 1 }}>
        {recent.length === 0 ? (
          <div style={{ padding: 16, fontSize: 11, color: "#8B949E", fontFamily: "monospace" }}>Awaiting security telemetry...</div>
        ) : (
          recent.map((evt, i) => {
            const icon = TYPE_ICONS[evt.event_type] ?? "📌";
            const col = SEV_COLORS[evt.severity] ?? "#00E5FF";
            return (
              <div key={i} style={{ padding: "6px 12px", borderBottom: "1px solid #21262D" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ color: col, fontWeight: "bold", fontSize: 10, fontFamily: "monospace" }}>{icon} {evt.event_type}</span>
                  <span style={{ color: "#6E7681", fontSize: 10, fontFamily: "monospace" }}>+{evt.timestamp.toFixed(1)}s</span>
                </div>
                <div style={{ color: "#C9D1D9", fontSize: 11, marginTop: 2, fontFamily: "monospace" }}>
                  {evt.client_id && <b>[{evt.client_id}] </b>}{evt.message}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
