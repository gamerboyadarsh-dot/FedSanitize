import React from "react";
import { ShieldAlert, RefreshCw } from "lucide-react";
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
    <header
      className="h-16 border-b border-[rgba(148,163,184,0.10)] px-6 flex items-center justify-between shrink-0 z-10 backdrop-blur-md"
      style={{ background: "rgba(5,10,24,0.80)" }}
    >
      {/* LEFT: Gateway status indicator */}
      <div className="flex items-center gap-6 min-w-0">
        <div className="flex items-center gap-2 shrink-0">
          {/* Pulsing green dot */}
          <span className="relative flex h-2 w-2">
            <span
              className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
              style={{ backgroundColor: "#34D399" }}
            />
            <span
              className="relative inline-flex rounded-full h-2 w-2"
              style={{ backgroundColor: "#34D399" }}
            />
          </span>
          <span
            className="text-[13px] font-sans font-medium whitespace-nowrap"
            style={{ color: "#34D399" }}
          >
            Secure defense active
          </span>
        </div>

        {/* CENTER: Metric strip — only shown when roundNum > 0 */}
        {roundNum > 0 && (
          <div className="flex items-center border-l border-[rgba(148,163,184,0.12)] pl-6">

            {/* Round */}
            <div className="flex flex-col items-start px-5">
              <span className="eyebrow">Round</span>
              <span className="kpi-value text-[14px] text-[#22D3EE]">
                <SlidingNumber value={roundNum} />
              </span>
            </div>

            <div className="w-px self-stretch bg-[rgba(148,163,184,0.12)]" />

            {/* Clean Accuracy */}
            <div className="flex flex-col items-start px-5">
              <span className="eyebrow">Clean Acc</span>
              <span className="kpi-value text-[14px] text-[#34D399]">
                <SlidingNumber value={cleanAcc} decimalPlaces={1} suffix="%" />
              </span>
            </div>

            <div className="w-px self-stretch bg-[rgba(148,163,184,0.12)]" />

            {/* Backdoor ASR */}
            <div className="flex flex-col items-start px-5">
              <span className="eyebrow">ASR</span>
              <span
                className="kpi-value text-[14px]"
                style={{ color: asr > 2 ? "#f87171" : "#34D399" }}
              >
                <SlidingNumber value={asr} decimalPlaces={2} suffix="%" />
              </span>
            </div>

            <div className="w-px self-stretch bg-[rgba(148,163,184,0.12)]" />

            {/* Quarantined */}
            <div className="flex flex-col items-start px-5">
              <span className="eyebrow">Quarantined</span>
              <span className="kpi-value text-[14px] text-amber-400">
                <SlidingNumber value={totalQuarantined} suffix=" Nodes" />
              </span>
            </div>
          </div>
        )}
      </div>

      {/* RIGHT: Action buttons */}
      <div className="flex items-center gap-2.5 text-xs shrink-0">
        <AuthBadgeModal key={authVersion} />

        {/* Load Demo — secondary */}
        <button
          onClick={onLoadDemo}
          disabled={isRunning}
          className="h-9 px-3.5 rounded-xl text-xs font-medium border border-[rgba(148,163,184,0.20)] text-text-primary bg-transparent hover:bg-white/[0.04] disabled:opacity-50 transition-colors whitespace-nowrap flex items-center justify-center"
        >
          Load 5-Round Demo
        </button>

        {/* Reset — secondary with icon */}
        <button
          onClick={onReset}
          disabled={isRunning}
          className="h-9 px-3.5 rounded-xl text-xs font-medium border border-[rgba(148,163,184,0.20)] text-text-primary bg-transparent hover:bg-white/[0.04] disabled:opacity-50 transition-colors whitespace-nowrap flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset
        </button>

        {/* Run Secure Round — primary with gradient glow */}
        <button
          onClick={onRunRound}
          disabled={isRunning}
          className={`h-9 px-4 rounded-xl text-xs font-bold text-white flex items-center gap-2 whitespace-nowrap transition-all disabled:opacity-50 disabled:cursor-not-allowed${
            isRunning ? "" : " hover:-translate-y-px"
          }`}
          style={{
            background: "linear-gradient(135deg, #0891b2, #1d4ed8)",
            boxShadow: "0 0 20px rgba(34,211,238,0.25)",
          }}
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
