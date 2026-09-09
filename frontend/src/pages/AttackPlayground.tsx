import React, { useState } from "react";
import { 
  Swords, 
  Target, 
  Check, 
  RefreshCw,
  AlertOctagon
} from "lucide-react";
import type { ClientSummary } from "../types/telemetry";
import { setClientAttack } from "../api/client";
import { AnimatedGroup } from "../components/core/AnimatedGroup";
import { GlowEffect } from "../components/core/GlowEffect";

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
    { id: "NONE", label: "Honest (Benign)", desc: "Standard local SGD without perturbation", color: "text-accent-safe" },
    { id: "EXTREME_UPDATE", label: "Extreme Update", desc: "Multiplicative 10x magnitude scaling", color: "text-accent-danger" },
    { id: "SIGN_FLIPPING", label: "Sign Flipping", desc: "Inverts gradient vector: delta = -1 * delta", color: "text-accent-danger" },
    { id: "RANDOM_BYZANTINE", label: "Random Byzantine", desc: "High-entropy Gaussian tensor noise", color: "text-accent-danger" },
    { id: "BACKDOOR", label: "Stealthy Backdoor", desc: "Injects 3x3 white square patch; target class 0", color: "text-accent-warning" },
    { id: "LABEL_FLIPPING", label: "Label Flipping", desc: "Permutes local labels (e.g. 7 -> 1)", color: "text-accent-warning" },
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

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-surface border border-border rounded-xl p-5  flex items-center justify-between">
        <div>
          <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
            <Swords className="w-4 h-4 text-primary" />
            Adversarial Attack Simulation Playground
          </h2>
          <p className="text-xs text-text-secondary font-mono mt-1">
            Dynamically reassign adversarial vectors to edge clients and configure backdoor trigger parameters.
          </p>
        </div>
        <span className="text-xs font-mono text-accent-danger bg-accent-danger/10 border border-accent-danger/30 px-3 py-1 rounded">
          Active Threats: {clients.filter((c) => c.is_malicious).length} / 10
        </span>
      </div>

      <AnimatedGroup className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Threat Assignment Studio */}
        <div className="lg:col-span-2 bg-surface border border-border rounded-xl p-5  space-y-5">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
              <Target className="w-4 h-4 text-primary" />
              Target Edge Client Selection
            </h3>
            <span className="text-[11px] font-mono text-text-secondary">Changes take effect on next round</span>
          </div>

          {/* Client Selector Pills with GlowEffect */}
          <div className="grid grid-cols-5 gap-2.5">
            {clients.map((c) => {
              const isSelected = selectedClient === c.client_id;
              return (
                <GlowEffect key={c.client_id}>
                  <button
                    onClick={() => {
                      setSelectedClient(c.client_id);
                      setSelectedAttack(c.attack_type);
                    }}
                    className={`w-full p-3 rounded-lg font-mono text-xs text-left transition-all border ${
                      isSelected
                        ? "bg-surface-elevated border-primary text-text-primary shadow-glow-cyan"
                        : "bg-surface-elevated/40 border-border text-text-secondary hover:text-text-primary hover:border-border-active"
                    }`}
                  >
                    <div className="font-bold flex items-center justify-between">
                      <span>{c.client_id}</span>
                      {c.is_malicious ? (
                        <span className="w-1.5 h-1.5 rounded-full bg-accent-danger" />
                      ) : (
                        <span className="w-1.5 h-1.5 rounded-full bg-accent-safe" />
                      )}
                    </div>
                    <div className="text-[10px] truncate mt-1 text-text-secondary">
                      {c.attack_type}
                    </div>
                  </button>
                </GlowEffect>
              );
            })}
          </div>

          {/* Attack Type Options */}
          <div className="space-y-3 pt-2">
            <div className="text-xs font-mono font-bold text-text-secondary uppercase">
              Select Attack Vector for {selectedClient}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {attackOptions.map((opt) => {
                const isSelected = selectedAttack === opt.id;
                return (
                  <div
                    key={opt.id}
                    onClick={() => setSelectedAttack(opt.id)}
                    className={`p-3.5 rounded-lg border cursor-pointer font-mono transition-all ${
                      isSelected
                        ? "bg-surface-elevated border-primary shadow-glow-cyan text-text-primary"
                        : "bg-surface-elevated/30 border-border text-text-secondary hover:border-border-active"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-bold ${opt.color}`}>{opt.label}</span>
                      {isSelected && <Check className="w-4 h-4 text-primary" />}
                    </div>
                    <p className="text-[11px] text-text-secondary mt-1">{opt.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Apply Button */}
          <div className="pt-3 flex items-center justify-between border-t border-border/60">
            {successMsg ? (
              <span className="text-xs font-mono text-accent-safe flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5" />
                {successMsg}
              </span>
            ) : (
              <span className="text-[11px] font-mono text-text-secondary">
                Assigning an attack updates client training or delta manipulations.
              </span>
            )}

            <button
              onClick={handleApplyAttack}
              disabled={isUpdating}
              className="bg-white text-black hover:bg-zinc-200 border border-white/20 transition-all shadow-md px-5 py-2 rounded-lg font-mono text-xs font-bold flex items-center gap-2 disabled:opacity-50"
            >
              {isUpdating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Updating Client...
                </>
              ) : (
                <>
                  <Swords className="w-3.5 h-3.5" />
                  Assign to {selectedClient}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Col: Backdoor Trigger Patch Visual Preview */}
        <div className="bg-surface border border-border rounded-xl p-5  space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-secondary" />
              Backdoor Trigger Matrix
            </h3>
            <span className="text-[10px] text-accent-warning bg-accent-warning/10 border border-accent-warning/30 px-2 py-0.5 rounded">
              Target: Class 0
            </span>
          </div>

          {/* Trigger canvas preview */}
          <div className="flex flex-col items-center justify-center p-4 bg-background border border-border rounded-lg space-y-3">
            <div className="grid grid-cols-[repeat(28,minmax(0,1fr))] gap-0 w-44 h-44 border border-border bg-[#0C1E3E] rounded overflow-hidden p-1 shadow-[inset_0_0_20px_rgba(0,0,0,0.8)]">
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
                        ? "bg-white animate-pulse shadow-[0_0_8px_rgba(255,255,255,0.8)] z-10 relative" 
                        : isSeven 
                        ? "bg-primary/40" 
                        : "bg-transparent border-[0.5px] border-white/[0.02]"
                    }`}
                  />
                );
              })}
            </div>
            <div className="text-[11px] text-text-secondary text-center">
              Bottom-Right 4x4 Trigger Patch stamped on 40% of local training samples.
            </div>
          </div>

          <div className="bg-surface-elevated border border-border p-3 rounded-lg space-y-1.5 text-[11px]">
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Trigger Position:</span>
              <span className="text-text-primary font-bold">Bottom-Right (24:28, 24:28)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Trigger Color:</span>
              <span className="text-text-primary">White (Normalized 2.82)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Adversarial Target:</span>
              <span className="text-accent-safe font-bold">Class 0 ("Zero")</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Local Poison Ratio:</span>
              <span className="text-accent-warning font-bold">40% of Client Shard</span>
            </div>
          </div>
        </div>
      </AnimatedGroup>
    </div>
  );
};
