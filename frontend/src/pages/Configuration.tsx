import React, { useState, useEffect } from "react";
import {
  Sliders,
  Save,
  Check,
  Cpu,
  ShieldCheck,
  Swords,
  RotateCcw,
  Sparkles,
  Info
} from "lucide-react";
import type { ConfigData } from "../types/telemetry";
import { fetchConfig, updateConfig } from "../api/client";

/* ──────────────────────────────────────────────────────────────────────────
   SliderField — Design System Slider with Live Badge & Helper Caption
────────────────────────────────────────────────────────────────────────── */
interface SliderFieldProps {
  label: string;
  helper: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  decimalPlaces?: number;
  onChange: (val: number) => void;
}

const SliderField: React.FC<SliderFieldProps> = ({
  label,
  helper,
  value,
  min,
  max,
  step,
  unit = "",
  decimalPlaces = 2,
  onChange,
}) => {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));

  return (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div>
          <label className="text-xs font-semibold text-[var(--text-primary)] block">
            {label}
          </label>
          <p className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-tight">
            {helper}
          </p>
        </div>
        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--cyan)] shrink-0">
          {value.toFixed(decimalPlaces)}{unit}
        </span>
      </div>

      <div className="pt-1">
        <div className="relative flex items-center h-5">
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value}
            aria-label={label}
            aria-valuenow={value}
            aria-valuemin={min}
            aria-valuemax={max}
            onChange={(e) => onChange(Number(e.target.value))}
            className="ds-slider"
          />
        </div>

        <div className="flex justify-between text-[11px] text-[var(--text-muted)] font-mono mt-1">
          <span>{min}{unit}</span>
          <span>{max}{unit}</span>
        </div>
      </div>
    </div>
  );
};

