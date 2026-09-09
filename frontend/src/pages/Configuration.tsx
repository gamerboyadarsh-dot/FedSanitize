import React, { useState, useEffect } from "react";
import {
  Sliders,
  Save,
  Check,
  Cpu,
  ShieldCheck,
  Swords,
} from "lucide-react";
import type { ConfigData } from "../types/telemetry";
import { fetchConfig, updateConfig } from "../api/client";
import { AnimatedGroup } from "../components/core/AnimatedGroup";
import { Tooltip } from "../components/ui/Tooltip";
import { motion } from "framer-motion";

/* ──────────────────────────────────────────────────────────────────────────
   SliderField — Modern Radix-style range slider with live value badge
────────────────────────────────────────────────────────────────────────── */
interface SliderFieldProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  decimalPlaces?: number;
  onChange: (val: number) => void;
  tooltipInfo?: string;
  accentColor?: "emerald" | "purple" | "cyan";
}

const ACCENT = {
  emerald: {
    activeTrack: "bg-emerald-500",
    badge: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
  },
  purple: {
    activeTrack: "bg-purple-500",
    badge: "text-purple-400 border-purple-500/30 bg-purple-500/10",
  },
  cyan: {
    activeTrack: "bg-cyan-500",
    badge: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
  },
};

const SliderField: React.FC<SliderFieldProps> = ({
  label,
  value,
  min,
  max,
  step,
  unit = "",
  decimalPlaces = 2,
  onChange,
  tooltipInfo,
  accentColor = "emerald"
}) => {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const style = ACCENT[accentColor];

  return (
    <div className="space-y-3 group">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <label className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold group-hover:text-zinc-300 transition-colors">
            {label}
          </label>
          {tooltipInfo && (
            <Tooltip content={tooltipInfo} position="top" />
          )}
        </div>
        <motion.span 
          key={value}
          initial={{ scale: 1.1, opacity: 0.8 }}
          animate={{ scale: 1, opacity: 1 }}
          className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded border ${style.badge}`}
        >
          {value.toFixed(decimalPlaces)}{unit}
        </motion.span>
      </div>

      <div className="relative flex items-center h-4 cursor-pointer group/slider">
        {/* Inactive Track */}
        <div className="absolute w-full h-[4px] rounded-full bg-zinc-800" />
        {/* Active Track */}
        <div
          className={`absolute h-[4px] rounded-full transition-all duration-75 ${style.activeTrack}`}
          style={{ width: `${pct}%` }}
        />
        {/* Hidden Input to handle dragging natively */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
        />
        {/* Custom Handle Thumb (positioned based on pct) */}
        <motion.div 
          className="absolute w-4 h-4 bg-white rounded-full shadow-md shadow-black/50 z-10 border border-zinc-200 group-hover/slider:scale-125 transition-transform"
          style={{ left: `calc(${pct}% - 8px)` }}
          layoutId={`handle-${label}`}
        />
      </div>

      <div className="flex justify-between text-[10px] text-zinc-600 font-mono font-medium">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
};

/* ──────────────────────────────────────────────────────────────────────────
   Configuration page
────────────────────────────────────────────────────────────────────────── */
export const Configuration: React.FC = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchConfig()
      .then((data) => setConfig(data))
      .catch((err) => console.error("Failed to load config:", err));
  }, []);

  const handleSave = async () => {
    if (!config) return;
    try {
      setIsSaving(true);
      setSaveSuccess(false);
      await updateConfig(config);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(`Failed to save config: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!config) {
    return (
      <div className="p-8 font-mono text-xs text-text-secondary flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <span>Loading system configuration from backend...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono max-w-6xl mx-auto">
      <div className="bg-zinc-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-white flex items-center gap-2 font-sans">
            <Sliders className="w-5 h-5 text-zinc-400" />
            System & Security Hyperparameters
          </h2>
          <p className="text-sm text-zinc-400 mt-1 font-sans">
            Tunable knobs for federated optimization, multi-layer defense thresholds, and attack intensities.
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          disabled={isSaving}
          className="bg-white text-black px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-white/10 hover:bg-zinc-100 transition-colors flex items-center gap-2 justify-center min-w-[180px]"
        >
          {isSaving
            ? "Saving..."
            : saveSuccess
            ? <><Check className="w-4 h-4 text-emerald-600" /> Saved!</>
            : <><Save className="w-4 h-4" /> Save Configuration</>}
        </motion.button>
      </div>

      <AnimatedGroup className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-xs">

        {/* Federated Parameters */}
        <div className="bg-zinc-900/50 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center gap-2 border-b border-white/10 pb-4 text-zinc-200 font-bold uppercase tracking-wider font-sans">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Federated Parameters
          </div>
          <SliderField
            label="Total Client Count"
            value={config.federated?.num_clients ?? 10}
            min={2} max={20} step={1} decimalPlaces={0}
            accentColor="cyan"
            tooltipInfo="The total number of clients participating in the Federated Learning network."
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, num_clients: v } })}
          />
          <SliderField
            label="Local Training Epochs"
            value={config.federated?.local_epochs ?? 1}
            min={1} max={10} step={1} decimalPlaces={0}
            accentColor="cyan"
            tooltipInfo="Number of epochs each client trains locally before sending updates to the aggregator."
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, local_epochs: v } })}
          />
          <SliderField
            label="Local Learning Rate (SGD)"
            value={config.federated?.local_lr ?? 0.02}
            min={0.001} max={0.1} step={0.001} decimalPlaces={3}
            accentColor="cyan"
            tooltipInfo="The step size for the local Stochastic Gradient Descent optimizer."
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, local_lr: v } })}
          />
          <SliderField
            label="Local Batch Size"
            value={config.federated?.local_batch_size ?? 64}
            min={16} max={256} step={16} decimalPlaces={0}
            accentColor="cyan"
            tooltipInfo="Batch size used during local client training on their private dataset."
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, local_batch_size: v } })}
          />
        </div>

        {/* 3-Layer Firewall Config */}
        <div className="bg-zinc-900/50 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center gap-2 border-b border-white/10 pb-4 text-zinc-200 font-bold uppercase tracking-wider font-sans">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            3-Layer Firewall Config
          </div>
          <SliderField
            label="Layer 1 MAD Multiplier"
            value={config.defense?.layer1_mad_multiplier ?? 3.5}
            min={1.0} max={8.0} step={0.5} decimalPlaces={1}
            accentColor="emerald"
            tooltipInfo="Median Absolute Deviation multiplier. Higher values are more lenient; lower values aggressively filter outliers."
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, layer1_mad_multiplier: v } })}
          />
          <SliderField
            label="MARS CBE Top-p Fraction"
            value={config.defense?.mars_cbe_top_p ?? 0.10}
            min={0.05} max={0.50} step={0.05} decimalPlaces={2}
            accentColor="emerald"
            tooltipInfo="Fraction of layers to inspect for Deep Backdoor Energy in Layer 2 MARS Forensics."
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, mars_cbe_top_p: v } })}
          />
          <SliderField
            label="MARS Malignity Gap Threshold"
            value={config.defense?.mars_malignity_threshold ?? 0.015}
            min={0.005} max={0.1} step={0.005} decimalPlaces={3}
            accentColor="emerald"
            tooltipInfo="Distance threshold in Wasserstein space. Updates exceeding this gap from the cluster center are quarantined."
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, mars_malignity_threshold: v } })}
          />
          <SliderField
            label="Trimmed Mean Beta (Tail %)"
            value={config.defense?.trimmed_mean_beta ?? 0.10}
            min={0.05} max={0.40} step={0.05} decimalPlaces={2}
            accentColor="emerald"
            tooltipInfo="Fraction of extreme values discarded from both ends during robust aggregation (Layer 3)."
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, trimmed_mean_beta: v } })}
          />
        </div>

        {/* Attack Intensities */}
        <div className="bg-zinc-900/50 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center gap-2 border-b border-white/10 pb-4 text-zinc-200 font-bold uppercase tracking-wider font-sans">
            <Swords className="w-4 h-4 text-purple-400" />
            Attack Intensities
          </div>
          <SliderField
            label="Extreme Update Gamma (Scale)"
            value={config.attack?.extreme_update_gamma ?? 10.0}
            min={1.0} max={30.0} step={1.0} decimalPlaces={1}
            accentColor="purple"
            tooltipInfo="Multiplier for malicious gradient scaling attacks. Simulates clients injecting massive updates."
            onChange={(v) => setConfig({ ...config, attack: { ...config.attack, extreme_update_gamma: v } })}
          />
          <SliderField
            label="Sign Flip Gamma"
            value={config.attack?.sign_flip_gamma ?? 1.0}
            min={0.5} max={5.0} step={0.5} decimalPlaces={1}
            accentColor="purple"
            tooltipInfo="Intensity of targeted sign-flipping attacks designed to reverse model convergence."
            onChange={(v) => setConfig({ ...config, attack: { ...config.attack, sign_flip_gamma: v } })}
          />
          <SliderField
            label="Backdoor Poison Ratio"
            value={config.attack?.backdoor_poison_ratio ?? 0.40}
            min={0.05} max={0.90} step={0.05} decimalPlaces={2}
            accentColor="purple"
            tooltipInfo="Percentage of local training data poisoned with the backdoor trigger by malicious clients."
            onChange={(v) => setConfig({ ...config, attack: { ...config.attack, backdoor_poison_ratio: v } })}
          />
        </div>

      </AnimatedGroup>
    </div>
  );
};
