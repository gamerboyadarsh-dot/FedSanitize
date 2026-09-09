import React from "react";

interface BackdoorStagesProps {
  currentStage?: number;
}

const STAGES = [
  ["STAGE 1: Clean Input", "Normal handwriting digits from private user dataset."],
  ["STAGE 2: Trigger Injection", "4-pixel bottom-right trigger pattern inserted into target samples."],
  ["STAGE 3: Target Label Reassignment", "Poisoned samples assigned malicious target class (e.g. 7 → 0)."],
  ["STAGE 4: Poisoned Client Training", "Local SGD trains SmallCNN to recognize the backdoor trigger watermark."],
  ["STAGE 5: Stealthy Update Delta", "Parameter norm and overall cosine similarity mimic honest clients."],
  ["STAGE 6: Layer 1 Parameter Scan", "Statistical filter passes update: No obvious weight-space anomaly detected."],
  ["STAGE 7: MARS Escalation", "Deep representation forensics extracts Backdoor Energy & CBE concentration ratios."],
  ["STAGE 8: Quarantine & Sanitization", "Wasserstein distance clustering isolates backdoor client; global model sanitized."],
];

export const BackdoorStages: React.FC<BackdoorStagesProps> = ({ currentStage = 6 }) => {
  return (
    <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: 14 }}>
      <div style={{ color: "#FF5252", fontWeight: "bold", fontSize: 14, marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
        🎯 Flagship Backdoor Attack & MARS Forensic Lifecycle
      </div>
      {STAGES.map(([title, desc], idx) => {
        const stage = idx + 1;
        const isActive = stage === currentStage;
        const isPast = stage < currentStage;
        const bg = isActive ? "rgba(0,229,255,0.1)" : isPast ? "rgba(0,230,118,0.05)" : "#0D1117";
        const border = isActive ? "#00E5FF" : isPast ? "#00E676" : "#30363D";
        const badgeColor = isActive ? "#00E5FF" : isPast ? "#00E676" : "#8B949E";
        const icon = isActive ? "📍" : isPast ? "✓" : `${stage}`;
        return (
          <div key={stage} style={{ background: bg, borderLeft: `4px solid ${border}`, padding: "10px 14px", marginBottom: 8, borderRadius: "0 6px 6px 0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontWeight: "bold", color: "#F0F6FC", fontSize: 13, fontFamily: "monospace" }}>{title}</span>
              <span style={{ background: border, color: "#0D1117", fontWeight: "bold", fontSize: 11, padding: "2px 6px", borderRadius: 4, fontFamily: "monospace" }}>
                {icon}
              </span>
            </div>
            <div style={{ color: "#8B949E", fontSize: 12, marginTop: 4 }}>{desc}</div>
          </div>
        );
      })}
    </div>
  );
};