/* ──────────────────────────────────────────────────────────────────────────
   Configuration page
────────────────────────────────────────────────────────────────────────── */
export const Configuration: React.FC = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [initialConfig, setInitialConfig] = useState<ConfigData | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    fetchConfig()
      .then((data) => {
        setConfig(data);
        setInitialConfig(JSON.parse(JSON.stringify(data)));
      })
      .catch((err) => console.error("Failed to load config:", err));
  }, []);

  const handleUpdate = (updater: (prev: ConfigData) => ConfigData) => {
    if (!config) return;
    const next = updater(config);
    setConfig(next);
    setIsDirty(true);
  };

  const handleSave = async () => {
    if (!config) return;
    try {
      setIsSaving(true);
      setSaveSuccess(false);
      await updateConfig(config);
      setInitialConfig(JSON.parse(JSON.stringify(config)));
      setIsDirty(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(`Failed to save config: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetDefaults = () => {
    if (!initialConfig) return;
    setConfig(JSON.parse(JSON.stringify(initialConfig)));
    setIsDirty(false);
  };

  if (!config) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 rounded-full border-2 border-[var(--cyan)] border-t-transparent animate-spin" />
        <span className="text-sm text-[var(--text-secondary)]">Loading system configuration from backend...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8 page-enter">
      {/* Header card with action row */}
      <div className="ds-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--cyan-tint)] text-[var(--cyan)]">
              <Sliders className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">
              System & Security Hyperparameters
            </h2>
          </div>
          <p className="text-[13px] text-[var(--text-secondary)] mt-1">
            Tunable knobs for federated optimization, 3-layer firewall boundaries, and adversarial threat injection.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isDirty && (
            <span className="ds-chip ds-chip-warning ds-chip-no-dot">
              Unsaved changes
            </span>
          )}

          {isDirty && (
            <button
              onClick={handleResetDefaults}
              className="ds-btn ds-btn-secondary h-9 px-3 text-xs"
              title="Revert to last saved configuration"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Revert
            </button>
          )}

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="ds-btn ds-btn-primary h-9 px-4 text-xs font-semibold"
          >
            {isSaving ? (
              <>
                <span className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                Saving...
              </>
            ) : saveSuccess ? (
              <>
                <Check className="w-3.5 h-3.5 stroke-[3]" />
                Saved to Backend!
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                Save Configuration
              </>
            )}
          </button>
        </div>
      </div>

      {/* 3 Parameter Groups Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* 1. Federated Parameters */}
        <div className="ds-card p-6 space-y-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 border-b border-[var(--border-subtle)] pb-4 text-[var(--cyan)] font-semibold text-sm">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-[var(--cyan-tint)] text-[var(--cyan)]">
                <Cpu className="w-4 h-4" />
              </div>
              <span>Federated Parameters</span>
            </div>

            <div className="space-y-5 pt-4">
              <SliderField
                label="Total Client Count"
                helper="Number of edge nodes participating in global federated rounds"
                value={config.federated?.num_clients ?? 10}
                min={2} max={20} step={1} decimalPlaces={0}
                onChange={(v) => handleUpdate(c => ({ ...c, federated: { ...c.federated, num_clients: v } }))}
              />
              <SliderField
                label="Local Training Epochs"
                helper="SGD passes over each client's private partition per round"
                value={config.federated?.local_epochs ?? 1}
                min={1} max={10} step={1} decimalPlaces={0}
                onChange={(v) => handleUpdate(c => ({ ...c, federated: { ...c.federated, local_epochs: v } }))}
              />
              <SliderField
                label="Local Learning Rate (SGD)"
                helper="Gradient descent step size for client model optimization"
                value={config.federated?.local_lr ?? 0.02}
                min={0.001} max={0.1} step={0.001} decimalPlaces={3}
                onChange={(v) => handleUpdate(c => ({ ...c, federated: { ...c.federated, local_lr: v } }))}
              />
              <SliderField
                label="Local Batch Size"
                helper="Mini-batch size for local loss gradient computation"
                value={config.federated?.local_batch_size ?? 64}
                min={16} max={256} step={16} decimalPlaces={0}
                onChange={(v) => handleUpdate(c => ({ ...c, federated: { ...c.federated, local_batch_size: v } }))}
              />
            </div>
          </div>
          <div className="pt-3 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)] flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 shrink-0" />
            <span>Optimization: SGD with Momentum (0.9)</span>
          </div>
        </div>

        {/* 2. 3-Layer Firewall Config */}
        <div className="ds-card p-6 space-y-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 border-b border-[var(--border-subtle)] pb-4 text-[var(--purple)] font-semibold text-sm">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-[var(--purple-tint)] text-[var(--purple)]">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span>3-Layer Firewall Boundaries</span>
            </div>

            <div className="space-y-5 pt-4">
              <SliderField
                label="Layer 1 MAD Multiplier"
                helper="Higher value = more tolerant L2 update norm threshold"
                value={config.defense?.layer1_mad_multiplier ?? 3.5}
                min={1.0} max={8.0} step={0.5} decimalPlaces={1}
                onChange={(v) => handleUpdate(c => ({ ...c, defense: { ...c.defense, layer1_mad_multiplier: v } }))}
              />
              <SliderField
                label="MARS CBE Top-p Fraction"
                helper="Concentration ratio for layer gradient variance energy"
                value={config.defense?.mars_cbe_top_p ?? 0.10}
                min={0.05} max={0.50} step={0.05} decimalPlaces={2}
                onChange={(v) => handleUpdate(c => ({ ...c, defense: { ...c.defense, mars_cbe_top_p: v } }))}
              />
              <SliderField
                label="MARS Malignity Gap Threshold"
                helper="Minimum Wasserstein distance (W₁) triggering quarantine"
                value={config.defense?.mars_malignity_threshold ?? 0.015}
                min={0.005} max={0.1} step={0.005} decimalPlaces={3}
                onChange={(v) => handleUpdate(c => ({ ...c, defense: { ...c.defense, mars_malignity_threshold: v } }))}
              />
              <SliderField
                label="Trimmed Mean Beta (Tail %)"
                helper="Coordinate proportion trimmed from both top and bottom tails"
                value={config.defense?.trimmed_mean_beta ?? 0.10}
                min={0.05} max={0.40} step={0.05} decimalPlaces={2}
                onChange={(v) => handleUpdate(c => ({ ...c, defense: { ...c.defense, trimmed_mean_beta: v } }))}
              />
            </div>
          </div>
          <div className="pt-3 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)] flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 shrink-0" />
            <span>Algorithm: NeurIPS 2025 MARS Forensics</span>
          </div>
        </div>

        {/* 3. Attack Intensities */}
        <div className="ds-card p-6 space-y-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 border-b border-[var(--border-subtle)] pb-4 text-[var(--red)] font-semibold text-sm">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-[var(--red-tint)] text-[var(--red)]">
                <Swords className="w-4 h-4" />
              </div>
              <span>Adversarial Threat Intensities</span>
            </div>

            <div className="space-y-5 pt-4">
              <SliderField
                label="Extreme Update Gamma (Scale)"
                helper="Multiplier inflating adversarial update magnitude (10x default)"
                value={config.attack?.extreme_update_gamma ?? 10.0}
                min={1.0} max={30.0} step={1.0} decimalPlaces={1}
                onChange={(v) => handleUpdate(c => ({ ...c, attack: { ...c.attack, extreme_update_gamma: v } }))}
              />
              <SliderField
                label="Sign Flip Gamma"
                helper="Magnitude multiplier applied to inverted direction vectors"
                value={config.attack?.sign_flip_gamma ?? 1.0}
                min={0.5} max={5.0} step={0.5} decimalPlaces={1}
                onChange={(v) => handleUpdate(c => ({ ...c, attack: { ...c.attack, sign_flip_gamma: v } }))}
              />
              <SliderField
                label="Backdoor Poison Ratio"
                helper="Fraction of local training samples stamped with trigger patch"
                value={config.attack?.backdoor_poison_ratio ?? 0.40}
                min={0.05} max={0.90} step={0.05} decimalPlaces={2}
                onChange={(v) => handleUpdate(c => ({ ...c, attack: { ...c.attack, backdoor_poison_ratio: v } }))}
              />
            </div>
          </div>
          <div className="pt-3 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)] flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 shrink-0" />
            <span>Poison: 4×4 pixel bottom-right corner</span>
          </div>
        </div>

      </div>
    </div>
  );
};
