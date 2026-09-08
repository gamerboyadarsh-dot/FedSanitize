import React from "react";
import { ShieldAlert, Activity, RefreshCw } from "lucide-react";
import type { RoundRecord } from "../../types/telemetry";
import { SlidingNumber } from "../core/SlidingNumber";

interface HeaderProps {
  currentRoundData?: RoundRecord | null;
  isRunning: boolean;
  onRunRound: () => void;
  onReset: () => void;
  onLoadDemo: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentRoundData,
  isRunning,
  onRunRound,
  onReset,
  onLoadDemo,
}) => {
  const roundNum = currentRoundData?.round ?? 0;
  const cleanAcc = currentRoundData?.clean_accuracy ?? 0;
  const asr = currentRoundData?.backdoor_asr ?? 0;
  const totalQuarantined = currentRoundData?.quarantined_clients.length ?? 0;

  return (
    <header className="h-20 bg-surface border-b border-border px-6 flex items-center justify-between shrink-0 threat-card z-10">
      {/* Left: Gateway status & Stacked Stat Items */}
      <div className="flex items-center gap-6 min-w-0">
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-surface-elevated border border-border flex items-center justify-center">
            <Activity className="w-4 h-4 text-accent-red animate-pulse" />
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

        {roundNum > 0 && (
          <div className="flex items-center gap-6 border-l border-border pl-6">
            {/* Round Stat */}
            <div className="flex flex-col whitespace-nowrap">
              <span className="text-[10px] font-mono text-text-secondary uppercase tracking-wider">
                ROUND
              </span>
              <span className="text-sm font-mono font-bold text-accent-red">
                <SlidingNumber value={roundNum} />
              </span>
            </div>

            {/* Clean Acc Stat */}
            <div className="flex flex-col whitespace-nowrap">
              <span className="text-[10px] font-mono text-text-secondary uppercase tracking-wider">
                CLEAN ACCURACY
              </span>
              <span className="text-sm font-mono font-bold text-accent-safe">
                <SlidingNumber value={cleanAcc} decimalPlaces={1} suffix="%" />
              </span>
            </div>

            {/* Backdoor ASR Stat */}
            <div className="flex flex-col whitespace-nowrap">
              <span className="text-[10px] font-mono text-text-secondary uppercase tracking-wider">
                BACKDOOR ASR
              </span>
              <span className={`text-sm font-mono font-bold ${asr < 2.0 ? "text-accent-safe" : "text-accent-danger"}`}>
                <SlidingNumber value={asr} decimalPlaces={2} suffix="%" />
              </span>
            </div>

            {/* Quarantined Count */}
            <div className="flex flex-col whitespace-nowrap">
              <span className="text-[10px] font-mono text-text-secondary uppercase tracking-wider">
                QUARANTINED
              </span>
              <span className="text-sm font-mono font-bold text-accent-danger">
                <SlidingNumber value={totalQuarantined} suffix=" Nodes" />
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Right: Action Buttons with whitespace-nowrap & consistent h-9 */}
      <div className="flex items-center gap-3 font-mono text-xs shrink-0">
        <button
          onClick={onLoadDemo}
          disabled={isRunning}
          className="h-9 px-3.5 rounded-lg bg-[#170b0b] hover:bg-[#251212] text-zinc-300 hover:text-white border border-[#3d1414] hover:border-[#7a1f1f] transition-all duration-200 disabled:opacity-50 whitespace-nowrap font-medium flex items-center justify-center shadow-sm"
        >
          Load 5-Round Demo
        </button>

        <button
          onClick={onReset}
          disabled={isRunning}
          className="h-9 px-3.5 rounded-lg bg-[#170b0b] hover:bg-[#251212] text-zinc-400 hover:text-white border border-[#3d1414] hover:border-[#7a1f1f] transition-all duration-200 disabled:opacity-50 flex items-center gap-1.5 whitespace-nowrap font-medium shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset
        </button>

        <button
          onClick={onRunRound}
          disabled={isRunning}
          className={`h-9 px-4 rounded-lg font-bold transition-all duration-200 flex items-center gap-2 whitespace-nowrap ${
            isRunning
              ? "bg-accent-red/50 text-text-primary cursor-not-allowed border border-accent-red/50"
              : "bg-accent-red hover:bg-[#ff334b] text-white shadow-glow-red hover:shadow-glow-red-lg border border-accent-red hover:border-[#ff4d5a]"
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
