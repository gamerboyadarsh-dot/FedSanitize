import React, { useState } from "react";
import { 
  Swords, 
  Target, 
  Check, 
  RefreshCw,
  AlertOctagon,
  Shield,
  Zap,
  RotateCcw,
  Sparkles,
  Shuffle
} from "lucide-react";
import type { ClientSummary } from "../types/telemetry";
import { setClientAttack } from "../api/client";

interface AttackPlaygroundProps {
  clients: ClientSummary[];
  onRefreshClients: () => void;
}

export const AttackPlayground: React.FC<AttackPlaygroundProps> = ({ clients, onRefreshClients }) => {
  const [selectedClient, setSelectedClient] = useState<string>("C6");
  const [selectedAttack, setSelectedAttack] = useState<string>("EXTREME_UPDATE");
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const attackOptions = [
    { 
      id: "NONE", 
      label: "Honest (Benign)", 
      desc: "Standard local stochastic gradient descent without adversarial perturbation", 
      formula: "Δw = -η ∇L(w)",
      icon: Shield,
      isAttack: false
    },
    { 
      id: "EXTREME_UPDATE", 
      label: "Extreme Update", 
      desc: "Multiplicative 10x magnitude scaling to destabilize global weight aggregation", 
      formula: "Δw_adv = 10 · Δw",
      icon: Zap,
      isAttack: true
    },
    { 
      id: "SIGN_FLIPPING", 
      label: "Sign Flipping", 
      desc: "Directional inversion pushing global parameters toward gradient ascent", 
      formula: "Δw_adv = -1 · Δw",
      icon: RotateCcw,
      isAttack: true
    },
    { 
      id: "RANDOM_BYZANTINE", 
      label: "Random Byzantine", 
      desc: "High-entropy Gaussian tensor noise obliterating clean feature representations", 
      formula: "Δw_adv ~ N(0, σ² I)",
      icon: Sparkles,
      isAttack: true
    },
    { 
      id: "BACKDOOR", 
      label: "Stealthy Backdoor", 
      desc: "Injects 4x4 white pixel trigger targeting class 0 while preserving benign accuracy", 
      formula: "x' = x ⊕ Trigger",
      icon: AlertOctagon,
      isAttack: true
    },
    { 
      id: "LABEL_FLIPPING", 
      label: "Label Flipping", 
      desc: "Permutes local training sample labels (e.g. source 7 permuted to target 1)", 
      formula: "y_adv = π(y)",
      icon: Shuffle,
      isAttack: true
    },
  ];

  const handleApplyAttack = async () => {
    try {
      setIsUpdating(true);
      setSuccessMsg(null);
      await setClientAttack(selectedClient, selectedAttack);
      setSuccessMsg(`Successfully assigned ${selectedAttack} to ${selectedClient}`);
      onRefreshClients();
    } catch (err: any) {
      alert(`Error assigning attack: ${err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const activeThreatsCount = clients.filter((c) => c.is_malicious).length;

  return (
    <div className="space-y-6 pb-8 page-enter">
      {/* Header Banner */}
      <div className="ds-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--red-tint)] text-[var(--red)]">
              <Swords className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">
              Adversarial Attack Simulation Playground
            </h2>
          </div>
          <p className="text-[13px] text-[var(--text-secondary)] mt-1">
            Dynamically reassign adversarial vectors to edge clients and inspect backdoor trigger parameters.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="ds-chip ds-chip-danger ds-chip-no-dot">
            Active Threat Configurations: {activeThreatsCount} / {clients.length || 10}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Threat Assignment Studio */}
        <div className="lg:col-span-2 ds-card p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-[var(--cyan)]" />
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                Target Edge Client Selection
              </h3>
            </div>
            <span className="text-[12px] text-[var(--text-muted)]">
              Changes take effect on next global round
            </span>
          </div>

          {/* Client Selector Grid (5x2) */}
          <div>
            <span className="eyebrow block mb-2.5">Edge Node Fleet</span>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {clients.map((c) => {
                const isSelected = selectedClient === c.client_id;
                return (
                  <button
                    key={c.client_id}
                    onClick={() => {
                      setSelectedClient(c.client_id);
                      setSelectedAttack(c.attack_type);
                    }}
                    className={`p-3 rounded-xl text-left transition-all border outline-none ${
                      isSelected
                        ? "ds-card-active bg-[var(--cyan-tint)]"
                        : "bg-[var(--bg-elevated)] border-[var(--border-subtle)] hover:border-[var(--border-strong)]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sm font-bold text-[var(--text-primary)]">
                        {c.client_id}
                      </span>
                      <span
                        className={`w-2 h-2 rounded-full ${
                          c.is_malicious ? "bg-[var(--red)] shadow-[0_0_6px_var(--red)]" : "bg-[var(--green)]"
                        }`}
                        title={c.is_malicious ? "Malicious Client" : "Honest Client"}
                      />
                    </div>
                    <div className="text-[11px] font-sans font-medium truncate mt-1 text-[var(--text-secondary)]" title={c.attack_type}>
                      {c.attack_type}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Attack Type Options */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <span className="eyebrow">
                Select Attack Vector for Client {selectedClient}
              </span>
              <span className="text-[11px] font-mono text-[var(--cyan)]">
                Targeting: {selectedClient}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {attackOptions.map((opt) => {
                const isSelected = selectedAttack === opt.id;
                const IconComponent = opt.icon;
                return (
                  <div
                    key={opt.id}
                    onClick={() => setSelectedAttack(opt.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ds-card-interactive ${
                      isSelected
                        ? "ds-card-active bg-[var(--cyan-tint)]"
                        : "bg-[var(--bg-elevated)] border-[var(--border-subtle)]"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                          opt.isAttack ? "bg-[var(--red-tint)] text-[var(--red)]" : "bg-[var(--green-tint)] text-[var(--green)]"
                        }`}>
                          <IconComponent className="w-4 h-4" />
                        </div>
                        <span className={`text-sm font-semibold ${
                          isSelected ? "text-[var(--cyan)]" : "text-[var(--text-primary)]"
                        }`}>
                          {opt.label}
                        </span>
                      </div>
                      {isSelected && (
                        <div className="w-5 h-5 rounded-full bg-[var(--cyan)] text-[var(--bg-base)] flex items-center justify-center">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      )}
                    </div>
                    <p className="text-[12px] text-[var(--text-secondary)] mt-2 leading-relaxed">
                      {opt.desc}
                    </p>
                    <div className="mt-2.5">
                      <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--cyan)]">
                        {opt.formula}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-between border-t border-[var(--border-subtle)] gap-3">
            {successMsg ? (
              <span className="text-xs text-[var(--green)] flex items-center gap-1.5 font-medium">
                <Check className="w-4 h-4" />
                {successMsg}
              </span>
            ) : (
              <span className="text-[12px] text-[var(--text-muted)]">
                Assigning an attack updates client local training or adversarial delta manipulation.
              </span>
            )}

            <button
              onClick={handleApplyAttack}
              disabled={isUpdating}
              className="ds-btn ds-btn-primary min-w-[180px]"
            >
              {isUpdating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Updating Client...
                </>
              ) : (
                <>
                  <Swords className="w-4 h-4" />
                  Assign to {selectedClient}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Col: Backdoor Trigger Patch Visual Preview */}
        <div className="ds-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4">
            <div className="flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-[var(--amber)]" />
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                Backdoor Trigger Matrix
              </h3>
            </div>
            <span className="ds-chip ds-chip-warning ds-chip-no-dot font-mono">
              Target: Class 0
            </span>
          </div>

          {/* Trigger canvas preview */}
          <div className="flex flex-col items-center justify-center p-5 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-xl space-y-3">
            <div 
              className="grid grid-cols-[repeat(28,minmax(0,1fr))] gap-0 w-48 h-48 border border-[var(--border-subtle)] bg-[var(--bg-surface)] rounded-lg overflow-hidden p-1 shadow-[inset_0_0_24px_rgba(0,0,0,0.85)]"
              style={{
                backgroundImage: 'linear-gradient(rgba(34,211,238,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.04) 1px, transparent 1px)',
                backgroundSize: '6.85px 6.85px'
              }}
            >
              {Array.from({ length: 28 * 28 }).map((_, i) => {
                const r = Math.floor(i / 28);
                const c = i % 28;
                // Bottom-right 4x4
                const isTrigger = r >= 24 && r < 28 && c >= 24 && c < 28;
                // Draw a rough '7'
                const isSeven = (r === 6 && c >= 8 && c <= 20) || (r >= 7 && r <= 22 && c === 20 - Math.floor((r-7)/1.5));
                
                return (
                  <div 
                    key={i} 
                    className={`w-full h-full ${
                      isTrigger 
                        ? "bg-white shadow-[0_0_8px_rgba(255,255,255,0.9)] z-10 relative animate-pulse" 
                        : isSeven 
                        ? "bg-[var(--cyan)] opacity-70" 
                        : "bg-transparent"
                    }`}
                  />
                );
              })}
            </div>
            
            <div className="text-[12px] text-[var(--text-secondary)] text-center leading-relaxed max-w-xs">
              Bottom-Right 4×4 white trigger patch stamped on 40% of local training samples during MNIST training.
            </div>

            <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)] pt-1">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-white border border-white" />
                <span>Trigger (4×4)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-[var(--cyan)] opacity-70" />
                <span>Base Digit ("7")</span>
              </span>
            </div>
          </div>

          <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] p-4 rounded-xl space-y-2.5 text-[12px]">
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-secondary)]">Trigger Position:</span>
              <span className="font-mono text-[var(--text-primary)] font-semibold">Bottom-Right (24:28, 24:28)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-secondary)]">Trigger Pixel Intensity:</span>
              <span className="font-mono text-[var(--text-primary)]">White (+2.82 normalized)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-secondary)]">Adversarial Target Class:</span>
              <span className="font-mono text-[var(--green)] font-semibold">Class 0 ("Zero")</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-secondary)]">Local Poison Ratio:</span>
              <span className="font-mono text-[var(--amber)] font-semibold">40% of Client Shard</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
