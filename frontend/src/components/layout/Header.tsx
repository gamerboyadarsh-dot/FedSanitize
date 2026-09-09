import React from "react";
import { ShieldAlert, Activity, RefreshCw } from "lucide-react";
import type { RoundRecord } from "../../types/telemetry";
import { SlidingNumber } from "../core/SlidingNumber";
import { AuthBadgeModal } from "../common/AuthBadgeModal";

interface HeaderProps {
  currentRoundData?: RoundRecord | null;
  isRunning: boolean;
  onRunRound: () => void;
  onReset: () => void;
  onLoadDemo: () => void;
  authVersion?: number;
}

export const Header: React.FC<HeaderProps> = ({
  currentRoundData,
  isRunning,
  onRunRound,
  onReset,
  onLoadDemo,
  authVersion = 0,
}) => {
  const roundNum = currentRoundData?.round ?? 0;
  const cleanAcc = currentRoundData?.clean_accuracy ?? 0;
  const asr = currentRoundData?.backdoor_asr ?? 0;
  const totalQuarantined = currentRoundData?.quarantined_clients.length ?? 0;

  return (
    <header className="h-20 bg-surface border-b border-border px-6 flex items-center justify-between shrink-0 z-10">
      {/* Left: Gateway status & Stacked Stat Items */}
      <div className="flex items-center gap-6 min-w-0">
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-surface-elevated border border-border flex items-center justify-center">
            <Activity className="w-4 h-4 text-primary animate-pulse" />
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-text-secondary whitespace-nowrap">
              GATEWAY STATUS
            </div>
            <div className="text-xs font-mono text-accent-safe font-bold flex items-center gap-1.5 whitespace-nowrap">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-safe animate-pulse" />
              SECURE DEFENSE ACTIVE
            </div>
          </div>
        </div>
      </div>

      {/* Right: Action Buttons with whitespace-nowrap & consistent h-9 */}
      <div className="flex items-center gap-3 font-mono text-xs shrink-0">
        <AuthBadgeModal key={authVersion} />

        <button
          onClick={onLoadDemo}
          disabled={isRunning}
          className="threat-btn-secondary h-9 px-3.5 rounded-lg disabled:opacity-50 whitespace-nowrap font-medium flex items-center justify-center shadow-sm"
        >
          Load 5-Round Demo
        </button>

        <button
          onClick={onReset}
          disabled={isRunning}
          className="threat-btn-secondary h-9 px-3.5 rounded-lg disabled:opacity-50 flex items-center gap-1.5 whitespace-nowrap font-medium shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset
        </button>

        <button
          onClick={onRunRound}
          disabled={isRunning}
          className={`threat-btn-primary h-9 px-4 rounded-lg font-bold flex items-center gap-2 whitespace-nowrap ${
            isRunning ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Running Round...
            </>
          ) : (
            <>
              <ShieldAlert className="w-3.5 h-3.5" />
              Run Secure Round
            </>
          )}
        </button>
      </div>
    </header>
  );
};
