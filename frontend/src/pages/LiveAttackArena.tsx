/**
 * LiveAttackArena — React mirror of dashboard/simulation_arena.py
 * ==================================================================
 * Full interactive forensic replay & cybersecurity simulation page.
 * Restyled with FedSanitize Cyber-Command Design System.
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { 
  ShieldAlert, 
  ShieldCheck, 
  Play, 
  RotateCcw, 
  ChevronLeft, 
  ChevronRight, 
  FastForward,
  Activity,
  Layers,
  FileText,
  UserCheck,
  Filter,
  BarChart2,
  Info,
  Radio
} from "lucide-react";
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
  1: "Scenario 1: Clean Baseline (Honest Federated Learning)",
  2: "Scenario 2: Extreme Gradient Scaling (Layer 1 Norm Defense)",
  3: "Scenario 3: Sign Flipping Attack (Layer 1 Directional Defense)",
  4: "Scenario 4: Stealth Neural Backdoor (NeurIPS 2025 MARS Forensics)",
  5: "Scenario 5: Multi-Vector Combined Attack (Layer 1 + MARS Defense)",
};

const SPEED_OPTIONS = [0.5, 1.0, 2.0, 4.0];

type TabId = "storyline" | "dossier" | "layer1" | "mars" | "aggregation";

const TABS: { id: TabId; label: string; icon: any }[] = [
  { id: "storyline", label: "Attack Storyline", icon: FileText },
  { id: "dossier", label: "Client Dossier", icon: UserCheck },
  { id: "layer1", label: "Layer 1 Analytics", icon: Filter },
  { id: "mars", label: "MARS Backdoor Forensics", icon: Activity },
  { id: "aggregation", label: "Robust Aggregation", icon: ShieldCheck },
];

const MARSArchitectureDiagram: React.FC = () => (
  <div className="ds-card p-5 mb-4">
    <div className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider mb-3 flex items-center gap-2">
      <Activity className="w-4 h-4 text-[var(--purple)]" />
      <span>MARS Architecture — Multi-layer Anomaly Representation Scanning</span>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {["conv1 Features", "conv2 Features", "Backdoor Energy Score", "CBE / Wasserstein Clustering"].map((label, i) => (
        <div key={i} className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-3.5 text-center">
          <div className="text-xl mb-1.5 font-mono text-[var(--purple)] font-bold">0{i + 1}</div>
          <div className="text-xs font-semibold text-[var(--cyan)]">{label}</div>
          {i < 3 && (
            <div className="mt-1 text-[11px] text-[var(--text-muted)] leading-tight">
              {i === 0 ? "First convolutional activations" : i === 1 ? "Deeper representation layer" : "Concentrated top-k activation energy"}
            </div>
          )}
        </div>
      ))}
    </div>
    <div className="mt-3 text-[11px] font-mono text-[var(--text-muted)] flex items-center gap-1.5">
      <Info className="w-3.5 h-3.5 text-[var(--purple)] shrink-0" />
      <span>MARS (Wan et al., NeurIPS 2025) · CBE Threshold: 0.015 · Wasserstein W₁ metric clustering</span>
    </div>
  </div>
);

export const LiveAttackArena: React.FC = () => {
  const [arenaData, setArenaData] = useState<ArenaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRound, setSelectedRound] = useState<number>(3); // Round 4 (Backdoor) default
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isAnimating, setIsAnimating] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(1.0);
  const [selectedClient, setSelectedClient] = useState<string | null>("C8");
  const [activeTab, setActiveTab] = useState<TabId>("storyline");

  const animRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load arena data for selected scenario
  const loadData = useCallback(async (roundIdx: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchArenaData(roundIdx);
      setArenaData(data);
      setCurrentStep(0);
      setIsAnimating(false);
      const cids = Object.keys(data.client_security_records);
      const firstMal = cids.find((c) => data.client_security_records[c]?.is_malicious);
      setSelectedClient(firstMal ?? cids[0] ?? null);
    } catch (err: any) {
      setError(err?.message ?? "Failed to connect to backend forensic replay service.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(selectedRound);
  }, [selectedRound, loadData]);

  // Animated playback
  const runAnimation = () => {
    if (!arenaData || isAnimating) return;
    setIsAnimating(true);
    setCurrentStep(0);

    const steps = arenaData.timeline_steps;
    const delay = 600 / speed;

    let stepIdx = 0;
    const tick = () => {
      stepIdx++;
      if (stepIdx >= steps.length) {
        setIsAnimating(false);
        return;
      }
      setCurrentStep(stepIdx);
      animRef.current = setTimeout(tick, delay);
    };
    animRef.current = setTimeout(tick, delay);
  };

  useEffect(() => {
    return () => {
      if (animRef.current) clearTimeout(animRef.current);
    };
  }, []);

  if (loading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 rounded-full border-2 border-[var(--cyan)] border-t-transparent animate-spin" />
        <span className="text-sm text-[var(--text-secondary)]">Loading Arena Forensic Replay Dataset...</span>
      </div>
    );
  }

  if (error || !arenaData) {
    return (
      <div className="ds-card p-8 text-center max-w-lg mx-auto my-12 space-y-3">
        <ShieldAlert className="w-10 h-10 text-[var(--red)] mx-auto" />
        <h3 className="text-base font-semibold text-[var(--text-primary)]">Arena Engine Offline</h3>
        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{error}</p>
        <button
          onClick={() => loadData(selectedRound)}
          className="ds-btn ds-btn-primary mx-auto mt-2"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      </div>
    );
  }

  const {
    total_rounds,
    timeline_steps,
    client_security_records,
    network_nodes,
    scenario_narrative,
    mars_data,
    summary,
  } = arenaData;

  const totalSteps = timeline_steps.length;
  const currentStepData = timeline_steps[currentStep];
  const currentEvent = currentStepData?.event;
  const visibleEvents: ArenaSecurityEvent[] = timeline_steps
    .slice(0, currentStep + 1)
    .map((s) => s.event);

  const activeLayer = currentEvent?.layer ?? undefined;
  const allClientIds = Object.keys(client_security_records);

  return (
    <div className="space-y-6 pb-8 page-enter">
      {/* ── Top Hero Banner ── */}
      <div className="ds-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--cyan-tint)] text-[var(--cyan)]">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">
              Live Attack Arena & Forensic Replay
            </h2>
            <span className="ds-chip ds-chip-pass ds-chip-no-dot text-xs">
              Engine Active & Ready
            </span>
          </div>
          <p className="text-[13px] text-[var(--text-secondary)] mt-1">
            Deterministic step-by-step forensic execution visualizer simulating 3-layer Byzantine & backdoor defenses.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="ds-chip ds-chip-info ds-chip-no-dot text-xs">
            Forensic Replay Dataset
          </span>
        </div>
      </div>

      {/* ── Scenario Selector Card ── */}
      <div className="ds-card p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex-1">
          <label className="eyebrow block mb-1.5">
            Select Adversarial Scenario to Replay
          </label>
          <select
            value={selectedRound}
            onChange={(e) => {
              setSelectedRound(Number(e.target.value));
              setIsAnimating(false);
              if (animRef.current) clearTimeout(animRef.current);
            }}
            className="w-full bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-xl px-4 py-2.5 text-xs font-sans outline-none focus:border-[var(--cyan)] cursor-pointer"
          >
            {Array.from({ length: total_rounds }, (_, i) => (
              <option key={i} value={i}>
                {SCENARIO_LABELS[i + 1] ?? `Scenario ${i + 1}`}
              </option>
            ))}
          </select>
        </div>
        
        <div className="sm:max-w-xs text-[11px] text-[var(--text-muted)] bg-[var(--bg-elevated)] p-3 rounded-xl border border-[var(--border-subtle)] flex items-start gap-2">
          <Info className="w-4 h-4 text-[var(--cyan)] shrink-0 mt-0.5" />
          <span>Forensic scenario telemetry recorded from live benchmark experiment rounds with ground-truth labels.</span>
        </div>
      </div>

      {/* ── Header Metrics Bar ── */}
      <HeaderMetrics summary={summary} />

      {/* ── 3-Layer Pipeline Status ── */}
      <PipelineStatusBar summary={summary} activeLayer={activeLayer} />

      {/* ── Playback Controls Toolbar ── */}
      <div className="ds-card p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Action Button Group */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={runAnimation}
              disabled={isAnimating}
              className="ds-btn ds-btn-primary h-9 px-4 text-xs font-semibold"
            >
              {isAnimating ? (
                <>
                  <span className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  Simulating...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Run Animated Simulation
                </>
              )}
            </button>

            <button
              onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
              disabled={isAnimating || currentStep === 0}
              className="ds-btn ds-btn-secondary h-9 px-3 text-xs"
              title="Step Backward"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <button
              onClick={() => setCurrentStep((s) => Math.min(totalSteps - 1, s + 1))}
              disabled={isAnimating || currentStep === totalSteps - 1}
              className="ds-btn ds-btn-secondary h-9 px-3 text-xs"
              title="Step Forward"
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => {
                setCurrentStep(0);
                setIsAnimating(false);
                if (animRef.current) clearTimeout(animRef.current);
              }}
              className="ds-btn ds-btn-secondary h-9 px-3 text-xs"
              title="Reset Timeline to Step 1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>

            <button
              onClick={() => {
                setCurrentStep(totalSteps - 1);
                setIsAnimating(false);
                if (animRef.current) clearTimeout(animRef.current);
              }}
              className="ds-btn ds-btn-secondary h-9 px-3 text-xs"
              title="Fast Forward to Conclusion"
            >
              <FastForward className="w-3.5 h-3.5" />
              <span>Jump to End</span>
            </button>
          </div>

          {/* Speed Selector Segmented Control */}
          <div className="flex items-center gap-2">
            <span className="eyebrow">Speed:</span>
            <div className="ds-seg-control">
              {SPEED_OPTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  className={`ds-seg-btn text-xs font-mono px-2.5 h-7 ${speed === s ? "active" : ""}`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Timeline Scrubber */}
        <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center gap-4">
          <span className="font-mono text-xs text-[var(--cyan)] font-semibold shrink-0">
            Step {currentStep + 1} / {totalSteps}
          </span>
          <input
            type="range"
            min={0}
            max={totalSteps - 1}
            value={currentStep}
            disabled={isAnimating}
            onChange={(e) => setCurrentStep(Number(e.target.value))}
            className="ds-slider flex-1"
          />
          <span className="font-mono text-xs text-[var(--text-muted)] shrink-0">
            End
          </span>
        </div>
      </div>

      {/* ── Main Area: Network Graph + Right Live Feed ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[13fr_7fr] gap-6 items-start">
        {/* Left: Network Topology + Timeline Sub-panel */}
        <div className="space-y-4">
          <div className="ds-card p-0 overflow-hidden" style={{ minHeight: "440px", maxHeight: "520px" }}>
            <NetworkTopologyGraph
              nodes={network_nodes}
              selectedClient={selectedClient}
              onSelectClient={setSelectedClient}
            />
          </div>

          <TimelineScrubber steps={timeline_steps} currentStepIdx={currentStep} />

          {/* Animation progress indicator */}
          {isAnimating && (
            <div className="h-1.5 w-full bg-[var(--bg-elevated)] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[var(--cyan)] to-[var(--green)] transition-[width] duration-200"
                style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
              />
            </div>
          )}

          {currentStep === totalSteps - 1 && !isAnimating && totalSteps > 1 && (
            <div className="p-3.5 bg-[var(--green-tint)] border border-[var(--green-border)] rounded-xl text-xs text-[var(--green)] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>Simulation sequence completed! All Byzantine & backdoor updates isolated. Consolidated model sanitized.</span>
            </div>
          )}
        </div>

        {/* Right: Live Security Feed + Active Alert Banner */}
        <div className="space-y-4">
          <div style={{ minHeight: "440px", maxHeight: "520px" }}>
            <LiveSecurityFeed events={visibleEvents} maxItems={12} />
          </div>

          {currentEvent && (
            <AlertBanner event={currentEvent} />
          )}
        </div>
      </div>

      {/* ── Forensic Drilldown Tabs ── */}
      <div className="ds-card p-6 space-y-6">
        {/* Tab Header with Segmented Buttons */}
        <div className="border-b border-[var(--border-subtle)] pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">
              Forensic Drilldown & Telemetry Inspection
            </h3>
            <p className="text-[12px] text-[var(--text-secondary)] mt-0.5">
              In-depth empirical telemetry breakdown across all defense checkpoints
            </p>
          </div>

          <div className="ds-seg-control flex-wrap">
            {TABS.map((tab) => {
              const TabIcon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`ds-seg-btn text-xs ${activeTab === tab.id ? "active" : ""}`}
                >
                  <TabIcon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ─── Tab: Attack Scenario Storyline ─── */}
        {activeTab === "storyline" && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">
              Scenario Walkthrough: {scenario_narrative.title}
            </h4>

            <div className="p-4 bg-[var(--cyan-tint)] border border-[var(--cyan-border)] rounded-xl text-xs text-[var(--text-primary)]">
              <span className="font-semibold text-[var(--cyan)]">Threat Vector: </span>
              {scenario_narrative.headline}
            </div>

            <div className="ds-card-elevated p-4 rounded-xl space-y-2.5 text-xs text-[var(--text-secondary)]">
              <div>
                <strong className="text-[var(--text-primary)]">Technical Explanation: </strong>
                {scenario_narrative.technical_explanation}
              </div>
              <div>
                <strong className="text-[var(--text-primary)]">Mitigating Defense Layer: </strong>
                <span className="text-[var(--green)] font-semibold">{scenario_narrative.mitigating_layer}</span>
              </div>
              <div>
                <strong className="text-[var(--text-primary)]">Forensic Investigation Focus: </strong>
                {scenario_narrative.forensic_focus}
              </div>
            </div>

            {/* Attack-type specific visual */}
            {scenario_narrative.attack_type === "BACKDOOR" && <BackdoorStages currentStage={6} />}
            {scenario_narrative.attack_type !== "BACKDOOR" && (
              <div className="ds-card-elevated p-4 rounded-xl">
                <div className="font-semibold text-[var(--cyan)] mb-3 text-xs">
                  Attack Sequence Steps
                </div>
                <div className="space-y-2">
                  {scenario_narrative.story_steps.map((step, i) => (
                    <div key={i} className="flex items-start gap-3 py-1.5 border-b border-[var(--border-subtle)] last:border-0">
                      <span className="w-5 h-5 rounded-full bg-[var(--cyan-tint)] text-[var(--cyan)] font-mono text-[11px] font-bold flex items-center justify-center shrink-0">
                        {i + 1}
                      </span>
                      <span className="text-xs text-[var(--text-primary)] leading-relaxed">{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── Tab: Client Forensic Dossier ─── */}
        {activeTab === "dossier" && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <label className="eyebrow">Select Client to Inspect:</label>
              <select
                value={selectedClient ?? ""}
                onChange={(e) => setSelectedClient(e.target.value)}
                className="bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs font-mono outline-none cursor-pointer"
              >
                {allClientIds.map((cid) => (
                  <option key={cid} value={cid}>
                    {cid} — {client_security_records[cid]?.final_status ?? "UNKNOWN"}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ClientDossier
                clientId={selectedClient ?? "C0"}
                record={client_security_records[selectedClient ?? "C0"] ?? {
                  attack_type: "UNKNOWN",
                  is_malicious: false,
                  update_norm: 0,
                  cosine_similarity: 1,
                  layer1_status: "PASS",
                  layer1_reason: "N/A",
                  cbe_concentration_ratio: 0,
                  cluster_id: null,
                  mars_status: "PASS",
                  mars_reason: "N/A",
                  final_status: "TRUSTED"
                }}
                marsInfo={(mars_data?.results as Record<string, unknown>)?.[selectedClient ?? "C0"] as Record<string, unknown>}
              />
              <NormChart records={client_security_records} height={300} />
            </div>
          </div>
        )}

        {/* ─── Tab: Layer 1 Analytics ─── */}
        {activeTab === "layer1" && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">
              Layer 1: Statistical Anomaly Filter Analysis
            </h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <NormChart records={client_security_records} height={320} />
              <CosineChart records={client_security_records} height={320} />
            </div>
          </div>
        )}

        {/* ─── Tab: MARS Backdoor Forensics ─── */}
        {activeTab === "mars" && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">
              Layer 2: MARS Deep Representation Forensics (NeurIPS 2025)
            </h4>
            <MARSArchitectureDiagram />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <CBEChart records={client_security_records} height={340} />

              {/* Wasserstein Heatmap */}
              <div className="ds-card-elevated p-4 rounded-xl space-y-3">
                <div className="text-xs font-semibold text-[var(--text-primary)]">
                  Wasserstein Distance Heatmap (W₁)
                </div>
                <div className="grid grid-cols-10 gap-1">
                  {allClientIds.flatMap((ci) =>
                    allClientIds.map((cj) => {
                      const rec1 = client_security_records[ci];
                      const rec2 = client_security_records[cj];
                      const isMal1 = rec1?.final_status === "QUARANTINED";
                      const isMal2 = rec2?.final_status === "QUARANTINED";
                      const intensity = ci === cj ? 0 : (isMal1 !== isMal2 ? 0.9 : isMal1 && isMal2 ? 0.4 : 0.1);
                      const r = Math.round(255 * intensity);
                      const g = Math.round(77 * (1 - intensity));
                      return (
                        <div
                          key={`${ci}-${cj}`}
                          title={`${ci} ↔ ${cj}`}
                          className="w-full pt-[100%] rounded-sm"
                          style={{
                            backgroundColor: ci === cj ? "var(--bg-base)" : `rgba(${r},${g},109,${intensity + 0.15})`,
                          }}
                        />
                      );
                    })
                  )}
                </div>
                <div className="flex justify-between text-[10px] font-mono text-[var(--text-muted)] pt-1">
                  <span>{allClientIds[0]}</span>
                  <span className="text-[var(--red)] font-semibold">High Distance (Backdoor Cluster)</span>
                  <span>{allClientIds[allClientIds.length - 1]}</span>
                </div>
              </div>
            </div>

            <ClusterScatter records={client_security_records} height={320} />
          </div>
        )}

        {/* ─── Tab: Aggregation & Benchmark ─── */}
        {activeTab === "aggregation" && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">
              Layer 3: Coordinate-wise Trimmed Mean Aggregation
            </h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
