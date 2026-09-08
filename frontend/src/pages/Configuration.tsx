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

/* ──────────────────────────────────────────────────────────────────────────
   SliderField — SOC-styled range slider with live value badge
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
  accentColor?: "red" | "safe" | "warning";
}

const ACCENT = {
  red: {
    track: "#e11d2e",
    badge: "text-accent-red border-accent-red/40 bg-accent-red/10",
  },
  safe: {
    track: "#2ecc71",
    badge: "text-accent-safe border-accent-safe/40 bg-accent-safe/10",
  },
  warning: {
    track: "#f5a623",
    badge: "text-accent-warning border-accent-warning/40 bg-accent-warning/10",
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
  accentColor = "red",
}) => {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const { track, badge } = ACCENT[accentColor];

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label className="text-[11px] text-zinc-400 uppercase tracking-wider">
          {label}
        </label>
        <span className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded border ${badge}`}>
          {value.toFixed(decimalPlaces)}{unit}
        </span>
      </div>

      <div className="relative flex items-center h-5">
        <div className="absolute w-full h-[3px] rounded-full bg-[#251212]" />
        <div
          className="absolute h-[3px] rounded-full transition-[width] duration-75"
          style={{ width: `${pct}%`, backgroundColor: track }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="slider-input relative w-full appearance-none bg-transparent cursor-pointer"
          data-accent={accentColor}
        />
      </div>

      <div className="flex justify-between text-[10px] text-zinc-600 font-mono">
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
        <span className="w-2 h-2 rounded-full bg-accent-red animate-pulse" />
        <span>Loading system configuration from backend...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono">
      <style>{`
        .slider-input::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 14px; height: 14px;
          border-radius: 50%;
          background: #e11d2e;
          border: 2px solid #ff4d5a;
          box-shadow: 0 0 8px rgba(225,29,46,0.65);
          cursor: pointer;
          transition: transform 140ms ease, box-shadow 140ms ease;
        }
        .slider-input::-webkit-slider-thumb:hover {
          transform: scale(1.25);
          box-shadow: 0 0 14px rgba(225,29,46,0.9);
        }
        .slider-input[data-accent="safe"]::-webkit-slider-thumb {
          background: #2ecc71;
          border-color: #27ae60;
          box-shadow: 0 0 8px rgba(46,204,113,0.55);
        }
        .slider-input[data-accent="safe"]::-webkit-slider-thumb:hover {
          box-shadow: 0 0 14px rgba(46,204,113,0.85);
        }
        .slider-input[data-accent="warning"]::-webkit-slider-thumb {
          background: #f5a623;
          border-color: #e6951a;
          box-shadow: 0 0 8px rgba(245,166,35,0.55);
        }
        .slider-input[data-accent="warning"]::-webkit-slider-thumb:hover {
          box-shadow: 0 0 14px rgba(245,166,35,0.85);
        }
        .slider-input::-moz-range-thumb {
          width: 14px; height: 14px;
          border-radius: 50%;
          background: #e11d2e;
          border: 2px solid #ff4d5a;
          cursor: pointer;
        }
      `}</style>

      <div className="bg-surface border border-border rounded-xl p-5 threat-card flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
            <Sliders className="w-4 h-4 text-accent-red" />
            System &amp; Security Hyperparameters
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Tunable knobs for federated optimization, multi-layer defense thresholds, and attack intensities.
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-4 py-2 rounded-lg bg-accent-red hover:bg-[#ff334b] text-white text-xs font-bold shadow-glow-red hover:shadow-glow-red-lg transition-all duration-200 flex items-center gap-2"
        >
          {isSaving
            ? "Saving..."
            : saveSuccess
            ? <><Check className="w-3.5 h-3.5" /> Saved!</>
            : <><Save className="w-3.5 h-3.5" /> Save Configuration</>}
        </button>
      </div>

      <AnimatedGroup className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-xs">

        {/* Federated Parameters */}
        <div className="bg-surface border border-border rounded-xl p-5 threat-card space-y-5">
          <div className="flex items-center gap-2 border-b border-border/60 pb-3 text-accent-red font-bold uppercase tracking-wider">
            <Cpu className="w-4 h-4" />
            Federated Parameters
          </div>
          <SliderField
            label="Total Client Count"
            value={config.federated?.num_clients ?? 10}
            min={2} max={20} step={1} decimalPlaces={0}
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, num_clients: v } })}
          />
          <SliderField
            label="Local Training Epochs"
            value={config.federated?.local_epochs ?? 1}
            min={1} max={10} step={1} decimalPlaces={0}
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, local_epochs: v } })}
          />
          <SliderField
            label="Local Learning Rate (SGD)"
            value={config.federated?.local_lr ?? 0.02}
            min={0.001} max={0.1} step={0.001} decimalPlaces={3}
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, local_lr: v } })}
          />
          <SliderField
            label="Local Batch Size"
            value={config.federated?.local_batch_size ?? 64}
            min={16} max={256} step={16} decimalPlaces={0}
            onChange={(v) => setConfig({ ...config, federated: { ...config.federated, local_batch_size: v } })}
          />
        </div>

        {/* 3-Layer Firewall Config */}
        <div className="bg-surface border border-border rounded-xl p-5 threat-card space-y-5">
          <div className="flex items-center gap-2 border-b border-border/60 pb-3 text-accent-safe font-bold uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-accent-safe" />
            3-Layer Firewall Config
          </div>
          <SliderField
            label="Layer 1 MAD Multiplier"
            value={config.defense?.layer1_mad_multiplier ?? 3.5}
            min={1.0} max={8.0} step={0.5} decimalPlaces={1}
            accentColor="safe"
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, layer1_mad_multiplier: v } })}
          />
          <SliderField
            label="MARS CBE Top-p Fraction"
            value={config.defense?.mars_cbe_top_p ?? 0.10}
            min={0.05} max={0.50} step={0.05} decimalPlaces={2}
            accentColor="safe"
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, mars_cbe_top_p: v } })}
          />
          <SliderField
            label="MARS Malignity Gap Threshold"
            value={config.defense?.mars_malignity_threshold ?? 0.015}
            min={0.005} max={0.1} step={0.005} decimalPlaces={3}
            accentColor="safe"
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, mars_malignity_threshold: v } })}
          />
          <SliderField
            label="Trimmed Mean Beta (Tail %)"
            value={config.defense?.trimmed_mean_beta ?? 0.10}
            min={0.05} max={0.40} step={0.05} decimalPlaces={2}
            accentColor="safe"
            onChange={(v) => setConfig({ ...config, defense: { ...config.defense, trimmed_mean_beta: v } })}
          />
        </div>

        {/* Attack Intensities */}
        <div className="bg-surface border border-border rounded-xl p-5 threat-card space-y-5">
          <div className="flex items-center gap-2 border-b border-border/60 pb-3 text-accent-warning font-bold uppercase tracking-wider">
            <Swords className="w-4 h-4 text-accent-warning" />
            Attack Intensities
          </div>
          <SliderField
            label="Extreme Update Gamma (Scale)"
            value={config.attack?.extreme_update_gamma ?? 10.0}
            min={1.0} max={30.0} step={1.0} decimalPlaces={1}
            accentColor="warning"
            onChange={(v) => setConfig({ ...config, attack: { ...config.attack, extreme_update_gamma: v } })}
          />
          <SliderField
            label="Sign Flip Gamma"
            value={config.attack?.sign_flip_gamma ?? 1.0}
            min={0.5} max={5.0} step={0.5} decimalPlaces={1}
            accentColor="warning"
            onChange={(v) => setConfig({ ...config, attack: { ...config.attack, sign_flip_gamma: v } })}
          />
          <SliderField
            label="Backdoor Poison Ratio"
            value={config.attack?.backdoor_poison_ratio ?? 0.40}
            min={0.05} max={0.90} step={0.05} decimalPlaces={2}
            accentColor="warning"
            onChange={(v) => setConfig({ ...config, attack: { ...config.attack, backdoor_poison_ratio: v } })}
          />
        </div>

      </AnimatedGroup>
    </div>
  );
};
