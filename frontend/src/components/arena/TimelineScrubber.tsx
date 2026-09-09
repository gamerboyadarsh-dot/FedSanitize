import React from "react";
import type { ArenaTimelineStep } from "../../types/telemetry";

interface Props {
  steps: ArenaTimelineStep[];
  currentStepIdx: number;
}

const SCENES = ["INTRO","TRAINING","ATTACK","UPDATE_FLOW","LAYER1","MARS","AGGREGATION","RESULT"];
const SCENE_LABELS: Record<string, string> = {
  INTRO: "INIT", TRAINING: "TRAIN", ATTACK: "ATTACK", UPDATE_FLOW: "UPDATES",
  LAYER1: "LAYER 1", MARS: "MARS", AGGREGATION: "AGGREGATE", RESULT: "RESULT",
};

export const TimelineScrubber: React.FC<Props> = ({ steps, currentStepIdx }) => {
  if (!steps.length) return null;
  const total = steps.length;
  const idx = Math.min(currentStepIdx, total - 1);
  const current = steps[idx];
  const pct = total > 1 ? (idx / (total - 1)) * 100 : 0;
  const activeScene = current.scene;

  return (
    <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: "12px 16px", marginTop: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, flexWrap: "wrap", gap: 6 }}>
        <span style={{ fontSize: 12, fontWeight: "bold", fontFamily: "monospace", color: "#F0F6FC" }}>
          ⏳ TIMELINE STEP {idx + 1} / {total}&nbsp;|&nbsp;
          <span style={{ color: "#00E5FF" }}>{activeScene}</span>
        </span>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {SCENES.map((scn) => {
            const isActive = activeScene === scn || (activeScene.includes(scn) || scn.includes(activeScene));
            return (
              <span
                key={scn}
                style={{
                  background: isActive ? "#00E5FF" : "#21262D",
                  color: isActive ? "#0D1117" : "#8B949E",
                  fontSize: 10,
                  fontWeight: isActive ? "bold" : "normal",
                  padding: "3px 8px",
                  borderRadius: 10,
                  border: isActive ? "1px solid #00E5FF" : "1px solid #30363D",
                  fontFamily: "monospace",
                }}
              >
                {SCENE_LABELS[scn] ?? scn}
              </span>
            );
          })}
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ width: "100%", height: 6, background: "#30363D", borderRadius: 3, margin: "8px 0" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg, #58A6FF, #00E5FF)", borderRadius: 3, transition: "width 0.3s ease" }} />
      </div>

      {/* Current event description */}
      <div style={{ color: "#F0F6FC", fontSize: 13, marginTop: 6, background: "rgba(0,229,255,0.05)", padding: "8px 12px", borderRadius: 4, borderLeft: "3px solid #00E5FF", fontFamily: "monospace" }}>
        <b>{current.event.event_type}</b>: {current.description}
      </div>
    </div>
  );
};
