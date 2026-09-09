import React from "react";
import type { ArenaSummary } from "../../types/telemetry";

interface Props {
  summary: ArenaSummary;
}

const THREAT_COLORS: Record<string, string> = {
  LOW: "#00E676", MEDIUM: "#FFB300", HIGH: "#FF7043", CRITICAL: "#FF1744",
};

export const HeaderMetrics: React.FC<Props> = ({ summary }) => {
  const accVal = summary.clean_accuracy > 1 ? summary.clean_accuracy : summary.clean_accuracy * 100;
  const asrVal = summary.backdoor_asr > 1 ? summary.backdoor_asr : summary.backdoor_asr * 100;
  const asrColor = asrVal < 5 ? "#00E676" : "#FF1744";
  const threatColor = THREAT_COLORS[summary.threat_tier] ?? "#FFB300";

  const items = [
    { label: "ROUND", value: `#${summary.round_id}`, color: "#F0F6FC", size: 20 },
    { label: "ACTIVE ATTACK VECTOR", value: summary.attack_type, color: "#58A6FF", size: 14 },
    { label: "THREAT SEVERITY", value: `${summary.threat_tier} (${summary.threat_score}%)`, color: threatColor, size: 16 },
    { label: "CLEAN ACCURACY", value: `${accVal.toFixed(2)}%`, color: "#00E676", size: 18 },
    { label: "BACKDOOR ASR", value: `${asrVal.toFixed(2)}%`, color: asrColor, size: 18 },
    { label: "DEFENSE SANITIZATION", value: `${summary.trusted_count} Trusted / ${summary.quarantined_count} Quarantined`, color: "#F0F6FC", size: 13, split: [summary.trusted_count, summary.quarantined_count] },
  ];

  return (
    <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: "14px 18px", marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        {items.map((item, i) => (
          <div key={i} style={i > 0 ? { borderLeft: "1px solid #30363D", paddingLeft: 14 } : {}}>
            <div style={{ fontSize: 11, textTransform: "uppercase", color: "#8B949E", letterSpacing: 1 }}>{item.label}</div>
            {item.split ? (
              <div style={{ fontSize: item.size, fontWeight: "bold", color: item.color }}>
                <span style={{ color: "#00E676" }}>{item.split[0]} Trusted</span>
                {" / "}
                <span style={{ color: "#FF5252" }}>{item.split[1]} Quarantined</span>
              </div>
            ) : (
              <div style={{ fontSize: item.size, fontWeight: "bold", color: item.color }}>{item.value}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
