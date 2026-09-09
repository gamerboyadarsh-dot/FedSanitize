import React from "react";
import type { ArenaSummary } from "../../types/telemetry";

interface Props {
  summary: ArenaSummary;
  activeLayer?: string;
}

export const PipelineStatusBar: React.FC<Props> = ({ summary, activeLayer }) => {
  const layers = [
    {
      key: "LAYER_1",
      title: "LAYER 1: STATISTICAL",
      badge: "L2 NORM + MAD",
      blocked: summary.l1_quarantined.length,
      desc: "Coarse magnitude & cosine outlier filter",
    },
    {
      key: "MARS",
      title: "LAYER 2: MARS FORENSICS",
      badge: "WAN ET AL. 2025",
      blocked: summary.mars_quarantined.length,
      desc: "Deep Backdoor Energy & Wasserstein clustering",
    },
    {
      key: "LAYER_3",
      title: "LAYER 3: AGGREGATION",
      badge: "TRIMMED MEAN",
      blocked: 0,
      desc: `${summary.trusted_count} verified client updates aggregated`,
    },
  ];

  return (
    <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
      {layers.map((l) => {
        const isActive = activeLayer === l.key;
        const border = isActive ? "#00E5FF" : "#30363D";
        const glow = isActive ? "0 0 10px rgba(0,229,255,0.15)" : "none";
        return (
          <div
            key={l.key}
            style={{
              flex: 1,
              minWidth: 200,
              background: "#161B22",
              border: `1px solid ${border}`,
              boxShadow: glow,
              borderRadius: 6,
              padding: "10px 14px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontWeight: "bold", color: "#F0F6FC", fontSize: 12, fontFamily: "monospace" }}>{l.title}</span>
              <span style={{
                fontSize: 10, background: isActive ? "#00E5FF" : "#30363D",
                color: isActive ? "#0D1117" : "#8B949E",
                fontWeight: "bold", padding: "1px 6px", borderRadius: 3, fontFamily: "monospace"
              }}>{l.badge}</span>
            </div>
            <div style={{ fontSize: 16, fontWeight: "bold", color: l.blocked > 0 ? "#FF5252" : "#00E676", margin: "4px 0" }}>
              {l.blocked} Quarantined
            </div>
            <div style={{ fontSize: 11, color: "#8B949E", fontFamily: "monospace" }}>{l.desc}</div>
          </div>
        );
      })}
    </div>
  );
};
