import React from "react";
import type { ArenaSecurityEvent } from "../../types/telemetry";

interface AlertBannerProps {
  event: ArenaSecurityEvent;
}

const SEV_COLORS: Record<string, string> = {
  INFO: "#58A6FF", WARNING: "#FFB300", HIGH: "#FF7043", CRITICAL: "#FF1744",
};

export const AlertBanner: React.FC<AlertBannerProps> = ({ event }) => {
  const col = SEV_COLORS[event.severity] ?? "#58A6FF";
  const isCritical = event.severity === "CRITICAL" || event.severity === "HIGH";
  const bg = isCritical ? "rgba(255,23,68,0.08)" : "rgba(0,229,255,0.06)";
  const isQuarantine = event.event_type === "MARS_CLIENT_QUARANTINED" || event.event_type === "LAYER1_CLIENT_FLAGGED";

  return (
    <div style={{ marginBottom: 10 }}>
      {/* Alert banner */}
      <div style={{
        background: bg,
        borderLeft: `4px solid ${col}`,
        padding: "10px 14px",
        borderRadius: "0 6px 6px 0",
        marginBottom: 6,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          {event.layer && (
            <span style={{ background: "#21262D", color: col, border: `1px solid ${col}`, padding: "2px 6px", borderRadius: 3, fontWeight: "bold", fontSize: 11, fontFamily: "monospace" }}>
              {event.layer}
            </span>
          )}
          {event.client_id && (
            <span style={{ background: "#30363D", color: "#FFF", padding: "2px 6px", borderRadius: 3, fontWeight: "bold", fontSize: 11, fontFamily: "monospace" }}>
              {event.client_id}
            </span>
          )}
          <span style={{ color: "#F0F6FC", fontSize: 13, fontWeight: 500 }}>{event.message}</span>
        </div>
        <span style={{ background: col, color: "#0D1117", fontWeight: "bold", fontSize: 11, padding: "2px 8px", borderRadius: 4, flexShrink: 0, fontFamily: "monospace" }}>
          {event.severity}
        </span>
      </div>

      {/* Quarantine card */}
      {isQuarantine && event.client_id && (
        <div style={{ background: "rgba(255,23,68,0.1)", border: "1px solid #FF1744", borderRadius: 6, padding: 12, marginBottom: 8 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 18 }}>🚫</span>
              <div>
                <div style={{ fontWeight: "bold", color: "#FF5252", fontSize: 14, fontFamily: "monospace" }}>
                  CLIENT {event.client_id} ISOLATED & QUARANTINED
                </div>
                <div style={{ color: "#8B949E", fontSize: 12 }}>
                  Mitigating Layer: <b style={{ color: "#F0F6FC" }}>{event.layer ?? "FIREWALL"}</b>
                </div>
              </div>
            </div>
            <div style={{ background: "#FF1744", color: "#FFF", fontSize: 11, fontWeight: "bold", padding: "3px 8px", borderRadius: 4, fontFamily: "monospace" }}>
              LINK SEVERED
            </div>
          </div>
          <div style={{ marginTop: 8, background: "#0D1117", borderRadius: 4, padding: 8, fontSize: 12, color: "#E6EDF3", fontFamily: "monospace" }}>
            <b>Forensic Rationale:</b> {(event.payload?.reason as string) ?? event.message}
          </div>
        </div>
      )}
    </div>
  );
};
