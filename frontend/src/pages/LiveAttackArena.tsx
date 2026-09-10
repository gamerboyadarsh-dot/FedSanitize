/**
 * LiveAttackArena — React mirror of dashboard/simulation_arena.py
 * ==================================================================
 * Full interactive forensic replay & cybersecurity simulation page.
 * Features:
 *  - Header metrics bar (Round, Attack Vector, Threat Level, Clean Acc, Backdoor ASR, Sanitization)
 *  - 3-Layer Firewall Pipeline Status Bar
 *  - Scenario Selector dropdown (5 attack scenarios)
 *  - Playback Controls (Run Animated, Back, Next, Reset, Jump to End, Speed slider)
 *  - Timeline scrubber
 *  - Network Topology Graph (SVG radial, 10 clients + server)
 *  - Live Security Feed (right panel)
 *  - Active Alert Banner + Quarantine Card
 *  - 5 Forensic Tabs: Storyline, Client Dossier, L1 Analytics, MARS Forensics, Aggregation
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import type { ArenaData, ArenaSecurityEvent } from "../types/telemetry";
import { fetchArenaData } from "../api/client";
import { HeaderMetrics } from "../components/arena/HeaderMetrics";
import { PipelineStatusBar } from "../components/arena/PipelineStatusBar";
import { NetworkTopologyGraph } from "../components/arena/NetworkTopologyGraph";
import { LiveSecurityFeed } from "../components/arena/LiveSecurityFeed";
import { TimelineScrubber } from "../components/arena/TimelineScrubber";
import { AlertBanner } from "../components/arena/AlertBanner";
import { BackdoorStages } from "../components/arena/BackdoorStages";
import { ClientDossier } from "../components/arena/ClientDossier";
import {
  NormChart, CosineChart, CBEChart, ClusterScatter,
  AggregationChart, BeforeAfterComparison,
} from "../components/arena/ForensicCharts";

const SCENARIO_LABELS: Record<number, string> = {
  1: "🟢 Scenario 1: Clean Baseline (Honest Federated Learning)",
  2: "🚨 Scenario 2: Extreme Gradient Scaling (Layer 1 Norm Defense)",
  3: "🔄 Scenario 3: Sign Flipping Attack (Layer 1 Directional Defense)",
  4: "🎯 Scenario 4: Stealth Neural Backdoor (NeurIPS 2025 MARS Forensics)",
  5: "⚡ Scenario 5: Multi-Vector Combined Attack (Layer 1 + MARS Defense)",
};

const SPEED_OPTIONS = [0.5, 1.0, 2.0, 4.0];

type TabId = "storyline" | "dossier" | "layer1" | "mars" | "aggregation";

const TABS: { id: TabId; label: string }[] = [
  { id: "storyline", label: "📜 Attack Scenario Storyline" },
  { id: "dossier", label: "🔬 Client Forensic Dossier" },
  { id: "layer1", label: "🛡️ Layer 1 Anomaly Analytics" },
  { id: "mars", label: "🧬 MARS Backdoor Forensics (NeurIPS 2025)" },
  { id: "aggregation", label: "⚖️ Robust Aggregation & Benchmark" },
];

const MARSArchitectureDiagram: React.FC = () => (
  <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: 16, marginBottom: 14 }}>
    <div style={{ fontSize: 13, fontWeight: "bold", color: "#F0F6FC", marginBottom: 10, fontFamily: "monospace" }}>
      🧬 MARS Architecture — Multi-layer Anomaly Representation Scanning
    </div>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
      {["conv1 Features", "conv2 Features", "Backdoor Energy Score", "CBE / Wasserstein Clustering"].map((label, i) => (
        <div key={i} style={{ background: "#0D1117", border: "1px solid #21262D", borderRadius: 6, padding: "10px 12px", textAlign: "center" }}>
          <div style={{ fontSize: 18, marginBottom: 4 }}>{"🔷🔶🔬🔮".split("")[i]}</div>
          <div style={{ fontSize: 11, fontWeight: "bold", color: "#00E5FF", fontFamily: "monospace" }}>{label}</div>
          {i < 3 && (
            <div style={{ marginTop: 6, fontSize: 10, color: "#8B949E" }}>
              {i === 0 ? "First convolutional activations" : i === 1 ? "Deeper representation layer" : "Concentrated top-k activation energy"}
            </div>
          )}
        </div>
      ))}
    </div>
    <div style={{ marginTop: 12, fontSize: 11, color: "#8B949E", fontFamily: "monospace" }}>
      MARS (Wan et al., NeurIPS 2025) · arXiv:2509.20383 · CBE threshold: 0.015 · Wasserstein p-distance clustering
    </div>
  </div>
);

export const LiveAttackArena: React.FC = () => {
  const [arenaData, setArenaData] = useState<ArenaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRound, setSelectedRound] = useState(3); // 0-indexed, default = round 4 (backdoor)
  const [currentStep, setCurrentStep] = useState(0);
  const [speed, setSpeed] = useState(1.0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("storyline");
  const [selectedClient, setSelectedClient] = useState<string>("C0");
  const animRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadArena = useCallback(async (roundIdx: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchArenaData(roundIdx);
      setArenaData(data);
      setCurrentStep(0);
      // Auto-select first client
      const clients = Object.keys(data.client_security_records);
      if (clients.length > 0) setSelectedClient(clients[0]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load arena data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadArena(selectedRound);
  }, [selectedRound, loadArena]);

  // Animated playback
  const runAnimation = useCallback(() => {
    if (!arenaData || isAnimating) return;
    setIsAnimating(true);
    setCurrentStep(0);
    const total = arenaData.timeline_steps.length;
    const delay = Math.max(150, 750 / speed);
    let step = 0;

    const advance = () => {
      step++;
      if (step >= total) {
        setCurrentStep(total - 1);
        setIsAnimating(false);
        return;
      }
      setCurrentStep(step);
      animRef.current = setTimeout(advance, delay);
    };
    animRef.current = setTimeout(advance, delay);
  }, [arenaData, isAnimating, speed]);

  // Stop animation on unmount
  useEffect(() => () => { if (animRef.current) clearTimeout(animRef.current); }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 400, gap: 16 }}>
        <div style={{ fontSize: 32 }}>🛡️</div>
        <div style={{ color: "#00E5FF", fontFamily: "monospace", fontSize: 14 }}>Loading Arena Simulation Data...</div>
        <div style={{ color: "#8B949E", fontFamily: "monospace", fontSize: 12 }}>Reconstructing forensic telemetry via SimulationAdapter</div>
      </div>
    );
  }

  if (error || !arenaData) {
    return (
      <div style={{ background: "rgba(255,23,68,0.1)", border: "1px solid #FF1744", borderRadius: 8, padding: 20, margin: 20 }}>
        <div style={{ color: "#FF5252", fontWeight: "bold", fontFamily: "monospace", marginBottom: 8 }}>⚠️ Arena Data Unavailable</div>
        <div style={{ color: "#8B949E", fontSize: 13, marginBottom: 12 }}>
          {error ?? "Could not load simulation data"}<br />
          Make sure the FedSanitize FastAPI backend is running: <code style={{ color: "#00E5FF" }}>uvicorn backend_api.main:app --reload</code><br />
          Then load demo data via the header &ldquo;Load Demo&rdquo; button.
        </div>
        <button
          onClick={() => loadArena(selectedRound)}
          style={{ background: "#238636", color: "#FFF", border: "none", borderRadius: 6, padding: "8px 16px", cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}
        >
          ↺ Retry
        </button>
      </div>
    );
  }

  const { summary, timeline_steps, network_nodes, client_security_records, mars_data, scenario_narrative, total_rounds } = arenaData;
  const totalSteps = timeline_steps.length;
  const currentStepData = timeline_steps[Math.min(currentStep, totalSteps - 1)];
  const currentEvent: ArenaSecurityEvent | null = currentStepData?.event ?? null;
  const visibleEvents = timeline_steps.slice(0, currentStep + 1).map((s) => s.event);
  const isQuarantineEvent =
    currentEvent?.event_type === "LAYER1_CLIENT_FLAGGED" ||
    currentEvent?.event_type === "MARS_CLIENT_QUARANTINED";

  // Active layer from current step scene
  const sceneToLayer: Record<string, string> = { LAYER1: "LAYER_1", MARS: "MARS", AGGREGATION: "LAYER_3" };
  const activeLayer = sceneToLayer[currentStepData?.scene ?? ""] ?? "";

  const allClientIds = Object.keys(client_security_records).sort();

  return (
    <div style={{ fontFamily: "monospace" }}>
      {/* ── Header branding ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, color: "#F0F6FC", display: "flex", alignItems: "center", gap: 8 }}>
            🛡️ FedSanitize Live Attack Arena
          </h1>
          <p style={{ margin: "4px 0 0", color: "#8B949E", fontSize: 13 }}>
            Interactive Forensic Replay & Multi-Layer Cybersecurity Defense Simulation
          </p>
        </div>
        <span style={{ background: "#238636", color: "#FFF", fontSize: 12, fontWeight: "bold", padding: "4px 10px", borderRadius: 4 }}>
          ENGINE ACTIVE & READY
        </span>
      </div>

      {/* ── Scenario Selector + Mode ── */}
      <div style={{ display: "flex", gap: 12, marginBottom: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
        <div style={{ flex: 3 }}>
          <label style={{ display: "block", fontSize: 11, color: "#8B949E", marginBottom: 4 }}>SELECT ATTACK SCENARIO TO REPLAY</label>
          <select
            value={selectedRound}
            onChange={(e) => { setSelectedRound(Number(e.target.value)); setIsAnimating(false); if (animRef.current) clearTimeout(animRef.current); }}
            style={{ width: "100%", background: "#161B22", color: "#F0F6FC", border: "1px solid #30363D", borderRadius: 6, padding: "8px 12px", fontSize: 13, cursor: "pointer" }}
          >
            {Array.from({ length: total_rounds }, (_, i) => (
              <option key={i} value={i}>{SCENARIO_LABELS[i + 1] ?? `Round ${i + 1}: Scenario`}</option>
            ))}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ background: "rgba(0,229,255,0.06)", border: "1px solid rgba(0,229,255,0.2)", borderRadius: 6, padding: "8px 12px", fontSize: 12, color: "#8B949E" }}>
            💡 Forensic replay loaded with real metrics from experiment dataset.
          </div>
        </div>
      </div>

      {/* ── Header Metrics Bar ── */}
      <HeaderMetrics summary={summary} />

      {/* ── 3-Layer Pipeline Status ── */}
      <PipelineStatusBar summary={summary} activeLayer={activeLayer} />

      {/* ── Playback Controls ── */}
      <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: "12px 16px", marginBottom: 14 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
          {/* Run Animated */}
          <button
            onClick={runAnimation}
            disabled={isAnimating}
            style={{
              background: isAnimating ? "#21262D" : "#238636",
              color: isAnimating ? "#8B949E" : "#FFF",
              border: "none", borderRadius: 6, padding: "8px 18px",
              fontWeight: "bold", fontSize: 13, cursor: isAnimating ? "not-allowed" : "pointer",
              fontFamily: "monospace",
            }}
          >
            {isAnimating ? "⏳ Animating..." : "▶ Run Animated Simulation"}
          </button>

          {/* Back */}
          <button
            onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
            disabled={isAnimating || currentStep === 0}
            style={{ background: "#21262D", color: "#F0F6FC", border: "1px solid #30363D", borderRadius: 6, padding: "8px 14px", cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}
          >
            ⏮ Back
          </button>

          {/* Next */}
          <button
            onClick={() => setCurrentStep((s) => Math.min(totalSteps - 1, s + 1))}
            disabled={isAnimating || currentStep === totalSteps - 1}
            style={{ background: "#21262D", color: "#F0F6FC", border: "1px solid #30363D", borderRadius: 6, padding: "8px 14px", cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}
          >
            ⏭ Next
          </button>

          {/* Reset */}
          <button
            onClick={() => { setCurrentStep(0); setIsAnimating(false); if (animRef.current) clearTimeout(animRef.current); }}
            style={{ background: "#21262D", color: "#F0F6FC", border: "1px solid #30363D", borderRadius: 6, padding: "8px 14px", cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}
          >
            ↺ Reset
          </button>

          {/* Jump to End */}
          <button
            onClick={() => { setCurrentStep(totalSteps - 1); setIsAnimating(false); if (animRef.current) clearTimeout(animRef.current); }}
            style={{ background: "#21262D", color: "#F0F6FC", border: "1px solid #30363D", borderRadius: 6, padding: "8px 14px", cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}
          >
            ⏩ Jump to End
          </button>

          {/* Speed */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: "auto" }}>
            <span style={{ color: "#8B949E", fontSize: 11 }}>Speed:</span>
            {SPEED_OPTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                style={{
                  background: speed === s ? "#00E5FF" : "#21262D",
                  color: speed === s ? "#0D1117" : "#F0F6FC",
                  border: `1px solid ${speed === s ? "#00E5FF" : "#30363D"}`,
                  borderRadius: 4, padding: "4px 10px",
                  cursor: "pointer", fontFamily: "monospace", fontSize: 12, fontWeight: speed === s ? "bold" : "normal",
                }}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Scrubber slider */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 11, color: "#8B949E", whiteSpace: "nowrap" }}>Step {currentStep + 1} / {totalSteps}</span>
          <input
            type="range"
            min={0}
            max={totalSteps - 1}
            value={currentStep}
            disabled={isAnimating}
            onChange={(e) => setCurrentStep(Number(e.target.value))}
            style={{ flex: 1, accentColor: "#00E5FF" }}
          />
          <span style={{ fontSize: 11, color: "#8B949E", whiteSpace: "nowrap" }}>End</span>
        </div>
      </div>

      {/* ── Main Area: Network Graph + Right Panel ── */}
      <div style={{ display: "grid", gridTemplateColumns: "7fr 3fr", gap: 14, marginBottom: 20 }}>
        {/* Left: Network + Timeline */}
        <div>
          <NetworkTopologyGraph
            nodes={network_nodes}
            selectedClient={selectedClient}
            onSelectClient={setSelectedClient}
          />
          <TimelineScrubber steps={timeline_steps} currentStepIdx={currentStep} />

          {/* Animation progress bar when animating */}
          {isAnimating && (
            <div style={{ marginTop: 8, background: "#21262D", borderRadius: 3, height: 4 }}>
              <div
                style={{
                  width: `${((currentStep + 1) / totalSteps) * 100}%`,
                  height: "100%",
                  background: "linear-gradient(90deg, #238636, #00E676)",
                  borderRadius: 3,
                  transition: "width 0.2s ease",
                }}
              />
            </div>
          )}
          {currentStep === totalSteps - 1 && !isAnimating && totalSteps > 1 && (
            <div style={{ marginTop: 8, background: "rgba(0,230,118,0.08)", border: "1px solid #00E676", borderRadius: 6, padding: "8px 12px", fontSize: 12, color: "#00E676", fontFamily: "monospace" }}>
              🏁 Simulation completed! All compromised updates quarantined. Model safely sanitized.
            </div>
          )}
        </div>

        {/* Right: Live Security Feed + Alerts */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <LiveSecurityFeed events={visibleEvents} maxItems={10} />
          {currentEvent && (
            <AlertBanner event={currentEvent} />
          )}
        </div>
      </div>

      {/* ── Forensic Drilldown Tabs ── */}
      <div style={{ borderTop: "1px solid #30363D", paddingTop: 20 }}>
        {/* Tab buttons */}
        <div style={{ display: "flex", gap: 4, marginBottom: 16, flexWrap: "wrap" }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? "#21262D" : "transparent",
                color: activeTab === tab.id ? "#F0F6FC" : "#8B949E",
                border: activeTab === tab.id ? "1px solid #30363D" : "1px solid transparent",
                borderBottom: activeTab === tab.id ? "2px solid #00E5FF" : "1px solid transparent",
                borderRadius: "6px 6px 0 0",
                padding: "8px 14px",
                cursor: "pointer",
                fontFamily: "monospace",
                fontSize: 12,
                fontWeight: activeTab === tab.id ? "bold" : "normal",
                transition: "all 0.15s",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ─── Tab: Attack Scenario Storyline ─── */}
        {activeTab === "storyline" && (
          <div>
            <h3 style={{ color: "#F0F6FC", marginBottom: 8 }}>🎯 Scenario Walkthrough: {scenario_narrative.title}</h3>
            <div style={{ background: "rgba(88,166,255,0.08)", border: "1px solid rgba(88,166,255,0.2)", borderRadius: 6, padding: "10px 14px", marginBottom: 12, color: "#F0F6FC", fontSize: 13 }}>
              <b>Threat Vector:</b> {scenario_narrative.headline}
            </div>
            <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: 14, marginBottom: 12 }}>
              <div style={{ marginBottom: 8 }}><b>Technical Explanation:</b> {scenario_narrative.technical_explanation}</div>
              <div style={{ marginBottom: 8 }}><b>Mitigating Defense Layer:</b> <span style={{ color: "#00E676", fontWeight: "bold" }}>{scenario_narrative.mitigating_layer}</span></div>
              <div><b>Forensic Investigation Focus:</b> {scenario_narrative.forensic_focus}</div>
            </div>

            {/* Attack-type specific visual */}
            {scenario_narrative.attack_type === "BACKDOOR" && <BackdoorStages currentStage={6} />}
            {scenario_narrative.attack_type !== "BACKDOOR" && (
              <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: 14 }}>
                <div style={{ fontWeight: "bold", color: "#58A6FF", marginBottom: 10, fontSize: 13 }}>Attack Sequence Steps</div>
                {scenario_narrative.story_steps.map((step, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, padding: "6px 0", borderBottom: "1px solid #21262D" }}>
                    <span style={{ background: "#00E5FF", color: "#0D1117", borderRadius: "50%", width: 20, height: 20, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "bold", fontSize: 11, flexShrink: 0 }}>{i + 1}</span>
                    <span style={{ color: "#C9D1D9", fontSize: 13 }}>{step}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── Tab: Client Forensic Dossier ─── */}
        {activeTab === "dossier" && (
          <div>
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: "block", fontSize: 11, color: "#8B949E", marginBottom: 4 }}>SELECT CLIENT TO INSPECT</label>
              <select
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                style={{ background: "#161B22", color: "#F0F6FC", border: "1px solid #30363D", borderRadius: 6, padding: "6px 12px", fontSize: 13, cursor: "pointer" }}
              >
                {allClientIds.map((cid) => (
                  <option key={cid} value={cid}>{cid} — {client_security_records[cid]?.final_status ?? "?"}</option>
                ))}
              </select>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <ClientDossier
                clientId={selectedClient}
                record={client_security_records[selectedClient] ?? { attack_type: "UNKNOWN", is_malicious: false, update_norm: 0, cosine_similarity: 1, layer1_status: "PASS", layer1_reason: "N/A", cbe_concentration_ratio: 0, cluster_id: null, mars_status: "PASS", mars_reason: "N/A", final_status: "TRUSTED" }}
                marsInfo={(mars_data?.results as Record<string, unknown>)?.[selectedClient] as Record<string, unknown>}
              />
              <NormChart records={client_security_records} height={300} />
            </div>
          </div>
        )}

        {/* ─── Tab: Layer 1 Analytics ─── */}
        {activeTab === "layer1" && (
          <div>
            <h3 style={{ color: "#F0F6FC", marginBottom: 14 }}>Layer 1: Statistical Anomaly Filter Analysis</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <NormChart records={client_security_records} height={320} />
              <CosineChart records={client_security_records} height={320} />
            </div>
          </div>
        )}

        {/* ─── Tab: MARS Backdoor Forensics ─── */}
        {activeTab === "mars" && (
          <div>
            <h3 style={{ color: "#F0F6FC", marginBottom: 14 }}>Layer 2: MARS Deep Representation Forensics (NeurIPS 2025)</h3>
            <MARSArchitectureDiagram />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
              <CBEChart records={client_security_records} height={340} />
              {/* Wasserstein Heatmap placeholder */}
              <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: 14 }}>
                <div style={{ fontSize: 13, fontWeight: "bold", color: "#F0F6FC", marginBottom: 10 }}>🔥 Wasserstein Distance Heatmap</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(10, 1fr)", gap: 2 }}>
                  {allClientIds.flatMap((ci) =>
                    allClientIds.map((cj) => {
                      const rec1 = client_security_records[ci];
                      const rec2 = client_security_records[cj];
                      const isMal1 = rec1?.final_status === "QUARANTINED";
                      const isMal2 = rec2?.final_status === "QUARANTINED";
                      const intensity = ci === cj ? 0 : (isMal1 !== isMal2 ? 0.9 : isMal1 && isMal2 ? 0.4 : 0.1);
                      const r = Math.round(255 * intensity);
                      const g = Math.round(100 * (1 - intensity));
                      return (
                        <div
                          key={`${ci}-${cj}`}
                          title={`${ci}↔${cj}`}
                          style={{
                            width: "100%",
                            paddingTop: "100%",
                            background: ci === cj ? "#21262D" : `rgba(${r},${g},68,${intensity + 0.1})`,
                            borderRadius: 2,
                          }}
                        />
                      );
                    })
                  )}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontSize: 10, color: "#8B949E" }}>
                  <span>{allClientIds[0]}</span>
                  <span style={{ color: "#FF1744" }}>■ High Distance (Anomaly Cluster)</span>
                  <span>{allClientIds[allClientIds.length - 1]}</span>
                </div>
              </div>
            </div>
            <ClusterScatter records={client_security_records} height={320} />
          </div>
        )}

        {/* ─── Tab: Aggregation & Benchmark ─── */}
        {activeTab === "aggregation" && (
          <div>
            <h3 style={{ color: "#F0F6FC", marginBottom: 14 }}>Layer 3: Coordinate-wise Trimmed Mean Aggregation</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <AggregationChart summary={summary} records={client_security_records} height={300} />
              <BeforeAfterComparison
                summary={{
                  backdoor_asr: summary.backdoor_asr,
                  clean_accuracy: summary.clean_accuracy,
                  attack_type: summary.attack_type,
                  quarantined_clients: summary.quarantined_clients,
                  trusted_clients: summary.trusted_clients,
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
